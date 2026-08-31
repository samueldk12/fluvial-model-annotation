import cv2
import numpy as np

class TemporalBackgroundSubtractor:
    def __init__(self, max_buffer_size=15, downscale_factor=2, update_interval=3):
        self.max_buffer_size = max_buffer_size
        self.downscale_factor = downscale_factor
        self.update_interval = update_interval
        self.frame_count = 0
        self.buffer = []
        self.cached_median_bg = None

    def update(self, frame_bgr):
        if frame_bgr is None or frame_bgr.size == 0:
            return

        self.frame_count += 1
        if self.frame_count % self.update_interval != 0 and len(self.buffer) > 0:
            return

        h, w = frame_bgr.shape[:2]
        small_w = max(64, w // self.downscale_factor)
        small_h = max(36, h // self.downscale_factor)
        small_gray = cv2.resize(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY), (small_w, small_h))

        self.buffer.append(small_gray)
        if len(self.buffer) > self.max_buffer_size:
            self.buffer.pop(0)

        if len(self.buffer) >= 3:
            self.cached_median_bg = np.median(np.array(self.buffer), axis=0).astype(np.uint8)
        else:
            self.cached_median_bg = self.buffer[-1]

    def compute_box_temporal_diff(self, frame_bgr, box):
        if self.cached_median_bg is None or frame_bgr is None:
            return 0.50

        h, w = frame_bgr.shape[:2]
        bg_h, bg_w = self.cached_median_bg.shape[:2]

        x1, y1, x2, y2 = [int(round(v)) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return 0.0

        scale_x = bg_w / float(w)
        scale_y = bg_h / float(h)

        bg_x1, bg_y1 = int(round(x1 * scale_x)), int(round(y1 * scale_y))
        bg_x2, bg_y2 = int(round(x2 * scale_x)), int(round(y2 * scale_y))
        bg_x1, bg_y1 = max(0, bg_x1), max(0, bg_y1)
        bg_x2, bg_y2 = min(bg_w, bg_x2), min(bg_h, bg_y2)

        if bg_x2 <= bg_x1 or bg_y2 <= bg_y1:
            return 0.0

        curr_gray = cv2.cvtColor(frame_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        bg_crop = self.cached_median_bg[bg_y1:bg_y2, bg_x1:bg_x2]

        if bg_crop.shape != curr_gray.shape:
            bg_crop = cv2.resize(bg_crop, (curr_gray.shape[1], curr_gray.shape[0]))

        abs_diff = cv2.absdiff(curr_gray, bg_crop)
        mean_diff = float(np.mean(abs_diff)) / 255.0
        return float(np.clip(mean_diff * 3.0, 0.0, 1.0))
