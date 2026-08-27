# -*- coding: utf-8 -*-
"""Testes Unitários: ModelRegistry, PluggableVisionPipeline e ArchitecturePresets."""

import os
import sys
import unittest
import numpy as np
import cv2

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.pipeline.architectures import ArchitecturePresetManager, PRE_ARCHITECTURE_PRODUCTION, TEST_ARCHITECTURE_EXPERIMENTAL
from src.pipeline.pluggable_pipeline import PluggableVisionPipeline, ModelRegistry
from src.pipeline.multi_domain_detector import compute_iou, is_plausible_vessel_size


class TestUnitPipeline(unittest.TestCase):

    def setUp(self):
        self.project_dir = project_dir
        self.registry = ModelRegistry(project_dir)
        self.preset_mgr = ArchitecturePresetManager(project_dir)
        self.pipeline = PluggableVisionPipeline(project_dir)

    def test_model_catalog_structure(self):
        """Verifica se o catálogo de modelos contém os modelos esperados e chaves obrigatórias."""
        catalog = self.registry.get_catalog()
        self.assertGreater(len(catalog), 0, "Catálogo de modelos não pode ser vazio")
        ids = [m["id"] for m in catalog]
        self.assertIn("ensemble_full", ids)
        self.assertIn("yolo11n", ids)
        self.assertIn("yolov8n", ids)
        self.assertIn("mewan2808_sar", ids)
        self.assertIn("sixopen_y8naval", ids)

        for m in catalog:
            self.assertIn("name", m)
            self.assertIn("framework", m)
            self.assertIn("available", m)

    def test_architecture_presets(self):
        """Verifica se as arquiteturas (Pré-Arquitetura de Produção e Arquitetura de Teste) estão registradas."""
        presets = self.preset_mgr.list_presets()
        preset_ids = [p["id"] for p in presets]
        self.assertIn("pre_arch_production", preset_ids)
        self.assertIn("test_arch_experimental", preset_ids)

        prod = self.preset_mgr.get_preset("pre_arch_production")
        self.assertTrue(prod["is_production"])
        self.assertEqual(prod["pipeline_config"]["active_model_id"], "ensemble_full")

        test_arch = self.preset_mgr.get_preset("test_arch_experimental")
        self.assertFalse(test_arch["is_production"])
        self.assertEqual(test_arch["pipeline_config"]["active_model_id"], "yolo11n")

    def test_apply_architecture_preset(self):
        """Verifica se a aplicação de um preset altera os parâmetros e modelo do pipeline com sucesso."""
        # Aplica arquitetura de teste
        res = self.pipeline.apply_architecture_preset("test_arch_experimental")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(self.pipeline.active_preset_id, "test_arch_experimental")
        self.assertEqual(self.pipeline.config["active_model_id"], "yolo11n")
        self.assertFalse(self.pipeline.config["enable_night_enhancement"])

        # Restaura pré-arquitetura de produção
        res_prod = self.pipeline.apply_architecture_preset("pre_arch_production")
        self.assertEqual(res_prod["status"], "ok")
        self.assertEqual(self.pipeline.active_preset_id, "pre_arch_production")
        self.assertEqual(self.pipeline.config["active_model_id"], "ensemble_full")
        self.assertTrue(self.pipeline.config["enable_night_enhancement"])

    def test_iou_computation(self):
        """Verifica precisão matemática do cálculo de IoU entre caixas."""
        box1 = [100, 100, 200, 200]
        box2 = [100, 100, 200, 200]
        self.assertAlmostEqual(compute_iou(box1, box2), 1.0, places=4)

        box3 = [300, 300, 400, 400]
        self.assertAlmostEqual(compute_iou(box1, box3), 0.0, places=4)

        # 50% de sobreposição horizontal
        box4 = [150, 100, 250, 200]
        iou_val = compute_iou(box1, box4)
        self.assertGreater(iou_val, 0.3)
        self.assertLess(iou_val, 0.4)

    def test_plausible_vessel_size(self):
        """Verifica o filtro de tamanho aceitável de embarcações."""
        valid_box = [10, 10, 150, 80]
        self.assertTrue(is_plausible_vessel_size(valid_box, max_w=650, max_h=280))

        huge_box = [0, 0, 1000, 500]
        self.assertFalse(is_plausible_vessel_size(huge_box, max_w=650, max_h=280))


if __name__ == "__main__":
    unittest.main()
