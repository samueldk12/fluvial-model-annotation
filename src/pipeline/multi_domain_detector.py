"""
Detector Multi-Dominio de Embarcacoes.

Combina 2 detectores especializados de barco (escolhidos por desempenho
real observado, nao por padrao), cada um cobrindo um dominio visual
diferente:
  - MeWan2808 YOLOv8 SAR (fine-tuned)   -> generalista: funcionou em porto
    otico, radar SAR, rio E na camera aerea ao vivo do Porto de Santos.
  - SixOpen Y8Naval (ONNX, 50 classes)  -> vista aerea/satelite de cima,
    da a categoria naval especifica (Cargo, Dock, classe de navio, etc.)

O terceiro modelo do catalogo (mayrajeo, otimizado so pra camera de porto
em angulo baixo) foi removido: no teste real com a camera ao vivo (vista
aerea/elevada, que e a unica fonte de video usada em producao agora), ele
nao encontrou NENHUM barco em conf=0.05, enquanto os outros dois acharam
varios.

Um terceiro modelo generico (COCO, yolov8n.pt - ja usado para
desambiguacao, nao e download novo) e reaproveitado com DUPLO papel:
  1. FONTE de deteccao de barco tambem: confirmado empiricamente que um
     barco pequeno com esteira, visivel e real, era invisivel para os dois
     especialistas em qualquer confianca (testado ate conf=0.03), mas o
     COCO generico o detectava (conf=0.09-0.22) - os especialistas sao
     overfit aos proprios datasets de treino e nao generalizam para todo
     tipo de embarcacao/angulo.
  2. FILTRO DE EXCLUSAO: rejeita "barco" que na verdade e pessoa/carro/
     caminhao/onibus (classes COCO 0/2/5/7).

Piscina/doca/predio confundidos com barco sao rejeitados por segmentacao
REAL de agua via eWaSR (github.com/tersekmatija/eWaSR, Apache-2.0, mesmo
grupo de pesquisa - ViCoS - que publica o LaRS): se a caixa nao esta
predominantemente sobre pixels classificados como agua, e rejeitada. Isso
substituiu duas heuristicas de cor/tamanho tentadas antes que nao
generalizavam (uma piscina tem textura igual a de um casco real; uma doca
do lado de um barco real tem estatisticas de cor da vizinhanca quase
identicas as do barco).
"""

import os
import json
import numpy as np
import cv2
from ultralytics import YOLO
import onnxruntime as ort
from src.utils.water_segmenter import WaterSegmenter

# Classes do COCO usadas para desambiguacao (nao sao "barco")
_COCO_PERSON = 0
_COCO_CAR = 2
_COCO_BUS = 5
_COCO_TRUCK = 7
_COCO_BOAT = 8
_DISTRACTOR_CLASSES = {_COCO_PERSON, _COCO_CAR, _COCO_BUS, _COCO_TRUCK}


def compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = max(1.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    area2 = max(1.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


def is_plausible_vessel_size(box, max_w=650.0, max_h=280.0):
    """Guarda-corpo bem folgado contra caixas absurdas (ex: um detector
    desregulado cobrindo quase o frame inteiro). NAO E um filtro fino: um
    cap de 170x90px foi usado antes e rejeitava - sem querer - um navio
    cargueiro real bem grande em primeiro plano (caixa de ~500x150px),
    porque uma caixa de doca falsa detectada antes tambem era grande
    (416x201px) e nao existe um limiar de tamanho unico que separe "navio
    grande de verdade" de "doca grande falsa" - os dois podem ocupar a
    mesma faixa de tamanho na tela. Quem faz esse trabalho fino agora e a
    segmentacao de agua (is_on_water); isto aqui so pega casos degenerados."""
    x1, y1, x2, y2 = box
    return (x2 - x1) <= max_w and (y2 - y1) <= max_h


class MultiDomainVesselDetector:
    def __init__(self, project_dir):
        self.project_dir = project_dir

        sar_path = os.path.join(project_dir, "models", "02_sar_radar_and_edge",
                                 "MeWan2808_YOLOv8_SAR", "unquantized", "best.pt")
        y8naval_path = os.path.join(project_dir, "models", "01_satellite_and_aerial_naval",
                                     "SixOpen_Y8NavalONNX", "Y8Naval.onnx")
        y8naval_cfg_path = os.path.join(project_dir, "models", "01_satellite_and_aerial_naval",
                                         "SixOpen_Y8NavalONNX", "config.json")
        generic_path = os.path.join(project_dir, "yolov8n.pt")

        self.sar = YOLO(sar_path) if os.path.exists(sar_path) else None

        self.y8naval_session = None
        self.y8naval_id2label = {}
        if os.path.exists(y8naval_path):
            self.y8naval_session = ort.InferenceSession(y8naval_path)
            if os.path.exists(y8naval_cfg_path):
                with open(y8naval_cfg_path, "r", encoding="utf-8") as f:
                    self.y8naval_id2label = json.load(f).get("id2label", {})

        # COCO generico: fonte extra de deteccao de barco (recall que os
        # especialistas nao tem) E filtro de exclusao pessoa/carro/caminhao/onibus.
        self.generic = YOLO(generic_path) if os.path.exists(generic_path) else None

        ewasr_path = os.path.join(project_dir, "extra_models", "eWaSR_ResNet18", "ewasr_resnet18.onnx")
        self.water_segmenter = WaterSegmenter(ewasr_path)

        loaded = [n for n, m in [("MeWan2808_SAR", self.sar),
                                  ("SixOpen_Y8Naval", self.y8naval_session),
                                  ("COCO_generico(boat+exclusao)", self.generic),
                                  ("eWaSR(segmentacao_agua)", self.water_segmenter.session)] if m is not None]
        print(f"[MultiDomainVesselDetector] Detectores carregados: {loaded}")

    def _detect_yolo(self, model, img_bgr, conf, source_name):
        if model is None:
            return []
        results = model.predict(img_bgr, conf=conf, verbose=False)
        dets = []
        for r in results:
            for b in r.boxes:
                coords = b.xyxy[0].cpu().numpy().tolist()
                dets.append({
                    "box": coords,
                    "conf": float(b.conf[0].item()),
                    "label": "Embarcacao",
                    "source": source_name
                })
        return dets

    def _detect_generic(self, img_bgr, conf):
        """Roda o COCO generico uma vez e separa candidatos de barco dos
        de exclusao (pessoa/carro/caminhao/onibus)."""
        if self.generic is None:
            return [], []
        results = self.generic.predict(img_bgr, conf=conf, verbose=False)
        boat_dets, distractor_boxes = [], []
        for r in results:
            for b in r.boxes:
                cls_id = int(b.cls[0])
                coords = b.xyxy[0].cpu().numpy().tolist()
                if cls_id == _COCO_BOAT:
                    boat_dets.append({
                        "box": coords,
                        "conf": float(b.conf[0].item()),
                        "label": "Embarcacao",
                        "source": "COCO_generico"
                    })
                elif cls_id in _DISTRACTOR_CLASSES:
                    distractor_boxes.append(coords)
        return boat_dets, distractor_boxes

    def _detect_y8naval(self, img_bgr, conf):
        if self.y8naval_session is None:
            return []
        orig_h, orig_w = img_bgr.shape[:2]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (640, 640))
        tensor = (img_resized.astype(np.float32) / 255.0).transpose(2, 0, 1)[None, ...]

        input_name = self.y8naval_session.get_inputs()[0].name
        raw_out = self.y8naval_session.run(None, {input_name: tensor})[0][0]  # (55, 8400): 4 bbox + 50 classes + 1 canal nao usado

        boxes_norm = raw_out[:4, :].T
        class_scores = raw_out[4:54, :].T
        scores = 1.0 / (1.0 + np.exp(-class_scores)) if (class_scores.max() > 1.0 or class_scores.min() < 0.0) else class_scores

        best_classes = np.argmax(scores, axis=1)
        best_scores = np.max(scores, axis=1)
        mask = best_scores >= conf
        if not np.any(mask):
            return []

        gain_x, gain_y = orig_w / 640.0, orig_h / 640.0
        fb = boxes_norm[mask]
        cx, cy, w, h = fb[:, 0] * gain_x, fb[:, 1] * gain_y, fb[:, 2] * gain_x, fb[:, 3] * gain_y
        x1 = np.clip(cx - w / 2.0, 0, orig_w)
        y1 = np.clip(cy - h / 2.0, 0, orig_h)
        x2 = np.clip(cx + w / 2.0, 0, orig_w)
        y2 = np.clip(cy + h / 2.0, 0, orig_h)

        dets = []
        for i, cls_id in enumerate(best_classes[mask]):
            dets.append({
                "box": [float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])],
                "conf": float(best_scores[mask][i]),
                "label": self.y8naval_id2label.get(str(int(cls_id)), f"Classe_{cls_id}"),
                "source": "SixOpen_Y8Naval"
            })
        return dets

    def _fuse_by_iou(self, all_dets, iou_thresh=0.35):
        """Agrupa deteccoes sobrepostas de fontes diferentes (consenso) via
        clustering guloso ordenado por confianca."""
        all_dets = sorted(all_dets, key=lambda d: d["conf"], reverse=True)
        clusters = []
        used = [False] * len(all_dets)

        for i, det in enumerate(all_dets):
            if used[i]:
                continue
            cluster = [det]
            used[i] = True
            for j in range(i + 1, len(all_dets)):
                if used[j]:
                    continue
                if compute_iou(det["box"], all_dets[j]["box"]) > iou_thresh:
                    cluster.append(all_dets[j])
                    used[j] = True
            clusters.append(cluster)

        fused = []
        for cluster in clusters:
            sources = sorted(set(d["source"] for d in cluster))
            best = max(cluster, key=lambda d: d["conf"])
            # Consenso entre fontes distintas aumenta a confianca final (capado em 0.98)
            consensus_bonus = 0.10 * (len(sources) - 1)
            fused.append({
                "box": best["box"],
                "conf": min(0.98, best["conf"] + consensus_bonus),
                "label": best["label"],
                "sources": sources,
                "num_fontes_concordantes": len(sources)
            })
        return fused

    def _reject_false_positives(self, boat_dets, distractor_boxes, water_mask, iou_thresh=0.40):
        """Descarta caixas de barco que na verdade sao pessoa/carro/
        caminhao/onibus (IoU) ou piscina/doca/predio (nem a caixa nem sua
        vizinhanca tem agua real segmentada pelo eWaSR - ver is_on_water)."""
        if not boat_dets:
            return boat_dets

        kept = []
        for d in boat_dets:
            if any(compute_iou(d["box"], db) > iou_thresh for db in distractor_boxes):
                continue
            if not is_plausible_vessel_size(d["box"]):
                continue
            if not self.water_segmenter.is_on_water(d["box"], water_mask):
                continue
            kept.append(d)
        return kept

    def detect(self, pil_image, conf=0.20, iou_thresh=0.35):
        img_bgr = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)

        generic_boats, distractor_boxes = self._detect_generic(img_bgr, conf)

        all_dets = []
        all_dets += self._detect_yolo(self.sar, img_bgr, conf, "MeWan2808_SAR_fluvial")
        all_dets += self._detect_y8naval(img_bgr, conf)
        all_dets += generic_boats

        fused = self._fuse_by_iou(all_dets, iou_thresh=iou_thresh)
        water_mask = self.water_segmenter.segment(img_bgr)
        return self._reject_false_positives(fused, distractor_boxes, water_mask)
