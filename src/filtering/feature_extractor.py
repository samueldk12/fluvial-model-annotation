import cv2
import numpy as np

class CandidateFeatureExtractor:
    FEATURE_NAMES = [
        'conf_calib',
        'num_sources_norm',
        'is_sar_source',
        'is_y8naval_source',
        'is_coco_source',
        'is_night_source',
        'water_interior_frac',
        'water_ring_frac',
        'laplacian_var_norm',
        'temporal_diff_score',
        'distractor_max_iou',
        'box_area_norm',
        'box_aspect_ratio_norm',
        'metric_length_norm',
        'metric_width_norm',
        'metric_area_norm',
        'y_center_norm'
    ]

    def __init__(self, homography=None):
        self.homography = homography

    @staticmethod
    def _compute_iou(box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        area1 = max(1.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
        area2 = max(1.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
        union = area1 + area2 - inter
        return inter / union if union > 0 else 0.0

    def compute_water_fractions(self, box, water_mask):
        if water_mask is None or water_mask.size == 0:
            return 0.50, 0.50

        mh, mw = water_mask.shape[:2]
        x1, y1, x2, y2 = [int(round(v)) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(mw, x2), min(mh, y2)

        if x2 <= x1 or y2 <= y1:
            return 0.0, 0.0

        interior_crop = water_mask[y1:y2, x1:x2]
        interior_frac = float(np.mean(interior_crop > 0)) if interior_crop.size > 0 else 0.0

        margin_x = max(4, int(round((x2 - x1) * 0.25)))
        margin_y = max(4, int(round((y2 - y1) * 0.25)))
        rx1 = max(0, x1 - margin_x)
        ry1 = max(0, y1 - margin_y)
        rx2 = min(mw, x2 + margin_x)
        ry2 = min(mh, y2 + margin_y)

        ring_region = water_mask[ry1:ry2, rx1:rx2]
        ring_mask = np.ones(ring_region.shape, dtype=bool)
        rel_y1 = y1 - ry1
        rel_y2 = y2 - ry1
        rel_x1 = x1 - rx1
        rel_x2 = x2 - rx1
        ring_mask[rel_y1:rel_y2, rel_x1:rel_x2] = False

        ring_pixels = ring_region[ring_mask]
        ring_frac = float(np.mean(ring_pixels > 0)) if ring_pixels.size > 0 else interior_frac
        return interior_frac, ring_frac

    @staticmethod
    def compute_laplacian_var(frame_bgr, box):
        if frame_bgr is None or frame_bgr.size == 0:
            return 0.50
        h, w = frame_bgr.shape[:2]
        x1, y1, x2, y2 = [int(round(v)) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return 0.0
        crop = frame_bgr[y1:y2, x1:x2]
        if crop.shape[0] > 128 or crop.shape[1] > 128:
            crop = cv2.resize(crop, (64, 64))
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(np.clip(var / 300.0, 0.0, 1.0))

    def extract_features(self, candidate, frame_bgr, water_mask, distractor_boxes, temporal_diff_score=0.50):
        h, w = frame_bgr.shape[:2] if frame_bgr is not None else (720, 1280)
        box = candidate['box']
        x1, y1, x2, y2 = box
        bw = max(1.0, x2 - x1)
        bh = max(1.0, y2 - y1)

        conf = float(candidate.get('conf', candidate.get('score', 0.0)))
        sources = candidate.get('sources', [candidate.get('source', '')])
        num_src = float(len(sources)) / 4.0

        is_sar = 1.0 if any('SAR' in s for s in sources) else 0.0
        is_y8naval = 1.0 if any('Y8Naval' in s for s in sources) else 0.0
        is_coco = 1.0 if any('COCO' in s for s in sources) else 0.0
        is_night = 1.0 if any('Night' in s for s in sources) else 0.0

        interior_frac, ring_frac = self.compute_water_fractions(box, water_mask)
        laplacian_norm = self.compute_laplacian_var(frame_bgr, box)

        max_distractor_iou = 0.0
        if distractor_boxes:
            max_distractor_iou = max(self._compute_iou(box, db) for db in distractor_boxes)

        area_norm = (bw * bh) / float(w * h)
        aspect_ratio = np.clip((bw / bh) / 15.0, 0.0, 1.0)
        y_center = ((y1 + y2) / 2.0) / float(h)

        metric_length = 0.10
        metric_width = 0.10
        metric_area = 0.05
        if self.homography is not None:
            try:
                dims = self.homography.box_to_metric_dimensions(box)
                metric_length = np.clip(dims['length_m'] / 400.0, 0.0, 1.0)
                metric_width = np.clip(dims['width_m'] / 70.0, 0.0, 1.0)
                metric_area = np.clip(dims['area_sqm'] / 28000.0, 0.0, 1.0)
            except Exception:
                pass

        feat_dict = {
            'conf_calib': conf,
            'num_sources_norm': num_src,
            'is_sar_source': is_sar,
            'is_y8naval_source': is_y8naval,
            'is_coco_source': is_coco,
            'is_night_source': is_night,
            'water_interior_frac': interior_frac,
            'water_ring_frac': ring_frac,
            'laplacian_var_norm': laplacian_norm,
            'temporal_diff_score': float(temporal_diff_score),
            'distractor_max_iou': float(max_distractor_iou),
            'box_area_norm': float(area_norm),
            'box_aspect_ratio_norm': float(aspect_ratio),
            'metric_length_norm': float(metric_length),
            'metric_width_norm': float(metric_width),
            'metric_area_norm': float(metric_area),
            'y_center_norm': float(y_center)
        }

        feat_vec = np.array([feat_dict[k] for k in self.FEATURE_NAMES], dtype=np.float64)
        return feat_vec, feat_dict
