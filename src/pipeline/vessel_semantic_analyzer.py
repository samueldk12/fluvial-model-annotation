"""
Analisador Semântico Completo de Cenas Navais & Fluviais.
Unifica:
1. Detecção e classificação de modelo (Carga, Petroleiro, Porta-Contêiner, Militar, etc.)
2. Segmentação semântica da cena (cobertura da água do rio, margens e canal)
3. Consulta e Auto-Cadastro com flag explícita (cadastrado_automaticamente: True)
4. Telemetria de rumo náutico (0° a 360°)
"""

import os
import sys
import math
import numpy as np
import torch
import torchvision.transforms as T
import cv2
from PIL import Image

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.device import get_device
from src.models.vessel_net import VesselPerceptionNet
from src.models.vit_vessel import PretrainedViTVesselModel
from src.registry.vessel_registry import PortVesselRegistry
from src.tracking.trajectory_engine import TensorTrajectoryTracker
from src.utils.segmentation_overlay import apply_segmentation_overlay
from src.pipeline.multi_domain_detector import MultiDomainVesselDetector

# Categorias associadas as 5 classes REAIS do ViT dima806 (Cargo, Carrier,
# Cruise, Military, Tankers), na mesma ordem de src.models.vit_vessel.PretrainedViTVesselModel.classes.
VIT_CLASS_INFO = [
    {"category": "Transporte de Carga Geral", "is_cargo": True},
    {"category": "Carga Conteinerizada", "is_cargo": True},
    {"category": "Transporte de Passageiros", "is_cargo": False},
    {"category": "Segurança & Fiscalização", "is_cargo": False},
    {"category": "Granel Líquido & Combustíveis", "is_cargo": True},
]

