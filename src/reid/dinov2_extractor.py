import math
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image

class RandomDeckOcclusion:
    def __init__(self, p=0.50, max_deck_coverage=0.35):
        self.p = float(p)
        self.max_deck_coverage = float(max_deck_coverage)

    def apply(self, img_bgr):
        if random.random() > self.p or img_bgr is None:
            return img_bgr
        h, w = img_bgr.shape[:2]
        if h < 10 or w < 10:
            return img_bgr

        out = img_bgr.copy()
        num_blocks = random.randint(1, 3)
        for _ in range(num_blocks):
            occ_w = random.randint(int(w * 0.10), int(w * self.max_deck_coverage))
            occ_h = random.randint(int(h * 0.10), int(h * 0.40))
            x1 = random.randint(0, max(0, w - occ_w))
            y1 = random.randint(0, max(0, int(h * 0.60) - occ_h))
            x2 = min(w, x1 + occ_w)
            y2 = min(h, y1 + occ_h)
            fill_color = (random.randint(40, 180), random.randint(40, 180), random.randint(40, 180))
            cv2.rectangle(out, (x1, y1), (x2, y2), fill_color, -1)
        return out


class ArcFaceHead(nn.Module):
    def __init__(self, in_features=384, num_classes=50, s=30.0, m=0.50):
        super().__init__()
        self.in_features = in_features
        self.num_classes = num_classes
        self.s = s
        self.m = m
        self.weight = nn.Parameter(torch.FloatTensor(num_classes, in_features))
        nn.init.xavier_uniform_(self.weight)

        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)
        self.th = math.cos(math.pi - m)
        self.mm = math.sin(math.pi - m) * m

    def forward(self, embedding, label=None):
        cosine = F.linear(F.normalize(embedding), F.normalize(self.weight))
        if label is None:
            return cosine * self.s

        sine = torch.sqrt(1.0 - torch.clamp(cosine ** 2, 0.0, 1.0))
        phi = cosine * self.cos_m - sine * self.sin_m
        phi = torch.where(cosine > self.th, phi, cosine - self.mm)

        one_hot = torch.zeros(cosine.size(), device=embedding.device)
        one_hot.scatter_(1, label.view(-1, 1).long(), 1.0)
        output = (one_hot * phi) + ((1.0 - one_hot) * cosine)
        output *= self.s
        return output


class DINOv2ReIDExtractor(nn.Module):
    def __init__(self, embedding_dim=384, device='cpu'):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.device = torch.device(device)
        self.deck_occlusion = RandomDeckOcclusion(p=0.30)

        self.backbone = None
        try:
            from transformers import AutoModel
            self.backbone = AutoModel.from_pretrained('facebook/dinov2-small')
            for param in self.backbone.parameters():
                param.requires_grad = False
            self.embedding_dim = self.backbone.config.hidden_size
        except Exception:
            self.backbone = nn.Sequential(
                nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(64, self.embedding_dim, bias=False)
            )

        self.arcface_head = ArcFaceHead(in_features=self.embedding_dim, num_classes=50)
        self.to(self.device)
        self.eval()

    def preprocess_image(self, img_input, apply_occlusion=False):
        if isinstance(img_input, np.ndarray):
            bgr = img_input
            if apply_occlusion:
                bgr = self.deck_occlusion.apply(bgr)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if len(bgr.shape) == 3 and bgr.shape[2] == 3 else bgr
            pil_img = Image.fromarray(rgb)
        else:
            pil_img = img_input

        pil_res = pil_img.resize((224, 224), Image.Resampling.BILINEAR)
        arr = np.array(pil_res).astype(np.float32) / 255.0

        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm_arr = (arr - mean) / std

        tensor = torch.from_numpy(norm_arr.transpose(2, 0, 1)).float()
        return tensor

    def extract_embedding(self, img_input, apply_occlusion=False):
        tensor = self.preprocess_image(img_input, apply_occlusion=apply_occlusion).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.backbone(tensor) if not hasattr(self.backbone, 'config') else self.backbone(pixel_values=tensor)
            if hasattr(outputs, 'last_hidden_state'):
                cls_feat = outputs.last_hidden_state[:, 0]
            elif hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                cls_feat = outputs.pooler_output
            else:
                cls_feat = outputs
            norm_feat = F.normalize(cls_feat, p=2, dim=1)
        return norm_feat.squeeze(0).cpu().numpy()

    def extract_batch(self, list_of_imgs):
        tensors = [self.preprocess_image(img) for img in list_of_imgs]
        batch = torch.stack(tensors).to(self.device)
        with torch.no_grad():
            outputs = self.backbone(batch) if not hasattr(self.backbone, 'config') else self.backbone(pixel_values=batch)
            if hasattr(outputs, 'last_hidden_state'):
                cls_feat = outputs.last_hidden_state[:, 0]
            elif hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                cls_feat = outputs.pooler_output
            else:
                cls_feat = outputs
            norm_feat = F.normalize(cls_feat, p=2, dim=1)
        return norm_feat.cpu().numpy()
