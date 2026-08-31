import numpy as np
import cv2

class WaterPlaneHomography:
    def __init__(self, homography_matrix=None):
        self.H = np.array(homography_matrix, dtype=np.float64) if homography_matrix is not None else None
        self.H_inv = np.linalg.inv(self.H) if self.H is not None and np.linalg.matrix_rank(self.H) == 3 else None
        self.last_reprojection_report = {}

    def compute_from_control_points(self, image_points, water_points, ransac_reproj_threshold=5.0):
        img_pts = np.array(image_points, dtype=np.float64).reshape(-1, 2)
        wat_pts = np.array(water_points, dtype=np.float64).reshape(-1, 2)

        if len(img_pts) < 4 or len(wat_pts) < 4:
            raise ValueError('At least 4 control point correspondences are required.')

        H, inliers_mask = cv2.findHomography(img_pts, wat_pts, cv2.RANSAC, ransac_reproj_threshold)
        if H is None:
            raise RuntimeError('Homography computation failed.')

        self.H = H.astype(np.float64)
        self.H_inv = np.linalg.inv(self.H)

        reprojected_water = self.image_to_water(img_pts)
        errors = np.linalg.norm(reprojected_water - wat_pts, axis=1)

        inliers = inliers_mask.ravel().astype(bool) if inliers_mask is not None else np.ones(len(img_pts), dtype=bool)
        inlier_errors = errors[inliers] if np.any(inliers) else errors

        self.last_reprojection_report = {
            'num_points': int(len(img_pts)),
            'num_inliers': int(np.sum(inliers)),
            'inlier_ratio': float(np.mean(inliers)),
            'rmse_meters': float(np.sqrt(np.mean(inlier_errors ** 2))),
            'mae_meters': float(np.mean(inlier_errors)),
            'max_error_meters': float(np.max(inlier_errors)),
            'homography_matrix': self.H.tolist()
        }
        return self.H, self.last_reprojection_report

    def image_to_water(self, image_points):
        if self.H is None:
            raise RuntimeError('Homography matrix not initialized.')
        pts = np.array(image_points, dtype=np.float64).reshape(-1, 2)
        ones = np.ones((len(pts), 1), dtype=np.float64)
        homogeneous = np.hstack([pts, ones])
        transformed = (self.H @ homogeneous.T).T
        z = transformed[:, 2:3]
        z[np.abs(z) < 1e-9] = 1e-9
        return transformed[:, :2] / z

    def water_to_image(self, water_points):
        if self.H_inv is None:
            raise RuntimeError('Inverse homography matrix not initialized.')
        pts = np.array(water_points, dtype=np.float64).reshape(-1, 2)
        ones = np.ones((len(pts), 1), dtype=np.float64)
        homogeneous = np.hstack([pts, ones])
        transformed = (self.H_inv @ homogeneous.T).T
        z = transformed[:, 2:3]
        z[np.abs(z) < 1e-9] = 1e-9
        return transformed[:, :2] / z

    def box_to_metric_dimensions(self, box):
        x1, y1, x2, y2 = box
        corners_img = np.array([
            [x1, y1],
            [x2, y1],
            [x2, y2],
            [x1, y2]
        ], dtype=np.float64)

        corners_water = self.image_to_water(corners_img)

        cx = float(np.mean(corners_water[:, 0]))
        cy = float(np.mean(corners_water[:, 1]))

        edge_top = np.linalg.norm(corners_water[1] - corners_water[0])
        edge_bottom = np.linalg.norm(corners_water[2] - corners_water[3])
        edge_left = np.linalg.norm(corners_water[3] - corners_water[0])
        edge_right = np.linalg.norm(corners_water[2] - corners_water[1])

        dim_u = (edge_top + edge_bottom) / 2.0
        dim_v = (edge_left + edge_right) / 2.0

        length_m = max(dim_u, dim_v)
        width_m = min(dim_u, dim_v)
        area_sqm = length_m * width_m

        diag1 = np.linalg.norm(corners_water[2] - corners_water[0])
        diag2 = np.linalg.norm(corners_water[3] - corners_water[1])
        diag_m = (diag1 + diag2) / 2.0

        return {
            'centroid_water_m': [cx, cy],
            'length_m': float(length_m),
            'width_m': float(width_m),
            'area_sqm': float(area_sqm),
            'diagonal_m': float(diag_m),
            'corners_water_m': corners_water.tolist()
        }
