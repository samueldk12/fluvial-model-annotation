# -*- coding: utf-8 -*-
"""
AI Vision Hub — Servidor Web Multi-Domínio de Visão Computacional & IA
Gerencia os 7 domínios especializados:
1. Naval & Aquático (naval)
2. Cidade Urbana & Trânsito (urbano)
3. Ambientes Fechados / Indoor (fechado)
4. Natureza & Vida Selvagem (natureza)
5. Objetos & Indústria / Varejo (objetos)
6. Tatuagens & Arte Corporal (tatuagens)
7. Digitais & Forense Biométrico (digitais)
"""

import os
import sys
import time
import json
import base64
import math
import threading
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
from src.annotation.class_presets import ClassPresetManager
from src.domains.domain_config import DOMAINS_CONFIG
from src.domains.domain_analyzer import DomainVisionAnalyzer
from src.domains.domain_registry import DomainRegistryManager

from src.web.templates_hub import HUB_PAGE
from src.web.templates_domain import get_domain_monitoring_html
from src.web.templates_annotation import ANNOTATION_PAGE
from src.web.templates_docs import get_docs_html, DOCS_PAGE
from src.web.templates_main import HTML_PAGE

app = Flask(__name__)

@app.after_request
def after_request_callback(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    return response

# ==========================================
# INICIALIZAÇÃO DOS MOTORES & PIPELINES
# ==========================================

# 1. Pipeline Naval Especializado
yolo_path = os.path.join(project_dir, "models", "02_sar_radar_and_edge", "mayrajeo_YOLOv8_Marine_Vessel", "YOLOv8n", "yolov8n.pt")
if not os.path.exists(yolo_path):
    yolo_path = "yolov8n.pt"

yolo_model = YOLO(yolo_path)
vit_analyzer = VesselSemanticAnalyzer()
ensemble_engine = VesselEnsembleEngine(yolo_model, vit_analyzer)
pluggable_pipeline = PluggableVisionPipeline(project_dir, default_ensemble_engine=ensemble_engine, vit_analyzer=vit_analyzer)

# 2. Gerenciadores Multi-Domínio
domain_analyzers = {
    d_id: DomainVisionAnalyzer(project_dir, d_id) for d_id in DOMAINS_CONFIG.keys()
}
domain_dataset_managers = {
    d_id: DatasetAnnotationManager(project_dir, d_id) for d_id in DOMAINS_CONFIG.keys()
}
dataset_manager = domain_dataset_managers["naval"]
class_preset_manager = ClassPresetManager(project_dir)

# 3. Estados de Transmissão por Domínio
domain_streams_state = {}
for d_id, conf in DOMAINS_CONFIG.items():
    domain_streams_state[d_id] = {
        "status": "VIGILANCIA_ATIVA",
        "current_stream_type": "LIVE",
        "current_youtube_url": conf["default_youtube_url"],
        "current_stream_title": conf["default_stream_title"],
        "night_vision": False,
        "latest_raw_frame": None,
        "last_telemetry": {
            "status": "VIGILANCIA_ATIVA",
            "latency_ms": 12.5,
            "semantica_cena": {k["key"]: k["default"] for k in conf.get("semantics_keys", [])},
            "targets": []
        }
    }

live_state = domain_streams_state["naval"]
vessel_history = {}


def get_live_stream_url(yt_url=None):
    target_url = yt_url or live_state.get("current_youtube_url")
    try:
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'noplaylist': True})
        info = ydl.extract_info(target_url, download=False)
        stream_url = info.get('url')
        if not stream_url and 'formats' in info:
            for f in reversed(info['formats']):
                if f.get('url'):
                    stream_url = f['url']
                    break
        return stream_url
    except Exception as e:
        return None


def _open_capture(source_type, domain_id="naval"):
    """Abre a fonte de vídeo (YouTube Live ou arquivo local de fallback/amostra)."""
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    
    if source_type != "LIVE":
        vpath = os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4")
        if not os.path.exists(vpath):
            vpath = os.path.join(project_dir, "data", "teste_porto_santos_1min.mp4")
        return cv2.VideoCapture(vpath) if os.path.exists(vpath) else None

    stream_url = get_live_stream_url(state.get("current_youtube_url"))
    cap = cv2.VideoCapture(stream_url) if stream_url else None
    if not cap or not cap.isOpened():
        vpath = os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4")
        cap = cv2.VideoCapture(vpath) if os.path.exists(vpath) else None
    return cap


