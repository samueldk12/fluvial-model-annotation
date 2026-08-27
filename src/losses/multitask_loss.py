"""
Funções de Perda Multitarefa para Treinamento da VesselPerceptionNet.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiTaskVesselLoss(nn.Module):
    """
    Perda combinada:
    Loss_Total = w_bbox * Loss_BBox + w_cls * Loss_Cls + w_triplet * Loss_Triplet
    """
    def __init__(self, w_bbox=1.0, w_cls=1.0, w_triplet=1.0, triplet_margin=0.3):
        super().__init__()
        self.w_bbox = w_bbox
        self.w_cls = w_cls
        self.w_triplet = w_triplet
        
        self.bbox_loss_fn = nn.SmoothL1Loss()
        self.class_loss_fn = nn.CrossEntropyLoss()
        self.triplet_loss_fn = nn.TripletMarginLoss(margin=triplet_margin, p=2)

    def forward(self, predictions, targets):
        """
        predictions: dict com 'bboxes', 'class_logits'
        targets: dict com 'bbox', 'class_label'
        """
        l_bbox = self.bbox_loss_fn(predictions["bboxes"], targets["bbox"])
        l_cls = self.class_loss_fn(predictions["class_logits"], targets["class_label"])
        
        total_loss = self.w_bbox * l_bbox + self.w_cls * l_cls
        return total_loss, {"loss_bbox": l_bbox.item(), "loss_cls": l_cls.item()}

    def compute_triplet_loss(self, anchor_emb, pos_emb, neg_emb):
        """
        Calcula a perda de tripla para afastar barcos distintos e aproximar o mesmo barco no espaço latente.
        """
        return self.triplet_loss_fn(anchor_emb, pos_emb, neg_emb)
