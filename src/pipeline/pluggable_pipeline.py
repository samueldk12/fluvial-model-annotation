# -*- coding: utf-8 -*-
"""
Pipeline de Visão Computacional Acoplável (Pluggable Vision Pipeline).
Permite trocar dinamicamente modelos (YOLOv8, YOLO11, YOLO26, SAR, ONNX, Checkpoints PyTorch,
modelos customizados por upload) e alternar submódulos (Visão Noturna, Segmentação de Água,
Memória Espacial, Classificador ViT, OCR) em tempo de execução com efeito imediato.
"""

import os
import sys
import time
import math
import glob
import json
import numpy as np
import cv2
import torch
from PIL import Image
from ultralytics import YOLO
import onnxruntime as ort

from src.utils.night_vision_enhancer import enhance_night_vision, is_night_or_low_light
from src.utils.water_segmenter import WaterSegmenter
from src.pipeline.multi_domain_detector import MultiDomainVesselDetector, compute_iou, is_plausible_vessel_size
from src.utils.vessel_fingerprinter import VesselFingerprintExtractor
from src.tracking.vessel_spatial_memory import VesselSpatialMemoryTracker
from src.tracking.bot_sort import BoTSORTTracker
from src.reid.dinov2_extractor import DINOv2ReIDExtractor
from src.reid.sqlite_hnsw_gallery import VesselReIDGallery