def generate_video_stream(source_type="LIVE", domain_id="naval"):
    """Gera stream MJPEG processado em tempo real para qualquer um dos 7 domínios."""
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    analyzer = domain_analyzers.get(domain_id, domain_analyzers["naval"])
    
    cap = _open_capture(source_type, domain_id)
    width, height = 1280, 720
    frame_count = 0
    sim_t = 0.0

    while True:
        frame = None
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

        # Se não houver vídeo aberto ou stream estiver indisponível, gera frame simulado realista
        if frame is None:
            sim_t += 0.04
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Fundo suave
            color_bg = (12, 16, 24)
            frame[:] = color_bg
            # Grid sutil
            for gx in range(0, width, 80):
                cv2.line(frame, (gx, 0), (gx, height), (20, 26, 38), 1)
            for gy in range(0, height, 80):
                cv2.line(frame, (0, gy), (width, gy), (20, 26, 38), 1)

            # Elementos animados realistas baseados no domínio
            cx1 = int(width * 0.35 + math.sin(sim_t * 0.8) * 120)
            cy1 = int(height * 0.5 + math.cos(sim_t * 0.5) * 60)
            cv2.rectangle(frame, (cx1 - 90, cy1 - 50), (cx1 + 90, cy1 + 50), (35, 50, 70), -1)

            cx2 = int(width * 0.7 + math.cos(sim_t * 0.6) * 100)
            cy2 = int(height * 0.45 + math.sin(sim_t * 0.4) * 40)
            cv2.rectangle(frame, (cx2 - 70, cy2 - 40), (cx2 + 70, cy2 + 40), (45, 60, 80), -1)

        frame_count += 1
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))

        state["latest_raw_frame"] = frame.copy()

        # Aplica visão noturna se ativada
        if state.get("night_vision"):
            frame = enhance_night_vision(frame)

        # Executa análise pelo analisador de domínio
        analysis_result, pil_annotated = analyzer.analyze_image(frame)
        display_frame = cv2.cvtColor(np.array(pil_annotated), cv2.COLOR_RGB2BGR)

        # Atualiza telemetria do domínio
        state["last_telemetry"] = {
            "status": analysis_result.get("status", "VIGILANCIA_ATIVA"),
            "latency_ms": analysis_result.get("tempo_processamento_ms", 12.0),
            "semantica_cena": analysis_result.get("semantica_cena", {}),
            "targets": analysis_result.get("targets_detectados", [])
        }

        ret_jpg, jpeg = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret_jpg:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

        time.sleep(0.035)


def generate_raw_video_stream(source_type="LIVE", domain_id="naval"):
    """Gera stream MJPEG limpo sem anotações para o estúdio de rotulagem."""
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    while True:
        frame = None
        if state.get("latest_raw_frame") is not None:
            frame = state["latest_raw_frame"].copy()
        else:
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.04)


# ==========================================
# ROTAS DE PÁGINAS PRINCIPAIS (HTML)
# ==========================================

@app.route("/")
@app.route("/hub")
@app.route("/portal")
def page_hub():
    """Página Inicial — Hub Multi-Domínio de Visão Computacional."""
    return render_template_string(HUB_PAGE)

@app.route("/naval")
def page_naval():
    """Painel de Monitoramento Naval & Aquático."""
    return render_template_string(HTML_PAGE)

@app.route("/urbano")
def page_urbano():
    return render_template_string(get_domain_monitoring_html("urbano"))

@app.route("/fechado")
@app.route("/indoor")
def page_fechado():
    return render_template_string(get_domain_monitoring_html("fechado"))

@app.route("/natureza")
def page_natureza():
    return render_template_string(get_domain_monitoring_html("natureza"))

@app.route("/objetos")
def page_objetos():
    return render_template_string(get_domain_monitoring_html("objetos"))

@app.route("/tatuagens")
def page_tatuagens():
    return render_template_string(get_domain_monitoring_html("tatuagens"))

@app.route("/digitais")
def page_digitais():
    return render_template_string(get_domain_monitoring_html("digitais"))

@app.route("/anotar")
@app.route("/<domain_id>/anotar")
def page_anotar(domain_id="naval"):
    """Estúdio de Anotação CVAT."""
    return render_template_string(ANNOTATION_PAGE)

@app.route("/sobre")
@app.route("/<domain_id>/sobre")
def page_sobre(domain_id="naval"):
    """Documentação Técnica e Especificações."""
    return render_template_string(get_docs_html(domain_id))


# ==========================================
# ROTAS DE STREAM DE VÍDEO MJPEG
# ==========================================

