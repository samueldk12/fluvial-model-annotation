# -*- coding: utf-8 -*-
"""
Gerenciador de Cadastros e Re-ID Isolado por Domínio.
Mantém bases de dados JSON persistentes para cada um dos 7 domínios de visão computacional.
"""

import os
import json
import time
import uuid

DEFAULT_SEEDS = {
    "naval": [
        {"id": "EMB-SAN-01", "name": "MSC Sandra (Porta-Contêineres)", "type": "Carga Geral", "origin": "MANUAL", "sightings": 12, "destination": "Terminal Santos Brasil"},
        {"id": "EMB-SAN-02", "name": "Rebocador Titan VIII", "type": "Rebocador", "origin": "MANUAL", "sightings": 45, "destination": "Canal Principal"},
        {"id": "EMB-SAN-03", "name": "Balsa FB-28 Santos-Guarujá", "type": "Balsa Mista", "origin": "MANUAL", "sightings": 138, "destination": "Travessia Ponta da Praia"}
    ],
    "urbano": [
        {"id": "VEI-SP-8942", "name": "Toyota Corolla Sedan", "type": "Automóvel", "origin": "MANUAL", "sightings": 8, "destination": "Av. Paulista sentido Consolação"},
        {"id": "VEI-SP-1029", "name": "Ônibus Urbano SPTrans (Linha 875A)", "type": "Transporte Coletivo", "origin": "MANUAL", "sightings": 34, "destination": "Corredor Central"},
        {"id": "VEI-SP-4410", "name": "Caminhão VUC Entregas", "type": "Carga Urbana", "origin": "MANUAL", "sightings": 5, "destination": "Rua Bela Cintra"}
    ],
    "fechado": [
        {"id": "USR-IND-104", "name": "Engenheiro de IA (Estação 04)", "type": "Equipe Técnica", "origin": "MANUAL", "sightings": 18, "destination": "Lab de Robótica"},
        {"id": "ATV-IND-002", "name": "Workstation GPU DirectML 01", "type": "Ativo de TI", "origin": "MANUAL", "sightings": 90, "destination": "Rack Central A"},
        {"id": "USR-IND-209", "name": "Supervisor de Operações", "type": "Gestão", "origin": "MANUAL", "sightings": 11, "destination": "Sala de Reuniões 02"}
    ],
    "natureza": [
        {"id": "FAU-NAT-701", "name": "Onça-Pintada (Panthera onca)", "type": "Mamífero Carnívoro", "origin": "MANUAL", "sightings": 4, "destination": "Trilha da Cachoeira"},
        {"id": "FAU-NAT-308", "name": "Tucano-Toco (Ramphastos toco)", "type": "Ave Silvestre", "origin": "MANUAL", "sightings": 27, "destination": "Copa dos Eucaliptos"},
        {"id": "FAU-NAT-115", "name": "Cervo-do-Pantanal (Blastocerus)", "type": "Herbívoro", "origin": "MANUAL", "sightings": 14, "destination": "Bebedouro Norte"}
    ],
    "objetos": [
        {"id": "SKU-IND-7731", "name": "Caixa Master Eletrônicos", "type": "Embalagem Papelão", "origin": "MANUAL", "sightings": 62, "destination": "Esteira de Paletização"},
        {"id": "SKU-IND-9020", "name": "Chave de Impacto Pneumática", "type": "Ferramenta Industrial", "origin": "MANUAL", "sightings": 19, "destination": "Bancada de Montagem 3"},
        {"id": "SKU-IND-3341", "name": "Frasco Polímero 500ml", "type": "Recipiente PET", "origin": "MANUAL", "sightings": 140, "destination": "Linha de Rotulagem"}
    ],
    "tatuagens": [
        {"id": "TAT-BIO-509", "name": "Dragão Oriental com Flor de Lótus", "type": "Braço & Ombro", "origin": "MANUAL", "sightings": 9, "destination": "Catálogo Estilo Oriental"},
        {"id": "TAT-BIO-112", "name": "Caravela & Rosa dos Ventos Old School", "type": "Antebraço", "origin": "MANUAL", "sightings": 15, "destination": "Catálogo Tradicional"},
        {"id": "TAT-BIO-884", "name": "Geometria Sagrada Fine Line", "type": "Costas", "origin": "MANUAL", "sightings": 6, "destination": "Catálogo Blackwork"}
    ],
    "digitais": [
        {"id": "FP-FOR-9041", "name": "Verticilo Espiral (Polegar Direito)", "type": "Papiloscopia Dedo 1", "origin": "MANUAL", "sightings": 22, "destination": "Banco Biométrico AFIS"},
        {"id": "FP-FOR-3312", "name": "Presilha Externa (Indicador Esquerdo)", "type": "Papiloscopia Dedo 7", "origin": "MANUAL", "sightings": 16, "destination": "Banco Biométrico AFIS"},
        {"id": "FP-FOR-7750", "name": "Arco Tenda com Minúcia Composta", "type": "Papiloscopia Dedo 3", "origin": "MANUAL", "sightings": 8, "destination": "Perícia Documental CNH"}
    ]
}

class DomainRegistryManager:
    """Gerencia a base de cadastro e Re-ID para um domínio específico."""

    def __init__(self, project_dir, domain_id="naval"):
        self.project_dir = project_dir
        self.domain_id = domain_id
        self.registries_dir = os.path.join(project_dir, "datasets", "registries")
        os.makedirs(self.registries_dir, exist_ok=True)
        self.file_path = os.path.join(self.registries_dir, f"registry_{domain_id}.json")
        self.items = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Inicializa com seeds padrão
        seeds = DEFAULT_SEEDS.get(self.domain_id, [])
        initial_dict = {item["id"]: item for item in seeds}
        self._save(initial_dict)
        return initial_dict

    def _save(self, data=None):
        if data is None:
            data = self.items
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Registry] Erro ao salvar {self.domain_id}: {e}")

    def get_all(self):
        """Retorna lista de todos os registros ordenados por visualizações."""
        return sorted(list(self.items.values()), key=lambda x: x.get("sightings", 1), reverse=True)

    def register_or_update(self, item_id, name, item_type, origin="AUTO", destination="Em Trânsito", metadata=None):
        """Atualiza ou cadastra automaticamente uma nova entidade detectada."""
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        if item_id in self.items:
            entry = self.items[item_id]
            entry["sightings"] = entry.get("sightings", 1) + 1
            entry["last_seen"] = now_str
            if destination:
                entry["destination"] = destination
            if metadata:
                entry.setdefault("metadata", {}).update(metadata)
        else:
            entry = {
                "id": item_id,
                "name": name,
                "type": item_type,
                "origin": origin,
                "sightings": 1,
                "first_seen": now_str,
                "last_seen": now_str,
                "destination": destination,
                "metadata": metadata or {}
            }
            self.items[item_id] = entry
        
        self._save()
        return entry