class ModelRegistry:
    """Catálogo e registro de modelos disponíveis e carregamento sob demanda."""

    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.custom_models_dir = os.path.join(project_dir, "models", "custom_uploaded")
        os.makedirs(self.custom_models_dir, exist_ok=True)
        self.loaded_models = {}

    def get_catalog(self):
        """Retorna a lista de todos os modelos identificados no sistema."""
        catalog = [
            {
                "id": "ensemble_full",
                "name": "Ensemble Multi-Domínio (SAR + Naval ONNX + COCO + eWaSR)",
                "type": "ensemble",
                "framework": "PyTorch + ONNX",
                "description": "Fusão consensual multi-especialista para máxima robustez contra falsos positivos e oclusões.",
                "path": "ensemble",
                "available": True,
                "is_ensemble": True,
                "default_conf": 0.20
            },
            {
                "id": "mewan2808_sar",
                "name": "MeWan2808 YOLOv8 SAR (Fluvial & Radar)",
                "type": "detector",
                "framework": "Ultralytics YOLOv8",
                "description": "Fine-tuned em imagens SAR e radar naval, alta sensibilidade para cascos em águas agitadas.",
                "path": os.path.join(self.project_dir, "models", "02_sar_radar_and_edge", "MeWan2808_YOLOv8_SAR", "unquantized", "best.pt"),
                "default_conf": 0.15
            },
            {
                "id": "sixopen_y8naval",
                "name": "SixOpen Y8Naval (Aéreo & Satélite - 50 Classes)",
                "type": "detector",
                "framework": "ONNX Runtime",
                "description": "Otimizado para câmeras aéreas elevadas e imagens de satélite, identifica tipo e porte naval.",
                "path": os.path.join(self.project_dir, "models", "01_satellite_and_aerial_naval", "SixOpen_Y8NavalONNX", "Y8Naval.onnx"),
                "default_conf": 0.20
            },
            {
                "id": "yolo11n",
                "name": "YOLO11n Baseline (Ultralytics v11)",
                "type": "detector",
                "framework": "Ultralytics YOLO11",
                "description": "Arquitetura Ultralytics v11 ultra-leve e rápida (C3k2/SPPF).",
                "path": os.path.join(self.project_dir, "yolo11n.pt"),
                "default_conf": 0.20
            },
            {
                "id": "yolo26n",
                "name": "YOLO26n Baseline (Ultralytics v26)",
                "type": "detector",
                "framework": "Ultralytics YOLO26",
                "description": "Baseline experimental YOLO26 com atenção aprimorada.",
                "path": os.path.join(self.project_dir, "yolo26n.pt"),
                "default_conf": 0.20
            },
            {
                "id": "yolov8n",
                "name": "YOLOv8n Geral (COCO)",
                "type": "detector",
                "framework": "Ultralytics YOLOv8",
                "description": "Detector padrão YOLOv8 nano treinado em COCO (filtro classe 8: boat).",
                "path": os.path.join(self.project_dir, "yolov8n.pt"),
                "default_conf": 0.20
            },
            {
                "id": "mayrajeo_marine",
                "name": "Mayrajeo YOLOv8 Marine Vessel",
                "type": "detector",
                "framework": "Ultralytics YOLOv8",
                "description": "Fine-tuned para embarcações em perspectiva de cais/porto em ângulo baixo.",
                "path": os.path.join(self.project_dir, "models", "02_sar_radar_and_edge", "mayrajeo_YOLOv8_Marine_Vessel", "YOLOv8n", "yolov8n.pt"),
                "default_conf": 0.15
            },
            {
                "id": "vessel_perception_net",
                "name": "VesselPerceptionNet (Custom PyTorch Real)",
                "type": "backbone_perception",
                "framework": "PyTorch",
                "description": "Rede integrada de percepção e extração latente treinada para o canal de Santos.",
                "path": os.path.join(self.project_dir, "checkpoints", "vessel_perception_net_real.pt"),
                "default_conf": 0.25
            }
        ]

        # Verifica existência de arquivos
        for m in catalog:
            if m["path"] != "ensemble":
                m["available"] = os.path.exists(m["path"])
                if m["available"]:
                    m["size_mb"] = round(os.path.getsize(m["path"]) / (1024 * 1024), 2)
            else:
                m["available"] = True

        # Escaneia modelos customizados enviados pelo usuário
        custom_files = glob.glob(os.path.join(self.custom_models_dir, "*.*"))
        for cf in custom_files:
            ext = os.path.splitext(cf)[1].lower()
            if ext in [".pt", ".onnx", ".torchscript"]:
                fname = os.path.basename(cf)
                catalog.append({
                    "id": f"custom_{fname}",
                    "name": f"Custom: {fname}",
                    "type": "custom",
                    "framework": "Ultralytics/ONNX" if ext == ".onnx" else "PyTorch",
                    "description": f"Modelo customizado acoplado pelo usuário ({fname}).",
                    "path": cf,
                    "available": True,
                    "is_custom": True,
                    "size_mb": round(os.path.getsize(cf) / (1024 * 1024), 2),
                    "default_conf": 0.20
                })

        return catalog

    def load_model(self, model_id):
        """Carrega ou retorna da memória o modelo especificado."""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]

        catalog = {m["id"]: m for m in self.get_catalog()}
        if model_id not in catalog:
            raise ValueError(f"Modelo com ID '{model_id}' não encontrado no catálogo.")

        info = catalog[model_id]
        path = info["path"]
        if not os.path.exists(path) and model_id != "ensemble_full":
            raise FileNotFoundError(f"Arquivo de pesos do modelo não encontrado: {path}")

        loaded = None
        if path.endswith(".onnx"):
            session = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
            loaded = {"type": "onnx", "session": session, "path": path}
        elif path.endswith(".pt"):
            try:
                # Tenta carregar como modelo Ultralytics YOLO
                yolo = YOLO(path)
                names = getattr(yolo, "names", {}) or {}
                loaded = {"type": "yolo", "model": yolo, "names": names, "path": path}
            except Exception as e:
                # Fallback para checkpoint PyTorch puro
                chk = torch.load(path, map_location="cpu", weights_only=False)
                loaded = {"type": "torch", "checkpoint": chk, "path": path}

        if loaded:
            self.loaded_models[model_id] = loaded
        return loaded


from src.pipeline.architectures import ArchitecturePresetManager, PRE_ARCHITECTURE_PRODUCTION, TEST_ARCHITECTURE_EXPERIMENTAL


