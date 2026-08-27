# -*- coding: utf-8 -*-
"""
Sistema Web de Monitoramento Naval - Porto de Santos
Painel Inteligente com Arquitetura de Modelos Acopláveis,
Estúdio de Anotação & Dataset YOLO, Memória Espacial e Telemetria em Tempo Real.
"""

import os
import sys
import time
import json
import base64
import math
import numpy as np
import cv2
import yt_dlp
from werkzeug.utils import secure_filename
from flask import Flask, Response, render_template_string, jsonify, request, send_from_directory, send_file
from ultralytics import YOLO

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.utils.night_vision_enhancer import enhance_night_vision
from src.pipeline.vessel_semantic_analyzer import VesselSemanticAnalyzer
from src.pipeline.vessel_ensemble_engine import VesselEnsembleEngine
from src.pipeline.pluggable_pipeline import PluggableVisionPipeline
from src.annotation.dataset_manager import DatasetAnnotationManager
from src.web.templates_main import HTML_PAGE
from src.web.templates_annotation import ANNOTATION_PAGE
from src.web.templates_docs import DOCS_PAGE

app = Flask(__name__)

@app.after_request
def after_request_callback(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    return response

# Inicialização dos Modelos e Motores
yolo_path = os.path.join(project_dir, "models", "02_sar_radar_and_edge", "mayrajeo_YOLOv8_Marine_Vessel", "YOLOv8n", "yolov8n.pt")
if not os.path.exists(yolo_path):
    yolo_path = "yolov8n.pt"

yolo_model = YOLO(yolo_path)
vit_analyzer = VesselSemanticAnalyzer()
ensemble_engine = VesselEnsembleEngine(yolo_model, vit_analyzer)

# Pipeline de Visão Acoplável & Gerenciador de Datasets
pluggable_pipeline = PluggableVisionPipeline(project_dir, default_ensemble_engine=ensemble_engine, vit_analyzer=vit_analyzer)
dataset_manager = DatasetAnnotationManager(project_dir)

_stream_generation = {"current": 0}

live_state = {
    "status": "VIGILANCIA_ATIVA",
    "total_detected": 0,
    "vessels": [],
    "vessel_history": [],
    "current_stream_type": "LIVE",
    "current_youtube_url": "https://www.youtube.com/watch?v=5BxqzvR6TgM",
    "current_stream_title": "Porto de Santos Ao Vivo",
    "gpu_info": "AMD Radeon RX 6750 XT (DirectML)"
}

vessel_history = {}


def get_live_stream_url(yt_url=None):
    target_url = yt_url or live_state.get("current_youtube_url")
    try:
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'noplaylist': True})
        info = ydl.extract_info(target_url, download=False)
        live_state["current_stream_title"] = info.get("title", "Stream do YouTube")
        stream_url = info.get('url')
        if not stream_url and 'formats' in info:
            for f in reversed(info['formats']):
                if f.get('url'):
                    stream_url = f['url']
                    break
        return stream_url
    except Exception as e:
        print(f"[YouTube] Erro ao obter URL: {e}")
        return None


def _open_capture(source_type):
    """Abre a fonte de vídeo (YouTube Live ou arquivo local de fallback)."""
    if source_type != "LIVE":
        vpath = os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4")
        if not os.path.exists(vpath):
            vpath = os.path.join(project_dir, "data", "teste_porto_santos_1min.mp4")
        return cv2.VideoCapture(vpath) if os.path.exists(vpath) else None

    stream_url = get_live_stream_url()
    cap = cv2.VideoCapture(stream_url) if stream_url else None
    return cap