@app.route("/video_feed")
def video_feed():
    domain = request.args.get("domain", "naval").lower()
    src_type = request.args.get("source", "LIVE")
    return Response(generate_video_stream(src_type, domain_id=domain),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video_feed_raw")
def video_feed_raw():
    domain = request.args.get("domain", "naval").lower()
    src_type = request.args.get("source", "LIVE")
    return Response(generate_raw_video_stream(src_type, domain_id=domain),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ==========================================
# ROTAS DE API: TELEMETRIA, REGISTROS E SNAPSHOTS
# ==========================================

@app.route("/api/live_telemetry")
@app.route("/api/<domain_id>/live_telemetry")
def api_domain_telemetry(domain_id="naval"):
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    return jsonify(state.get("last_telemetry", {}))

@app.route("/api/registry")
@app.route("/api/<domain_id>/registry")
def api_domain_registry(domain_id="naval"):
    analyzer = domain_analyzers.get(domain_id, domain_analyzers["naval"])
    return jsonify({"status": "ok", "domain": domain_id, "items": analyzer.registry.get_all()})

@app.route("/api/set_stream_source", methods=["POST", "OPTIONS"])
@app.route("/api/<domain_id>/set_stream_source", methods=["POST", "OPTIONS"])
def api_set_stream_source(domain_id="naval"):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    new_src = data.get("source", "LIVE")
    yt_url = data.get("youtube_url")
    if yt_url:
        state["current_youtube_url"] = yt_url
    state["current_stream_type"] = new_src
    return jsonify({"status": "ok", "domain": domain_id, "new_source": new_src})

@app.route("/api/toggle_night_vision", methods=["POST", "OPTIONS"])
@app.route("/api/<domain_id>/toggle_night_vision", methods=["POST", "OPTIONS"])
def api_toggle_night_vision(domain_id="naval"):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    state["night_vision"] = bool(data.get("night_vision", False))
    return jsonify({"status": "ok", "night_vision": state["night_vision"]})

@app.route("/api/live_raw_snapshot", methods=["GET"])
@app.route("/api/<domain_id>/live_raw_snapshot", methods=["GET"])
def api_live_raw_snapshot(domain_id="naval"):
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    frame = state.get("latest_raw_frame")
    if frame is None:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    b64_str = base64.b64encode(buf).decode("utf-8")
    return jsonify({
        "status": "ok",
        "domain": domain_id,
        "image_base64": f"data:image/jpeg;base64,{b64_str}",
        "width": frame.shape[1],
        "height": frame.shape[0],
        "timestamp": time.time()
    })

@app.route("/api/live_raw_snapshot.jpg", methods=["GET"])
@app.route("/api/<domain_id>/live_raw_snapshot.jpg", methods=["GET"])
def api_live_raw_snapshot_jpg(domain_id="naval"):
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    frame = state.get("latest_raw_frame")
    if frame is None:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return Response(buf.tobytes(), mimetype="image/jpeg")

@app.route("/api/analyze_image", methods=["POST", "OPTIONS"])
@app.route("/api/<domain_id>/analyze_image", methods=["POST", "OPTIONS"])
def api_analyze_image(domain_id="naval"):
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
    
    analyzer = domain_analyzers.get(domain_id, domain_analyzers["naval"])
    res, _ = analyzer.analyze_image(img)
    return jsonify(res)


# ==========================================
# ROTAS DE API: ARQUITETURAS & PRESETS
# ==========================================

@app.route("/api/architectures", methods=["GET"])
def api_architectures():
    presets = pluggable_pipeline.preset_manager.list_presets()
    return jsonify({
        "status": "ok",
        "active_preset_id": pluggable_pipeline.active_preset_id,
        "presets": presets
    })

@app.route("/api/architectures/apply", methods=["POST", "OPTIONS"])
def api_architectures_apply():
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
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    saved = pluggable_pipeline.preset_manager.save_preset(data)
    return jsonify({"status": "ok", "preset": saved})

@app.route("/api/models", methods=["GET"])
def api_models():
    return jsonify(pluggable_pipeline.get_status())

@app.route("/api/models/set_active", methods=["POST", "OPTIONS"])
def api_models_set_active():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    updated_status = pluggable_pipeline.update_config(data)
    return jsonify({"status": "ok", "pipeline_status": updated_status})

@app.route("/api/models/upload", methods=["POST", "OPTIONS"])
def api_models_upload():
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

@app.route("/api/videos", methods=["GET"])
def api_videos():
    vids = []
    for root_dir in [os.path.join(project_dir, "data"), os.path.join(project_dir, "data", "uploads")]:
        if os.path.exists(root_dir):
            for f in os.listdir(root_dir):
                if f.endswith(('.mp4', '.webm', '.mov', '.avi')):
                    vids.append({"filename": f, "path": f"/media/video/{f}"})
    return jsonify({"videos": vids})

@app.route("/api/upload_video", methods=["POST", "OPTIONS"])
def api_upload_video():
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


# ==========================================
# ROTAS DE API: CONJUNTOS DE CLASSES & PRESETS
# ==========================================

@app.route("/api/class_sets", methods=["GET"])
def api_class_sets():
    domain_req = request.args.get("domain")
    presets = class_preset_manager.list_presets(domain_filter=domain_req)
    mgr = domain_dataset_managers.get(domain_req, dataset_manager) if domain_req else dataset_manager
    current_classes = mgr.get_classes()
    return jsonify({
        "status": "ok",
        "current_classes": current_classes,
        "presets": presets
    })

@app.route("/api/class_sets/save", methods=["POST", "OPTIONS"])
def api_class_sets_save():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    saved = class_preset_manager.save_preset(data)
    domain_req = data.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    if data.get("set_as_active", True) and "classes" in data:
        class_names = [c["name"] for c in data["classes"]]
        mgr.set_classes(class_names)
    return jsonify({"status": "ok", "preset": saved, "active_classes": mgr.get_classes()})

@app.route("/api/class_sets/set_active", methods=["POST", "OPTIONS"])
def api_class_sets_set_active():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    preset_id = data.get("preset_id")
    preset = class_preset_manager.get_preset(preset_id)
    domain_req = data.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    if preset and "classes" in preset:
        class_names = [c["name"] for c in preset["classes"]]
        mgr.set_classes(class_names)
    return jsonify({"status": "ok", "active_preset": preset, "active_classes": mgr.get_classes()})


# ==========================================
# ROTAS DE API: ESTÚDIO DE ANOTAÇÃO & DATASET
# ==========================================
# ROTAS DE API: ESTÚDIO DE ANOTAÇÃO & DATASET
# ==========================================

@app.route("/api/annotation/models", methods=["GET"])
def api_annotation_models():
    """Retorna os modelos de IA disponíveis para acoplar ao estúdio de anotação."""
    domain_req = request.args.get("domain", "naval")
    catalog = pluggable_pipeline.registry.get_catalog()
    models = [
        {
            "id": "domain_default",
            "name": f"Modelo Especialista ({domain_req.capitalize()})",
            "type": "domain_analyzer",
            "framework": "Ultralytics / PyTorch",
            "description": f"Detector padrão com filtros configurados para o domínio {domain_req}.",
            "available": True,
            "default_conf": 0.18
        }
    ]
    for m in catalog:
        models.append({
            "id": m["id"],
            "name": m["name"],
            "type": m.get("type", "detector"),
            "framework": m.get("framework", "PyTorch"),
            "description": m.get("description", ""),
            "available": m.get("available", True),
            "is_custom": m.get("is_custom", False),
            "default_conf": m.get("default_conf", 0.20)
        })
    return jsonify({
        "status": "ok",
        "active_model_id": pluggable_pipeline.config.get("active_model_id", "yolo11n"),
        "models": models
    })

@app.route("/api/annotation/save", methods=["POST", "OPTIONS"])
def api_annotation_save():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    domain_req = data.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)

    base64_str = data.get("image_base64")
    boxes = data.get("boxes", [])
    polygons = data.get("polygons", [])
    source_video = data.get("source_video", "video")
    frame_ts = data.get("frame_timestamp", 0.0)
    notes = data.get("notes", "")
    is_ai_assisted = data.get("is_ai_assisted", True)
    model_used = data.get("model_used", "yolo11n")
    human_corrected = data.get("human_corrected", True)

    if not base64_str:
        return jsonify({"error": "Imagem em base64 ausente"}), 400

    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]

    img_bytes = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        return jsonify({"error": "Falha ao decodificar imagem"}), 400

    result = mgr.save_annotation(
        img_bgr,
        boxes=boxes,
        polygons=polygons,
        source_video=source_video,
        frame_timestamp=frame_ts,
        notes=notes,
        is_ai_assisted=is_ai_assisted,
        model_used=model_used,
        human_corrected=human_corrected
    )
    return jsonify(result)

