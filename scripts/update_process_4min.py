# -*- coding: utf-8 -*-
"""
Processador de Vídeo Consolidado (4 Minutos) - Porto de Santos
Utiliza Memoria Espacial, Ensemble Neural e Rastro Historico 100% Limpo.
"""

import os
import sys
import time
import shutil
import numpy as np
import cv2
from ultralytics import YOLO

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.utils.night_vision_enhancer import enhance_night_vision
from src.pipeline.vessel_semantic_analyzer import VesselSemanticAnalyzer
from src.pipeline.vessel_ensemble_engine import VesselEnsembleEngine
from src.utils.vessel_fingerprinter import VesselFingerprintExtractor
from src.tracking.vessel_spatial_memory import VesselSpatialMemoryTracker

def process_and_join_4min():
    print("=" * 70)
    print("[SISTEMA NAVAL] Gerando Video de 4 Minutos (100% Limpo & Rastro Historico)...")
    print("=" * 70)

    yolo_path = os.path.join(project_dir, "models", "02_sar_radar_and_edge", "mayrajeo_YOLOv8_Marine_Vessel", "YOLOv8n", "yolov8n.pt")
    if not os.path.exists(yolo_path):
        yolo_path = "yolov8n.pt"

    yolo_model = YOLO(yolo_path)
    vit_analyzer = VesselSemanticAnalyzer()
    ensemble_engine = VesselEnsembleEngine(yolo_model, vit_analyzer)
    fingerprinter = VesselFingerprintExtractor()
    spatial_memory = VesselSpatialMemoryTracker(spatial_gate_radius=60.0, memory_retention_time=4.0)

    videos_input = [
        os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4"),
        os.path.join(project_dir, "data", "teste_porto_santos_1min.mp4")
    ]

    out_web_path = os.path.join(project_dir, "static", "video_analisado_4minutos.avi")
    os.makedirs(os.path.dirname(out_web_path), exist_ok=True)

    width, height = 1280, 720
    fps = 15.0
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out_writer = cv2.VideoWriter(out_web_path, fourcc, fps, (width, height))

    total_frames_processed = 0
    sim_time = 0.0

    try:
        for v_path in videos_input:
            if not os.path.exists(v_path):
                continue
            cap = cv2.VideoCapture(v_path)
            frame_idx = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                if frame_idx % 2 != 0:
                    continue

                total_frames_processed += 1
                sim_time += (1.0 / fps)

                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))

                display_frame = frame.copy()

                night_frame = enhance_night_vision(frame, gamma=0.50, clip_limit=3.8)
                ensemble_raw_dets = ensemble_engine.run_ensemble(frame, night_frame, height, width)
                confirmed_vessels = spatial_memory.update(ensemble_raw_dets, fingerprinter, frame, sim_time)

                current_min_label = f"Minuto {min(4, 1 + total_frames_processed // 375)}/4"

                if len(confirmed_vessels) > 0:
                    for tr in confirmed_vessels:
                        b = tr["bbox"]
                        x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                        cx, cy = tr["cx"], tr["cy"]
                        v_id = tr["vessel_id"]
                        is_stationary = tr["is_stationary"]
                        speed_val = tr["speed"]
                        dynamic_dest = tr["destination"]

                        # 1. RASTRO HISTÓRICO (Trajetoria Passada)
                        trail = tr.get("trajectory_trail", [])
                        if len(trail) >= 2:
                            pts_poly = np.array([[p["x"], p["y"]] for p in trail], np.int32).reshape((-1, 1, 2))
                            cv2.polylines(display_frame, [pts_poly], False, (0, 240, 255), 2, cv2.LINE_AA)
                            for p in trail:
                                cv2.circle(display_frame, (p["x"], p["y"]), 3, (0, 200, 255), -1)

                        # 2. CONTORNO DO BARCO
                        hull_color = (0, 230, 118) if is_stationary else (0, 240, 255)
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), hull_color, 2)

                        # 3. PREVISAO PARA ONDE VAI
                        if is_stationary:
                            cv2.circle(display_frame, (int(cx), int(cy)), 3, (0, 230, 118), -1)
                        else:
                            preds = spatial_memory.predict_future_positions(tr, [5.0, 10.0])
                            if len(preds) >= 2:
                                p5, p10 = preds[0], preds[1]
                                cv2.line(display_frame, (int(cx), int(cy)), (p10["x"], p10["y"]), (0, 255, 120), 2, cv2.LINE_AA)
                                cv2.circle(display_frame, (p10["x"], p10["y"]), 5, (0, 255, 120), -1)
                                dest_label = f"-> {dynamic_dest[:18]}"
                                cv2.putText(display_frame, dest_label, (p10["x"] + 6, p10["y"] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 120), 1, cv2.LINE_AA)

                        # 4. ETIQUETA NO VIDEO: APENAS ID E ESTADO
                        status_short = "PARADO (0.0 nos)" if is_stationary else f"NAVEGANDO ({speed_val:.1f} px/s)"
                        tag_str = f"{v_id} | {status_short}"
                        (tw, th), _ = cv2.getTextSize(tag_str, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)
                        tag_y = max(th + 8, y1 - 6)
                        tag_bg = display_frame.copy()
                        cv2.rectangle(tag_bg, (x1, tag_y - th - 5), (x1 + tw + 10, tag_y + 3), (6, 12, 18), -1)
                        cv2.addWeighted(tag_bg, 0.85, display_frame, 0.15, 0, display_frame)
                        cv2.rectangle(display_frame, (x1, tag_y - th - 5), (x1 + tw + 10, tag_y + 3), hull_color, 1)
                        cv2.putText(display_frame, tag_str, (x1 + 5, tag_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)

                else:
                    cv2.putText(display_frame, "CANAL DE NAVEGACAO LIVRE - MEMORIA ATIVA", (width // 2 - 270, int(height * 0.38)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 180), 2)

                # HUD Global
                hud_bg = display_frame.copy()
                cv2.rectangle(hud_bg, (0, 0), (width, 42), (5, 9, 14), -1)
                cv2.addWeighted(hud_bg, 0.90, display_frame, 0.10, 0, display_frame)
                
                status_msg = f"● [{current_min_label}] Video Consolidado (4 Min) | GPU: AMD Radeon RX 6750 XT"
                cv2.putText(display_frame, status_msg, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 229, 255), 2)
                cv2.putText(display_frame, "MEMORIA ESPACIAL: RASTRO & IDENTIDADE", (width - 430, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 120), 2)

                out_writer.write(display_frame)
                if total_frames_processed % 150 == 0:
                    print(f"  -> Processados {total_frames_processed} quadros ({total_frames_processed/15.0:.1f}s de video)...")

            cap.release()

    finally:
        out_writer.release()

    desktop_dst = "C:/Users/samue/Desktop/Video_Analisado_4Minutos_Porto_Santos.mp4"
    if os.path.exists(out_web_path):
        shutil.copy2(out_web_path, desktop_dst)
        print(f"\n[OK] Video de 4 minutos gerado com sucesso!")
        print(f"     Web:     '{out_web_path}' ({os.path.getsize(out_web_path)/(1024*1024):.2f} MB)")
        print(f"     Desktop: '{desktop_dst}' ({os.path.getsize(desktop_dst)/(1024*1024):.2f} MB)")

if __name__ == "__main__":
    process_and_join_4min()
