import cv2
import numpy as np

from src.ocr.hull_rectifier import HullPerspectiveRectifier
from src.ocr.imo_validator import IMOValidator

class TwoStageMarineOCREngine:
    def __init__(self, use_gpu=False):
        self.rectifier = HullPerspectiveRectifier()
        self.validator = IMOValidator()
        self.reader = None
        self._init_reader(use_gpu)

    def _init_reader(self, use_gpu):
        try:
            import easyocr
            self.reader = easyocr.Reader(['en', 'pt'], gpu=use_gpu, verbose=False)
        except Exception:
            self.reader = None

    def detect_text_regions(self, img_bgr):
        if img_bgr is None or img_bgr.size == 0:
            return []

        h, w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if len(img_bgr.shape) == 3 else img_bgr
        mser = cv2.MSER_create(min_area=40, max_area=int(w * h * 0.15))
        regions, bboxes = mser.detectRegions(gray)

        boxes = []
        for box in bboxes:
            bx, by, bw, bh = box
            aspect = bw / float(max(1, bh))
            if 0.2 <= aspect <= 12.0 and bh >= 8:
                boxes.append([bx, by, bx + bw, by + bh])

        if not boxes:
            boxes = [[0, 0, w, h]]

        return boxes

    def recognize_text(self, img_bgr, text_boxes=None):
        if img_bgr is None or img_bgr.size == 0:
            return []

        enhanced = self.rectifier.rectify_and_enhance(img_bgr, upscale_factor=2.0)
        results = []

        if self.reader is not None:
            try:
                ocr_out = self.reader.readtext(enhanced)
                for item in ocr_out:
                    poly, text, conf = item
                    is_valid, formatted_imo, _ = self.validator.validate_7digit_imo(text)
                    results.append({
                        'text': text.strip(),
                        'conf': float(conf),
                        'poly': poly,
                        'is_valid_imo': is_valid,
                        'formatted_imo': formatted_imo if is_valid else None
                    })
            except Exception:
                pass

        if not results:
            raw_text = ''
            valid_imos = self.validator.extract_and_validate_from_text(raw_text)
            for vi in valid_imos:
                results.append({
                    'text': vi,
                    'conf': 0.80,
                    'poly': [[0, 0], [100, 0], [100, 30], [0, 30]],
                    'is_valid_imo': True,
                    'formatted_imo': vi
                })

        return results
