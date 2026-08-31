import numpy as np

class COCOEvaluator:
    def __init__(self, iou_thresholds=None, area_ranges=None):
        self.iou_thresholds = iou_thresholds if iou_thresholds is not None else np.linspace(0.50, 0.95, 10)
        self.area_ranges = area_ranges if area_ranges is not None else {
            'all': (0, float('inf')),
            'small': (0, 1024),
            'medium': (1024, 9216),
            'large': (9216, float('inf'))
        }

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

    @staticmethod
    def _xywh_to_xyxy(box):
        return [box[0], box[1], box[0] + box[2], box[1] + box[3]]

    @staticmethod
    def _compute_box_area(box):
        return max(0.0, (box[2] - box[0]) * (box[3] - box[1]))

    def evaluate(self, ground_truth, predictions):
        images_map = {img['id']: img for img in ground_truth.get('images', [])}
        categories = {cat['id']: cat['name'] for cat in ground_truth.get('categories', [])}

        gt_by_img = {}
        for ann in ground_truth.get('annotations', []):
            img_id = ann['image_id']
            if img_id not in gt_by_img:
                gt_by_img[img_id] = []
            box = ann['bbox']
            if len(box) == 4:
                xyxy = self._xywh_to_xyxy(box)
                gt_by_img[img_id].append({
                    'id': ann.get('id', len(gt_by_img[img_id])),
                    'category_id': ann['category_id'],
                    'bbox': xyxy,
                    'area': ann.get('area', self._compute_box_area(xyxy)),
                    'iscrowd': ann.get('iscrowd', 0)
                })

        dt_by_img = {}
        for pred in predictions:
            img_id = pred['image_id']
            if img_id not in dt_by_img:
                dt_by_img[img_id] = []
            box = pred['bbox']
            if len(box) == 4:
                xyxy = self._xywh_to_xyxy(box) if pred.get('is_xywh', False) else box
                dt_by_img[img_id].append({
                    'category_id': pred.get('category_id', 0),
                    'bbox': xyxy,
                    'score': float(pred.get('score', pred.get('conf', 0.0))),
                    'area': self._compute_box_area(xyxy)
                })

        cat_ids = list(categories.keys()) if categories else [0]
        results_by_cat = {}

        for cat_id in cat_ids:
            results_by_cat[cat_id] = self._evaluate_category(cat_id, gt_by_img, dt_by_img)

        return self._summarize_metrics(results_by_cat, categories)

    def _evaluate_category(self, cat_id, gt_by_img, dt_by_img):
        cat_metrics = {}
        for area_name, (area_min, area_max) in self.area_ranges.items():
            all_scores = []
            all_matches = {iou_th: [] for iou_th in self.iou_thresholds}
            total_gts = 0

            for img_id, gts in gt_by_img.items():
                filtered_gts = [
                    g for g in gts
                    if g['category_id'] == cat_id and area_min <= g['area'] < area_max
                ]
                dts = dt_by_img.get(img_id, [])
                filtered_dts = [
                    d for d in dts
                    if d['category_id'] == cat_id and area_min <= d['area'] < area_max
                ]
                filtered_dts = sorted(filtered_dts, key=lambda x: x['score'], reverse=True)

                total_gts += len(filtered_gts)

                if len(filtered_dts) == 0:
                    continue

                gt_matched = {iou_th: set() for iou_th in self.iou_thresholds}
                for dt in filtered_dts:
                    all_scores.append(dt['score'])
                    for iou_th in self.iou_thresholds:
                        best_iou = 0.0
                        best_gt_idx = -1
                        for gt_idx, gt in enumerate(filtered_gts):
                            if gt_idx in gt_matched[iou_th]:
                                continue
                            iou = self._compute_iou(dt['bbox'], gt['bbox'])
                            if iou > best_iou:
                                best_iou = iou
                                best_gt_idx = gt_idx

                        if best_iou >= iou_th and best_gt_idx >= 0:
                            gt_matched[iou_th].add(best_gt_idx)
                            all_matches[iou_th].append(1)
                        else:
                            all_matches[iou_th].append(0)

            aps = []
            precisions_at_50 = 0.0
            recalls_at_50 = 0.0
            f1_at_50 = 0.0

            for iou_th in self.iou_thresholds:
                matches = all_matches[iou_th]
                if len(matches) == 0 or total_gts == 0:
                    aps.append(0.0)
                    continue

                sorted_indices = np.argsort(-np.array(all_scores)) if len(all_scores) == len(matches) else range(len(matches))
                tp = np.array(matches)[sorted_indices]
                fp = 1 - tp
                tp_cum = np.cumsum(tp)
                fp_cum = np.cumsum(fp)
                rec = tp_cum / max(1, total_gts)
                prec = tp_cum / (tp_cum + fp_cum)

                if abs(iou_th - 0.50) < 1e-4 and len(prec) > 0:
                    precisions_at_50 = float(prec[-1])
                    recalls_at_50 = float(rec[-1])
                    if (precisions_at_50 + recalls_at_50) > 0:
                        f1_at_50 = float(2 * (precisions_at_50 * recalls_at_50) / (precisions_at_50 + recalls_at_50))

                rec_curve = np.linspace(0.0, 1.00, 101)
                prec_interpolated = np.zeros(101)
                for i, r in enumerate(rec_curve):
                    mask = rec >= r
                    if np.any(mask):
                        prec_interpolated[i] = np.max(prec[mask])
                    else:
                        prec_interpolated[i] = 0.0

                ap = float(np.mean(prec_interpolated))
                aps.append(ap)

            cat_metrics[area_name] = {
                'ap50': aps[0] if len(aps) > 0 else 0.0,
                'ap75': aps[5] if len(aps) > 5 else 0.0,
                'ap50_95': float(np.mean(aps)) if len(aps) > 0 else 0.0,
                'precision50': precisions_at_50,
                'recall50': recalls_at_50,
                'f1_50': f1_at_50,
                'total_gt': total_gts,
                'total_dt': len(all_scores)
            }
        return cat_metrics

    def _summarize_metrics(self, results_by_cat, categories):
        macro_summary = {}
        for area_name in self.area_ranges.keys():
            ap50_list = [m[area_name]['ap50'] for m in results_by_cat.values()]
            ap75_list = [m[area_name]['ap75'] for m in results_by_cat.values()]
            ap50_95_list = [m[area_name]['ap50_95'] for m in results_by_cat.values()]
            p50_list = [m[area_name]['precision50'] for m in results_by_cat.values()]
            r50_list = [m[area_name]['recall50'] for m in results_by_cat.values()]
            f1_list = [m[area_name]['f1_50'] for m in results_by_cat.values()]
            total_gts = sum(m[area_name]['total_gt'] for m in results_by_cat.values())
            total_dts = sum(m[area_name]['total_dt'] for m in results_by_cat.values())

            macro_summary[area_name] = {
                'mAP50': float(np.mean(ap50_list)) if ap50_list else 0.0,
                'mAP75': float(np.mean(ap75_list)) if ap75_list else 0.0,
                'mAP50_95': float(np.mean(ap50_95_list)) if ap50_95_list else 0.0,
                'precision50': float(np.mean(p50_list)) if p50_list else 0.0,
                'recall50': float(np.mean(r50_list)) if r50_list else 0.0,
                'f1_50': float(np.mean(f1_list)) if f1_list else 0.0,
                'total_gt': total_gts,
                'total_dt': total_dts
            }

        per_category_formatted = {}
        for cat_id, res in results_by_cat.items():
            cat_name = categories.get(cat_id, f'class_{cat_id}')
            per_category_formatted[cat_name] = res

        return {
            'overall': macro_summary['all'],
            'small': macro_summary['small'],
            'medium': macro_summary['medium'],
            'large': macro_summary['large'],
            'by_category': per_category_formatted
        }
