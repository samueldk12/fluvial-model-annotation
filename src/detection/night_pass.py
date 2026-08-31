import cv2
import numpy as np

class HysteresisNightPass:
    def __init__(self, enter_thresh=45.0, exit_thresh=65.0, clip_limit=3.0, tile_grid_size=(8, 8)):
        self.enter_thresh = float(enter_thresh)
        self.exit_thresh = float(exit_thresh)
        self.clip_limit = float(clip_limit)
        self.tile_grid_size = tile_grid_size
        self.is_night_mode = False
        self.clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)

    def measure_frame_brightness(self, frame_bgr):
        if frame_bgr is None or frame_bgr.size == 0:
            return 128.0
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    def update_night_state(self, frame_bgr):
        brightness = self.measure_frame_brightness(frame_bgr)
        if not self.is_night_mode:
            if brightness < self.enter_thresh:
                self.is_night_mode = True
        else:
            if brightness > self.exit_thresh:
                self.is_night_mode = False
        return self.is_night_mode, brightness

    def enhance_frame_clahe(self, frame_bgr):
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_clahe = self.clahe.apply(l)
        lab_clahe = cv2.merge((l_clahe, a, b))
        return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

    def run_night_pass(self, frame_bgr, detector_fn, conf=0.05):
        is_night, brightness = self.update_night_state(frame_bgr)
        if not is_night:
            return [], False, brightness

        enhanced = self.enhance_frame_clahe(frame_bgr)
        night_dets = detector_fn(enhanced, conf=conf)
        for d in night_dets:
            d['source'] = 'Night_CLAHE'
            d['is_night_enhanced'] = True

        return night_dets, True, brightness
