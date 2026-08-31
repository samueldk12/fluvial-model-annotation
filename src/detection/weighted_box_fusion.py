import numpy as np

class WeightedBoxFusion:
    def __init__(self, iou_threshold=0.45, skip_box_threshold=0.03, conf_type='avg'):
        self.iou_threshold = iou_threshold
        self.skip_box_threshold = skip_box_threshold
        self.conf_type = conf_type

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

    def fuse(self, detections_list, model_weights=None, num_models=None):
        if not detections_list:
            return []

        weights = model_weights or {}
        valid_dets = []
        for det in detections_list:
            conf = float(det.get('conf', det.get('score', 0.0)))
            if conf >= self.skip_box_threshold:
                src = det.get('source', 'unknown')
                w = float(weights.get(src, 1.0))
                valid_dets.append({
                    'box': list(det['box']),
                    'conf': conf,
                    'label': det.get('label', 'Embarcacao'),
                    'source': src,
                    'weight': w,
                    'raw': det
                })

        if not valid_dets:
            return []

        valid_dets.sort(key=lambda x: x['conf'], reverse=True)

        clusters = []

        for det in valid_dets:
            box = det['box']
            matched_cluster = None
            best_iou = 0.0

            for cl in clusters:
                iou = self._compute_iou(box, cl['fused_box'])
                if iou >= self.iou_threshold and iou > best_iou:
                    best_iou = iou
                    matched_cluster = cl

            if matched_cluster is not None:
                matched_cluster['detections'].append(det)
                matched_cluster['fused_box'] = self._recompute_fused_box(matched_cluster['detections'])
            else:
                clusters.append({
                    'detections': [det],
                    'fused_box': list(box),
                    'label': det['label']
                })

        total_models = max(1, num_models if num_models is not None else len({d['source'] for d in valid_dets}))
        fused_results = []

        for cl in clusters:
            dets = cl['detections']
            fused_box = cl['fused_box']
            sources = list(dict.fromkeys(d['source'] for d in dets))

            scores = np.array([d['conf'] for d in dets], dtype=np.float64)
            w_arr = np.array([d['weight'] for d in dets], dtype=np.float64)

            if self.conf_type == 'avg':
                fused_conf = float(np.mean(scores))
            elif self.conf_type == 'weighted':
                fused_conf = float(np.sum(scores * w_arr) / np.sum(w_arr))
            elif self.conf_type == 'max':
                fused_conf = float(np.max(scores))
            else:
                fused_conf = float(np.mean(scores))

            agreement_ratio = min(1.0, len(sources) / float(total_models))
            if len(sources) > 1:
                fused_conf = min(1.0, fused_conf * (0.90 + 0.20 * agreement_ratio))

            fused_results.append({
                'box': [float(v) for v in fused_box],
                'conf': float(np.clip(fused_conf, 0.0, 1.0)),
                'label': cl['label'],
                'sources': sources,
                'source': f'WBF_Ensemble({len(sources)}_fontes)',
                'num_fused_boxes': len(dets),
                'detections': dets
            })

        fused_results.sort(key=lambda x: x['conf'], reverse=True)
        return fused_results

    @staticmethod
    def _recompute_fused_box(detections):
        weights = np.array([d['weight'] * d['conf'] for d in detections], dtype=np.float64)
        w_sum = np.sum(weights)
        if w_sum <= 0:
            boxes = np.array([d['box'] for d in detections], dtype=np.float64)
            return np.mean(boxes, axis=0).tolist()

        x1 = np.sum([d['box'][0] * w for d, w in zip(detections, weights)]) / w_sum
        y1 = np.sum([d['box'][1] * w for d, w in zip(detections, weights)]) / w_sum
        x2 = np.sum([d['box'][2] * w for d, w in zip(detections, weights)]) / w_sum
        y2 = np.sum([d['box'][3] * w for d, w in zip(detections, weights)]) / w_sum
        return [float(x1), float(y1), float(x2), float(y2)]
