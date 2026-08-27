"""
VesselPerceptionNet: Arquitetura Neural Modular em PyTorch para Percepção Fluvial e Naval.

Unifica em tensores:
1. Extração de características convolucionais residuais
2. Cabeça de Detecção de Embarcações (Bounding Boxes e Classes)
3. Cabeça de Segmentação Semântica (Máscara Pixel-a-Pixel de Barcos, Rio e Margens)
4. Cabeça de Re-Identificação Única (Embeddings de 512 dimensões com norma unitária L2)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.LeakyReLU(0.1, inplace=True)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        return self.relu(out)

class VesselBackbone(nn.Module):
    """
    Backbone convolucional hierárquico com blocos residuais.
    Entrada:  Tensor [Batch, 3, H, W]
    Saída:    Tensor de Features [Batch, 256, H/16, W/16]
    """
    def __init__(self, in_channels=3, base_channels=32):
        super().__init__()
        # Estágio 1: H/2
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, base_channels, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(base_channels),
            nn.LeakyReLU(0.1, inplace=True)
        )
        
        # Estágio 2: H/4
        self.layer1 = nn.Sequential(
            nn.Conv2d(base_channels, base_channels * 2, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(base_channels * 2),
            nn.LeakyReLU(0.1, inplace=True),
            ResidualBlock(base_channels * 2)
        )
        
        # Estágio 3: H/8
        self.layer2 = nn.Sequential(
            nn.Conv2d(base_channels * 2, base_channels * 4, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(base_channels * 4),
            nn.LeakyReLU(0.1, inplace=True),
            ResidualBlock(base_channels * 4),
            ResidualBlock(base_channels * 4)
        )
        
        # Estágio 4: H/16
        self.layer3 = nn.Sequential(
            nn.Conv2d(base_channels * 4, base_channels * 8, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(base_channels * 8),
            nn.LeakyReLU(0.1, inplace=True),
            ResidualBlock(base_channels * 8)
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.layer1(x)
        x = self.layer2(x)
        features = self.layer3(x) # [B, 256, H/16, W/16]
        return features

class SegmentationHead(nn.Module):
    """
    Cabeça de Segmentação Semântica Pixel-a-Pixel:
    Decodifica o tensor de features para gerar máscaras [B, num_seg_classes, H, W]
    Classes: 0: Fundo/Margem, 1: Água Navegável do Rio, 2: Casco da Embarcação
    """
    def __init__(self, in_channels=256, num_seg_classes=3):
        super().__init__()
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(in_channels, 128, kernel_size=4, stride=2, padding=1), # H/8
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.1, inplace=True),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),   # H/4
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.1, inplace=True),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),    # H/2
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.1, inplace=True),
            nn.ConvTranspose2d(32, num_seg_classes, kernel_size=4, stride=2, padding=1) # H
        )

    def forward(self, features):
        return self.decoder(features)

class DetectionHead(nn.Module):
    """
    Cabeça de Detecção: Prediz caixas delimitadoras normalizadas [cx, cy, w, h],
    confiança do objeto e probabilidades de classe naval.
    """
    def __init__(self, in_features=256, num_classes=10):
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc_shared = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Dropout(0.2)
        )
        self.bbox_head = nn.Sequential(
            nn.Linear(256, 64),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Linear(64, 4),
            nn.Sigmoid()
        )
        self.conf_head = nn.Sequential(
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
        self.class_head = nn.Linear(256, num_classes)

    def forward(self, features):
        pooled = self.pool(features).flatten(1)
        shared = self.fc_shared(pooled)
        bboxes = self.bbox_head(shared)
        conf = self.conf_head(shared)
        class_logits = self.class_head(shared)
        return bboxes, conf, class_logits

class ReIDEmbeddingHead(nn.Module):
    """
    Cabeça de Re-Identificação Única (Vessel Re-ID):
    Extrai um vetor latente de 512 dimensões com normalização L2 unitária.
    """
    def __init__(self, in_features=256, embedding_dim=512):
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.proj = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.LeakyReLU(0.1, inplace=True),
            nn.Linear(512, embedding_dim),
            nn.BatchNorm1d(embedding_dim)
        )

    def forward(self, features):
        pooled = self.pool(features).flatten(1)
        embeddings = self.proj(pooled)
        return F.normalize(embeddings, p=2, dim=1)

class VesselPerceptionNet(nn.Module):
    """
    Rede Neural Completa para Percepção, Segmentação Semântica, Re-ID e Detecção de Embarcações.
    """
    def __init__(self, num_classes=10, embedding_dim=512, num_seg_classes=3):
        super().__init__()
        self.backbone = VesselBackbone(in_channels=3, base_channels=32)
        self.det_head = DetectionHead(in_features=256, num_classes=num_classes)
        self.reid_head = ReIDEmbeddingHead(in_features=256, embedding_dim=embedding_dim)
        self.seg_head = SegmentationHead(in_channels=256, num_seg_classes=num_seg_classes)

    def forward(self, x):
        """
        Entrada:
          x: Tensor [Batch, 3, H, W]
        Retorna:
          dict contendo:
            'bboxes': [B, 4]
            'confidence': [B, 1]
            'class_logits': [B, num_classes]
            'embeddings': [B, embedding_dim]
            'seg_masks': [B, 3, H, W] (Logits de segmentação: Fundo, Água, Barco)
        """
        features = self.backbone(x)
        bboxes, conf, class_logits = self.det_head(features)
        embeddings = self.reid_head(features)
        seg_masks = self.seg_head(features)
        
        return {
            "bboxes": bboxes,              # [B, 4] -> (cx, cy, w, h)
            "confidence": conf,            # [B, 1] -> [0.0 a 1.0]
            "class_logits": class_logits,  # [B, num_classes]
            "embeddings": embeddings,      # [B, embedding_dim] normalizado
            "seg_masks": seg_masks         # [B, 3, H, W]
        }

    def compute_similarity(self, emb1, emb2):
        return torch.sum(emb1 * emb2, dim=-1)
