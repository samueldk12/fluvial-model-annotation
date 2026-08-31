# -*- coding: utf-8 -*-
"""
Gerenciador de Presets e Arquiteturas de Visão Computacional.
Define a Pré-Arquitetura (Produção/Baseline) e a Nova Arquitetura de Teste/Experimentação,
permitindo salvar, exportar e carregar novas configurações em tempo de execução.
"""

import os
import json
import time

PRE_ARCHITECTURE_PRODUCTION = {
    "id": "pre_arch_production",
    "name": "Arquitetura de Produção: Ensemble Multi-Domínio (WBF + BoT-SORT + DINOv2 + IMO OCR)",
    "description": "Arquitetura oficial de produção: Fusão WBF (SAR MeWan2808 + SixOpen Y8Naval + COCO), Tiling na calha distante, Classificador Probabilístico 17D com Fundo Mediana, Rastreamento BoT-SORT com Âncora Histerese, DINOv2 Re-ID com Galeria HNSW e Validação Matemática IMO.",
    "version": "2.0.0-production",
    "is_production": True,
    "pipeline_config": {
        "active_model_id": "ensemble_full",
        "conf_threshold": 0.05,
        "iou_threshold": 0.35,
        "enable_night_enhancement": True,
        "enable_spatial_memory": True,
        "enable_water_segmentation": True,
        "enable_vit_reid": True,
        "enable_ocr": True,
        "min_vessel_size_px": 16
    },
    "ensemble_weights": {
        "mewan2808_sar": 0.40,
        "sixopen_y8naval": 0.35,
        "coco_generic": 0.25
    },
    "spatial_memory_params": {
        "spatial_gate_radius": 60.0,
        "memory_retention_time": 4.0,
        "reid_cosine_threshold": 0.92,
        "stationary_dist_threshold": 12.0
    }
}

TEST_ARCHITECTURE_EXPERIMENTAL = {
    "id": "test_arch_experimental",
    "name": "Arquitetura de Teste: YOLO11n + YOLO26n Edge Ultra-Rápido",
    "description": "Nova arquitetura experimental projetada para teste de alta taxa de quadros (FPS), baixa latência (<15ms) e validação rápida em hardware edge com atenção C3k2.",
    "version": "2.0.0-test",
    "is_production": False,
    "pipeline_config": {
        "active_model_id": "yolo11n",
        "conf_threshold": 0.20,
        "iou_threshold": 0.50,
        "enable_night_enhancement": False,  # Desativado para velocidade máxima em teste
        "enable_spatial_memory": True,
        "enable_water_segmentation": False, # Desativado para benchmark de ultra-baixa latência
        "enable_vit_reid": False,
        "enable_ocr": False,
        "min_vessel_size_px": 12
    },
    "ensemble_weights": {
        "yolo11n": 0.60,
        "yolo26n": 0.40
    },
    "spatial_memory_params": {
        "spatial_gate_radius": 45.0,
        "memory_retention_time": 2.5,
        "reid_cosine_threshold": 0.85,
        "stationary_dist_threshold": 10.0
    }
}


class ArchitecturePresetManager:
    """Gerencia snapshots e alternância de arquiteturas de visão computacional."""

    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.presets_dir = os.path.join(project_dir, "models", "architecture_presets")
        os.makedirs(self.presets_dir, exist_ok=True)
        self._init_default_presets()

    def _init_default_presets(self):
        """Grava os presets padrão se não existirem."""
        for arch in [PRE_ARCHITECTURE_PRODUCTION, TEST_ARCHITECTURE_EXPERIMENTAL]:
            fpath = os.path.join(self.presets_dir, f"{arch['id']}.json")
            if not os.path.exists(fpath):
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(arch, f, indent=2, ensure_ascii=False)

    def list_presets(self):
        """Retorna todas as arquiteturas disponíveis."""
        presets = []
        if os.path.exists(self.presets_dir):
            for f in os.listdir(self.presets_dir):
                if f.endswith(".json"):
                    fpath = os.path.join(self.presets_dir, f)
                    try:
                        with open(fpath, "r", encoding="utf-8") as fp:
                            data = json.load(fp)
                            presets.append(data)
                    except Exception:
                        pass
        return presets

    def get_preset(self, preset_id):
        """Busca uma arquitetura por ID."""
        for p in self.list_presets():
            if p.get("id") == preset_id:
                return p
        return None

    def save_preset(self, preset_data):
        """Salva uma nova arquitetura personalizada."""
        pid = preset_data.get("id") or f"arch_{int(time.time())}"
        preset_data["id"] = pid
        preset_data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        fpath = os.path.join(self.presets_dir, f"{pid}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(preset_data, f, indent=2, ensure_ascii=False)
        return preset_data
