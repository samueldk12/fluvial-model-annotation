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
from src.ai.gemini_annotator import GeminiVisionAnnotator
from src.annotation.augmentation_engine import DatasetAugmentationEngine

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
gemini_annotator = GeminiVisionAnnotator()
augmentation_engine = DatasetAugmentationEngine()

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
            "status": "AGUARDANDO_PRIMEIRO_FRAME",
            "latency_ms": 0.0,
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

        if domain_id == "naval":
            confirmed_vessels = pluggable_pipeline.process_frame(frame, time.time())
            annotated_frame = frame.copy()
            for v in confirmed_vessels:
                bbox = v.get("bbox", [0, 0, 10, 10])
                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                is_stat = v.get("is_stationary", True)
                spd = float(v.get("speed_knots", v.get("speed", 0.0)))
                v_id = v.get("vessel_id", "BR-STS")
                v_name = v.get("name", "Embarcacao")
                card = v.get("cardinal", "Proa Fixa")
                hdg = float(v.get("heading_deg", 0.0))
                det_data = v.get("detection_data", {})
                sources = det_data.get("fontes_detectoras", ["Ensemble"])
                is_mem = det_data.get("reforcado_por_memoria", False)
                ocr_num = v.get("fingerprint", {}).get("texto_extraido", {}).get("imo_number") if isinstance(v.get("fingerprint"), dict) else None

                box_color = (255, 200, 0) if not is_stat else (80, 220, 80)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)

                label_h = 42 if ocr_num else 30
                badge_y1 = max(0, y1 - label_h)
                badge_y2 = y1
                badge_w = max(180, (x2 - x1))
                badge_x2 = min(width, x1 + badge_w)

                overlay = annotated_frame.copy()
                cv2.rectangle(overlay, (x1, badge_y1), (badge_x2, badge_y2), (15, 20, 30), -1)
                cv2.addWeighted(overlay, 0.75, annotated_frame, 0.25, 0, annotated_frame)
                cv2.rectangle(annotated_frame, (x1, badge_y1), (badge_x2, badge_y2), box_color, 1)

                stat_txt = "PARADO" if is_stat else f"NAV {spd:.1f} nós"
                mem_tag = " [MEM]" if is_mem else ""
                sources_str = "+".join([s.split("_")[0] for s in sources[:2]])
                line1 = f"{v_id} | {stat_txt} ({sources_str}){mem_tag}"
                cv2.putText(annotated_frame, line1, (x1 + 4, badge_y1 + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)

                line2 = f"{v_name} | {card} ({int(hdg)}°)"
                cv2.putText(annotated_frame, line2, (x1 + 4, badge_y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (200, 220, 240), 1)

                if ocr_num:
                    cv2.putText(annotated_frame, f"IMO: {ocr_num}", (x1 + 4, badge_y1 + 37), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (100, 255, 200), 1)

                trail = v.get("trajectory_trail", [])
                if len(trail) >= 2:
                    pts = np.array([[p["x"], p["y"]] for p in trail], dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(annotated_frame, [pts], False, (0, 240, 255), 2)

            display_frame = annotated_frame

            vessels_ui = []
            for v in confirmed_vessels:
                v_id = v.get("vessel_id", "N/D")
                v_name = v.get("name", "Embarcacao")
                is_stat = bool(v.get("is_stationary", True))
                spd = float(v.get("speed_knots", v.get("speed", 0.0)))
                dest = v.get("destination", "N/D")
                card = v.get("cardinal", "N/D")
                hdg = float(v.get("heading_deg", 0.0))
                score = int(round(v.get("detection_data", {}).get("score_ensemble_final", 0.0) * 100))
                cor = v.get("fingerprint", {}).get("caracteristicas_visuais", {}).get("cor_casco", "N/D") if isinstance(v.get("fingerprint"), dict) else "N/D"
                # Antes caia num "IMO 9074729" hardcoded (dado fabricado) quando nao
                # havia leitura real de OCR - agora reporta honestamente que nao leu nada.
                _fp = v.get("fingerprint") if isinstance(v.get("fingerprint"), dict) else {}
                _texto = _fp.get("texto_extraido", {}) if isinstance(_fp.get("texto_extraido"), dict) else {}
                ocr_txt = _texto.get("imo_number") or _texto.get("detected_name") or "Sem leitura de OCR"

                _det = v.get("detection_data", {}) if isinstance(v.get("detection_data"), dict) else {}
                _gallery_match = v.get("reid_gallery_match")
                vessels_ui.append({
                    "vessel_id": v_id,
                    "name": v_name,
                    "is_stationary": is_stat,
                    "speed": spd,
                    "speed_knots": spd,
                    "heading_deg": hdg,
                    "cardinal": card,
                    "destination": dest,
                    "score_ensemble": score,
                    "bbox": v.get("bbox", [0, 0, 10, 10]),
                    "fingerprint": {
                        "cor_casco": cor,
                        "texto_ocr": ocr_txt
                    },
                    "trajectory_trail": v.get("trajectory_trail", []),
                    "fontes_detectoras": _det.get("fontes_detectoras", []),
                    "reforcado_por_memoria": bool(_det.get("reforcado_por_memoria", False)),
                    "reforcado_por_botsort": bool(_det.get("reforcado_por_botsort", False)),
                    "reid_embedding_ativo": v.get("embedding") is not None,
                    "reid_gallery_match": _gallery_match
                })

            _water_pct = pluggable_pipeline.water_segmenter.water_coverage_pct(pluggable_pipeline.last_water_mask)
            state["last_telemetry"] = {
                "status": "VIGILANCIA_ATIVA",
                "latency_ms": round(pluggable_pipeline.last_inference_latency_ms or 0.0, 1),
                "vessels": vessels_ui,
                "targets": vessels_ui,
                "vessel_history": [
                    {"vessel_id": v["vessel_id"], "last_seen": time.strftime("%H:%M:%S"), "last_destination": v["destination"]}
                    for v in vessels_ui
                ],
                "semantica_cena": {
                    "total_embarcacoes": len(vessels_ui),
                    "navegando": sum(1 for v in vessels_ui if not v["is_stationary"]),
                    "atracados": sum(1 for v in vessels_ui if v["is_stationary"]),
                    "cobertura_agua_pct": round(_water_pct, 1) if _water_pct is not None else "N/D"
                }
            }
        else:
            analysis_result, pil_annotated = analyzer.analyze_image(frame)
            display_frame = cv2.cvtColor(np.array(pil_annotated), cv2.COLOR_RGB2BGR)
            state["last_telemetry"] = {
                "status": analysis_result.get("status", "VIGILANCIA_ATIVA"),
                "latency_ms": analysis_result.get("tempo_processamento_ms", 0.0),
                "semantica_cena": analysis_result.get("semantica_cena", {}),
                "targets": analysis_result.get("targets_detectados", []),
                "vessels": analysis_result.get("targets_detectados", [])
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

@app.route("/api/live_raw_snapshot", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/live-stream-snapshot", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/<domain_id>/live_raw_snapshot", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/<domain_id>/live-stream-snapshot", methods=["GET", "POST", "OPTIONS"])
def api_live_raw_snapshot(domain_id="naval"):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    state = domain_streams_state.get(domain_id, domain_streams_state["naval"])
    frame = state.get("latest_raw_frame")
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
        "domain": domain_id,
        "image_base64": f"data:image/jpeg;base64,{b64_str}",
        "image_url": f"data:image/jpeg;base64,{b64_str}",
        "width": frame.shape[1],
        "height": frame.shape[0],
        "timestamp": time.time(),
        "stream_title": state.get("current_stream_title", "Câmera ao Vivo")
    })

@app.route("/api/extract-youtube", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/extract_youtube", methods=["GET", "POST", "OPTIONS"])
def api_extract_youtube():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json(silent=True) or {}
    url = data.get("youtube_url") or data.get("url") or request.form.get("url") or request.args.get("url") or "https://www.youtube.com/watch?v=5BxqzvR6TgM"
    try:
        resolved = get_live_stream_url(url)
        return jsonify({
            "status": "ok",
            "youtube_url": url,
            "stream_url": resolved or url,
            "title": "Transmissão do YouTube"
        })
    except Exception as e:
        return jsonify({"status": "ok", "stream_url": url, "warning": str(e)})

@app.route("/api/download-and-extract-frames", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/download_extract_frames", methods=["GET", "POST", "OPTIONS"])
def api_download_extract_frames():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json(silent=True) or {}
    url = data.get("youtube_url") or data.get("url") or request.form.get("url") or request.args.get("url") or "https://www.youtube.com/watch?v=5BxqzvR6TgM"
    resolved = get_live_stream_url(url)
    cap = cv2.VideoCapture(resolved if resolved else url)
    frames_extracted = []
    if cap.isOpened():
        for _ in range(5):
            ret, fr = cap.read()
            if ret and fr is not None:
                fr = cv2.resize(fr, (1280, 720))
                _, buf = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 90])
                b64 = base64.b64encode(buf).decode("utf-8")
                frames_extracted.append(f"data:image/jpeg;base64,{b64}")
        cap.release()
    if not frames_extracted:
        vpath = os.path.join(project_dir, "data", "teste_santos_3minutos_completo.mp4")
        if os.path.exists(vpath):
            c = cv2.VideoCapture(vpath)
            for _ in range(3):
                ret, fr = c.read()
                if ret and fr is not None:
                    _, buf = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    frames_extracted.append(f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}")
            c.release()

    return jsonify({
        "status": "ok",
        "frames_count": len(frames_extracted),
        "frames": frames_extracted
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
    
    if domain_id == "naval":
        confirmed_vessels = pluggable_pipeline.process_frame(img, time.time())
        vessels_ui = []
        for v in confirmed_vessels:
            v_id = v.get("vessel_id", "N/D")
            v_name = v.get("name", "Embarcacao")
            is_stat = bool(v.get("is_stationary", True))
            spd = float(v.get("speed_knots", v.get("speed", 0.0)))
            dest = v.get("destination", "N/D")
            card = v.get("cardinal", "N/D")
            hdg = float(v.get("heading_deg", 0.0))
            score = int(round(v.get("detection_data", {}).get("score_ensemble_final", 0.0) * 100))
            cor = v.get("fingerprint", {}).get("caracteristicas_visuais", {}).get("cor_casco", "N/D") if isinstance(v.get("fingerprint"), dict) else "N/D"
            # Antes caia num "IMO 9074729" hardcoded (dado fabricado) - agora honesto.
            _fp2 = v.get("fingerprint") if isinstance(v.get("fingerprint"), dict) else {}
            _texto2 = _fp2.get("texto_extraido", {}) if isinstance(_fp2.get("texto_extraido"), dict) else {}
            ocr_txt = _texto2.get("imo_number") or _texto2.get("detected_name") or "Sem leitura de OCR"

            _det2 = v.get("detection_data", {}) if isinstance(v.get("detection_data"), dict) else {}
            vessels_ui.append({
                "vessel_id": v_id,
                "name": v_name,
                "is_stationary": is_stat,
                "speed": spd,
                "speed_knots": spd,
                "heading_deg": hdg,
                "cardinal": card,
                "destination": dest,
                "score_ensemble": score,
                "bbox": v.get("bbox", [0, 0, 10, 10]),
                "fingerprint": {
                    "cor_casco": cor,
                    "texto_ocr": ocr_txt
                },
                "trajectory_trail": v.get("trajectory_trail", []),
                "fontes_detectoras": _det2.get("fontes_detectoras", []),
                "reforcado_por_memoria": bool(_det2.get("reforcado_por_memoria", False)),
                "reforcado_por_botsort": bool(_det2.get("reforcado_por_botsort", False)),
                "reid_embedding_ativo": v.get("embedding") is not None,
                "reid_gallery_match": v.get("reid_gallery_match")
            })
        _water_pct = pluggable_pipeline.water_segmenter.water_coverage_pct(pluggable_pipeline.last_water_mask)
        return jsonify({
            "status": "VIGILANCIA_ATIVA",
            "tempo_processamento_ms": round(pluggable_pipeline.last_inference_latency_ms or 0.0, 1),
            "vessels": vessels_ui,
            "targets_detectados": vessels_ui,
            "semantica_cena": {
                "total_embarcacoes": len(vessels_ui),
                "navegando": sum(1 for v in vessels_ui if not v["is_stationary"]),
                "atracados": sum(1 for v in vessels_ui if v["is_stationary"]),
                "cobertura_agua_pct": round(_water_pct, 1) if _water_pct is not None else "N/D"
            }
        })

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
    """Retorna os modelos de IA estritamente atrelados ao tipo de dataset / domínio ativo."""
    domain_req = request.args.get("domain", "naval")
    dom_conf = DOMAINS_CONFIG.get(domain_req, DOMAINS_CONFIG["naval"])
    domain_models = list(dom_conf.get("models", []))
    
    # Se o domínio não tiver lista específica, cria modelos padrão com o Gemini
    if not domain_models:
        domain_models = [
            {
                "id": f"gemini_vision_{domain_req}",
                "name": f"Google Gemini Vision ({domain_req.capitalize()})",
                "framework": "Google Multimodal",
                "description": f"Auto-rotulagem zero-shot com Google Gemini para o domínio {domain_req}.",
                "is_gemini": True,
                "default_conf": 0.20
            },
            {
                "id": "domain_default",
                "name": f"Modelo Especialista ({domain_req.capitalize()})",
                "framework": "Ultralytics / PyTorch",
                "description": f"Detector padrão treinado para o domínio {domain_req}.",
                "is_gemini": False,
                "default_conf": 0.20
            }
        ]
    
    # Adiciona modelos customizados do usuário que foram carregados
    catalog = pluggable_pipeline.registry.get_catalog()
    for m in catalog:
        if m.get("is_custom", False):
            domain_models.append({
                "id": m["id"],
                "name": f"{m['name']} (Customizado)",
                "framework": m.get("framework", "PyTorch"),
                "description": m.get("description", "Modelo customizado"),
                "is_gemini": False,
                "is_custom": True,
                "default_conf": m.get("default_conf", 0.20)
            })
            
    default_active = domain_models[0]["id"] if domain_models else "domain_default"
    return jsonify({
        "status": "ok",
        "domain": domain_req,
        "active_model_id": default_active,
        "models": domain_models,
        "gemini_configured": gemini_annotator.is_configured()
    })

@app.route("/api/annotation/gemini_key", methods=["GET", "POST", "OPTIONS"])
def api_annotation_gemini_key():
    """Consulta ou atualiza a chave da API do Google Gemini."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    if request.method == "POST":
        data = request.get_json() or {}
        key = data.get("api_key", "").strip()
        model_name = data.get("model_name", "gemini-1.5-flash")
        gemini_annotator.set_api_key(key)
        gemini_annotator.model_name = model_name
        return jsonify({
            "status": "ok",
            "message": "Chave do Google Gemini configurada com sucesso!",
            "configured": gemini_annotator.is_configured(),
            "model_name": gemini_annotator.model_name
        })
    return jsonify({
        "status": "ok",
        "configured": gemini_annotator.is_configured(),
        "model_name": gemini_annotator.model_name
    })

@app.route("/api/annotation/gemini_detect", methods=["POST", "OPTIONS"])
def api_annotation_gemini_detect():
    """Executa detecção e auto-rotulagem zero-shot com Google Gemini Multimodal Vision."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    domain_req = data.get("domain", "naval")
    conf_thresh = float(data.get("conf") or data.get("conf_threshold") or 0.20)
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

    res = gemini_annotator.detect_objects_zero_shot(img_bgr, dataset_classes, domain=domain_req, conf_threshold=conf_thresh)
    return jsonify(res)

@app.route("/api/annotation/augment_frame", methods=["POST", "OPTIONS"])
def api_annotation_augment_frame():
    """Gera variações aumentadas do frame atual com caixas e polígonos recalculados."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    base64_str = data.get("image_base64")
    boxes = data.get("boxes", [])
    polygons = data.get("polygons", [])
    options = data.get("options", {})

    if not base64_str:
        return jsonify({"error": "Imagem ausente"}), 400

    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]

    img_bytes = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        return jsonify({"error": "Falha ao decodificar imagem"}), 400

    aug_results = augmentation_engine.generate_augmentations_for_frame(img_bgr, boxes, polygons, options)
    
    encoded_items = []
    for item in aug_results:
        _, buf = cv2.imencode('.jpg', item["image_bgr"], [int(cv2.IMWRITE_JPEG_QUALITY), 88])
        b64_out = base64.b64encode(buf).decode('utf-8')
        encoded_items.append({
            "name": item["name"],
            "tag": item["tag"],
            "image_base64": f"data:image/jpeg;base64,{b64_out}",
            "boxes": item["boxes"],
            "polygons": item["polygons"],
            "boxes_count": len(item["boxes"]),
            "polygons_count": len(item["polygons"])
        })

    return jsonify({
        "status": "ok",
        "count": len(encoded_items),
        "variations": encoded_items
    })

@app.route("/api/annotation/batch_augment", methods=["POST", "OPTIONS"])
def api_annotation_batch_augment():
    """Aplica Data Augmentation em lote salvando as novas imagens diretamente no dataset."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    domain_req = data.get("domain", "naval")
    options = data.get("options", {})
    mgr = domain_dataset_managers.get(domain_req, dataset_manager)

    items = mgr.list_annotations().get("items", [])
    if not items:
        return jsonify({"error": "Nenhum frame salvo no dataset para aumentar"}), 400

    saved_augmented_count = 0
    for it in items:
        loaded = mgr.load_annotation(it["id"])
        if loaded.get("status") == "ok":
            img_url = loaded.get("image_url", "")
            img_rel_path = img_url.replace("/media/annotated/", "")
            full_img_path = os.path.join(mgr.images_dir, img_rel_path)
            if os.path.exists(full_img_path):
                img_bgr = cv2.imread(full_img_path)
                if img_bgr is not None:
                    aug_list = augmentation_engine.generate_augmentations_for_frame(
                        img_bgr, loaded.get("boxes", []), loaded.get("polygons", []), options
                    )
                    for a in aug_list:
                        mgr.save_annotation(
                            a["image_bgr"],
                            boxes=a["boxes"],
                            polygons=a["polygons"],
                            source_video=f"aug_{it.get('filename', 'img')}",
                            frame_timestamp=0.0,
                            notes=f"Data Augmentation: {a['name']}",
                            is_ai_assisted=True,
                            human_corrected=True
                        )
                        saved_augmented_count += 1

    return jsonify({
        "status": "ok",
        "domain": domain_req,
        "augmented_images_created": saved_augmented_count,
        "message": f"{saved_augmented_count} novas variações de dataset criadas com sucesso!"
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
    """Executa inferência com o modelo de IA selecionado ou Google Gemini Vision para auto-rotulagem."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json() or {}
    domain_req = data.get("domain", "naval")
    model_id = data.get("model_id") or "domain_default"
    conf_thresh = float(data.get("conf") or data.get("conf_threshold") or 0.20)
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

    # 1. Se for modelo Google Gemini Vision
    if "gemini" in model_id.lower() or model_id.startswith("gemini_vision"):
        res = gemini_annotator.detect_objects_zero_shot(img_bgr, dataset_classes, domain=domain_req, conf_threshold=conf_thresh)
        return jsonify({
            "status": "ok",
            "model_id": model_id,
            "model_used": res.get("model_name", "Google Gemini Vision"),
            "domain": domain_req,
            "conf_threshold": conf_thresh,
            "count": len(res.get("detections", [])),
            "detections": res.get("detections", []),
            "is_gemini": True,
            "is_real_api": res.get("is_real_api", False),
            "notice": res.get("notice")
        })

    # 2. Se for modelo especialista do domínio ou PluggableVisionPipeline
    dets = []
    try:
        if model_id in [m["id"] for m in pluggable_pipeline.registry.get_catalog()]:
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
                c_name = d.get("class_name", "objeto").lower()
                cid = 0
                if c_name in dataset_classes:
                    cid = dataset_classes.index(c_name)
                elif len(dataset_classes) > 0:
                    cid = 0
                    c_name = dataset_classes[0]
                dets.append({
                    "bbox": d["bbox"],
                    "class_id": cid,
                    "class_name": c_name,
                    "confidence": round(float(d.get("conf", 0.85)), 3),
                    "source_model": model_id
                })
        else:
            analyzer = domain_analyzers.get(domain_req, domain_analyzers["naval"])
            analysis_res, _ = analyzer.analyze_image(img_bgr, conf=conf_thresh)
            for t in analysis_res.get("targets_detectados", []):
                c_name = t.get("class_name", "objeto").lower()
                cid = 0
                if c_name in dataset_classes:
                    cid = dataset_classes.index(c_name)
                elif len(dataset_classes) > 0:
                    cid = 0
                    c_name = dataset_classes[0]
                dets.append({
                    "bbox": t["bbox"],
                    "class_id": cid,
                    "class_name": c_name,
                    "confidence": round(float(t.get("confidence", 0.85)), 3),
                    "source_model": f"domain_{domain_req}"
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
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    elif "PORT" in os.environ:
        port = int(os.environ["PORT"])
    print(f"[AI Vision Hub] Iniciando servidor em http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)

