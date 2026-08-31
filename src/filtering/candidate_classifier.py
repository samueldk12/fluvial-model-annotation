import os
import json
import numpy as np

class CandidateClassifier:
    DEFAULT_WEIGHTS = {
        'conf_calib': 4.50,
        'num_sources_norm': 3.00,
        'is_sar_source': 1.00,
        'is_y8naval_source': 1.20,
        'is_coco_source': 0.80,
        'is_night_source': 0.80,
        'water_interior_frac': 2.80,
        'water_ring_frac': 3.50,
        'laplacian_var_norm': 2.50,
        'temporal_diff_score': 1.80,
        'distractor_max_iou': -8.00,
        'box_area_norm': -1.20,
        'box_aspect_ratio_norm': 0.50,
        'metric_length_norm': 0.60,
        'metric_width_norm': 0.40,
        'metric_area_norm': 0.30,
        'y_center_norm': 0.30
    }
    DEFAULT_BIAS = -5.80

    def __init__(self, weights_path=None, threshold=0.55):
        self.weights_path = weights_path
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self.bias = self.DEFAULT_BIAS
        self.threshold = float(threshold)
        if weights_path and os.path.exists(weights_path):
            self.load(weights_path)

    def predict_proba(self, feature_dict_or_vec, feature_names=None):
        if isinstance(feature_dict_or_vec, dict):
            feat_dict = feature_dict_or_vec
        else:
            names = feature_names or list(self.weights.keys())
            feat_dict = {k: float(v) for k, v in zip(names, feature_dict_or_vec)}

        logit = self.bias
        contributions = {}
        for k, w in self.weights.items():
            val = float(feat_dict.get(k, 0.0))
            contrib = w * val
            contributions[k] = contrib
            logit += contrib

        water_ring = float(feat_dict.get('water_ring_frac', 1.0))
        water_int = float(feat_dict.get('water_interior_frac', 1.0))
        if water_ring < 0.20 and water_int < 0.20:
            logit -= 3.50
            contributions['water_penalty'] = -3.50

        lap_var = float(feat_dict.get('laplacian_var_norm', 1.0))
        if lap_var < 0.05:
            logit -= 3.00
            contributions['low_contrast_penalty'] = -3.00

        prob = 1.0 / (1.0 + np.exp(-np.clip(logit, -20.0, 20.0)))
        return float(prob), contributions

    def classify(self, feature_dict_or_vec, feature_names=None):
        prob, contributions = self.predict_proba(feature_dict_or_vec, feature_names)
        is_accepted = prob >= self.threshold

        rejection_reason = None
        if not is_accepted:
            min_k = min(contributions.keys(), key=lambda k: contributions[k])
            feat_dict = feature_dict_or_vec if isinstance(feature_dict_or_vec, dict) else {}
            if feat_dict.get('distractor_max_iou', 0.0) > 0.35:
                rejection_reason = 'DISTRACTOR_OVERLAP_COCO'
            elif feat_dict.get('water_ring_frac', 1.0) < 0.20 and feat_dict.get('water_interior_frac', 1.0) < 0.20:
                rejection_reason = 'NOT_ON_WATER_SCORE'
            elif feat_dict.get('laplacian_var_norm', 1.0) < 0.08:
                rejection_reason = 'LOW_LAPLACIAN_EDGE_CONTRAST'
            elif feat_dict.get('conf_calib', 1.0) < 0.20:
                rejection_reason = 'LOW_CONFIDENCE_SCORE'
            else:
                rejection_reason = f'CLASSIFIER_REJECTED_{min_k.upper()}'

        return {
            'probability': prob,
            'decision': 'ACCEPTED' if is_accepted else 'REJECTED',
            'rejection_reason': rejection_reason,
            'contributions': contributions
        }

    def save(self, path=None):
        target_path = path or self.weights_path or 'data/candidate_classifier_weights.json'
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump({
                'weights': self.weights,
                'bias': self.bias,
                'threshold': self.threshold
            }, f, indent=2, ensure_ascii=False)
        self.weights_path = target_path

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.weights = data.get('weights', self.weights)
            self.bias = float(data.get('bias', self.bias))
            self.threshold = float(data.get('threshold', self.threshold))
        self.weights_path = path