class PluggableVisionPipeline:
    """Motor de execução de visão computacional modular e acoplável."""

    def __init__(self, project_dir, default_ensemble_engine=None, vit_analyzer=None):
        self.project_dir = project_dir
        self.registry = ModelRegistry(project_dir)
        self.preset_manager = ArchitecturePresetManager(project_dir)
        self.vit_analyzer = vit_analyzer
        self.fingerprinter = VesselFingerprintExtractor()
        self.spatial_memory = VesselSpatialMemoryTracker(spatial_gate_radius=60.0, memory_retention_time=4.0)
        ewasr_path = os.path.join(project_dir, "extra_models", "eWaSR_ResNet18", "ewasr_resnet18.onnx")
        self.water_segmenter = WaterSegmenter(ewasr_path)
        self.last_water_mask = None

        # BoT-SORT: sem camera_geometry (nao ha calibracao real desta camera), entao
        # roda em modo honesto - Kalman + custo IoU/aparencia para associacao robusta de
        # trajetoria, mas SEM fingir velocidade em nos/destino GPS que exigiriam uma
        # homografia calibrada que nao existe. Ver bot_sort.py e AUDITORIA_ARQUITETURA.md.
        # Limiares recalibrados: esta câmera opera com scores tipicamente 0.15-0.35
        # (ver comentário em vessel_spatial_memory.py), bem abaixo dos 0.40-0.50 default
        # do BoT-SORT (calibrados p/ detectores fortes de benchmark MOT convencional).
        self.bot_sort = BoTSORTTracker(track_high_thresh=0.18, track_low_thresh=0.07, new_track_thresh=0.18, match_thresh=0.70, camera_geometry=None)

        # DINOv2 Re-ID: so ativa se o backbone real (facebook/dinov2-small) carregar.
        # Se cair no fallback de CNN aleatoria nao-treinada (sem internet/cache), os
        # embeddings seriam ruido e pareceriam "similaridade real" sem ser - por isso
        # desligamos o recurso inteiro nesse caso em vez de fabricar Re-ID falso.
        self.dinov2_extractor = None
        try:
            _dinov2 = DINOv2ReIDExtractor()
            if hasattr(_dinov2.backbone, "config"):
                self.dinov2_extractor = _dinov2
                print("[PluggableVisionPipeline] DINOv2 Re-ID carregado (facebook/dinov2-small).")
            else:
                print("[PluggableVisionPipeline] DINOv2 caiu no fallback nao-treinado - Re-ID por embedding DESLIGADO (evitando dado fabricado).")
        except Exception as e:
            print(f"[PluggableVisionPipeline] DINOv2 indisponivel ({e}) - Re-ID por embedding DESLIGADO.")

        self.reid_gallery = None
        try:
            gallery_db_path = os.path.join(project_dir, "data", "vessel_gallery.db")
            self.reid_gallery = VesselReIDGallery(db_path=gallery_db_path, embedding_dim=getattr(self.dinov2_extractor, "embedding_dim", 384))
        except Exception as e:
            print(f"[PluggableVisionPipeline] Galeria Re-ID (SQLite+HNSW) indisponivel ({e}).")

        # Configuração do pipeline ativo (inicializado com a Pré-Arquitetura de Produção)
        self.active_preset_id = "pre_arch_production"
        self.config = {
            "active_model_id": "ensemble_full",
            "conf_threshold": 0.05,
            "iou_threshold": 0.35,
            "enable_night_enhancement": True,
            "enable_spatial_memory": True,
            "enable_water_segmentation": True,
            "enable_vit_reid": True,
            "enable_ocr": True,
            "min_vessel_size_px": 16,
            "custom_classes_filter": None
        }

        # MultiDomainVesselDetector para o ensemble completo
        self.multi_detector = getattr(vit_analyzer, "multi_detector", None)
        if self.multi_detector is None:
            self.multi_detector = MultiDomainVesselDetector(project_dir)

        self.last_inference_latency_ms = 0.0
        self.last_detection_count = 0

    def apply_architecture_preset(self, preset_id_or_data):
        """Aplica um preset de arquitetura completo (Pré-Arquitetura Produção ou Teste)."""
        if isinstance(preset_id_or_data, str):
            preset = self.preset_manager.get_preset(preset_id_or_data)
            if not preset:
                raise ValueError(f"Preset de arquitetura '{preset_id_or_data}' não encontrado.")
        else:
            preset = preset_id_or_data

        self.active_preset_id = preset.get("id", "custom_arch")
        if "pipeline_config" in preset:
            self.update_config(preset["pipeline_config"])

        if "spatial_memory_params" in preset:
            sm_p = preset["spatial_memory_params"]
            if "spatial_gate_radius" in sm_p:
                self.spatial_memory.spatial_gate_radius = float(sm_p["spatial_gate_radius"])
            if "memory_retention_time" in sm_p:
                self.spatial_memory.memory_retention_time = float(sm_p["memory_retention_time"])
            if "reid_cosine_threshold" in sm_p:
                self.spatial_memory.reid_cosine_threshold = float(sm_p["reid_cosine_threshold"])

        return {
            "status": "ok",
            "active_preset_id": self.active_preset_id,
            "preset_name": preset.get("name"),
            "pipeline_status": self.get_status()
        }

    def update_config(self, new_params: dict):
        """Atualiza a configuração do pipeline em tempo real."""
        for k, v in new_params.items():
            if k in self.config:
                if k in ["conf_threshold", "iou_threshold"]:
                    self.config[k] = float(v)
                elif k in ["enable_night_enhancement", "enable_spatial_memory",
                          "enable_water_segmentation", "enable_vit_reid", "enable_ocr"]:
                    self.config[k] = bool(v)
                else:
                    self.config[k] = v
        return self.get_status()

    def get_status(self):
        """Retorna o status completo do pipeline e dos modelos."""
        catalog = self.registry.get_catalog()
        presets = self.preset_manager.list_presets()
        return {
            "config": self.config,
            "active_model_id": self.config["active_model_id"],
            "active_preset_id": self.active_preset_id,
            "last_latency_ms": round(self.last_inference_latency_ms, 1),
            "last_detection_count": self.last_detection_count,
            "catalog": catalog,
            "presets": presets
        }

    def _infer_single_yolo(self, yolo_wrapper, frame_bgr, conf):
        """Executa inferência com um detector YOLO individual."""
        model = yolo_wrapper["model"]
        names = yolo_wrapper["names"]
        
        # Filtra classes se for modelo COCO (80 classes -> 8=boat)
        target_classes = None
        if len(names) >= 80 and 8 in names:
            target_classes = [8]
        elif any("boat" in str(v).lower() or "ship" in str(v).lower() or "vessel" in str(v).lower() for v in names.values()):
            target_classes = [k for k, v in names.items() if any(w in str(v).lower() for w in ["boat", "ship", "vessel"])]

        kwargs = {"conf": conf, "verbose": False}
        if target_classes:
            kwargs["classes"] = target_classes

        res = model.predict(frame_bgr, **kwargs)
        detections = []
        for r in res:
            for b in r.boxes:
                box = b.xyxy[0].cpu().numpy().tolist()
                c = float(b.conf[0].item())
                cls_id = int(b.cls[0].item())
                cls_name = names.get(cls_id, f"class_{cls_id}")
                detections.append({
                    "bbox": box,
                    "conf": c,
                    "sources": [yolo_wrapper.get("path", "yolo_custom")],
                    "class_id": cls_id,
                    "class_name": cls_name
                })
        return detections

    def _infer_single_onnx(self, onnx_wrapper, frame_bgr, conf):
        """Executa inferência com um modelo ONNX (SixOpen ou custom)."""
        session = onnx_wrapper["session"]
        h_orig, w_orig = frame_bgr.shape[:2]
        
        # Redimensiona para 640x640 no formato NCHW RGB normalizado
        img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (640, 640))
        inp = img_resized.astype(np.float32) / 255.0
        inp = np.transpose(inp, (2, 0, 1))
        inp = np.expand_dims(inp, axis=0)

        input_name = session.get_inputs()[0].name
        outs = session.run(None, {input_name: inp})
        raw = outs[0]

        detections = []
        if raw.ndim == 3 and raw.shape[1] > raw.shape[2]:
            raw = np.transpose(raw, (0, 2, 1))

        if raw.ndim == 3:
            pred = raw[0]
            for row in pred:
                cx, cy, bw, bh = row[0:4]
                scores = row[4:]
                if len(scores) > 0:
                    cls_id = int(np.argmax(scores))
                    max_score = float(scores[cls_id])
                else:
                    max_score = 0.5
                    cls_id = 0

                if max_score >= conf:
                    x1 = max(0.0, (cx - bw / 2.0) * (w_orig / 640.0))
                    y1 = max(0.0, (cy - bh / 2.0) * (h_orig / 640.0))
                    x2 = min(float(w_orig), (cx + bw / 2.0) * (w_orig / 640.0))
                    y2 = min(float(h_orig), (cy + bh / 2.0) * (h_orig / 640.0))
                    detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "conf": max_score,
                        "sources": ["SixOpen_Y8Naval_ONNX"],
                        "class_id": cls_id,
                        "class_name": f"naval_{cls_id}"
                    })
        return detections

    def detect_raw(self, frame_bgr, conf=None):
        """Executa a detecção bruta conforme o modelo atualmente acoplado."""
        active_id = self.config["active_model_id"]
        conf_val = conf if conf is not None else self.config["conf_threshold"]

        if active_id == "ensemble_full":
            pil_img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            raw_dets = self.multi_detector.detect(pil_img, conf=conf_val)
            res = []
            for d in raw_dets:
                res.append({
                    "bbox": d["box"],
                    "conf": d["conf"],
                    "sources": d.get("sources", ["ensemble"]),
                    "class_name": "embarcacao"
                })
            return res

        # Modelo individual
        try:
            wrapper = self.registry.load_model(active_id)
        except Exception as e:
            print(f"[PluggableVisionPipeline] Erro ao carregar {active_id}: {e}. Fallback para multi_detector.")
            pil_img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            return [{"bbox": d["box"], "conf": d["conf"], "sources": ["fallback_ensemble"], "class_name": "embarcacao"}
                    for d in self.multi_detector.detect(pil_img, conf=conf_val)]

        if wrapper["type"] == "yolo":
            return self._infer_single_yolo(wrapper, frame_bgr, conf_val)
        elif wrapper["type"] == "onnx":
            return self._infer_single_onnx(wrapper, frame_bgr, conf_val)
        else:
            # Fallback
            pil_img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            return [{"bbox": d["box"], "conf": d["conf"], "sources": [active_id], "class_name": "embarcacao"}
                    for d in self.multi_detector.detect(pil_img, conf=conf_val)]

    def process_frame(self, frame_bgr, now_ts=None):
        """
        Processa um frame de vídeo completo aplicando o pipeline modular configurado.
        Retorna lista de embarcações confirmadas e atualizadas.
        """
        t0 = time.time()
        if now_ts is None:
            now_ts = time.time()

        h, w = frame_bgr.shape[:2]
        conf_thresh = self.config["conf_threshold"]

        # 1. Visão Noturna Modular
        if self.config["enable_night_enhancement"]:
            night_frame = enhance_night_vision(frame_bgr, gamma=0.50, clip_limit=3.8)
        else:
            night_frame = frame_bgr

        # 2. Prior de Posição da Memória Espacial
        position_priors = []
        if self.config["enable_spatial_memory"]:
            position_priors = self.spatial_memory.get_active_position_priors(now_ts)

        # 3. Detecção com o Modelo Acoplado Ativo
        raw_dets = self.detect_raw(frame_bgr, conf=conf_thresh)

        # 4. Segmentação de Água (se ativada)
        water_mask = None
        if self.config["enable_water_segmentation"] and self.water_segmenter.session is not None:
            water_mask = self.water_segmenter.segment(frame_bgr)
        self.last_water_mask = water_mask

        # 5. Filtros de Validação (Segmentação de Água, Laplaciano, Tamanho)
        filtered_candidates = []
        for d in raw_dets:
            b = d["bbox"]
            x1, y1, x2, y2 = b
            bw = x2 - x1
            bh = y2 - y1

            if bw < self.config["min_vessel_size_px"] or bh < self.config["min_vessel_size_px"]:
                continue

            # Prior boost se tiver memória espacial
            boost = 0.0
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            for p in position_priors:
                if math.hypot(cx - p["cx"], cy - p["cy"]) < p["radius"]:
                    boost = 0.15
                    break

            effective_conf = min(0.99, d["conf"] + boost)
            if effective_conf < conf_thresh:
                continue

            # Segmentação de água eWaSR modular
            if water_mask is not None:
                if not self.water_segmenter.is_on_water(b, water_mask):
                    continue

            # Score Laplaciano
            crop = frame_bgr[max(0, int(y1)):min(h, int(y2)), max(0, int(x1)):min(w, int(x2))]
            if crop.size > 0:
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                lap_score = min(0.95, max(0.20, cv2.Laplacian(gray, cv2.CV_64F).var() / 250.0))
            else:
                lap_score = 0.50

            filtered_candidates.append({
                "bbox": b,
                "score_ensemble_final": effective_conf,
                "conf_normal": d["conf"],
                "conf_night": d["conf"],
                "canal_mais_confiavel": d.get("sources", ["ativo"])[0],
                "score_laplaciano": lap_score,
                "fontes_detectoras": d.get("sources", [self.config["active_model_id"]]),
                "reforcado_por_memoria": boost > 0.0,
                "class_name": d.get("class_name", "embarcacao")
            })

        # NMS entre candidatos
        final_dets = []
        filtered_candidates.sort(key=lambda x: x["score_ensemble_final"], reverse=True)
        iou_thresh = self.config["iou_threshold"]
        for c in filtered_candidates:
            overlap = False
            for f in final_dets:
                if compute_iou(c["bbox"], f["bbox"]) > iou_thresh:
                    overlap = True
                    break
            if not overlap:
                final_dets.append(c)

        # 5b. Re-ID DINOv2: extrai embedding real por candidato (se ativado e modelo carregado)
        if self.config["enable_vit_reid"] and self.dinov2_extractor is not None:
            for d in final_dets:
                x1, y1, x2, y2 = [int(v) for v in d["bbox"]]
                crop = frame_bgr[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                if crop.size > 0:
                    try:
                        d["embedding"] = self.dinov2_extractor.extract_embedding(crop).tolist()
                    except Exception:
                        pass

        # 5c. BoT-SORT: Kalman + custo IoU/aparencia para confirmar continuidade real de
        # trajetoria entre frames, substituindo o reforço ingênuo por raio fixo por uma
        # associação de verdade (predição de posição + comparação de embedding real).
        bot_sort_input = [
            {"bbox": d["bbox"], "conf": d["score_ensemble_final"], "label": d.get("class_name", "Embarcacao"), "embedding": d.get("embedding")}
            for d in final_dets
        ]
        bot_tracks = self.bot_sort.update(bot_sort_input, now_ts)
        for bt in bot_tracks:
            if bt["hits"] < 2:
                continue
            best_det, best_iou = None, 0.30
            for d in final_dets:
                iou = compute_iou(d["bbox"], bt["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_det = d
            if best_det is not None:
                best_det["reforcado_por_memoria"] = True
                best_det["reforcado_por_botsort"] = True
                best_det["score_ensemble_final"] = min(0.99, best_det["score_ensemble_final"] + 0.10)

        # 5. Memória Espacial & Rastreamento Temporal
        if self.config["enable_spatial_memory"]:
            confirmed_vessels = self.spatial_memory.update(final_dets, self.fingerprinter, frame_bgr, now_ts, enable_ocr=self.config["enable_ocr"])

            # 5d. Galeria Re-ID persistente (SQLite + HNSW): registra/busca embeddings reais
            # entre sessões, permitindo Re-ID real de embarcações vistas em execuções anteriores.
            if self.config["enable_vit_reid"] and self.reid_gallery is not None:
                for v in confirmed_vessels:
                    emb = v.get("embedding")
                    if emb is None:
                        continue
                    v_id = v.get("vessel_id")
                    fp = v.get("fingerprint", {}) if isinstance(v.get("fingerprint"), dict) else {}
                    meta = {
                        "name": v.get("name", ""),
                        "imo": fp.get("numero_imo", ""),
                        "category_5classes": "Embarcacao"
                    }
                    try:
                        matches = self.reid_gallery.search(emb, k=1, similarity_threshold=0.75)
                        if matches and matches[0]["vessel_id"] != v_id:
                            v["reid_gallery_match"] = {
                                "vessel_id": matches[0]["vessel_id"],
                                "name": matches[0]["name"],
                                "similarity_score": matches[0]["similarity_score"],
                                "first_seen": matches[0]["first_seen"]
                            }
                        self.reid_gallery.register_or_update_vessel(v_id, emb, meta)
                    except Exception:
                        pass
        else:
            # Rastreamento simplificado direto sem memória temporal
            confirmed_vessels = []
            for idx, d in enumerate(final_dets):
                b = d["bbox"]
                cx = (b[0] + b[2]) / 2.0
                cy = (b[1] + b[3]) / 2.0
                confirmed_vessels.append({
                    "vessel_id": f"BR-STS-{idx+1:02d}",
                    "name": f"Embarcação {idx+1}",
                    "bbox": b,
                    "cx": cx,
                    "cy": cy,
                    "is_stationary": True,
                    "speed": 0.0,
                    "heading_deg": 0.0,
                    "cardinal": "N/D",
                    "destination": "Área de Fundeio / Canal",
                    "detection_data": d,
                    "fingerprint": {
                        "cor_casco": "N/D",
                        "texto_ocr": "N/D",
                        "proporcao_dimensao": "N/D"
                    },
                    "trajectory_trail": []
                })

        self.last_inference_latency_ms = (time.time() - t0) * 1000.0
        self.last_detection_count = len(confirmed_vessels)
        return confirmed_vessels
