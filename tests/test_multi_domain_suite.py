# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados para a Plataforma Multi-Domínio de Visão Computacional.
Testa os 7 domínios, analisadores, gerenciadores de dataset e rotas HTTP do servidor Flask.
"""

import os
import sys
import unittest
import numpy as np
import cv2

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.domains.domain_config import DOMAINS_CONFIG
from src.domains.domain_analyzer import DomainVisionAnalyzer
from src.domains.domain_registry import DomainRegistryManager
from src.annotation.dataset_manager import DatasetAnnotationManager
from src.annotation.class_presets import ClassPresetManager
from src.web.app import app


class TestMultiDomainPlatform(unittest.TestCase):

    def setUp(self):
        self.project_dir = project_root
        self.domains = ["naval", "urbano", "fechado", "natureza", "objetos", "tatuagens", "digitais"]

    def test_01_domain_configs(self):
        """Verifica se todos os 7 domínios estão corretamente configurados."""
        for d in self.domains:
            self.assertIn(d, DOMAINS_CONFIG, f"Domínio {d} ausente na configuração")
            conf = DOMAINS_CONFIG[d]
            self.assertIn("name", conf)
            self.assertIn("icon", conf)
            self.assertIn("accent_color", conf)
            self.assertIn("classes", conf)
            self.assertGreater(len(conf["classes"]), 0)

    def test_02_domain_analyzers(self):
        """Testa inicialização e análise de imagem para cada um dos 7 domínios."""
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Desenha alguns retângulos coloridos para teste
        cv2.rectangle(test_img, (50, 50), (200, 200), (0, 255, 0), -1)
        cv2.rectangle(test_img, (300, 200), (500, 400), (0, 0, 255), -1)

        for d in self.domains:
            analyzer = DomainVisionAnalyzer(self.project_dir, d)
            res, annotated = analyzer.analyze_image(test_img)
            self.assertEqual(res["dominio"], d)
            self.assertIn("semantica_cena", res)
            self.assertIn("targets_detectados", res)
            self.assertIsNotNone(annotated)

    def test_03_domain_registries(self):
        """Testa o isolamento e persistência do registro de cadastros por domínio."""
        for d in self.domains:
            reg = DomainRegistryManager(self.project_dir, d)
            items = reg.get_all()
            self.assertIsInstance(items, list)
            self.assertGreater(len(items), 0)

    def test_04_dataset_managers(self):
        """Testa o gerenciamento de datasets YOLO específico para cada domínio."""
        for d in self.domains:
            mgr = DatasetAnnotationManager(self.project_dir, d)
            classes = mgr.get_classes()
            self.assertIsInstance(classes, list)
            self.assertGreater(len(classes), 0)

    def test_05_class_presets(self):
        """Testa se os presets padrão para cada domínio estão disponíveis."""
        cpm = ClassPresetManager(self.project_dir)
        presets = cpm.list_presets()
        self.assertGreaterEqual(len(presets), 7)

    def test_06_flask_routes(self):
        """Testa resposta HTTP 200 de todas as páginas e rotas do servidor Flask."""
        client = app.test_client()

        # 1. Página Inicial / Hub
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"AI VISION HUB", r.data)

        # 2. Páginas de cada um dos 7 domínios
        for d in self.domains:
            # Página de Monitoramento
            r_mon = client.get(f"/{d}")
            self.assertEqual(r_mon.status_code, 200, f"Falha ao carregar /{d}")

            # Estúdio de Anotação
            r_ano = client.get(f"/{d}/anotar")
            self.assertEqual(r_ano.status_code, 200, f"Falha ao carregar /{d}/anotar")

            # Documentação Técnica
            r_doc = client.get(f"/{d}/sobre")
            self.assertEqual(r_doc.status_code, 200, f"Falha ao carregar /{d}/sobre")

            # API de Telemetria
            r_tel = client.get(f"/api/{d}/live_telemetry")
            self.assertEqual(r_tel.status_code, 200)

            # API de Registros
            r_reg = client.get(f"/api/{d}/registry")
            self.assertEqual(r_reg.status_code, 200)


if __name__ == "__main__":
    unittest.main()
