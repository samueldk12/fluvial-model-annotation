"""
Segmentacao real de agua/ceu/obstaculo via eWaSR (ResNet-18), do mesmo grupo
de pesquisa (ViCoS) que publica o LaRS. Pesos: github.com/tersekmatija/eWaSR
(Apache-2.0), MaSTr1325 (ja catalogado neste repositorio).

Substitui as heuristicas de cor/tamanho usadas antes para rejeitar piscina/
doca/predio confundidos com barco: aquelas comparavam estatisticas de cor
da vizinhanca da caixa, e falhavam quando o falso-positivo tinha uma
vizinhanca de agua tao "limpa" quanto a de um barco real (testado: doca
real ao lado de agua deu estatisticas quase identicas a de um barco de
verdade no mesmo canal). Segmentacao pixel-a-pixel nao tem essa ambiguidade:
verifica diretamente se a CAIXA em si esta sobre agua, nao sobre o que a
cerca.
"""

import os
import numpy as np
import cv2
import onnxruntime as ort

_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
_INPUT_W, _INPUT_H = 512, 384
_WATER_CLASS_IDX = 1  # confirmado visualmente: canal 1 = agua nesta ordem de saida do modelo


class WaterSegmenter:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(model_path) if os.path.exists(model_path) else None
        if self.session is None:
            print(f"[WaterSegmenter] Aviso: pesos nao encontrados em '{model_path}', segmentacao de agua desativada.")

    def segment(self, frame_bgr):
        """Retorna uma mascara booleana [H,W] (resolucao original do frame)
        com True nos pixels classificados como agua. None se o modelo nao
        estiver disponivel (chamador deve tratar como 'sem informacao')."""
        if self.session is None:
            return None
        h0, w0 = frame_bgr.shape[:2]
        img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (_INPUT_W, _INPUT_H))
        x = resized.astype(np.float32) / 255.0
        x = (x - _MEAN) / _STD
        x = x.transpose(2, 0, 1)[None, ...].astype(np.float32)

        pred = self.session.run(["prediction"], {"image": x})[0][0]  # [3, H/4, W/4]
        seg_small = np.argmax(pred, axis=0).astype(np.uint8)
        seg_full = cv2.resize(seg_small, (w0, h0), interpolation=cv2.INTER_NEAREST)
        return seg_full == _WATER_CLASS_IDX

    def water_fraction(self, box, water_mask):
        """Fracao de pixels da caixa que sao agua. 1.0 se nao houver mascara
        (nao bloqueia deteccoes quando o segmentador esta indisponivel).

        Cuidado: um casco real preenche boa parte da PROPRIA caixa com
        pixels classificados como 'obstaculo' (e exatamente pra isso que
        serve essa classe - um barco E um obstaculo na agua). Uma caixa
        bem ajustada ao redor de um barco de verdade costuma ter fracao de
        agua BAIXA (~0.15-0.35), nao alta. Por isso e usada com limiar
        baixo, combinada com is_on_water() (que olha a VIZINHANCA)."""
        if water_mask is None:
            return 1.0
        h, w = water_mask.shape[:2]
        x1, y1, x2, y2 = [int(max(0, min(v, w if i % 2 == 0 else h))) for i, v in enumerate(box)]
        if x2 <= x1 or y2 <= y1:
            return 0.0
        region = water_mask[y1:y2, x1:x2]
        if region.size == 0:
            return 0.0
        return float(region.mean())

    def ring_water_fraction(self, box, water_mask, margin=15):
        """Fracao de agua na VIZINHANCA da caixa (anel ao redor, excluindo
        a caixa em si). Um barco flutuando de verdade tem agua aberta dos
        lados; piscina/doca/predio tem estrutura solida do lado, nao agua."""
        if water_mask is None:
            return 1.0
        h, w = water_mask.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in box]
        ex1, ey1 = max(0, x1 - margin), max(0, y1 - margin)
        ex2, ey2 = min(w, x2 + margin), min(h, y2 + margin)
        outer = water_mask[ey1:ey2, ex1:ex2]
        if outer.size == 0:
            return 0.0
        mask = np.ones(outer.shape, dtype=bool)
        iy1, iy2 = max(0, y1 - ey1), max(0, y2 - ey1)
        ix1, ix2 = max(0, x1 - ex1), max(0, x2 - ex1)
        mask[iy1:iy2, ix1:ix2] = False
        ring = outer[mask]
        return float(ring.mean()) if ring.size > 0 else 0.0

    def is_on_water(self, box, water_mask, min_interior=0.15, min_ring=0.60):
        """Regra combinada: aceita se a propria caixa ja tem alguma agua
        (barco flutuando parcialmente cercado) OU se a vizinhanca e
        predominantemente agua aberta (barco pequeno com caixa apertada,
        quase so casco). Rejeita quando nem a caixa nem a vizinhanca tem
        agua significativa (piscina, doca, predio, barco fora d'agua)."""
        if water_mask is None:
            return True
        interior = self.water_fraction(box, water_mask)
        if interior >= min_interior:
            return True
        return self.ring_water_fraction(box, water_mask, margin=15) >= min_ring

    def water_coverage_pct(self, water_mask):
        """Percentual de pixels de agua no frame inteiro (para exibir na UI)."""
        if water_mask is None:
            return None
        return float(water_mask.mean() * 100.0)
