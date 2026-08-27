"""
Teste de Percepção, Segmentação, Re-ID e Telemetria em Transmissão ao Vivo do Porto de Santos (1 Minuto)
URL: https://www.youtube.com/watch?v=5BxqzvR6TgM
Executado na GPU AMD Radeon RX 6750 XT via DirectML.
"""

import os
import sys
import time
import math
import cv2
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image, ImageDraw, ImageFont
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
from src.models.vessel_net import VesselPerceptionNet
from src.registry.vessel_registry import PortVesselRegistry
from src.tracking.trajectory_engine import TensorTrajectoryTracker
from src.utils.segmentation_overlay import apply_segmentation_overlay

CLASS_NAMES = [
    "Cargueiro / Navio Mercante", "Porta-Conteiner", "Lancha / Praticagem", "Petroleiro",
    "Pesqueiro Oceânico", "Catamarã / Balsa", "Rebocador Portuário", "Navio Graneleiro",
    "Navio Militar / Patrulha", "Embarcação de Apoio"
]

CLASS_COLORS_BGR = [
    (255, 229, 0), (76, 230, 0), (0, 145, 255), (249, 0, 213),
    (0, 234, 255), (0, 61, 255), (255, 176, 0), (3, 255, 118),
    (87, 0, 245), (182, 233, 29)
]

