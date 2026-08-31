import numpy as np
import cv2

class TiledInferenceEngine:
    def __init__(self, y_min_ratio=0.20, y_max_ratio=0.65, num_tiles_x=3, overlap_ratio=0.20):
        self.y_min_ratio = float(y_min_ratio)
        self.y_max_ratio = float(y_max_ratio)
        self.num_tiles_x = int(num_tiles_x)
        self.overlap_ratio = float(overlap_ratio)

    def generate_tiles(self, image_shape):
        h, w = image_shape[:2]
        band_y1 = int(round(h * self.y_min_ratio))
        band_y2 = int(round(h * self.y_max_ratio))
        band_h = band_y2 - band_y1

        if self.num_tiles_x <= 1:
            return [{
                'tile_id': 'tile_band_full',
                'bbox': [0, band_y1, w, band_y2],
                'offset_x': 0,
                'offset_y': band_y1,
                'width': w,
                'height': band_h
            }]

        tile_w = int(round(w / (self.num_tiles_x - (self.num_tiles_x - 1) * self.overlap_ratio)))
        stride_x = int(round(tile_w * (1.0 - self.overlap_ratio)))

        tiles = []
        for i in range(self.num_tiles_x):
            x1 = min(w - tile_w, i * stride_x)
            x2 = min(w, x1 + tile_w)
            tiles.append({
                'tile_id': f'tile_dist_{i}',
                'bbox': [x1, band_y1, x2, band_y2],
                'offset_x': x1,
                'offset_y': band_y1,
                'width': x2 - x1,
                'height': band_h
            })
        return tiles

    def run_tiled_and_full_inference(self, image_bgr, detector_fn, conf=0.05):
        h, w = image_bgr.shape[:2]
        all_detections = []

        full_dets = detector_fn(image_bgr, conf=conf)
        for d in full_dets:
            det_copy = d.copy()
            det_copy['is_tiled'] = False
            all_detections.append(det_copy)

        tiles = self.generate_tiles(image_bgr.shape)
        for tile in tiles:
            x1, y1, x2, y2 = tile['bbox']
            crop = image_bgr[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            tile_dets = detector_fn(crop, conf=conf)
            for d in tile_dets:
                bx1, by1, bx2, by2 = d['box']
                global_box = [
                    float(bx1 + tile['offset_x']),
                    float(by1 + tile['offset_y']),
                    float(bx2 + tile['offset_x']),
                    float(by2 + tile['offset_y'])
                ]
                d_copy = d.copy()
                d_copy['box'] = global_box
                d_copy['is_tiled'] = True
                d_copy['tile_id'] = tile['tile_id']
                all_detections.append(d_copy)

        return all_detections