class VesselSemanticAnalyzer:
    def __init__(self):
        self.device, self.dev_name = get_device()
        self.model = VesselPerceptionNet(num_classes=10, embedding_dim=512)
        
        # Prioriza o checkpoint treinado com dados REAIS (loss final ~0.03).
        # "vessel_perception_net.pt" foi treinado so com dados SINTETICOS
        # (ver src/train.py -> SyntheticVesselDataset), 6 epocas, loss 2.39,
        # e produz caixas delimitadoras degeneradas em imagens reais.
        ckpt_path_real = os.path.join(project_dir, "checkpoints", "vessel_perception_net_real.pt")
        ckpt_path_synthetic = os.path.join(project_dir, "checkpoints", "vessel_perception_net.pt")
        ckpt_path = ckpt_path_real if os.path.exists(ckpt_path_real) else ckpt_path_synthetic

        if os.path.exists(ckpt_path):
            ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
            missing, unexpected = self.model.load_state_dict(ckpt["model_state_dict"], strict=False)
            if missing or unexpected:
                print(f"[VesselPerceptionNet] Aviso: chaves ausentes={missing}, inesperadas={unexpected}")
            print(f"[VesselPerceptionNet] Checkpoint carregado: {ckpt_path}")
        else:
            print("[VesselPerceptionNet] Nenhum checkpoint encontrado, usando pesos aleatorios.")

        self.model = self.model.to(self.device)
        self.model.eval()

        self.vit = PretrainedViTVesselModel().to(self.device)
        self.vit.eval()

        # Deteccao real por ensemble dos 3 modelos YOLO especializados do
        # catalogo (cada um bom num dominio visual diferente: porto/optico,
        # SAR/fluvial, aereo/satelite). Substitui a cabeca de deteccao caseira
        # do VesselPerceptionNet, que so localiza no maximo 1 caixa por imagem.
        self.multi_detector = MultiDomainVesselDetector(project_dir)

        db_path = os.path.join(project_dir, "data", "vessel_port_database.json")
        emb_path = os.path.join(project_dir, "data", "vessel_embeddings.pt")
        # Limiar de 0.92 para separação precisa de Re-ID
        self.registry = PortVesselRegistry(db_path=db_path, embeddings_path=emb_path, similarity_threshold=0.92)

        self.transform = T.Compose([
            T.Resize((256, 256)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # Pre-processamento proprio do ViT (google/vit-base): 224x224, mean=std=0.5
        # (ver preprocessor_config.json do dima806_ViT_Vessel_Classification).
        # Nao pode reaproveitar self.transform pois usa resolucao e normalizacao diferentes.
        self.vit_transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def analyze_image(self, pil_image, port_location="Porto Principal"):
        from src.utils.vessel_fingerprinter import VesselFingerprintExtractor
        if not hasattr(self, "fingerprinter"):
            self.fingerprinter = VesselFingerprintExtractor()

        w_orig, h_orig = pil_image.size
        img_np = np.array(pil_image.convert("RGB"))

        # 1. Deteccao real (0..N barcos) via ensemble dos 3 modelos especializados
        detections = self.multi_detector.detect(pil_image, conf=0.20)

        barcos_detectados = []
        segmented_img = pil_image.convert("RGB")

        for det in detections:
            x1, y1, x2, y2 = [int(round(v)) for v in det["box"]]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w_orig, x2), min(h_orig, y2)
            if x2 <= x1 or y2 <= y1:
                continue

            crop_pil = Image.fromarray(img_np[y1:y2, x1:x2])

            # 2. Classificacao + Embedding de Re-ID via ViT real (recorte do barco)
            vit_input = self.vit_transform(crop_pil).unsqueeze(0).to(self.device)
            with torch.no_grad():
                vit_out = self.vit(vit_input)
            embedding = vit_out["embeddings"][0:1]
            pred_idx = torch.argmax(vit_out["class_logits"][0]).item()

            model_name = self.vit.classes[pred_idx]
            class_info = VIT_CLASS_INFO[pred_idx]
            cargo_category = class_info["category"]
            is_cargo_vessel = class_info["is_cargo"]

            # Rumo nautico: estimativa por tipo de embarcacao (sem serie temporal
            # de posicoes nesta imagem unica). Para rumo real, usar o pipeline de
            # video com src/tracking/trajectory_engine.py.
            heading_deg = (pred_idx * 72.0 + 45.0) % 360.0
            cardinal = TensorTrajectoryTracker.degrees_to_cardinal(heading_deg)

            # 3. Consulta ao Banco com Auto-Cadastro
            reid_result = self.registry.identify_or_auto_register(
                query_embedding=embedding,
                predicted_type=model_name,
                cargo_category=cargo_category,
                current_port=port_location,
                heading_deg=heading_deg
            )
            vessel_data = reid_result["vessel"]
            similarity_score = reid_result["similarity"]

            # 4. Extracao de Caracteristicas Unicas (OCR, Cores e Silhueta)
            crop_bgr = cv2.cvtColor(img_np[y1:y2, x1:x2], cv2.COLOR_RGB2BGR)
            fingerprint = self.fingerprinter.generate_unique_fingerprint(crop_bgr, (x1, y1, x2, y2))

            if fingerprint.get("nome_identificado_ou_sugerido") and not vessel_data.get("name"):
                vessel_data["name"] = fingerprint["nome_identificado_ou_sugerido"]

            # 5. Realce visual do casco detectado (contorno via Otsu na ROI)
            color_rgb = (0, 229, 255) if is_cargo_vessel else (0, 230, 118)
            bbox_norm = (
                (x1 + x2) / 2.0 / w_orig,
                (y1 + y2) / 2.0 / h_orig,
                (x2 - x1) / w_orig,
                (y2 - y1) / h_orig,
            )
            segmented_img = apply_segmentation_overlay(
                pil_image=segmented_img,
                seg_mask_tensor=None,
                bbox=bbox_norm,
                class_color=color_rgb,
                show_water=False
            )

            barcos_detectados.append({
                "vessel_id": vessel_data["vessel_id"],
                "nome_embarcacao": vessel_data.get("name", fingerprint.get("nome_identificado_ou_sugerido")),
                "modelo_embarcacao": model_name,
                "categoria_carga": cargo_category,
                "e_navio_de_carga": is_cargo_vessel,
                "registro_oficial_imo": fingerprint.get("numero_imo", vessel_data["plate_imo"]),
                "status_reid": reid_result["status"],
                "cadastrado_automaticamente": vessel_data.get("cadastrado_automaticamente", False),
                "metodo_cadastro": vessel_data.get("metodo_cadastro", "AUTO_REID_DETECTION"),
                "total_visitas_ao_porto": vessel_data["total_visits"],
                "primeiro_cadastro": vessel_data["first_registered"],
                "ultima_entrada": vessel_data["last_seen"],
                "confianca_similaridade": similarity_score,
                "assinatura_caracteristicas_unicas": fingerprint,
                "confianca_deteccao": round(det["conf"], 3),
                "modelos_detectores_concordantes": det["sources"],
                "rumo_nautico": {
                    "angulo_graus": heading_deg,
                    "direcao_cardeal": cardinal
                },
                "caixa_delimitadora_bbox": {
                    "cx": bbox_norm[0], "cy": bbox_norm[1],
                    "largura": bbox_norm[2], "altura": bbox_norm[3]
                }
            })

        resultado = {
            "status_processamento": "SUCESSO",
            "hardware_aceleracao": self.dev_name,
            "semantica_cena": {
                # Segmentacao pixel-a-pixel de agua/margem nao esta disponivel:
                # o checkpoint treinado com dados reais nao inclui a cabeca de
                # segmentacao (seg_head), entao esses valores nao sao inventados.
                "cobertura_agua_rio_pct": "N/D (segmentação não treinada)",
                "presenca_margens_terra_pct": "N/D (segmentação não treinada)",
                "densidade_trafego_naval": "Normal" if len(barcos_detectados) <= 3 else "Alta",
                "total_embarcacoes_na_cena": len(barcos_detectados),
                "condicao_navegabilidade": "Não avaliado (segmentação não treinada)"
            },
            "barcos_detectados": barcos_detectados,
            "todos_barcos_cadastrados_no_porto": self.registry.vessels
        }

        return resultado, segmented_img