@app.route("/api/annotation/load/<image_id>", methods=["GET"])
def api_annotation_load(image_id):
    domain_req = request.args.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    res = mgr.load_annotation(image_id)
    if res.get("status") == "error":
        return jsonify(res), 404
    return jsonify(res)

@app.route("/api/annotation/import_zip", methods=["POST", "OPTIONS"])
def api_annotation_import_zip():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo ZIP enviado"}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.zip'):
        return jsonify({"error": "O arquivo deve ser um arquivo compactado .ZIP"}), 400

    domain_req = request.form.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    res, err = mgr.import_dataset_zip(file)
    if err:
        return jsonify({"error": err}), 400
    return jsonify(res)

@app.route("/api/annotation/list", methods=["GET"])
def api_annotation_list():
    domain_req = request.args.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    return jsonify(mgr.list_annotations())

@app.route("/api/annotation/delete/<image_id>", methods=["DELETE", "OPTIONS"])
def api_annotation_delete(image_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    domain_req = request.args.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    res = mgr.delete_annotation(image_id)
    return jsonify(res)

@app.route("/api/annotation/export_zip", methods=["GET"])
def api_annotation_export_zip():
    domain_req = request.args.get("domain", "naval")
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    zip_path, err = mgr.export_dataset_zip(split_ratio=0.8)
    if err:
        return jsonify({"error": err}), 400
    return send_file(zip_path, as_attachment=True, download_name=f"dataset_yolo_{domain_req}.zip", mimetype="application/zip")

@app.route("/api/annotation/auto_detect", methods=["POST", "OPTIONS"])
def api_annotation_auto_detect():
    """Executa inferência com o modelo de IA selecionado para auto-rotulagem de frames."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    domain_req = data.get("domain", "naval")
    model_id = data.get("model_id") or pluggable_pipeline.config.get("active_model_id", "domain_default")
    conf_thresh = float(data.get("conf") or data.get("conf_threshold") or 0.18)
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

    mgr = domain_dataset_managers.get(domain_req, dataset_manager)
    dataset_classes = mgr.get_classes()

    dets = []
    # 1. Se model_id for domain_default, usa o analisador do domínio
    if model_id == "domain_default" or model_id not in [m["id"] for m in pluggable_pipeline.registry.get_catalog()]:
        analyzer = domain_analyzers.get(domain_req, domain_analyzers["naval"])
        analysis_res, _ = analyzer.analyze_image(img_bgr, conf=conf_thresh)
        for t in analysis_res.get("targets_detectados", []):
            c_name = t.get("class_name", "objeto").lower()
            # Mapeia para class_id do dataset se existir
            cid = 0
            if c_name in dataset_classes:
                cid = dataset_classes.index(c_name)
            elif "embarcacao" in dataset_classes:
                cid = dataset_classes.index("embarcacao")
            dets.append({
                "bbox": t["bbox"],
                "class_id": cid,
                "class_name": c_name,
                "confidence": round(float(t.get("confidence", 0.85)), 3),
                "source_model": f"domain_{domain_req}"
            })
    else:
        # 2. Executa inferência via PluggableVisionPipeline com o modelo especificado
        try:
            if model_id == "ensemble_full":
                raw_dets = pluggable_pipeline.detect_raw(img_bgr, conf=conf_thresh)
            else:
                wrapper = pluggable_pipeline.registry.load_model(model_id)
                if wrapper["type"] == "yolo":
                    raw_dets = pluggable_pipeline._infer_single_yolo(wrapper, img_bgr, conf=conf_thresh)
                elif wrapper["type"] == "onnx":
                    raw_dets = pluggable_pipeline._infer_single_onnx(wrapper, img_bgr, conf=conf_thresh)
                else:
                    raw_dets = pluggable_pipeline.detect_raw(img_bgr, conf=conf_thresh)

            for d in raw_dets:
                c_name = d.get("class_name", "embarcacao").lower()
                cid = 0
                if c_name in dataset_classes:
                    cid = dataset_classes.index(c_name)
                elif "embarcacao" in dataset_classes:
                    cid = dataset_classes.index("embarcacao")
                dets.append({
                    "bbox": d["bbox"],
                    "class_id": cid,
                    "class_name": c_name,
                    "confidence": round(float(d.get("conf", 0.85)), 3),
                    "source_model": model_id
                })
        except Exception as e:
            print(f"[Auto-Detect] Erro com modelo {model_id}: {e}. Fallback para domain analyzer.")
            analyzer = domain_analyzers.get(domain_req, domain_analyzers["naval"])
            analysis_res, _ = analyzer.analyze_image(img_bgr, conf=conf_thresh)
            for t in analysis_res.get("targets_detectados", []):
                dets.append({
                    "bbox": t["bbox"],
                    "class_id": 0,
                    "class_name": t.get("class_name", "objeto"),
                    "confidence": round(float(t.get("confidence", 0.80)), 3),
                    "source_model": "fallback"
                })

    return jsonify({
        "status": "ok",
        "model_id": model_id,
        "model_used": model_id,
        "domain": domain_req,
        "conf_threshold": conf_thresh,
        "count": len(dets),
        "detections": dets
    })



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
