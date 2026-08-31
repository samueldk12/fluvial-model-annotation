import cv2
import numpy as np

class HullPerspectiveRectifier:
    def __init__(self, clip_limit=3.0, tile_grid_size=(8, 8)):
        self.clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tile_grid_size)

    def enhance_contrast_clahe(self, img_bgr):
        if img_bgr is None or img_bgr.size == 0:
            return img_bgr

        if len(img_bgr.shape) == 2:
            return self.clahe.apply(img_bgr)

        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        cl = self.clahe.apply(l_channel)
        enhanced_lab = cv2.merge((cl, a_channel, b_channel))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    def warp_perspective_quad(self, img_bgr, quad_pts):
        if img_bgr is None or img_bgr.size == 0 or quad_pts is None or len(quad_pts) != 4:
            return img_bgr

        pts = np.array(quad_pts, dtype=np.float32)
        tl, tr, br, bl = pts[0], pts[1], pts[2], pts[3]

        width_a = np.linalg.norm(br - bl)
        width_b = np.linalg.norm(tr - tl)
        max_w = max(32, int(max(width_a, width_b)))

        height_a = np.linalg.norm(tr - br)
        height_b = np.linalg.norm(tl - bl)
        max_h = max(16, int(max(height_a, height_b)))

        dst = np.array([
            [0, 0],
            [max_w - 1, 0],
            [max_w - 1, max_h - 1],
            [0, max_h - 1]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(pts, dst)
        warped = cv2.warpPerspective(img_bgr, M, (max_w, max_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return warped

    def rectify_and_enhance(self, crop_bgr, quad_pts=None, upscale_factor=2.0):
        if crop_bgr is None or crop_bgr.size == 0:
            return crop_bgr

        h, w = crop_bgr.shape[:2]
        if quad_pts is not None:
            rectified = self.warp_perspective_quad(crop_bgr, quad_pts)
        else:
            rectified = crop_bgr

        if upscale_factor > 1.0:
            target_w = int(round(rectified.shape[1] * upscale_factor))
            target_h = int(round(rectified.shape[0] * upscale_factor))
            upscaled = cv2.resize(rectified, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        else:
            upscaled = rectified

        enhanced = self.enhance_contrast_clahe(upscaled)
        return enhanced
