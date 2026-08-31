import os
import json
import time
import cv2

class StructuredCandidateLogger:
    def __init__(self, log_dir='data/evaluation_audit'):
        self.log_dir = log_dir
        self.crops_dir = os.path.join(log_dir, 'crops')
        os.makedirs(self.crops_dir, exist_ok=True)
        self.jsonl_path = os.path.join(log_dir, 'candidates_audit.jsonl')
        self.entries = []

    def log_candidate(self, frame_bgr, candidate_data):
        timestamp = candidate_data.get('timestamp', time.time())
        cand_id = candidate_data.get('candidate_id', f'cand_{int(timestamp * 1000)}_{len(self.entries)}')
        box = candidate_data.get('box', [0, 0, 0, 0])
        x1, y1, x2, y2 = [int(round(v)) for v in box]

        crop_filename = None
        if frame_bgr is not None and frame_bgr.size > 0:
            h, w = frame_bgr.shape[:2]
            cx1, cy1 = max(0, x1), max(0, y1)
            cx2, cy2 = min(w, x2), min(h, y2)
            if cx2 > cx1 and cy2 > cy1:
                crop = frame_bgr[cy1:cy2, cx1:cx2]
                if crop.size > 0:
                    crop_filename = f'{cand_id}.jpg'
                    crop_path = os.path.join(self.crops_dir, crop_filename)
                    cv2.imwrite(crop_path, crop)

        entry = {
            'candidate_id': cand_id,
            'frame_id': candidate_data.get('frame_id', 'unknown_frame'),
            'timestamp': timestamp,
            'bbox': box,
            'width': max(0, x2 - x1),
            'height': max(0, y2 - y1),
            'area': max(0, (x2 - x1) * (y2 - y1)),
            'sources': candidate_data.get('sources', []),
            'raw_conf': candidate_data.get('raw_conf', 0.0),
            'fused_conf': candidate_data.get('fused_conf', 0.0),
            'edge_score': candidate_data.get('edge_score', None),
            'laplacian_var': candidate_data.get('laplacian_var', None),
            'water_interior_fraction': candidate_data.get('water_interior_fraction', None),
            'water_ring_fraction': candidate_data.get('water_ring_fraction', None),
            'is_on_water': candidate_data.get('is_on_water', None),
            'distractor_max_iou': candidate_data.get('distractor_max_iou', None),
            'size_plausible': candidate_data.get('size_plausible', True),
            'vertical_band_valid': candidate_data.get('vertical_band_valid', True),
            'prior_boost_applied': candidate_data.get('prior_boost_applied', False),
            'decision': candidate_data.get('decision', 'REJECTED'),
            'rejection_reason': candidate_data.get('rejection_reason', None),
            'crop_file': crop_filename
        }

        self.entries.append(entry)
        with open(self.jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        return entry

    def get_summary(self):
        total = len(self.entries)
        accepted = sum(1 for e in self.entries if e['decision'] == 'ACCEPTED')
        rejected = total - accepted
        reasons = {}
        for e in self.entries:
            r = e.get('rejection_reason')
            if r:
                reasons[r] = reasons.get(r, 0) + 1
        return {
            'total_candidates': total,
            'accepted': accepted,
            'rejected': rejected,
            'acceptance_rate': float(accepted / total) if total > 0 else 0.0,
            'rejection_reasons': reasons
        }
