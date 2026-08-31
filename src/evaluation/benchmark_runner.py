import os
import sys
import time
import json
import numpy as np
import cv2
from PIL import Image

from src.evaluation.coco_evaluator import COCOEvaluator
from src.evaluation.dataset_splitter import TemporalDatasetSplitter
from src.evaluation.candidate_logger import StructuredCandidateLogger
from src.pipeline.multi_domain_detector import MultiDomainVesselDetector, is_plausible_vessel_size, compute_iou
from src.pipeline.vessel_ensemble_engine import VesselEnsembleEngine
from src.models.vit_vessel import PretrainedViTVesselModel

class BaselineBenchmarkRunner:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.evaluator = COCOEvaluator()
        self.splitter = TemporalDatasetSplitter()
        self.logger = StructuredCandidateLogger(os.path.join(project_dir, 'data', 'evaluation_audit'))

        self.detector = MultiDomainVesselDetector(project_dir)
        self.vit = PretrainedViTVesselModel()
        self.ensemble = VesselEnsembleEngine(None, self)
        self.ensemble.multi_detector = self.detector

    def _resolve_image_path(self, fn):
        candidates = [
            os.path.join(self.project_dir, 'data', 'evaluation_dataset', 'images', fn),
            os.path.join(self.project_dir, 'datasets', 'annotated_frames', 'images', fn),
            os.path.join(self.project_dir, 'data', fn),
            os.path.join(self.project_dir, 'datasets', 'annotated_frames', fn)
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def run_baseline_benchmark(self, dataset_coco_or_manifest=None, eval_split='val'):
        if dataset_coco_or_manifest is None:
            multi_day_path = os.path.join(self.project_dir, 'data', 'evaluation_dataset', 'santos_coco_benchmark.json')
            manifest_path = os.path.join(self.project_dir, 'datasets', 'annotated_frames', 'manifest.json')
            if os.path.exists(multi_day_path):
                with open(multi_day_path, 'r', encoding='utf-8') as f:
                    coco_dataset = json.load(f)
            elif os.path.exists(manifest_path):
                coco_dataset = self.splitter.convert_manifest_to_coco(manifest_path)
            else:
                coco_dataset = {'images': [], 'annotations': [], 'categories': [{'id': 0, 'name': 'embarcacao'}]}
        elif isinstance(dataset_coco_or_manifest, str) and dataset_coco_or_manifest.endswith('.json'):
            with open(dataset_coco_or_manifest, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if 'images' in raw and 'annotations' in raw:
                coco_dataset = raw
            else:
                coco_dataset = self.splitter.convert_manifest_to_coco(raw)
        else:
            coco_dataset = dataset_coco_or_manifest

        splits = self.splitter.split_coco_dataset(coco_dataset)
        eval_dataset = splits.get(eval_split, splits['val']) if eval_split != 'all' else coco_dataset

        predictions = []
        latencies = []

        for img_info in eval_dataset.get('images', []):
            img_id = img_info['id']
            fn = img_info.get('file_name', img_info.get('filename', str(img_id) + '.jpg'))
            img_path = self._resolve_image_path(fn)

            if img_path and os.path.exists(img_path):
                frame_bgr = cv2.imread(img_path)
            else:
                w, h = img_info.get('width', 1280), img_info.get('height', 720)
                frame_bgr = np.zeros((h, w, 3), dtype=np.uint8)

            t0 = time.time()
            h, w = frame_bgr.shape[:2]

            self.detector.bg_subtractor.update(frame_bgr)

            generic_boats, distractor_boxes = self.detector._detect_generic(frame_bgr, conf=0.05)
            sar_dets = self.detector._detect_yolo(self.detector.sar, frame_bgr, conf=0.05, source_name='MeWan2808_SAR_fluvial')
            y8_dets = self.detector._detect_y8naval(frame_bgr, conf=0.05)

            def sar_tiler_fn(crop, conf=0.05):
                return self.detector._detect_yolo(self.detector.sar, crop, conf, 'MeWan2808_SAR_fluvial')
            tiled_sar = self.detector.tiler.run_tiled_and_full_inference(frame_bgr, sar_tiler_fn, conf=0.05)
            extra_tiled = [d for d in tiled_sar if d.get('is_tiled')]

            all_raw = generic_boats + sar_dets + y8_dets + extra_tiled
            fused = self.detector._fuse_by_iou(all_raw, iou_thresh=0.35)
            water_mask = self.detector.water_segmenter.segment(frame_bgr)

            for cand in fused:
                box = cand['box']
                temp_diff = self.detector.bg_subtractor.compute_box_temporal_diff(frame_bgr, box)
                feat_vec, feat_dict = self.detector.feature_extractor.extract_features(cand, frame_bgr, water_mask, distractor_boxes, temp_diff)
                classification = self.detector.candidate_classifier.classify(feat_dict)

                is_accepted = (classification['decision'] == 'ACCEPTED')
                rejection_reason = classification.get('rejection_reason')

                self.logger.log_candidate(frame_bgr, {
                    'candidate_id': f'{img_id}_cand_{len(self.logger.entries)}',
                    'frame_id': img_id,
                    'timestamp': time.time(),
                    'box': box,
                    'sources': cand.get('sources', []),
                    'raw_conf': cand.get('conf', 0.0),
                    'fused_conf': classification['probability'],
                    'edge_score': feat_dict['laplacian_var_norm'],
                    'laplacian_var': feat_dict['laplacian_var_norm'],
                    'water_interior_fraction': feat_dict['water_interior_frac'],
                    'water_ring_fraction': feat_dict['water_ring_frac'],
                    'is_on_water': feat_dict['water_ring_frac'] > 0.30 or feat_dict['water_interior_frac'] > 0.30,
                    'distractor_max_iou': feat_dict['distractor_max_iou'],
                    'size_plausible': True,
                    'vertical_band_valid': True,
                    'decision': 'ACCEPTED' if is_accepted else 'REJECTED',
                    'rejection_reason': rejection_reason
                })

                if is_accepted:
                    predictions.append({
                        'image_id': img_id,
                        'category_id': 0,
                        'bbox': box,
                        'score': classification['probability'],
                        'is_xywh': False
                    })

            lat = (time.time() - t0) * 1000.0
            latencies.append(lat)

        metrics = self.evaluator.evaluate(eval_dataset, predictions)

        benchmark_result = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pipeline_name': 'etapa_d_unified_filtering',
            'split_evaluated': eval_split,
            'split_summary': splits['summary'],
            'metrics': metrics,
            'latency': {
                'mean_ms': float(np.mean(latencies)) if latencies else 0.0,
                'median_ms': float(np.median(latencies)) if latencies else 0.0,
                'p95_ms': float(np.percentile(latencies, 95)) if latencies else 0.0,
                'fps': float(1000.0 / np.mean(latencies)) if latencies and np.mean(latencies) > 0 else 0.0,
                'total_frames_evaluated': len(latencies)
            },
            'candidate_audit_summary': self.logger.get_summary()
        }

        out_path = os.path.join(self.project_dir, 'data', 'evaluation_audit', 'etapa_d_metrics.json')
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(benchmark_result, f, indent=2, ensure_ascii=False)

        return benchmark_result
