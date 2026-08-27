# -*- coding: utf-8 -*-
"""
Testes de Integracao e Validacao do Fluxo de Anotacao com Modelo de IA Atrelado,
Edicao Interativa, Exclusao Total e Active Learning (Human-in-the-Loop).
"""

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
from src.annotation.dataset_manager import DatasetAnnotationManager


class TestAnnotationAiModelWorkflow(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

        # Cria imagem de teste com retangulos para simular barcos
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (300, 250), (200, 200, 200), -1)
        cv2.rectangle(img, (350, 200), (550, 400), (180, 180, 180), -1)
        _, buf = cv2.imencode(".jpg", img)
        self.b64_img = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

    def test_get_annotation_models_catalog(self):
        """Testa GET /api/annotation/models para retornar o catalogo de modelos de IA."""
        res = self.client.get("/api/annotation/models?domain=naval")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("models", data)
        self.assertGreater(len(data["models"]), 0)
        model_ids = [m["id"] for m in data["models"]]
        self.assertIn("yolo11n", model_ids)

    def test_annotation_auto_detect_with_specific_model(self):
        """Testa POST /api/annotation/auto_detect passando model_id e conf threshold."""
        payload = {
            "image_base64": self.b64_img,
            "model_id": "yolo11n",
            "conf": 0.15,
            "domain": "naval"
        }
        res = self.client.post("/api/annotation/auto_detect",
                               data=json.dumps(payload),
                               content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("detections", data)
        self.assertIn("model_used", data)
        self.assertEqual(data["model_used"], "yolo11n")

    def test_annotation_save_and_active_learning_metadata(self):
        """Testa POST /api/annotation/save salvando metadados de auxilio de IA e correcao humana."""
        boxes = [
            {
                "x1": 100, "y1": 100, "x2": 300, "y2": 250,
                "class_id": 0, "class_name": "embarcacao", "confidence": 0.92,
                "source_model": "yolo11n"
            }
        ]
        payload = {
            "image_base64": self.b64_img,
            "boxes": boxes,
            "polygons": [],
            "domain": "naval",
            "source_video": "teste_workflow_video.mp4",
            "frame_timestamp": 12.5,
            "model_used": "yolo11n",
            "is_ai_assisted": True,
            "human_corrected": True,
            "notes": "Caixa ajustada pelo operador humano apos deteccao da IA."
        }
        res = self.client.post("/api/annotation/save",
                               data=json.dumps(payload),
                               content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("image_id", data)
        image_id = data["image_id"]

        # Verifica na lista do dataset
        res_list = self.client.get("/api/annotation/list?domain=naval")
        self.assertEqual(res_list.status_code, 200)
        d_list = json.loads(res_list.data)
        self.assertGreater(d_list["total_images"], 0)

        # Carrega o frame anotado
        res_load = self.client.get(f"/api/annotation/load/{image_id}?domain=naval")
        self.assertEqual(res_load.status_code, 200)
        d_load = json.loads(res_load.data)
        self.assertEqual(d_load["status"], "ok")
        self.assertEqual(len(d_load["boxes"]), 1)

        # Deleta a anotacao para limpeza do teste
        res_del = self.client.delete(f"/api/annotation/delete/{image_id}?domain=naval")
        self.assertEqual(res_del.status_code, 200)

    def test_multi_domain_annotation_models(self):
        """Testa GET /api/annotation/models para dominios alem do naval (urbano, natureza, etc)."""
        for dom in ["urbano", "natureza", "fechado"]:
            res = self.client.get(f"/api/annotation/models?domain={dom}")
            self.assertEqual(res.status_code, 200)
            data = json.loads(res.data)
            self.assertEqual(data["status"], "ok")
            self.assertIn("models", data)


if __name__ == "__main__":
    unittest.main()
