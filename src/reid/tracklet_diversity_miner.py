import numpy as np
import cv2

class TrackletDiversityMiner:
    def __init__(self, max_exemplars=4, min_laplacian_var=15.0):
        self.max_exemplars = int(max_exemplars)
        self.min_laplacian_var = float(min_laplacian_var)

    def _compute_sharpness(self, crop):
        if crop is None or crop.size == 0:
            return 0.0
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def mine_exemplars(self, tracklet_observations):
        if not tracklet_observations:
            return []

        valid_obs = []
        for obs in tracklet_observations:
            crop = obs.get('crop')
            if crop is None or crop.shape[0] < 16 or crop.shape[1] < 16:
                continue
            sharpness = self._compute_sharpness(crop)
            if sharpness >= self.min_laplacian_var or len(tracklet_observations) <= 2:
                valid_obs.append({
                    'crop': crop,
                    'embedding': obs.get('embedding'),
                    'sharpness': sharpness,
                    'timestamp': obs.get('timestamp', 0.0),
                    'bbox': obs.get('bbox', [0, 0, 0, 0])
                })

        if not valid_obs:
            return tracklet_observations[:self.max_exemplars]

        if len(valid_obs) <= self.max_exemplars:
            return valid_obs

        embs = [v['embedding'] for v in valid_obs if v['embedding'] is not None]
        if len(embs) < len(valid_obs):
            valid_obs.sort(key=lambda x: x['sharpness'], reverse=True)
            return valid_obs[:self.max_exemplars]

        embs_arr = np.array(embs, dtype=np.float32)
        norms = np.linalg.norm(embs_arr, axis=1, keepdims=True)
        embs_arr = embs_arr / np.maximum(1e-7, norms)

        selected_indices = [0]
        for _ in range(1, self.max_exemplars):
            dist_to_selected = []
            for i in range(len(valid_obs)):
                if i in selected_indices:
                    dist_to_selected.append(-1.0)
                else:
                    min_cos_sim = max(np.dot(embs_arr[i], embs_arr[s]) for s in selected_indices)
                    dist_to_selected.append(1.0 - min_cos_sim)

            next_idx = int(np.argmax(dist_to_selected))
            selected_indices.append(next_idx)

        return [valid_obs[i] for i in selected_indices]

    def compute_master_embedding(self, mined_exemplars):
        embs = [ex['embedding'] for ex in mined_exemplars if ex.get('embedding') is not None]
        if not embs:
            return None
        weights = [max(1.0, float(ex.get('sharpness', 10.0))) for ex in mined_exemplars if ex.get('embedding') is not None]
        total_w = sum(weights)
        norm_weights = [w / total_w for w in weights]

        embs_arr = np.array(embs, dtype=np.float32)
        master = np.sum(embs_arr * np.array(norm_weights)[:, None], axis=0)
        norm = np.linalg.norm(master)
        if norm > 1e-7:
            master = master / norm
        return master
