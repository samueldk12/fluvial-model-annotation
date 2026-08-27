"""
Motor de Ensemble Neural com Votação Estrita por Consenso.
Elimina falsos positivos de ondas/reflexos exigindo estrutura real de borda
(Laplaciano) e cruza visão normal x realce noturno.

IMPORTANTE: a deteccao em si usa os 3 modelos especializados do catalogo
(MultiDomainVesselDetector: mayrajeo/optico-porto, MeWan2808/SAR-fluvial,
SixOpen/aereo-satelite), nao um unico YOLO. Confirmado empiricamente que a
camera ao vivo do Porto de Santos (vista elevada/aerea) tem barcos reais que
o mayrajeo sozinho NUNCA detecta (0 caixas mesmo em conf=0.05), mas que o
SixOpen (treinado em imagens aereas) e o MeWan2808 encontram sem problema.
"""

import cv2
import numpy as np
import torch
import math
from PIL import Image
from src.utils.night_vision_enhancer import is_night_or_low_light

class VesselEnsembleEngine:
    def __init__(self, yolo_model, vit_analyzer):
        self.yolo = yolo_model
        self.analyzer = vit_analyzer

        # Usa o detector multi-dominio (3 modelos) ja carregado dentro do
        # VesselSemanticAnalyzer, em vez de depender de um unico modelo YOLO
        # que so cobre uma fatia estreita de condicoes de camera.
        self.multi_detector = getattr(vit_analyzer, "multi_detector", None)
        if self.multi_detector is None:
            print("[VesselEnsembleEngine] AVISO: multi_detector nao encontrado no analyzer; usando apenas o YOLO unico como fallback.")

        # O indice de classe "boat" varia conforme o modelo YOLO carregado:
        # no COCO generico (80 classes) 'boat' e o indice 8, mas em modelos
        # fine-tuned (ex: mayrajeo, classe unica) 'boat' costuma ser o indice 0.
        # So relevante para o fallback de modelo unico.
        names = getattr(yolo_model, "names", {}) or {}
        boat_ids = [idx for idx, name in names.items() if "boat" in str(name).lower() or "vessel" in str(name).lower() or "ship" in str(name).lower()]
        self.target_classes = boat_ids if boat_ids else None

    def compute_iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = max(1.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
        area2 = max(1.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
        union = area1 + area2 - inter
        return inter / union if union > 0 else 0.0

    def _prior_boost(self, box, position_priors):
        """"Se ali tinha um barco no frame anterior, um barco fraco no
        mesmo lugar agora ganha mais forca": se o centro da caixa cai
        dentro do raio de alguma posicao esperada (memoria espacial),
        retorna um bonus de confianca. Sem isso, uma deteccao fraca mas
        correta perto de um barco ja confirmado era descartada do mesmo
        jeito que um falso positivo isolado - mas o contexto temporal diz
        que ali e MAIS provavel ser um barco de verdade, nao menos."""
        if not position_priors:
            return 0.0
        cx = (box[0] + box[2]) / 2.0
        cy = (box[1] + box[3]) / 2.0
        for p in position_priors:
            dist = math.hypot(cx - p["cx"], cy - p["cy"])
            if dist < p["radius"]:
                return 0.15
        return 0.0

    def evaluate_edge_contrast(self, frame_bgr, bbox):
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        h, w = frame_bgr.shape[:2]
        crop = frame_bgr[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
        if crop.size == 0:
            return 0.30

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
        return min(0.95, max(0.20, laplacian / 250.0))

    def _detect_pass(self, frame_bgr, height, conf, min_w, min_h):
        """Roda o detector multi-dominio (ou fallback single-model) e aplica
        os filtros de tamanho minimo e faixa vertical da calha."""
        raw = []
        if self.multi_detector is not None:
            pil_img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            for d in self.multi_detector.detect(pil_img, conf=conf):
                raw.append({"bbox": d["box"], "conf": d["conf"], "sources": d["sources"]})
        else:
            res = self.yolo.predict(frame_bgr, conf=conf, classes=self.target_classes, verbose=False)
            for r in res:
                for b in r.boxes:
                    raw.append({"bbox": b.xyxy[0].cpu().numpy().tolist(), "conf": float(b.conf[0].item()), "sources": ["yolo_unico"]})

        # Faixa vertical bem larga (5%-97% da altura): a original (22%-76%)
        # foi calibrada so para o video gravado de camera fechada, onde o
        # canal ocupa a faixa central. Numa camera aerea/elevada como a ao
        # vivo do Porto de Santos, barcos atracados no cais aparecem perto
        # da base do frame (fora daquela faixa) e eram descartados mesmo
        # sendo deteccoes reais e validas.
        filtered = []
        for d in raw:
            x1, y1, x2, y2 = d["bbox"]
            bw = x2 - x1
            bh = y2 - y1
            cy = (y1 + y2) / 2.0
            if (height * 0.05 < cy < height * 0.97) and bw >= min_w and bh >= min_h:
                filtered.append(d)
        return filtered

    def run_ensemble(self, raw_frame_bgr, enhanced_night_bgr, height, width, position_priors=None):
        """
        Executa a inferência multi-dominio e realiza a VOTAÇÃO POR CONSENSO
        entre visao normal e realce noturno.

        position_priors: lista opcional de {"cx","cy","radius"} vinda de
        VesselSpatialMemoryTracker.get_active_position_priors() - reforca
        deteccoes fracas proximas de onde ja se sabia que tinha barco.
        """
        # Limiares recalibrados: modelos individuais dao confianca de so
        # 0.10-0.30 para barcos pequenos/distantes REAIS nesta camera
        # (confirmado amostrando frames: as mesmas caixas aparecem quase no
        # mesmo lugar em frames bem distantes entre si - nao e ruido). Quem
        # filtra ruido/reflexo agora e o evaluate_edge_contrast (estrutura
        # real vs. reflexo liso), nao mais um piso de confianca alto.
        DETECT_CONF = 0.12
        MIN_BOX_W, MIN_BOX_H = 10, 6

        normal_detections = self._detect_pass(raw_frame_bgr, height, DETECT_CONF, MIN_BOX_W, MIN_BOX_H)

        # So roda a passada noturna (e exige consenso day/night) quando a
        # cena REALMENTE esta escura. Aplicar o realce noturno numa cena de
        # dia claro distorce a imagem sem necessidade e, na pratica, reduzia
        # deteccoes reais: um frame diurno com 7 barcos reais encontrados na
        # passada normal caia para 1 so por causa da checagem cruzada inutil
        # contra a versao "noturna" de uma imagem que ja estava clara.
        is_dark, _brightness = is_night_or_low_light(raw_frame_bgr)
        night_detections = self._detect_pass(enhanced_night_bgr, height, DETECT_CONF, MIN_BOX_W, MIN_BOX_H) if is_dark else []

        fused_vessels = []
        visited_night = set()

        # Cruzamento e Votação por Consenso entre passada normal e noturna
        for n_det in normal_detections:
            n_box = n_det["bbox"]
            conf_norm = n_det["conf"]
            matched_night = None
            matched_idx = None

            for i, n_night in enumerate(night_detections):
                if i in visited_night:
                    continue
                if self.compute_iou(n_box, n_night["bbox"]) > 0.35:
                    matched_night = n_night
                    matched_idx = i
                    break

            if matched_night is not None:
                visited_night.add(matched_idx)
                conf_night = matched_night["conf"]

                w_norm = conf_norm / (conf_norm + conf_night)
                w_night = conf_night / (conf_norm + conf_night)
                fused_box = [
                    w_norm * n_box[0] + w_night * matched_night["bbox"][0],
                    w_norm * n_box[1] + w_night * matched_night["bbox"][1],
                    w_norm * n_box[2] + w_night * matched_night["bbox"][2],
                    w_norm * n_box[3] + w_night * matched_night["bbox"][3],
                ]

                score_final = 0.50 * conf_norm + 0.50 * conf_night
                vencedor = "VISÃO NOTURNA" if conf_night > conf_norm else "VISÃO NORMAL"
                delta_str = f"+{abs(conf_night - conf_norm)*100:.1f}% ({vencedor})"
            else:
                conf_night = 0.0
                fused_box = n_box
                score_final = conf_norm
                vencedor = "VISÃO NORMAL"
                delta_str = f"{conf_norm*100:.1f}% Normal"

            # Rejeita reflexos/ondas: um casco real tem bordas estruturais
            # nitidas (variancia alta do Laplaciano); reflexo de luz na agua
            # e tipicamente liso/borrado.
            edge_score = self.evaluate_edge_contrast(raw_frame_bgr, fused_box)
            boost = self._prior_boost(fused_box, position_priors)
            score_boosted = min(0.98, score_final + boost)
            if score_boosted >= 0.15 and edge_score >= 0.35:
                fused_vessels.append({
                    "bbox": fused_box,
                    "conf_normal": conf_norm,
                    "conf_night": conf_night,
                    "canal_mais_confiavel": vencedor,
                    "vantagem_confiabilidade": delta_str,
                    "score_ensemble_final": float(score_boosted),
                    "edge_score": round(edge_score, 3),
                    "fontes_detectoras": n_det["sources"],
                    "reforcado_por_memoria": boost > 0
                })

        # Adicionar detecções noturnas sem par na passada normal
        for i, n_night in enumerate(night_detections):
            if i in visited_night:
                continue
            conf_night = n_night["conf"]
            boost = self._prior_boost(n_night["bbox"], position_priors)
            score_boosted = min(0.98, conf_night + boost)
            if score_boosted < 0.20:
                continue
            edge_score = self.evaluate_edge_contrast(raw_frame_bgr, n_night["bbox"])
            if edge_score < 0.35:
                continue
            fused_vessels.append({
                "bbox": n_night["bbox"],
                "conf_normal": 0.0,
                "conf_night": conf_night,
                "canal_mais_confiavel": "VISÃO NOTURNA",
                "vantagem_confiabilidade": f"{conf_night*100:.1f}% Noturna (Alta Confiança)",
                "score_ensemble_final": float(score_boosted),
                "edge_score": round(edge_score, 3),
                "fontes_detectoras": n_night["sources"],
                "reforcado_por_memoria": boost > 0
            })

        return fused_vessels
