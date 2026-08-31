import os
import json
import numpy as np
import cv2
from PIL import Image
from ultralytics import YOLO
import onnxruntime as ort

from src.utils.water_segmenter import WaterSegmenter
from src.geometry.metric_conversions import NauticalThresholds
from src.detection.weighted_box_fusion import WeightedBoxFusion
from src.detection.tiled_inference import TiledInferenceEngine
from src.detection.confidence_calibrator import ModelConfidenceCalibrator
from src.detection.night_pass import HysteresisNightPass
from src.filtering.temporal_background import TemporalBackgroundSubtractor
from src.filtering.feature_extractor import CandidateFeatureExtractor
from src.filtering.candidate_classifier import CandidateClassifier

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
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area1 = max(1.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    area2 = max(1.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0

def is_plausible_vessel_size(box, max_w=650.0, max_h=280.0, homography=None):
    if homography is not None:
        try:
            dims = homography.box_to_metric_dimensions(box)
            return NauticalThresholds.is_plausible_vessel_metric(dims['length_m'], dims['width_m'], dims.get('area_sqm'))
        except Exception:
            pass
    x1, y1, x2, y2 = box
    return (x2 - x1) <= max_w and (y2 - y1) <= max_h

class MultiDomainVesselDetector:
    def __init__(self, project_dir):
        self.project_dir = project_dir

        sar_path = os.path.join(project_dir, 'models', '02_sar_radar_and_edge', 'MeWan2808_YOLOv8_SAR', 'unquantized', 'best.pt')
        y8naval_path = os.path.join(project_dir, 'models', '01_satellite_and_aerial_naval', 'SixOpen_Y8NavalONNX', 'Y8Naval.onnx')
        y8naval_cfg_path = os.path.join(project_dir, 'models', '01_satellite_and_aerial_naval', 'SixOpen_Y8NavalONNX', 'config.json')
        generic_path = os.path.join(project_dir, 'yolov8n.pt')

        self.sar = YOLO(sar_path) if os.path.exists(sar_path) else None

        self.y8naval_session = None
        self.y8naval_id2label = {}
        if os.path.exists(y8naval_path):
            self.y8naval_session = ort.InferenceSession(y8naval_path)
            if os.path.exists(y8naval_cfg_path):
                with open(y8naval_cfg_path, 'r', encoding='utf-8') as f:
                    self.y8naval_id2label = json.load(f).get('id2label', {})

        self.generic = YOLO(generic_path) if os.path.exists(generic_path) else None

        ewasr_path = os.path.join(project_dir, 'extra_models', 'eWaSR_ResNet18', 'ewasr_resnet18.onnx')
        self.water_segmenter = WaterSegmenter(ewasr_path)

        self.wbf = WeightedBoxFusion(iou_threshold=0.45, skip_box_threshold=0.03)
        self.tiler = TiledInferenceEngine(y_min_ratio=0.20, y_max_ratio=0.65, num_tiles_x=3, overlap_ratio=0.20)
        self.calibrator = ModelConfidenceCalibrator()
        self.night_pass = HysteresisNightPass(enter_thresh=45.0, exit_thresh=65.0)

        self.bg_subtractor = TemporalBackgroundSubtractor()
        self.feature_extractor = CandidateFeatureExtractor()
        self.candidate_classifier = CandidateClassifier()

        loaded = [n for n, m in [('MeWan2808_SAR', self.sar),
                                  ('SixOpen_Y8Naval', self.y8naval_session),
                                  ('COCO_generico(boat+exclusao)', self.generic),
                                  ('eWaSR(segmentacao_agua)', self.water_segmenter.session)] if m is not None]
        print(f'[MultiDomainVesselDetector] Detectores carregados: {loaded}')

    def _detect_yolo(self, model, img_bgr, conf, source_name):
        if model is None:
            return []
        results = model.predict(img_bgr, conf=conf, verbose=False)
        dets = []
        for r in results:
            for b in r.boxes:
                coords = b.xyxy[0].cpu().numpy().tolist()
                dets.append({
                    'box': coords,
                    'conf': float(b.conf[0].item()),
                    'label': 'Embarcacao',
                    'source': source_name
                })
        return dets

    def _detect_generic(self, img_bgr, conf):
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
                        'box': coords,
                        'conf': float(b.conf[0].item()),
                        'label': 'Embarcacao',
                        'source': 'COCO_generico'
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
        raw_out = self.y8naval_session.run(None, {input_name: tensor})[0][0]

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
                'box': [float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])],
                'conf': float(best_scores[mask][i]),
                'label': self.y8naval_id2label.get(str(int(cls_id)), f'Classe_{cls_id}'),
                'source': 'SixOpen_Y8Naval'
            })
        return dets

    def _fuse_by_iou(self, all_dets, iou_thresh=0.35):
        if not all_dets:
            return []
        calibrated = self.calibrator.calibrate_detections(all_dets)
        model_weights = {
            'MeWan2808_SAR_fluvial': 1.2,
            'SixOpen_Y8Naval': 1.1,
            'COCO_generico': 1.0,
            'Night_CLAHE': 1.15
        }
        return self.wbf.fuse(calibrated, model_weights=model_weights)

    def _reject_false_positives(self, boat_dets, distractor_boxes, water_mask, frame_bgr=None):
        if not boat_dets:
            return boat_dets

        if frame_bgr is not None:
            self.bg_subtractor.update(frame_bgr)

        kept = []
        for d in boat_dets:
            temp_diff = 0.50
            if frame_bgr is not None:
                temp_diff = self.bg_subtractor.compute_box_temporal_diff(frame_bgr, d['box'])

            feat_vec, feat_dict = self.feature_extractor.extract_features(d, frame_bgr, water_mask, distractor_boxes, temp_diff)
            classification = self.candidate_classifier.classify(feat_dict)

            if classification['decision'] == 'ACCEPTED':
                d_copy = d.copy()
                d_copy['classifier_probability'] = classification['probability']
                d_copy['features'] = feat_dict
                kept.append(d_copy)

        return kept

    def detect(self, image_input, conf=0.20, iou_thresh=0.35, enable_tiling=True):
        if isinstance(image_input, np.ndarray):
            img_bgr = image_input
        else:
            img_bgr = cv2.cvtColor(np.array(image_input.convert('RGB')), cv2.COLOR_RGB2BGR)

        generic_boats, distractor_boxes = self._detect_generic(img_bgr, conf)

        all_dets = []
        all_dets += self._detect_yolo(self.sar, img_bgr, conf, 'MeWan2808_SAR_fluvial')
        all_dets += self._detect_y8naval(img_bgr, conf)
        all_dets += generic_boats

        if enable_tiling:
            def sar_tiler_fn(crop, conf=conf):
                return self._detect_yolo(self.sar, crop, conf, 'MeWan2808_SAR_fluvial')
            tiled_sar = self.tiler.run_tiled_and_full_inference(img_bgr, sar_tiler_fn, conf=conf)
            all_dets += [d for d in tiled_sar if d.get('is_tiled')]

        night_dets, is_night, _ = self.night_pass.run_night_pass(img_bgr, lambda img, conf=conf: self._detect_yolo(self.sar, img, conf, 'Night_CLAHE'), conf=conf)
        all_dets += night_dets

        fused = self._fuse_by_iou(all_dets, iou_thresh=iou_thresh)
        water_mask = self.water_segmenter.segment(img_bgr)
        return self._reject_false_positives(fused, distractor_boxes, water_mask, frame_bgr=img_bgr)
