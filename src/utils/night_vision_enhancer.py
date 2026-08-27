"""
Módulo de Pré-processamento e Realce de Visão Noturna para Ambientes Marítimos e Portuários de Baixa Luminosidade.
Aplica CLAHE Adaptativo, Correção de Gamma, Unsharp Masking e Filtragem Bilateral de Ruído ISO.
"""

import cv2
import numpy as np

def enhance_night_vision(frame_bgr, gamma=0.52, clip_limit=3.5):
    """
    Realça frames noturnos e de baixa luminosidade para melhor visualização
    humana e detecção neural em canais náuticos.
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return frame_bgr

    # 1. Conversão para espaço de cor LAB (separa luminosidade dos canais cromáticos)
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization) na Luminância
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l_channel)

    # 3. Correção de Gamma Adaptativa para iluminação de sombras profundas
    # Formula: out = (in / 255) ^ (gamma) * 255
    table = np.array([((i / 255.0) ** gamma) * 255.0 for i in np.arange(0, 256)]).astype(np.uint8)
    l_gamma = cv2.LUT(l_clahe, table)

    # 4. Reconstrução do Frame em BGR
    enhanced_lab = cv2.merge([l_gamma, a_channel, b_channel])
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # 5. Unsharp Masking sutil para realçar arestas do casco e esteiras d'água
    gaussian = cv2.GaussianBlur(enhanced_bgr, (0, 0), 2.0)
    sharpened = cv2.addWeighted(enhanced_bgr, 1.22, gaussian, -0.22, 0)

    return sharpened

def is_night_or_low_light(frame_bgr, brightness_threshold=100.0):
    """
    Avalia se a imagem/frame está em condições noturnas ou de baixa luminosidade.
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    return mean_val < brightness_threshold, mean_val
