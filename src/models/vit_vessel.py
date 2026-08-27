"""
Módulo de Visão Transformer Pré-Treinado para Re-Identificação e Classificação Naval (dima806 ViT).
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import ViTForImageClassification, ViTConfig

_DEFAULT_MODEL_DIR = os.path.join(
    "models", "03_vessel_transformers", "dima806_ViT_Vessel_Classification"
)

class PretrainedViTVesselModel(nn.Module):
    """
    Vision Transformer pré-treinado (google/vit-base-patch16-224, 12 camadas,
    hidden_size=768) com cabeça de classificação de 5 classes navais:
    ['Cargo', 'Carrier', 'Cruise', 'Military', 'Tankers'].

    Carrega o backbone COMPLETO (embeddings de patch + 12 blocos de
    self-attention + layernorm) a partir do model.safetensors local, e não
    apenas a cabeça classificadora. Requer entrada [B, 3, 224, 224]
    normalizada com mean=std=0.5 (ver preprocessor_config.json do modelo).
    """
    def __init__(self, model_dir=_DEFAULT_MODEL_DIR):
        super().__init__()
        self.classes = ["Cargueiro (Cargo)", "Porta-Contêiner (Carrier)", "Navio de Cruzeiro / Passageiros", "Embarcação Militar / Patrulha", "Petroleiro (Tanker)"]

        if os.path.isdir(model_dir) and os.path.exists(os.path.join(model_dir, "model.safetensors")):
            self.vit = ViTForImageClassification.from_pretrained(model_dir)
            print(f"[ViT Naval] Backbone ViT-Base completo (12 camadas) carregado de '{model_dir}'.")
        else:
            print(f"[ViT Naval] Aviso: pesos nao encontrados em '{model_dir}', usando ViT-Base com inicializacao aleatoria.")
            self.vit = ViTForImageClassification(ViTConfig(num_labels=5))

    def forward(self, x):
        """
        Entrada: Tensor [B, 3, 224, 224] (normalizado com mean=std=0.5)
        Retorna:
          embeddings: [B, 768] (token CLS do backbone, normalizado L2 para Re-ID)
          class_logits: [B, 5]
        """
        backbone_out = self.vit.vit(pixel_values=x)
        cls_token = backbone_out.last_hidden_state[:, 0]
        logits = self.vit.classifier(cls_token)
        embeddings_norm = F.normalize(cls_token, p=2, dim=1)

        return {
            "embeddings": embeddings_norm,
            "class_logits": logits
        }
