import numpy as np
from collections import defaultdict

class MOTEvaluator:
    def __init__(self, iou_threshold=0.50):
        self.iou_threshold = float(iou_threshold)

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

    def evaluate_tracks(self, ground_truth_tracks, predicted_tracks):
        gt_by_frame = defaultdict(list)
        for gt in ground_truth_tracks:
            gt_by_frame[gt['frame_id']].append(gt)

        dt_by_frame = defaultdict(list)
        for dt in predicted_tracks:
            dt_by_frame[dt['frame_id']].append(dt)

        all_frames = sorted(list(set(list(gt_by_frame.keys()) + list(dt_by_frame.keys()))))

        total_gt = len(ground_truth_tracks)
        total_dt = len(predicted_tracks)

        tp = 0
        fp = 0
        fn = 0
        id_switches = 0
        gt_last_assigned_dt = {}

        global_gt_dt_overlap = defaultdict(lambda: defaultdict(int))
        gt_lengths = defaultdict(int)
        dt_lengths = defaultdict(int)

        for gt in ground_truth_tracks:
            gt_lengths[gt['track_id']] += 1
        for dt in predicted_tracks:
            dt_lengths[dt['track_id']] += 1

        for f in all_frames:
            gts = gt_by_frame.get(f, [])
            dts = dt_by_frame.get(f, [])

            if not gts:
                fp += len(dts)
                continue
            if not dts:
                fn += len(gts)
                continue

            cost_matrix = np.zeros((len(gts), len(dts)), dtype=np.float64)
            for i, g in enumerate(gts):
                for j, d in enumerate(dts):
                    cost_matrix[i, j] = self._compute_iou(g['bbox'], d['bbox'])

            matched_gts = set()
            matched_dts = set()

            pairs = []
            for i in range(len(gts)):
                for j in range(len(dts)):
                    if cost_matrix[i, j] >= self.iou_threshold:
                        pairs.append((cost_matrix[i, j], i, j))
            pairs.sort(key=lambda x: x[0], reverse=True)

            for iou_val, i, j in pairs:
                if i not in matched_gts and j not in matched_dts:
                    matched_gts.add(i)
                    matched_dts.add(j)
                    tp += 1
                    gt_id = gts[i]['track_id']
                    dt_id = dts[j]['track_id']
                    global_gt_dt_overlap[gt_id][dt_id] += 1

                    if gt_id in gt_last_assigned_dt:
                        if gt_last_assigned_dt[gt_id] != dt_id:
                            id_switches += 1
                    gt_last_assigned_dt[gt_id] = dt_id

            fn += len(gts) - len(matched_gts)
            fp += len(dts) - len(matched_dts)

        idtp = 0
        all_gt_ids = list(gt_lengths.keys())
        all_dt_ids = list(dt_lengths.keys())

        used_dt_for_id = set()
        sorted_gt_matches = []
        for gt_id in all_gt_ids:
            for dt_id, overlap_count in global_gt_dt_overlap[gt_id].items():
                sorted_gt_matches.append((overlap_count, gt_id, dt_id))
        sorted_gt_matches.sort(key=lambda x: x[0], reverse=True)

        assigned_gt = set()
        for overlap_count, gt_id, dt_id in sorted_gt_matches:
            if gt_id not in assigned_gt and dt_id not in used_dt_for_id:
                assigned_gt.add(gt_id)
                used_dt_for_id.add(dt_id)
                idtp += overlap_count

        idfn = max(0, total_gt - idtp)
        idfp = max(0, total_dt - idtp)
        idf1 = (2.0 * idtp) / max(1.0, (2.0 * idtp + idfp + idfn))
        id_precision = idtp / max(1.0, idtp + idfp)
        id_recall = idtp / max(1.0, idtp + idfn)

        mota = 1.0 - (float(fn + fp + id_switches) / max(1.0, float(total_gt)))
        mota = float(np.clip(mota, 0.0, 1.0))

        det_a = float(tp) / max(1.0, float(tp + fn + fp))
        ass_a = float(idtp) / max(1.0, float(idtp + idfn + idfp))
        hota = float(np.sqrt(det_a * ass_a))

        return {
            'hota': hota,
            'idf1': float(idf1),
            'id_precision': float(id_precision),
            'id_recall': float(id_recall),
            'id_switches': int(id_switches),
            'mota': mota,
            'deta': det_a,
            'assa': ass_a,
            'tp': int(tp),
            'fp': int(fp),
            'fn': int(fn),
            'total_gt_boxes': int(total_gt),
            'total_dt_boxes': int(total_dt)
        }
