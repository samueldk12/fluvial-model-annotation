import os
import json
import numpy as np

from src.geometry.homography import WaterPlaneHomography

DEFAULT_SANTOS_CONTROL_POINTS = {
    'camera_id': 'santos_port_elevated_01',
    'location': 'Porto de Santos - Canal de Acesso / Ponta da Praia',
    'image_resolution': [1920, 1080],
    'reference_coordinate_system': 'EPSG_METRIC_LOCAL_WATER_PLANE',
    'control_points': [
        {
            'name': 'Ponte de Atracacao P1 (Margem Esquerda - Proa Norte)',
            'image_px': [320.0, 480.0],
            'water_m': [-120.0, 350.0]
        },
        {
            'name': 'Ponte de Atracacao P2 (Margem Esquerda - Meio Cais)',
            'image_px': [290.0, 720.0],
            'water_m': [-140.0, 150.0]
        },
        {
            'name': 'Bóia de Balizamento Canal Centro-Norte (B01)',
            'image_px': [960.0, 420.0],
            'water_m': [0.0, 420.0]
        },
        {
            'name': 'Bóia de Balizamento Canal Centro-Sul (B02)',
            'image_px': [980.0, 850.0],
            'water_m': [10.0, 80.0]
        },
        {
            'name': 'Terminal Marítimo Cais Direito T1 (Norte)',
            'image_px': [1650.0, 460.0],
            'water_m': [160.0, 380.0]
        },
        {
            'name': 'Terminal Marítimo Cais Direito T2 (Sul)',
            'image_px': [1780.0, 780.0],
            'water_m': [185.0, 120.0]
        },
        {
            'name': 'Travessia de Balsas (Ponta da Praia)',
            'image_px': [1280.0, 960.0],
            'water_m': [40.0, 20.0]
        },
        {
            'name': 'Bacia de Evolução / Fundo Norte',
            'image_px': [750.0, 310.0],
            'water_m': [-30.0, 650.0]
        }
    ]
}

class CameraGeometryConfig:
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config_data = DEFAULT_SANTOS_CONTROL_POINTS.copy()
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
        self.homography = WaterPlaneHomography()
        self.calibrate()

    def load_from_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            self.config_data = json.load(f)
        self.config_path = path

    def save_to_file(self, path=None):
        target_path = path or self.config_path or 'data/camera_geometry_config.json'
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        self.config_path = target_path

    def calibrate(self, ransac_threshold=4.0):
        pts = self.config_data.get('control_points', [])
        img_pts = [p['image_px'] for p in pts]
        wat_pts = [p['water_m'] for p in pts]
        H, report = self.homography.compute_from_control_points(img_pts, wat_pts, ransac_threshold)
        return report

    def get_homography(self):
        return self.homography
