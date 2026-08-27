# -*- coding: utf-8 -*-
"""Testes Unitários: DatasetAnnotationManager (Padrão YOLO e Exportação)."""

import os
import sys
import unittest
import numpy as np
import cv2
import zipfile

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.annotation.dataset_manager import DatasetAnnotationManager, DEFAULT_CLASSES


class TestUnitDatasetCVAT(unittest.TestCase):

    def setUp(self):
        self.mgr = DatasetAnnotationManager(project_dir)
        self.mgr.set_classes(DEFAULT_CLASSES)
        self.dummy_img = np.zeros((720, 1280, 3), dtype=np.uint8)

    def tearDown(self):
        self.mgr.set_classes(DEFAULT_CLASSES)

    def test_classes_list(self):
        """Verifica se a lista de classes náuticas contém as 8 classes padrão."""
        classes = self.mgr.get_classes()
        self.assertGreaterEqual(len(classes), 8)
        self.assertIn("embarcacao", classes)
        self.assertIn("navio_cargueiro", classes)
        self.assertIn("rebocador", classes)

    def test_save_annotation_yolo_normalization(self):
        """Verifica se o salvamento de anotações gera arquivos .jpg, .txt com coordenadas normalizadas [0, 1]."""
        test_boxes = [
            {"class_id": 0, "x1": 128, "y1": 72, "x2": 640, "y2": 360},
            {"class_id": 1, "x1": 640, "y1": 360, "x2": 1280, "y2": 720}
        ]

        res = self.mgr.save_annotation(self.dummy_img, test_boxes, source_video="test_unit.mp4", frame_timestamp=5.0)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["num_boxes"], 2)

        # Valida arquivo de imagem
        img_path = os.path.join(self.mgr.images_dir, res["filename"])
        self.assertTrue(os.path.exists(img_path))

        # Valida arquivo de label YOLO
        manifest = self.mgr._load_manifest()
        info = manifest[res["image_id"]]
        label_path = os.path.join(self.mgr.labels_dir, info["label_file"])
        self.assertTrue(os.path.exists(label_path))

        # Lê e valida formato do arquivo txt
        with open(label_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)

        for l in lines:
            parts = l.strip().split()
            self.assertEqual(len(parts), 5)
            cls_id = int(parts[0])
            cx, cy, w, h = map(float, parts[1:])
            self.assertGreaterEqual(cls_id, 0)
            self.assertGreaterEqual(cx, 0.0)
            self.assertLessEqual(cx, 1.0)
            self.assertGreaterEqual(cy, 0.0)
            self.assertLessEqual(cy, 1.0)
            self.assertGreater(w, 0.0)
            self.assertLessEqual(w, 1.0)
            self.assertGreater(h, 0.0)
            self.assertLessEqual(h, 1.0)

    def test_export_zip_integrity(self):
        """Verifica a integridade do pacote ZIP exportado (data.yaml, images, labels)."""
        zip_path, err = self.mgr.export_dataset_zip(split_ratio=0.8)
        self.assertIsNone(err)
        self.assertTrue(os.path.exists(zip_path))

        with zipfile.ZipFile(zip_path, "r") as zf:
            files = zf.namelist()
            self.assertIn("data.yaml", files)
            self.assertIn("classes.txt", files)
            # Verifica se há pastas de imagens e labels
            has_images = any(f.startswith("images/") for f in files)
            has_labels = any(f.startswith("labels/") for f in files)
            self.assertTrue(has_images)
            self.assertTrue(has_labels)


if __name__ == "__main__":
    unittest.main()
