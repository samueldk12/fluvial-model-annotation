# -*- coding: utf-8 -*-
"""Testes de Integração de API e Endpoints Flask."""

import os
import sys
import json
import base64
import unittest
import numpy as np
import cv2

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.web.app import app


class TestIntegrationAPI(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_pages_render(self):
        """Verifica se as rotas principais renderizam com código HTTP 200."""
        r_home = self.client.get("/")
        self.assertEqual(r_home.status_code, 200)

        r_anotar = self.client.get("/anotar")
        self.assertEqual(r_anotar.status_code, 200)
        self.assertIn(b"CVAT", r_anotar.data)

        r_sobre = self.client.get("/sobre")
        self.assertEqual(r_sobre.status_code, 200)

    def test_api_models(self):
        """Verifica o endpoint GET /api/models."""
        res = self.client.get("/api/models")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("catalog", data)
        self.assertIn("active_model_id", data)

    def test_api_architectures(self):
        """Verifica endpoints /api/architectures e /api/architectures/apply."""
        res = self.client.get("/api/architectures")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("presets", data)

        # Testa aplicar arquitetura de teste
        res_apply = self.client.post("/api/architectures/apply",
                                     data=json.dumps({"preset_id": "test_arch_experimental"}),
                                     content_type="application/json")
        self.assertEqual(res_apply.status_code, 200)
        d_apply = json.loads(res_apply.data)
        self.assertEqual(d_apply["active_preset_id"], "test_arch_experimental")

        # Restaura pré-arquitetura de produção
        res_rest = self.client.post("/api/architectures/apply",
                                    data=json.dumps({"preset_id": "pre_arch_production"}),
                                    content_type="application/json")
        self.assertEqual(res_rest.status_code, 200)

    def test_api_annotation_workflow(self):
        """Testa o fluxo completo de anotação (auto-detect, save, list e export_zip)."""
        # 1. Gera imagem de teste em base64
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", img)
        b64_str = base64.b64encode(buf).decode("utf-8")

        # 2. Auto-Detect
        res_det = self.client.post("/api/annotation/auto_detect",
                                   data=json.dumps({"image_base64": b64_str}),
                                   content_type="application/json")
        self.assertEqual(res_det.status_code, 200)

        # 3. Salvar Anotação
        save_payload = {
            "image_base64": b64_str,
            "boxes": [{"class_id": 0, "x1": 50, "y1": 50, "x2": 200, "y2": 150}],
            "source_video": "api_test.mp4",
            "frame_timestamp": 1.2
        }
        res_save = self.client.post("/api/annotation/save",
                                    data=json.dumps(save_payload),
                                    content_type="application/json")
        self.assertEqual(res_save.status_code, 200)
        d_save = json.loads(res_save.data)
        self.assertEqual(d_save["status"], "ok")

        # 4. Listar Anotações
        res_list = self.client.get("/api/annotation/list")
        self.assertEqual(res_list.status_code, 200)
        d_list = json.loads(res_list.data)
        self.assertGreaterEqual(d_list["total_images"], 1)

        # 5. Exportar ZIP
        res_zip = self.client.get("/api/annotation/export_zip")
        self.assertEqual(res_zip.status_code, 200)
        self.assertTrue("zip" in res_zip.content_type.lower())

    def test_live_stream_and_snapshot_api(self):
        """Verifica os endpoints de captura e snapshot de transmissão ao vivo."""
        res_snap = self.client.get("/api/live_raw_snapshot")
        self.assertEqual(res_snap.status_code, 200)
        d_snap = json.loads(res_snap.data)
        self.assertEqual(d_snap["status"], "ok")
        self.assertIn("image_base64", d_snap)
        self.assertIn("width", d_snap)
        self.assertIn("height", d_snap)

        res_jpg = self.client.get("/api/live_raw_snapshot.jpg")
        self.assertEqual(res_jpg.status_code, 200)
        self.assertEqual(res_jpg.content_type, "image/jpeg")


if __name__ == "__main__":
    unittest.main()