class BackgroundVideoBroadcaster:
    """Thread contínuo em segundo plano que lê a fonte de vídeo / live e mantém os buffers de frames sempre atualizados."""
    def __init__(self):
        self.lock = threading.Lock()
        self.latest_raw_frame = None
        self.latest_display_frame = None
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        global live_state, pluggable_pipeline
        consecutive_failures = 0
        last_reconnect_attempt = 0.0
        width, height = 1280, 720
        frame_count = 0
        last_confirmed = []
        cap = _open_capture("LIVE")

        while self.running:
            frame = None
            if cap and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    consecutive_failures += 1
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if ret:
                        consecutive_failures = 0
                else:
                    consecutive_failures = 0

            if cap is None or not cap.isOpened() or consecutive_failures >= 15:
                now = time.time()
                if now - last_reconnect_attempt > 3.0:
                    last_reconnect_attempt = now
                    consecutive_failures = 0
                    if cap is not None:
                        try: cap.release()
                        except Exception: pass
                    cap = _open_capture("LIVE")
                time.sleep(0.1)
                continue

            if frame is None:
                time.sleep(0.03)
                continue

            frame_count += 1
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))

            raw_copy = frame.copy()
            display_frame = frame.copy()
            now_ts = time.time()

            if frame_count % 2 == 0 or frame_count == 1:
                last_confirmed = pluggable_pipeline.process_frame(frame, now_ts)

            confirmed_vessels = last_confirmed
            current_live_vessels = []

            if len(confirmed_vessels) > 0:
                for v_mem in confirmed_vessels:
                    b = v_mem["bbox"]
                    x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                    cx, cy = v_mem["cx"], v_mem["cy"]
                    v_id = v_mem["vessel_id"]
                    det = v_mem.get("detection_data", {})
                    is_stationary = v_mem.get("is_stationary", True)
                    speed_val = v_mem.get("speed", 0.0)
                    heading_deg = v_mem.get("heading_deg", 0.0)
                    cardinal = v_mem.get("cardinal", "N/D")
                    dynamic_destination = v_mem.get("destination", "Canal de Santos")
                    fingerprint = v_mem.get("fingerprint", {})
                    v_name = v_mem.get("name", "Embarcação")

                    trail = v_mem.get("trajectory_trail", [])
                    if len(trail) >= 2:
                        pts_poly = np.array([[p["x"], p["y"]] for p in trail], np.int32).reshape((-1, 1, 2))
                        cv2.polylines(display_frame, [pts_poly], False, (0, 240, 255), 2, cv2.LINE_AA)
                        for p in trail:
                            cv2.circle(display_frame, (p["x"], p["y"]), 3, (0, 200, 255), -1)

                    hull_color = (0, 230, 118) if is_stationary else (0, 240, 255)
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), hull_color, 2)

                    if is_stationary:
                        cv2.circle(display_frame, (int(cx), int(cy)), 3, (0, 230, 118), -1)
                    else:
                        future_pts = pluggable_pipeline.spatial_memory.predict_future_positions(v_mem, [5.0, 10.0])
                        if len(future_pts) >= 2:
                            p10 = future_pts[1]
                            cv2.line(display_frame, (int(cx), int(cy)), (p10["x"], p10["y"]), (0, 255, 120), 2, cv2.LINE_AA)
                            cv2.circle(display_frame, (p10["x"], p10["y"]), 5, (0, 255, 120), -1)
                            dest_label = f"-> {dynamic_destination[:18]}"
                            cv2.putText(display_frame, dest_label, (p10["x"] + 6, p10["y"] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 120), 1, cv2.LINE_AA)

                    ens_pct_tag = int(det.get("score_ensemble_final", 0.85) * 100)
                    status_short = "PARADO (0.0 nos)" if is_stationary else f"NAVEGANDO ({speed_val:.1f} px/s)"
                    tag_str = f"{v_id} | {status_short} | {ens_pct_tag}%"
                    (tw, th), _ = cv2.getTextSize(tag_str, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)
                    tag_y = max(th + 8, y1 - 6)
                    tag_bg = display_frame.copy()
                    cv2.rectangle(tag_bg, (x1, tag_y - th - 5), (x1 + tw + 10, tag_y + 3), (6, 12, 18), -1)
                    cv2.addWeighted(tag_bg, 0.45, display_frame, 0.55, 0, display_frame)
                    cv2.rectangle(display_frame, (x1, tag_y - th - 5), (x1 + tw + 10, tag_y + 3), hull_color, 1)
                    cv2.putText(display_frame, tag_str, (x1 + 5, tag_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)

                    current_live_vessels.append({
                        "vessel_id": v_id,
                        "name": v_name,
                        "is_stationary": is_stationary,
                        "speed": speed_val,
                        "heading_deg": heading_deg,
                        "cardinal": cardinal,
                        "destination": dynamic_destination,
                        "score_ensemble": ens_pct_tag,
                        "fontes_detectoras": det.get("fontes_detectoras", []),
                        "fingerprint": fingerprint,
                        "trajectory_trail": trail
                    })

                live_state["status"] = f"{len(confirmed_vessels)} EMBARCAÇÃO(ÕES) RASTREADA(S)"
                live_state["total_detected"] = len(confirmed_vessels)
                live_state["vessels"] = current_live_vessels
            else:
                live_state["status"] = "CANAL_LIVRE"
                live_state["total_detected"] = 0
                live_state["vessels"] = []

            hud_bg = display_frame.copy()
            cv2.rectangle(hud_bg, (0, 0), (width, 42), (5, 9, 14), -1)
            cv2.addWeighted(hud_bg, 0.45, display_frame, 0.55, 0, display_frame)

            active_mod = pluggable_pipeline.config.get("active_model_id", "ensemble_full").upper()
            lat_ms = pluggable_pipeline.last_inference_latency_ms
            src_label = f"● {live_state.get('current_stream_title', 'Ao Vivo')[:35]}"
            cv2.putText(display_frame, f"{src_label} | GPU: DirectML", (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 229, 255), 2)
            cv2.putText(display_frame, f"MODELO: {active_mod} ({lat_ms:.0f}ms)", (width - 430, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 120), 2)

            with self.lock:
                self.latest_raw_frame = raw_copy
                self.latest_display_frame = display_frame

            time.sleep(0.033) # ~30 FPS

    def get_raw_frame(self):
        with self.lock:
            if self.latest_raw_frame is not None:
                return self.latest_raw_frame.copy()
        return None

    def get_display_frame(self):
        with self.lock:
            if self.latest_display_frame is not None:
                return self.latest_display_frame.copy()
        return None

video_broadcaster = BackgroundVideoBroadcaster()


def generate_video_stream():
    """Gera stream MJPEG com sobreposições neurais em tempo real."""
    while True:
        frame = video_broadcaster.get_display_frame()
        if frame is not None:
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.033)