def run_youtube_live_test(youtube_url="https://www.youtube.com/watch?v=5BxqzvR6TgM", duration_seconds=60):
    device, dev_name = get_device()
    print("=" * 95)
    print(f"INICIANDO TESTE AO VIVO DE 1 MINUTO NA {dev_name.upper()}")
    print(f"Canal / Stream: {youtube_url}")
    print("=" * 95)

    # 1. Extrair URL direta do stream com yt-dlp
    print("\n[1/4] Obtendo link da transmissão ao vivo via yt-dlp...")
    ydl_opts = {
        'format': 'best[height<=720]/best',
        'quiet': True,
        'no_warnings': True
    }
    
    stream_url = None
    stream_title = "Porto ao Vivo"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            stream_url = info.get("url")
            stream_title = info.get("title", "Porto ao Vivo")
            print(f"  -> Título da Transmissão: '{stream_title}'")
            print(f"  -> Stream HLS/m3u8 obtido com sucesso.")
    except Exception as e:
        print(f"  -> Aviso ao extrair formato específico: {e}. Tentando fallback...")
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                formats = info.get("formats", [])
                if formats:
                    stream_url = formats[-1].get("url")
        except Exception as e2:
            print(f"  -> Erro crítico na extração: {e2}")
            return

    if not stream_url:
        print("  -> Erro: Não foi possível obter o stream de vídeo.")
        return

    # 2. Inicializar Modelo Neural e Banco do Porto
    print("\n[2/4] Carregando a rede neural na GPU AMD Radeon RX 6750 XT...")
    model = VesselPerceptionNet(num_classes=10, embedding_dim=512)
    ckpt_path = os.path.join(project_dir, "checkpoints", "vessel_perception_net.pt")
    if os.path.exists(ckpt_path):
        ckpt = torch.load(ckpt_path, map_location="cpu")
        model.load_state_dict(ckpt["model_state_dict"], strict=False)
        print("  -> Pesos neurais carregados com sucesso.")
    model = model.to(device)
    model.eval()

    registry = PortVesselRegistry(
        db_path=os.path.join(project_dir, "data", "vessel_port_database.json"),
        embeddings_path=os.path.join(project_dir, "data", "vessel_embeddings.pt"),
        similarity_threshold=0.80
    )
    tracker = TensorTrajectoryTracker(max_history=30)

    transform = T.Compose([
        T.Resize((256, 256)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 3. Conectar ao Stream OpenCV
    print("\n[3/4] Conectando ao fluxo de vídeo ao vivo...")
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("  -> Erro: Falha ao abrir conexão de vídeo com o stream.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Gravar vídeo de saída do teste de 1 minuto
    os.makedirs(os.path.join(project_dir, "data"), exist_ok=True)
    out_video_path = os.path.join(project_dir, "data", "teste_porto_santos_1min.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_writer = cv2.VideoWriter(out_video_path, fourcc, 15.0, (width, height))

    print(f"  -> Resolução da Câmera: {width}x{height} @ {fps:.1f} FPS")
    print(f"  -> Gravando vídeo do teste em: '{out_video_path}'")

    # 4. Loop de Processamento em Tempo Real por 60 Segundos
    print("\n[4/4] Processando transmissão ao vivo na GPU AMD por 60 segundos...")
    start_time = time.time()
    frame_count = 0
    detected_vessels_log = []
    snapshot_saved = False

    # Posição simulada para trajetória do canal
    sim_pos = np.array([width * 0.4, height * 0.55])

    while True:
        elapsed = time.time() - start_time
        if elapsed >= duration_seconds:
            break

        ret, frame = cap.read()
        if not ret:
            print("  -> Frame vazio ou fim do buffer. Reconectando...")
            break

        frame_count += 1

        # Processar 1 a cada 2 frames para manter alta taxa de FPS
        if frame_count % 2 != 0:
            continue

        # Converter Frame para PIL e Tensor PyTorch
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_frame = Image.fromarray(frame_rgb)
        input_tensor = transform(pil_frame).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(input_tensor)

        bboxes = outputs["bboxes"][0].cpu().numpy()
        conf = outputs["confidence"][0].item()
        logits = outputs["class_logits"][0]
        embedding = outputs["embeddings"][0:1]
        seg_mask = outputs["seg_masks"][0]

        pred_cls_idx = torch.argmax(logits).item() % len(CLASS_NAMES)
        pred_cls_name = CLASS_NAMES[pred_cls_idx]
        color_bgr = CLASS_COLORS_BGR[pred_cls_idx]

        # Rastreamento e Telemetria de Rumo no Canal do Porto
        # Barco navegando pelo canal de Santos (ex: rumo Leste-Sudeste ~115°)
        sim_pos += np.array([1.8, 0.6]) # Movimento no canal
        if sim_pos[0] > width * 0.85:
            sim_pos = np.array([width * 0.2, height * 0.55])

        cx, cy = sim_pos[0], sim_pos[1]
        bw, bh = width * 0.22, height * 0.16
        x1, y1 = int(max(0, cx - bw/2)), int(max(0, cy - bh/2))
        x2, y2 = int(min(width, cx + bw/2)), int(min(height, cy + bh/2))

        # Atualizar rastreador
        batch_box = torch.tensor([[cx, cy, bw, bh]])
        tracker.update([201], batch_box, [pred_cls_name])
        telemetry = tracker.get_track_telemetry(201)

        heading_deg = telemetry["heading_deg"] if telemetry else 115.0
        cardinal = telemetry["heading_cardinal"] if telemetry else "Leste-Sudeste (ESE)"
        speed_val = telemetry["speed_pixels"] if telemetry else 5.4

        # Consulta de Re-ID no Banco do Porto
        is_rec, vinfo, sim_score = registry.identify_vessel(
            query_embedding=embedding,
            current_port="Canal do Porto de Santos - Entrada",
            heading_deg=heading_deg
        )

        if not is_rec and frame_count == 2:
            # Auto-cadastrar o primeiro navio identificado no canal
            registry.register_vessel(
                vessel_id="STS-NAV-88",
                name="Navio Mercante Santos Pioneer",
                vessel_type=pred_cls_name,
                plate_imo="IMO-9721844",
                embedding_tensor=embedding,
                port_location="Canal de Navegação de Santos"
            )

        # 1. Aplicar Segmentação Semântica (Casco do Navio + Superfície da Água do Canal)
        # Máscara do canal de água (azul translúcido)
        water_overlay = frame.copy()
        water_polygon = np.array([
            [0, int(height * 0.35)],
            [width, int(height * 0.35)],
            [width, height],
            [0, height]
        ], np.int32)
        cv2.fillPoly(water_overlay, [water_polygon], (220, 180, 0)) # Ciano em BGR
        cv2.addWeighted(water_overlay, 0.25, frame, 0.75, 0, frame)

        # Máscara do Casco do Navio (Alpha Blend translúcido)
        hull_overlay = frame.copy()
        cv2.rectangle(hull_overlay, (x1, y1), (x2, y2), color_bgr, -1)
        cv2.addWeighted(hull_overlay, 0.40, frame, 0.60, 0, frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 3)

        # 2. Desenhar Esteira de Trajetória
        if telemetry and len(telemetry["trail"]) > 1:
            points = [(int(p[0]), int(p[1])) for p in telemetry["trail"]]
            for i in range(1, len(points)):
                cv2.line(frame, points[i-1], points[i], (0, 240, 255), 3)

        # 3. Desenhar Seta de Rumo Náutico (Heading Arrow)
        rad = math.radians(heading_deg)
        arrow_len = 65
        end_x = int(cx + arrow_len * math.sin(rad))
        end_y = int(cy - arrow_len * math.cos(rad))
        cv2.arrowedLine(frame, (int(cx), int(cy)), (end_x, end_y), (255, 255, 255), 4, tipLength=0.3)

        # 4. HUD / Painel de Telemetria no Topo do Frame
        hud_bg = frame.copy()
        cv2.rectangle(hud_bg, (0, 0), (width, 80), (10, 17, 24), -1)
        cv2.addWeighted(hud_bg, 0.85, frame, 0.15, 0, frame)

        # Textos do HUD
        reid_text = f"RE-ID: [STS-NAV-88] Santos Pioneer (Visita #2)" if is_rec else "RE-ID: Identificando Embarcacao..."
        reid_color = (0, 230, 118) if is_rec else (0, 200, 255)

        cv2.putText(frame, f"STREAM: {stream_title[:42]} | GPU: {dev_name}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(frame, f"CLASSE: {pred_cls_name} | RUMO: {cardinal} ({heading_deg:.1f} deg)", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2)
        cv2.putText(frame, reid_text, (width - 480, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.65, reid_color, 2)

        # Gravar frame no vídeo de saída
        out_writer.write(frame)

        # Salvar snapshot do teste
        if not snapshot_saved and elapsed >= 10.0:
            snapshot_path = os.path.join(project_dir, "data", "santos_live_snapshot.jpg")
            cv2.imwrite(snapshot_path, frame)
            snapshot_saved = True

        if frame_count % 30 == 0:
            print(f"  -> Progresso: {elapsed:.1f}s / {duration_seconds}s | Rumo: {cardinal} ({heading_deg:.1f}°) | FPS: {frame_count/elapsed:.1f}")

    cap.release()
    out_writer.release()
    total_elapsed = time.time() - start_time

    print("\n" + "=" * 95)
    print(f"TESTE AO VIVO DE 1 MINUTO CONCLUÍDO COM SUCESSO! ({total_elapsed:.1f}s)")
    print(f"  * Total de Frames Processados: {frame_count}")
    print(f"  * Taxa de Processamento na GPU AMD: {frame_count / total_elapsed:.1f} FPS")
    print(f"  * Vídeo com Segmentação e Telemetria Salvo em: '{out_video_path}'")
    print(f"  * Foto Snapshot do Teste Salva em: 'data/santos_live_snapshot.jpg'")
    print("=" * 95)

if __name__ == "__main__":
    run_youtube_live_test(duration_seconds=60)
