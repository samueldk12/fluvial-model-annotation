# -*- coding: utf-8 -*-
"""Teste Comparativo Automatizado: Pré-Arquitetura (Produção) vs Nova Arquitetura de Teste (Edge)."""

import os
import sys
import time
import unittest
import numpy as np
import cv2

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.pipeline.pluggable_pipeline import PluggableVisionPipeline


class TestBenchmarkComparison(unittest.TestCase):

    def setUp(self):
        self.pipeline = PluggableVisionPipeline(project_dir)
        sample_path = os.path.join(project_dir, "data", "santos_live_snapshot.jpg")
        if os.path.exists(sample_path):
            self.test_img = cv2.imread(sample_path)
        else:
            self.test_img = np.zeros((720, 1280, 3), dtype=np.uint8)

    def test_compare_production_vs_test_architecture(self):
        """Executa e compara latência e métricas entre a Pré-Arquitetura e a Arquitetura de Teste."""
        print("\n" + "=" * 70)
        print("BENCHMARK COMPARATIVO: PRÉ-ARQUITETURA (PROD) vs ARQUITETURA DE TESTE (EDGE)")
        print("=" * 70)

        # 1. Benchmark da Pré-Arquitetura (Produção)
        self.pipeline.apply_architecture_preset("pre_arch_production")
        # Warmup
        _ = self.pipeline.process_frame(self.test_img)
        
        times_prod = []
        for _ in range(3):
            t0 = time.time()
            vessels_prod = self.pipeline.process_frame(self.test_img)
            times_prod.append((time.time() - t0) * 1000.0)

        avg_lat_prod = np.mean(times_prod)

        # 2. Benchmark da Nova Arquitetura de Teste (Edge)
        self.pipeline.apply_architecture_preset("test_arch_experimental")
        # Warmup
        _ = self.pipeline.process_frame(self.test_img)

        times_test = []
        for _ in range(3):
            t0 = time.time()
            vessels_test = self.pipeline.process_frame(self.test_img)
            times_test.append((time.time() - t0) * 1000.0)

        avg_lat_test = np.mean(times_test)

        speedup = (avg_lat_prod / avg_lat_test) if avg_lat_test > 0 else 1.0

        print(f"\n1. Pré-Arquitetura (Produção Multi-Domínio):")
        print(f"   - Latência Média: {avg_lat_prod:.1f} ms por frame (~{1000.0/max(avg_lat_prod,1):.1f} FPS)")
        print(f"   - Embarcações Rastreadas: {len(vessels_prod)}")
        print(f"   - Robustez / Consenso: Máxima (3 detectores + eWaSR + ViT + Memória)")

        print(f"\n2. Nova Arquitetura de Teste (YOLO11n Edge):")
        print(f"   - Latência Média: {avg_lat_test:.1f} ms por frame (~{1000.0/max(avg_lat_test,1):.1f} FPS)")
        print(f"   - Embarcações Rastreadas: {len(vessels_test)}")
        print(f"   - Foco: Velocidade e Inferência Ultra-Leve em Edge")
        print(f"   - Speedup Observado: {speedup:.2f}x mais rápida")

        print("=" * 70 + "\n")

        # Restaura produção
        self.pipeline.apply_architecture_preset("pre_arch_production")
        self.assertGreater(avg_lat_prod, 0.0)
        self.assertGreater(avg_lat_test, 0.0)


if __name__ == "__main__":
    unittest.main()
