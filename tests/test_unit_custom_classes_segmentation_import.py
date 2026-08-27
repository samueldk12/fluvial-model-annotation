# -*- coding: utf-8 -*-
"""Testes Unitários e de Integração: Conjuntos de Classes, Segmentação Poligonal e Importação de Datasets."""

import os
import sys
import json
import base64
import zipfile
import unittest
import numpy as np
import cv2

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.annotation.class_presets import ClassPresetManager
from src.annotation.dataset_manager import DatasetAnnotationManager, DEFAULT_CLASSES
from src.web.app import app


class TestCustomClassesSegmentationImport(unittest.TestCase):

    def setUp(self):
        self.class_mgr = ClassPresetManager(project_dir)
        self.ds_mgr = DatasetAnnotationManager(project_dir)
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()
        self.dummy_img = np.zeros((720, 1280, 3), dtype=np.uint8)

    def tearDown(self):
        self.ds_mgr.set_classes(DEFAULT_CLASSES)

    def test_class_presets_management(self):
        """Verifica a listagem, criação e persistência de conjuntos de classes."""
        presets = self.class_mgr.list_presets()
        preset_ids = [p["id"] for p in presets]
        self.assertIn("nautical_default", preset_ids)
        self.assertIn("environment_segmentation", preset_ids)
        self.assertIn("port_security_people", preset_ids)
        self.assertIn("port_infrastructure", preset_ids)

        # Valida classes específicas de segmentação de ambiente (água, porto, floresta, etc.)
        env_preset = self.class_mgr.get_preset("environment_segmentation")
        self.assertIsNotNone(env_preset)
        env_class_names = [c["name"] for c in env_preset["classes"]]
        self.assertIn("agua", env_class_names)
        self.assertIn("porto", env_class_names)
        self.assertIn("floresta", env_class_names)
        self.assertIn("margem_solo", env_class_names)
        self.assertIn("edificacao_urbana", env_class_names)
        self.assertIn("ceu", env_class_names)

        # Cria novo conjunto personalizado
        custom_set = {
            "id": "test_security_set",
            "name": "Segurança & Pessoas Teste",
            "classes": [
                {"name": "pessoa"},
                {"name": "operador"},
                {"name": "colete_salva_vidas"}
            ]
        }
        saved = self.class_mgr.save_preset(custom_set)
        self.assertEqual(saved["id"], "test_security_set")
        self.assertEqual(len(saved["classes"]), 3)

        retrieved = self.class_mgr.get_preset("test_security_set")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Segurança & Pessoas Teste")

    def test_save_polygon_segmentation(self):
        """Verifica o salvamento de anotação com polígonos de segmentação no formato YOLO-seg."""
        polygons = [
            {
                "class_id": 0,
                "points": [{"x": 100, "y": 100}, {"x": 200, "y": 100}, {"x": 200, "y": 200}, {"x": 100, "y": 200}]
            },
            {
                "class_id": 1,
                "points": [{"x": 300, "y": 300}, {"x": 400, "y": 320}, {"x": 380, "y": 420}, {"x": 280, "y": 390}]
            }
        ]

        res = self.ds_mgr.save_annotation(self.dummy_img, boxes=[], polygons=polygons, source_video="test_seg.mp4")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["num_polygons"], 2)

        # Valida conteúdo do arquivo de label YOLO
        manifest = self.ds_mgr._load_manifest()
        info = manifest[res["image_id"]]
        label_path = os.path.join(self.ds_mgr.labels_dir, info["label_file"])

        with open(label_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        self.assertEqual(len(lines), 2)
        # Cada polígono tem 4 vértices -> 1 class_id + 8 floats normalizados
        parts = lines[0].split()
        self.assertEqual(len(parts), 9)
        self.assertEqual(int(parts[0]), 0)

        # Testa carregamento do frame para continuação
        loaded = self.ds_mgr.load_annotation(res["image_id"])
        self.assertEqual(loaded["status"], "ok")
        self.assertEqual(len(loaded["polygons"]), 2)
        self.assertEqual(len(loaded["polygons"][0]["points"]), 4)

    def test_import_and_resume_dataset_zip(self):
        """Verifica a importação de dataset ZIP e continuação das anotações."""
        # 1. Cria um ZIP sintético com 1 imagem e 1 label
        test_zip_path = os.path.join(self.ds_mgr.exports_dir, "test_import_pack.zip")
        with zipfile.ZipFile(test_zip_path, "w") as zf:
            _, img_buf = cv2.imencode(".jpg", self.dummy_img)
            zf.writestr("images/sample_01.jpg", img_buf.tobytes())
            zf.writestr("labels/sample_01.txt", "0 0.500000 0.500000 0.200000 0.200000\n1 0.1 0.1 0.2 0.1 0.2 0.2\n")
            zf.writestr("classes.txt", "pessoa\noperador\nveiculo\n")

        # 2. Importa o ZIP
        res, err = self.ds_mgr.import_dataset_zip(test_zip_path)
        self.assertIsNone(err)
        self.assertEqual(res["status"], "ok")
        self.assertGreaterEqual(res["imported_images"], 1)
        self.assertIn("pessoa", self.ds_mgr.get_classes())

    def test_api_class_sets_endpoints(self):
        """Verifica endpoints /api/class_sets, /api/class_sets/save e /api/class_sets/set_active."""
        res = self.client.get("/api/class_sets")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("presets", data)
        preset_ids = [p["id"] for p in data["presets"]]
        self.assertIn("environment_segmentation", preset_ids)

        # Ativa o preset de segmentação de ambiente
        set_active_res = self.client.post("/api/class_sets/set_active",
                                          data=json.dumps({"preset_id": "environment_segmentation"}),
                                          content_type="application/json")
        self.assertEqual(set_active_res.status_code, 200)
        act_data = json.loads(set_active_res.data)
        self.assertIn("agua", act_data["active_classes"])
        self.assertIn("porto", act_data["active_classes"])
        self.assertIn("floresta", act_data["active_classes"])

        save_res = self.client.post("/api/class_sets/save",
                                    data=json.dumps({
                                        "id": "api_test_set",
                                        "name": "Conjunto API",
                                        "classes": [{"name": "barco"}, {"name": "porto"}]
                                    }),
                                    content_type="application/json")
        self.assertEqual(save_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
