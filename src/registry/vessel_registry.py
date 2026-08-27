"""
Módulo de Banco de Dados Persistente e Registro de Embarcações (Port Vessel Registry).
Suporta cadastro manual e auto-cadastro automático com flag explícita e validação de dimensão de embeddings.
"""

import os
import json
import time
import random
from datetime import datetime
import torch
import torch.nn.functional as F

class PortVesselRegistry:
    def __init__(self, db_path="data/vessel_port_database.json", embeddings_path="data/vessel_embeddings.pt", similarity_threshold=0.80, embedding_dim=768):
        self.db_path = db_path
        self.embeddings_path = embeddings_path
        self.similarity_threshold = similarity_threshold
        self.embedding_dim = embedding_dim
        
        self.vessels = {}
        self.embedding_tensor = None
        self.vessel_id_list = []
        
        self.load_database()

    def load_database(self):
        """Carrega a base de dados do disco se existir e valida compatibilidade dimensional."""
        if os.path.exists(self.db_path) and os.path.exists(self.embeddings_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.vessels = json.load(f)
                loaded_data = torch.load(self.embeddings_path, map_location="cpu")
                emb = loaded_data["embeddings"]
                
                # Validação de compatibilidade dimensional (ex: 768D vs legado 512D)
                if emb is not None and emb.shape[1] != self.embedding_dim:
                    print(f"[BD Porto] Dimensão dos embeddings incompatível ({emb.shape[1]}D != {self.embedding_dim}D). Recriando base limpa...")
                    self.vessels = {}
                    self.embedding_tensor = None
                    self.vessel_id_list = []
                else:
                    self.embedding_tensor = emb
                    self.vessel_id_list = loaded_data["vessel_ids"]
                    print(f"[BD Porto] Base carregada com sucesso: {len(self.vessels)} embarcações cadastradas ({self.embedding_dim}D).")
            except Exception as e:
                print(f"[BD Porto] Aviso ao carregar base: {e}. Iniciando nova base.")
                self.vessels = {}
                self.embedding_tensor = None
                self.vessel_id_list = []
        else:
            self.vessels = {}
            self.embedding_tensor = None
            self.vessel_id_list = []

    def save_database(self):
        """Salva os metadados em JSON e os tensores de embeddings em arquivo PyTorch .pt."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.embeddings_path), exist_ok=True)
        
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.vessels, f, indent=2, ensure_ascii=False)
            
        if self.embedding_tensor is not None:
            torch.save({
                "embeddings": self.embedding_tensor,
                "vessel_ids": self.vessel_id_list
            }, self.embeddings_path)

    def register_vessel(self, vessel_id, name, vessel_type, plate_imo, embedding_tensor, port_location="Porto Principal", automatic=False, cargo_type="Carga Geral"):
        """
        Cadastra uma nova embarcação no banco de dados do porto.
        automatic: boolean indicando se o cadastro foi realizado automaticamente pelo sistema de IA.
        """
        if embedding_tensor.dim() == 1:
            embedding_tensor = embedding_tensor.unsqueeze(0)
            
        norm_emb = F.normalize(embedding_tensor.detach().cpu(), p=2, dim=1)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.vessels[vessel_id] = {
            "vessel_id": vessel_id,
            "name": name,
            "type": vessel_type,
            "cargo_type": cargo_type,
            "plate_imo": plate_imo,
            "cadastrado_automaticamente": automatic,
            "metodo_cadastro": "AUTO_REID_DETECTION" if automatic else "CADASTRO_MANUAL_OPERADOR",
            "first_registered": now_str,
            "last_seen": now_str,
            "total_visits": 1,
            "visit_history": [
                {
                    "timestamp": now_str,
                    "port": port_location,
                    "event": "CADASTRO_AUTOMATICO" if automatic else "CADASTRO_INICIAL"
                }
            ]
        }

        # Atualizar tensor mestre de busca
        if self.embedding_tensor is None:
            self.embedding_tensor = norm_emb
            self.vessel_id_list = [vessel_id]
        else:
            self.embedding_tensor = torch.cat([self.embedding_tensor, norm_emb], dim=0)
            self.vessel_id_list.append(vessel_id)

        self.save_database()
        origem = "AUTOMATICA" if automatic else "MANUAL"
        print(f"[CADASTRO {origem}] Embarcação '{name}' (ID: {vessel_id} | Modelo: {vessel_type}) registrada com sucesso no porto!")
        return self.vessels[vessel_id]

    def identify_or_auto_register(self, query_embedding, predicted_type, cargo_category="Carga Geral", current_port="Porto Principal", heading_deg=None):
        """
        Consulta o banco. Se a embarcação for reconhecida, retorna os dados e incrementa a visita.
        Se NÃO for reconhecida, realiza o AUTO-CADASTRO com flag cadastrado_automaticamente=True.
        """
        if query_embedding.dim() == 1:
            query_embedding = query_embedding.unsqueeze(0)
            
        norm_query = F.normalize(query_embedding.detach().cpu(), p=2, dim=1)
        best_score = 0.0

        # 1. Se houver barcos cadastrados, calcula a similaridade de cosseno
        if self.embedding_tensor is not None and len(self.vessel_id_list) > 0 and self.embedding_tensor.shape[1] == norm_query.shape[1]:
            similarities = torch.mm(norm_query, self.embedding_tensor.t()).squeeze(0)
            best_score_t, best_idx = torch.max(similarities, dim=0)
            best_score = best_score_t.item()
            best_vessel_id = self.vessel_id_list[best_idx.item()]

            if best_score >= self.similarity_threshold:
                vessel = self.vessels[best_vessel_id]
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                vessel["last_seen"] = now_str
                vessel["total_visits"] += 1
                
                visit_record = {
                    "timestamp": now_str,
                    "port": current_port,
                    "similarity_score": round(best_score, 4),
                    "heading_deg": round(heading_deg, 1) if heading_deg is not None else None,
                    "event": "RETOQUE_REIDENTIFICADO"
                }
                vessel["visit_history"].append(visit_record)
                self.save_database()
                return {
                    "status": "RE_IDENTIFICADO",
                    "is_new": False,
                    "vessel": vessel,
                    "similarity": round(best_score, 4)
                }

        # 2. Se NÃO reconheceu (Barco Novo Desconhecido) -> Auto-cadastro com flag automática
        random_suffix = random.randint(1000, 9999)
        auto_id = f"AUTO-BR-{random_suffix}"
        auto_name = f"Embarcação Não Registrada {auto_id}"
        auto_imo = f"AUTO-IMO-{random.randint(1000000, 9999999)}"

        new_vessel = self.register_vessel(
            vessel_id=auto_id,
            name=auto_name,
            vessel_type=predicted_type,
            plate_imo=auto_imo,
            embedding_tensor=norm_query,
            port_location=current_port,
            automatic=True,
            cargo_type=cargo_category
        )

        return {
            "status": "AUTO_CADASTRADO_NOVO",
            "is_new": True,
            "vessel": new_vessel,
            "similarity": round(best_score, 4)
        }
