"""
Módulo Utilitário de Segmentação Semântica e Panóptica Fluvial com Alpha Blending.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2

def apply_segmentation_overlay(pil_image, seg_mask_tensor=None, bbox=None, class_color=(0, 229, 255), show_water=True):
    """
    Gera a sobreposição de segmentação pixel a pixel:
    - Casco da Embarcação (Máscara precisa com preenchimento colorido translúcido e borda de contorno)
    - Superfície da Água do Rio (Máscara ciano translúcida)
    - Margens / Céu
    """
    orig_w, orig_h = pil_image.size
    img_np = np.array(pil_image.convert("RGBA"))
    overlay = np.zeros_like(img_np, dtype=np.uint8)

    # 1. Se receber tensor de segmentação
    if seg_mask_tensor is not None:
        if hasattr(seg_mask_tensor, "cpu"):
            mask_np = seg_mask_tensor.detach().cpu().numpy()
        else:
            mask_np = seg_mask_tensor

        # Redimensionar para tamanho original
        if mask_np.ndim == 3:
            # Argmax dos 3 canais: 0: Fundo, 1: Água, 2: Barco
            pred_map = np.argmax(mask_np, axis=0)
        else:
            pred_map = mask_np

        pred_map_resized = cv2.resize(pred_map.astype(np.uint8), (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

        # Máscara da Água (Azul Ciano)
        if show_water:
            water_mask = (pred_map_resized == 1)
            overlay[water_mask] = [0, 160, 255, 75] # Ciano translúcido

        # Máscara do Barco (Cor da Classe)
        boat_mask = (pred_map_resized == 2)
        r, g, b = class_color[:3]
        overlay[boat_mask] = [r, g, b, 140]

    # 2. Refinamento de Máscara por Contorno da Caixa Delimitadora
    if bbox is not None:
        cx, cy, bw, bh = bbox[0] * orig_w, bbox[1] * orig_h, bbox[2] * orig_w, bbox[3] * orig_h
        x1, y1 = int(max(0, cx - bw/2)), int(max(0, cy - bh/2))
        x2, y2 = int(min(orig_w, cx + bw/2)), int(min(orig_h, cy + bh/2))

        # Recorte do barco para extração de contorno por limiarização de Otsu/Gradiente
        roi = np.array(pil_image.convert("RGB"))[y1:y2, x1:x2]
        if roi.size > 0:
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
            # Suavização Gaussiana
            blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
            # Limiarização adaptativa
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Criar máscara poligonal da embarcação
            hull_mask = np.zeros((orig_h, orig_w), dtype=np.uint8)
            hull_mask[y1:y2, x1:x2] = thresh

            # Aplicar cor da classe sobre o casco segmentado
            r, g, b = class_color[:3]
            overlay[hull_mask > 0] = [r, g, b, 130]

            # Desenhar Contorno Sólido ao Redor do Casco
            contours, _ = cv2.findContours(hull_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) > 80:
                    cv2.drawContours(overlay, [cnt], -1, (255, 255, 255, 240), 2)

    # 3. Mesclar camada de segmentação com a imagem original
    pil_overlay = Image.fromarray(overlay, mode="RGBA")
    blended = Image.alpha_composite(pil_image.convert("RGBA"), pil_overlay)
    
    return blended.convert("RGB")