def generate_raw_video_stream():
    """Gera stream MJPEG limpo (sem caixas) para o estúdio de anotação."""
    while True:
        frame = video_broadcaster.get_raw_frame()
        if frame is not None:
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.033)


# ==========================================
# ROTAS DE PÁGINAS & ARQUIVOS ESTÁTICOS
# ==========================================

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/anotar")
def page_anotar():
    return render_template_string(ANNOTATION_PAGE)

@app.route("/sobre")
def sobre():
    return render_template_string(DOCS_PAGE)

@app.route("/sobre/exemplos/<path:filename>")
def sobre_exemplos(filename):
    examples_dir = os.path.join(project_dir, "docs_examples")
    return send_from_directory(examples_dir, filename)

@app.route("/media/video/<path:filename>")
def serve_video(filename):
    vdir = os.path.join(project_dir, "data")
    if not os.path.exists(os.path.join(vdir, filename)):
        vdir = os.path.join(project_dir, "data", "uploads")
    return send_from_directory(vdir, filename)

@app.route("/media/annotated/<path:filename>")
def serve_annotated_image(filename):
    img_dir = os.path.join(project_dir, "datasets", "annotated_frames", "images")
    return send_from_directory(img_dir, filename)

@app.route("/video_feed")
def video_feed():
    return Response(generate_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video_feed_raw")
def video_feed_raw():
    return Response(generate_raw_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/live_raw_snapshot", methods=["GET"])
def api_live_raw_snapshot():
    """Captura o frame limpo atual da transmissão ao vivo em alta resolução."""
    frame = video_broadcaster.get_raw_frame()
    if frame is None:
        vpath = os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4")
        if os.path.exists(vpath):
            c = cv2.VideoCapture(vpath)
            ret, frame = c.read()
            c.release()
    if frame is None:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    b64_str = base64.b64encode(buf).decode("utf-8")
    return jsonify({
        "status": "ok",
        "image_base64": f"data:image/jpeg;base64,{b64_str}",
        "width": frame.shape[1],
        "height": frame.shape[0],
        "timestamp": time.time(),
        "stream_title": live_state.get("current_stream_title", "Câmera ao Vivo - Porto de Santos")
    })

@app.route("/api/live_raw_snapshot.jpg", methods=["GET"])
def api_live_raw_snapshot_jpg():
    """Retorna o frame atual da transmissão ao vivo como imagem JPEG binária."""
    frame = video_broadcaster.get_raw_frame()
    if frame is None:
        vpath = os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4")
        if os.path.exists(vpath):
            c = cv2.VideoCapture(vpath)
            ret, frame = c.read()
            c.release()
    if frame is None:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return Response(buf.tobytes(), mimetype="image/jpeg")


# ==========================================
# ROTAS DE API: TELEMETRIA & FONTES
# ==========================================

@app.route("/api/live_telemetry")
def api_live_telemetry():
    return jsonify(live_state)

@app.route("/api/set_stream_source", methods=["POST", "OPTIONS"])
def api_set_stream_source():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    new_src = data.get("source", "LIVE")
    yt_url = data.get("youtube_url")
    if yt_url:
        live_state["current_youtube_url"] = yt_url
    live_state["current_stream_type"] = new_src
    return jsonify({"status": "ok", "new_source": new_src})


# ==========================================
# ROTAS DE API: ARQUITETURAS & PRESETS
# ==========================================

@app.route("/api/architectures", methods=["GET"])
def api_architectures():
    """Retorna todas as arquiteturas pré-configuradas (Produção, Teste, Custom)."""
    presets = pluggable_pipeline.preset_manager.list_presets()
    return jsonify({
        "status": "ok",
        "active_preset_id": pluggable_pipeline.active_preset_id,
        "presets": presets
    })

@app.route("/api/architectures/apply", methods=["POST", "OPTIONS"])
def api_architectures_apply():
    """Aplica uma arquitetura completa em tempo real (ex: Produção ou Teste)."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    preset_id = data.get("preset_id", "pre_arch_production")
    try:
        res = pluggable_pipeline.apply_architecture_preset(preset_id)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/architectures/save", methods=["POST", "OPTIONS"])
def api_architectures_save():
    """Salva uma nova arquitetura personalizada."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    saved = pluggable_pipeline.preset_manager.save_preset(data)
    return jsonify({"status": "ok", "preset": saved})


# ==========================================
# ROTAS DE API: MODELOS ACOPLÁVEIS
# ==========================================

@app.route("/api/models", methods=["GET"])
def api_models():
    """Retorna o catálogo de modelos disponíveis e a configuração atual."""
    return jsonify(pluggable_pipeline.get_status())

@app.route("/api/models/set_active", methods=["POST", "OPTIONS"])
def api_models_set_active():
    """Altera o modelo ativo e configurações do pipeline em tempo de execução."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    updated_status = pluggable_pipeline.update_config(data)
    return jsonify({"status": "ok", "pipeline_status": updated_status})

@app.route("/api/models/upload", methods=["POST", "OPTIONS"])
def api_models_upload():
    """Recebe e acopla um novo arquivo de modelo (.pt ou .onnx)."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    if not (filename.endswith('.pt') or filename.endswith('.onnx')):
        return jsonify({"error": "Formato inválido. Envie um arquivo .pt ou .onnx"}), 400

    custom_dir = os.path.join(project_dir, "models", "custom_uploaded")
    os.makedirs(custom_dir, exist_ok=True)
    save_path = os.path.join(custom_dir, filename)
    file.save(save_path)

    return jsonify({"status": "ok", "filename": filename, "path": save_path})


# ==========================================
# ROTAS DE API: VÍDEOS & UPLOAD
# ==========================================

@app.route("/api/videos", methods=["GET"])
def api_videos():
    """Lista todos os vídeos disponíveis na pasta data."""
    vids = []
    for root_dir in [os.path.join(project_dir, "data"), os.path.join(project_dir, "data", "uploads")]:
        if os.path.exists(root_dir):
            for f in os.listdir(root_dir):
                if f.endswith(('.mp4', '.webm', '.mov', '.avi')):
                    vids.append({"filename": f, "path": f"/media/video/{f}"})
    return jsonify({"videos": vids})

@app.route("/api/upload_video", methods=["POST", "OPTIONS"])
def api_upload_video():
    """Recebe upload de vídeo local do usuário para anotação."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    fname = secure_filename(file.filename) or f"video_{int(time.time())}.mp4"
    uploads_dir = os.path.join(project_dir, "data", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    save_path = os.path.join(uploads_dir, fname)
    file.save(save_path)
    return jsonify({"status": "ok", "filename": fname, "url": f"/media/video/{fname}"})


from src.annotation.class_presets import ClassPresetManager

class_preset_manager = ClassPresetManager(project_dir)


# ==========================================
# ROTAS DE API: CONJUNTOS DE CLASSES & PRESETS
# ==========================================

@app.route("/api/class_sets", methods=["GET"])
def api_class_sets():
    """Retorna todos os conjuntos de classes (presets e personalizados)."""
    presets = class_preset_manager.list_presets()
    current_classes = dataset_manager.get_classes()
    return jsonify({
        "status": "ok",
        "current_classes": current_classes,
        "presets": presets
    })

@app.route("/api/class_sets/save", methods=["POST", "OPTIONS"])
def api_class_sets_save():
    """Salva um novo conjunto de classes ou atualiza o atual."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    saved = class_preset_manager.save_preset(data)
    # Se solicitado, define como conjunto ativo no dataset
    if data.get("set_as_active", True) and "classes" in data:
        class_names = [c["name"] for c in data["classes"]]
        dataset_manager.set_classes(class_names)
    return jsonify({"status": "ok", "preset": saved, "active_classes": dataset_manager.get_classes()})

@app.route("/api/class_sets/set_active", methods=["POST", "OPTIONS"])
def api_class_sets_set_active():
    """Define o conjunto de classes ativo no dataset."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    preset_id = data.get("preset_id")
    preset = class_preset_manager.get_preset(preset_id)
    if preset and "classes" in preset:
        class_names = [c["name"] for c in preset["classes"]]
        dataset_manager.set_classes(class_names)
    return jsonify({"status": "ok", "active_preset": preset, "active_classes": dataset_manager.get_classes()})


# ==========================================
# ROTAS DE API: ESTÚDIO DE ANOTAÇÃO & DATASET
# ==========================================

@app.route("/api/annotation/save", methods=["POST", "OPTIONS"])
def api_annotation_save():
    """Salva frame anotado + caixas delimitadoras + polígonos no dataset YOLO."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    base64_str = data.get("image_base64")
    boxes = data.get("boxes", [])
    polygons = data.get("polygons", [])
    source_video = data.get("source_video", "video")
    frame_ts = data.get("frame_timestamp", 0.0)

    if not base64_str:
        return jsonify({"error": "Imagem em base64 ausente"}), 400

    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]

    img_bytes = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        return jsonify({"error": "Falha ao decodificar imagem"}), 400

    result = dataset_manager.save_annotation(
        img_bgr,
        boxes=boxes,
        polygons=polygons,
        source_video=source_video,
        frame_timestamp=frame_ts
    )
    return jsonify(result)

@app.route("/api/annotation/load/<image_id>", methods=["GET"])
def api_annotation_load(image_id):
    """Carrega imagem e anotações existentes no canvas para edição/continuação."""
    res = dataset_manager.load_annotation(image_id)
    if res.get("status") == "error":
        return jsonify(res), 404
    return jsonify(res)

@app.route("/api/annotation/import_zip", methods=["POST", "OPTIONS"])
def api_annotation_import_zip():
    """Importa um dataset YOLO (.zip) para continuar a anotação."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo ZIP enviado"}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.zip'):
        return jsonify({"error": "O arquivo deve ser um arquivo compactado .ZIP"}), 400

    res, err = dataset_manager.import_dataset_zip(file)
    if err:
        return jsonify({"error": err}), 400
    return jsonify(res)

@app.route("/api/annotation/list", methods=["GET"])
def api_annotation_list():
    """Lista todas as anotações registradas no dataset."""
    return jsonify(dataset_manager.list_annotations())

@app.route("/api/annotation/delete/<image_id>", methods=["DELETE", "OPTIONS"])
def api_annotation_delete(image_id):
    """Exclui uma imagem e suas anotações do dataset."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    res = dataset_manager.delete_annotation(image_id)
    return jsonify(res)

@app.route("/api/annotation/export_zip", methods=["GET"])
def api_annotation_export_zip():
    """Gera e retorna o dataset completo no formato YOLO em arquivo .ZIP."""
    zip_path, err = dataset_manager.export_dataset_zip(split_ratio=0.8)
    if err:
        return jsonify({"error": err}), 400
    return send_file(zip_path, as_attachment=True, download_name="dataset_yolo_naval.zip", mimetype="application/zip")

@app.route("/api/annotation/auto_detect", methods=["POST", "OPTIONS"])
def api_annotation_auto_detect():
    """Executa o modelo atualmente acoplado no frame enviado para pré-rotulagem automática (Active Learning)."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    base64_str = data.get("image_base64")
    if not base64_str:
        return jsonify({"error": "Imagem ausente"}), 400

    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]

    img_bytes = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        return jsonify({"error": "Falha ao decodificar imagem"}), 400

    # Executa detecção com modelo ativo
    dets = pluggable_pipeline.detect_raw(img_bgr, conf=0.12)
    return jsonify({"status": "ok", "detections": dets})

@app.route("/api/analyze_image", methods=["POST", "OPTIONS"])
def api_analyze_image():
    """Análise estática de foto única enviada."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    file_bytes = file.read()
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "Falha ao decodificar imagem"}), 400
    vessels = pluggable_pipeline.process_frame(img)
    return jsonify({"status": "ok", "vessels": vessels})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
