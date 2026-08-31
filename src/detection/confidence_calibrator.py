import os
import json
import numpy as np

class ModelConfidenceCalibrator:
    DEFAULT_CALIBRATION_PARAMS = {
        'MeWan2808_SAR': {'method': 'platt', 'a': 4.2, 'b': -0.8},
        'SixOpen_Y8Naval': {'method': 'platt', 'a': 3.8, 'b': -0.5},
        'COCO_generico': {'method': 'platt', 'a': 5.0, 'b': -1.2},
        'Night_CLAHE': {'method': 'platt', 'a': 3.5, 'b': -0.6},
        'default': {'method': 'platt', 'a': 4.0, 'b': -0.7}
    }

    def __init__(self, calibration_path=None):
        self.calibration_path = calibration_path
        self.calibrators = self.DEFAULT_CALIBRATION_PARAMS.copy()
        if calibration_path and os.path.exists(calibration_path):
            self.load(calibration_path)

    def calibrate(self, raw_score, model_name):
        score = float(np.clip(raw_score, 0.0, 1.0))
        params = self.calibrators.get(model_name, self.calibrators.get('default'))

        method = params.get('method', 'platt')
        if method == 'platt':
            a = float(params.get('a', 4.0))
            b = float(params.get('b', -0.7))
            logit = a * score + b
            calibrated = 1.0 / (1.0 + np.exp(-logit))
            return float(np.clip(calibrated, 0.0, 1.0))
        elif method == 'isotonic':
            x_thresholds = np.array(params.get('x_thresh', [0.0, 0.2, 0.5, 0.8, 1.0]))
            y_values = np.array(params.get('y_vals', [0.0, 0.25, 0.55, 0.85, 1.0]))
            return float(np.interp(score, x_thresholds, y_values))
        else:
            return score

    def calibrate_detections(self, detections_list):
        calibrated_dets = []
        for det in detections_list:
            d_copy = det.copy()
            src = d_copy.get('source', 'default')
            raw_conf = float(d_copy.get('conf', d_copy.get('score', 0.0)))
            calib_conf = self.calibrate(raw_conf, src)
            d_copy['raw_conf'] = raw_conf
            d_copy['conf'] = calib_conf
            calibrated_dets.append(d_copy)
        return calibrated_dets

    def save(self, path=None):
        target_path = path or self.calibration_path or 'data/confidence_calibration.json'
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(self.calibrators, f, indent=2, ensure_ascii=False)
        self.calibration_path = target_path

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            self.calibrators = json.load(f)
        self.calibration_path = path
