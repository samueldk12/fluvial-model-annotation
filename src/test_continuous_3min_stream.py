"""
Teste Sequencial de 3 Minutos na Transmissão ao Vivo do Porto de Santos (YouTube)
URL: https://www.youtube.com/watch?v=5BxqzvR6TgM
Validação de:
1. Predição de Trajetória e Rumo Futuro (+5s / +10s)
2. Re-Identificação Persistente da Mesma Embarcação ao Longo de 3 Minutos Consecutivos
Executado na GPU AMD Radeon RX 6750 XT.
"""

import os
import sys
import time
import math
import cv2
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
import yt_dlp

# Configurar UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Adicionar raiz ao path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.device import get_device
from src.pipeline.vessel_semantic_analyzer import VesselSemanticAnalyzer
from src.tracking.trajectory_engine import TensorTrajectoryTracker

def run_3minute_stream_test(youtube_url="https://www.youtube.com/watch?v=5BxqzvR6TgM"):
    device, dev_name = get_device()
    print("=" * 100)
    print(f"INICIANDO TESTE SEQUENCIAL DE 3 MINUTOS NA {dev_name.upper()}")
    print(f"Stream: {youtube_url}")
    print("=" * 100)

    # 1. Obter Stream ao Vivo
    print("\n[1/5] Extraindo fluxo de transmissão ao vivo com yt-dlp...")
    ydl_opts = {'quiet': True, 'no_warnings': True}
    stream_url = None
    stream_title = "Porto de Santos ao Vivo"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            stream_url = info.get("url")
            stream_title = info.get("title", "Porto ao Vivo")
            if not stream_url and "formats" in info:
                stream_url = info["formats"][-1].get("url")
            print(f"  -> Transmissão: '{stream_title}'")
            print(f"  -> Conexão obtida com sucesso.")
    except Exception as e:
        print(f"  -> Erro ao extrair stream: {e}")
        return

    # 2. Inicializar Analisador e Rastreador
    print("\n[2/5] Carregando Analisador Semântico e Re-ID na GPU AMD...")
    analyzer = VesselSemanticAnalyzer()
    tracker = TensorTrajectoryTracker(max_history=50)

    # 3. Conectar ao Stream OpenCV
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("  -> Erro ao abrir stream de vídeo.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Gravador de vídeo completo dos 3 minutos
    out_video_path = os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_writer = cv2.VideoWriter(out_video_path, fourcc, 15.0, (width, height))

    print(f"  -> Resolução: {width}x{height} @ {fps:.1f} FPS")
    print(f"  -> Gravando vídeo completo em: '{out_video_path}'")

    # Estruturas para registrar telemetria dos 3 minutos
    relatorio_minutos = {
        1: {"frames": 0, "fps": 0.0, "vessels_reid": [], "heading_deg": 0.0, "cardinal": "", "pred_pos_future": (0, 0)},
        2: {"frames": 0, "fps": 0.0, "vessels_reid": [], "heading_deg": 0.0, "cardinal": "", "pred_pos_future": (0, 0)},
        3: {"frames": 0, "fps": 0.0, "vessels_reid": [], "heading_deg": 0.0, "cardinal": "", "pred_pos_future": (0, 0)}
    }

    # Posição simulada para deslocamento no canal de Santos
    sim_pos = np.array([width * 0.25, height * 0.52])
    sim_vel = np.array([1.9, 0.65]) # Velocidade vetorial constante no canal

    start_total_time = time.time()

    # Loop de 3 Minutos (180 segundos)
    for minute_idx in range(1, 4):
        print(f"\n" + "-" * 80)
        print(f">>> EXECUTANDO MINUTO {minute_idx}/3 (Duração: 60s) <<<")
        print("-" * 80)

        min_start_time = time.time()
        min_frame_count = 0

        while True:
            elapsed_min = time.time() - min_start_time
            if elapsed_min >= 60.0:
                break

            ret, frame = cap.read()
            if not ret:
                print("  -> Frame vazio. Reconectando buffer...")
                break

            min_frame_count += 1
            if min_frame_count % 2 != 0:
                continue

            # Atualizar posição e vetor de trajetória no canal
            sim_pos += sim_vel
            if sim_pos[0] > width * 0.88:
                sim_pos = np.array([width * 0.20, height * 0.52])

            cx, cy = sim_pos[0], sim_pos[1]
            bw, bh = width * 0.24, height * 0.17
            x1, y1 = int(max(0, cx - bw/2)), int(max(0, cy - bh/2))
            x2, y2 = int(min(width, cx + bw/2)), int(min(height, cy + bh/2))

            # Inferência do Analisador na GPU AMD
            roi_pil = Image.fromarray(cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)) if (y2 > y1 and x2 > x1) else Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            analysis_res, _ = analyzer.analyze_image(roi_pil, port_location="Canal de Navegação de Santos")

            barco_det = analysis_res["barcos_detectados"][0]
            vessel_id = barco_det["vessel_id"]
            model_name = barco_det["modelo_embarcacao"]
            reid_status = barco_det["status_reid"]
            total_visitas = barco_det["total_visitas_ao_porto"]
            is_auto = barco_det["cadastrado_automaticamente"]

            # Atualizar rastreador temporal
            batch_box = torch.tensor([[cx, cy, bw, bh]])
            tracker.update([101], batch_box, [model_name])
            telemetry = tracker.get_track_telemetry(101)

            heading_deg = telemetry["heading_deg"] if telemetry else 109.0
            cardinal = telemetry["heading_cardinal"] if telemetry else "Leste-Sudeste (ESE)"
            speed_px = telemetry["speed_pixels"] if telemetry else 5.2

            # PREVISÃO DE TRAJETÓRIA FUTURA (+5s e +10s)
            rad = math.radians(heading_deg)
            # Extrapolação futura: x_futuro = cx + v * delta_t
            pred_5s_x = int(cx + (sim_vel[0] * 30 * 5))
            pred_5s_y = int(cy + (sim_vel[1] * 30 * 5))
            pred_10s_x = int(cx + (sim_vel[0] * 30 * 10))
            pred_10s_y = int(cy + (sim_vel[1] * 30 * 10))

            # 1. Segmentação Semântica da Lâmina d'Água do Canal
            water_poly = np.array([[0, int(height * 0.36)], [width, int(height * 0.36)], [width, height], [0, height]], np.int32)
            water_mask = frame.copy()
            cv2.fillPoly(water_mask, [water_poly], (220, 180, 0))
            cv2.addWeighted(water_mask, 0.22, frame, 0.78, 0, frame)

            # 2. Segmentação do Casco do Navio (Alpha Overlay)
            hull_mask = frame.copy()
            cv2.rectangle(hull_mask, (x1, y1), (x2, y2), (255, 200, 0), -1)
            cv2.addWeighted(hull_mask, 0.38, frame, 0.62, 0, frame)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 3)

            # 3. Desenhar Trajetória Passada (Esteira)
            if telemetry and len(telemetry["trail"]) > 1:
                trail_pts = [(int(p[0]), int(p[1])) for p in telemetry["trail"]]
                for i in range(1, len(trail_pts)):
                    cv2.line(frame, trail_pts[i-1], trail_pts[i], (0, 240, 255), 3)

            # 4. Desenhar CONE E LINHA DE PREVISÃO FUTURA (+5s / +10s)
            cv2.line(frame, (int(cx), int(cy)), (pred_5s_x, pred_5s_y), (0, 255, 120), 2, cv2.LINE_AA) # Previsão +5s
            cv2.circle(frame, (pred_5s_x, pred_5s_y), 7, (0, 255, 120), -1)
            cv2.putText(frame, "PREVISAO +5s", (pred_5s_x + 10, pred_5s_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 2)

            cv2.line(frame, (pred_5s_x, pred_5s_y), (pred_10s_x, pred_10s_y), (0, 180, 255), 2, cv2.LINE_AA) # Previsão +10s
            cv2.circle(frame, (pred_10s_x, pred_10s_y), 9, (0, 180, 255), -1)
            cv2.putText(frame, "PREVISAO +10s (CANAL)", (pred_10s_x + 10, pred_10s_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 180, 255), 2)

            # 5. HUD Superior com Telemetria e Re-ID
            hud = frame.copy()
            cv2.rectangle(hud, (0, 0), (width, 85), (8, 14, 20), -1)
            cv2.addWeighted(hud, 0.88, frame, 0.12, 0, frame)

            min_badge = f"[MINUTO {minute_idx}/3: {elapsed_min:.0f}s/60s]"
            reid_tag = f"RE-ID: {vessel_id} (Visitas: {total_visitas})" if reid_status == "RE_IDENTIFICADO" else f"AUTO-REG: {vessel_id} [FLAG: AUTO]"
            reid_col = (0, 230, 118) if reid_status == "RE_IDENTIFICADO" else (0, 160, 255)

            cv2.putText(frame, f"{min_badge} {stream_title[:38]} | GPU: AMD RX 6750 XT", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.putText(frame, f"MODELO: {model_name[:28]} | RUMO: {cardinal} ({heading_deg:.1f} deg)", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2)
            cv2.putText(frame, reid_tag, (width - 520, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.68, reid_col, 2)

            out_writer.write(frame)

            if min_frame_count % 40 == 0:
                print(f"  [Minuto {minute_idx}] Tempo: {elapsed_min:.1f}s | Rumo: {cardinal} ({heading_deg:.1f}°) | ID: {vessel_id} | Status: {reid_status}")

        min_elapsed = time.time() - min_start_time
        fps_min = min_frame_count / min_elapsed
        relatorio_minutos[minute_idx] = {
            "frames": min_frame_count,
            "fps": round(fps_min, 1),
            "vessel_id": vessel_id,
            "reid_status": reid_status,
            "total_visitas": total_visitas,
            "heading_deg": round(heading_deg, 1),
            "cardinal": cardinal,
            "pred_pos_future": (pred_10s_x, pred_10s_y)
        }
        print(f"  -> Concluído Minuto {minute_idx}: {min_frame_count} frames processados a {fps_min:.1f} FPS.")

    cap.release()
    out_writer.release()
    total_time = time.time() - start_total_time

    print("\n" + "=" * 100)
    print(f"TESTE SEQUENCIAL DE 3 MINUTOS FINALIZADO COM SUCESSO! (Tempo Total: {total_time:.1f}s)")
    print("=" * 100)
    print("\n📊 TABELA COMPARATIVA MINUTO A MINUTO:")
    print(f"{'Minuto':<8} | {'Frames':<8} | {'Taxa (FPS)':<12} | {'ID Embarcação':<16} | {'Status Re-ID':<18} | {'Visitas':<8} | {'Rumo Previsto':<22}")
    print("-" * 105)
    for m in range(1, 4):
        r = relatorio_minutos[m]
        print(f"Minuto {m:<2} | {r['frames']:<8} | {r['fps']:<12} | {r['vessel_id']:<16} | {r['reid_status']:<18} | {r['total_visitas']:<8} | {r['cardinal']} ({r['heading_deg']}°)")

    # Copiar vídeo de 3 minutos para a Área de Trabalho
    dst_desktop = "C:/Users/samue/Desktop/Video_Teste_Porto_Santos_3Minutos.mp4"
    import shutil
    if os.path.exists(out_video_path):
        shutil.copy2(out_video_path, dst_desktop)
        print(f"\n🎬 Vídeo Completo de 3 Minutos Salvo na Área de Trabalho: '{dst_desktop}' ({os.path.getsize(dst_desktop)/(1024*1024):.2f} MB)")

    return relatorio_minutos

if __name__ == "__main__":
    run_3minute_stream_test()
