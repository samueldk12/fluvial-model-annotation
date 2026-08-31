# -*- coding: utf-8 -*-
"""Template HTML da página principal do Painel Naval Inteligente com Arquitetura Acoplável."""

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Naval Inteligente — Porto de Santos</title>
    <style>
        :root {
            --bg-dark: #0b0e13;
            --bg-canvas: #07090c;
            --bg-card: #10141b;
            --bg-card-hover: #141a22;
            --bg-inset: #0a0d12;
            --border: #1c232c;
            --border-strong: #262e39;
            --accent-cyan: #4c9fb0;
            --accent-green: #3fa66b;
            --accent-orange: #c98a3e;
            --accent-blue: #3d6fa8;
            --accent-purple: #8b5cf6;
            --accent-red: #c65950;
            --text-main: #e4e8ee;
            --text-muted: #8590a0;
            --text-faint: #57616f;
            --radius-sm: 4px;
            --radius-md: 6px;
            --radius-lg: 8px;
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            --font-mono: 'Cascadia Mono', Consolas, 'Liberation Mono', monospace;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; }
        body {
            background: var(--bg-canvas);
            color: var(--text-main);
            font-family: var(--font-sans);
            padding: 16px;
            -webkit-font-smoothing: antialiased;
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }

        /* ===== TOPBAR ===== */
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 18px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            margin-bottom: 14px;
        }
        .brand { display: flex; align-items: center; gap: 12px; }
        .brand-mark {
            width: 32px; height: 32px;
            display: flex; align-items: center; justify-content: center;
            border-radius: var(--radius-sm);
            background: var(--accent-blue);
            color: #fff;
        }
        .brand-text h1 { font-size: 15px; font-weight: 700; color: var(--text-main); }
        .brand-text .sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
        .topbar-right { display: flex; align-items: center; gap: 8px; }
        .status-chip {
            display: flex; align-items: center; gap: 6px;
            padding: 5px 10px; border-radius: var(--radius-sm);
            font-size: 11px; font-weight: 600;
            background: var(--bg-inset); color: var(--text-main);
            border: 1px solid var(--border-strong);
        }
        .status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--accent-green); flex-shrink: 0; }
        .gpu-meta {
            font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);
            padding: 5px 9px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: var(--radius-sm);
        }
        .topbar-btn {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 6px 12px; font-size: 11.5px; font-weight: 600;
            color: var(--text-main); background: var(--bg-inset);
            border: 1px solid var(--border-strong); border-radius: var(--radius-sm);
            text-decoration: none; cursor: pointer; transition: all 0.15s ease;
        }
        .topbar-btn:hover { background: var(--bg-card-hover); border-color: var(--accent-blue); }
        .topbar-btn.highlight { background: rgba(201,138,62,0.15); border-color: var(--accent-orange); color: #fff; }
        .topbar-btn.highlight:hover { background: var(--accent-orange); color: #000; }

        /* ===== LAYOUT ===== */
        .grid { display: grid; grid-template-columns: 310px 1fr 370px; gap: 14px; align-items: start; }
        .col-stack { display: flex; flex-direction: column; gap: 14px; }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 14px;
        }
        .card h3 { font-size: 11.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
        .panel-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .panel-title h3 { margin-bottom: 0; }
        .badge { padding: 2px 7px; border-radius: var(--radius-sm); font-size: 10.5px; font-weight: 700; border: 1px solid transparent; }
        .badge.blue { color: var(--accent-blue); background: rgba(61,111,168,0.12); border-color: rgba(61,111,168,0.3); }
        .badge.green { color: var(--accent-green); background: rgba(63,166,107,0.12); border-color: rgba(63,166,107,0.3); }
        .badge.orange { color: var(--accent-orange); background: rgba(201,138,62,0.12); border-color: rgba(201,138,62,0.3); }
        .badge.purple { color: var(--accent-purple); background: rgba(139,92,246,0.12); border-color: rgba(139,92,246,0.3); }

        /* Form Controls */
        .form-group { margin-bottom: 9px; }
        .form-label { display: block; font-size: 10.5px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; }
        .select-input, .text-input {
            width: 100%; padding: 6px 8px; background: var(--bg-inset); border: 1px solid var(--border-strong);
            border-radius: 4px; color: var(--text-main); font-size: 11.5px; font-family: inherit; outline: none;
        }
        .select-input:focus, .text-input:focus { border-color: var(--accent-blue); }

        /* Sliders */
        .slider-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 11px; }
        .range-slider {
            width: 100%; -webkit-appearance: none; height: 5px; border-radius: 3px;
            background: var(--border-strong); outline: none; margin-bottom: 8px;
        }
        .range-slider::-webkit-slider-thumb {
            -webkit-appearance: none; width: 13px; height: 13px; border-radius: 50%;
            background: var(--accent-cyan); cursor: pointer;
        }

        /* Checkbox Switch */
        .switch-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 5px 0; border-bottom: 1px solid rgba(28,35,44,0.6); font-size: 11.5px;
        }
        .switch-row:last-child { border-bottom: none; }
        .switch { position: relative; display: inline-block; width: 32px; height: 17px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .switch-slider {
            position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
            background-color: var(--border-strong); transition: .2s; border-radius: 17px;
        }
        .switch-slider:before {
            position: absolute; content: ""; height: 11px; width: 11px; left: 3px; bottom: 3px;
            background-color: white; transition: .2s; border-radius: 50%;
        }
        input:checked + .switch-slider { background-color: var(--accent-green); }
        input:checked + .switch-slider:before { transform: translateX(15px); }

        /* Buttons */
        .btn {
            width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;
            padding: 8px 10px; margin-bottom: 6px; border-radius: var(--radius-sm);
            font-size: 11.5px; font-weight: 600; font-family: inherit; cursor: pointer;
            border: 1px solid var(--border-strong); background: var(--bg-inset); color: var(--text-main);
            transition: all 0.15s ease;
        }
        .btn:hover { background: var(--bg-card-hover); border-color: var(--accent-blue); }
        .btn.primary { background: var(--accent-blue); color: #fff; border-color: var(--accent-blue); }
        .btn.primary:hover { background: #325a87; }
        .btn.outline-cyan { border-color: var(--accent-cyan); color: var(--accent-cyan); }
        .btn.outline-cyan:hover { background: rgba(76,159,176,0.15); }

        /* Video Feed Container */
        .video-box {
            position: relative; background: #000; border: 1px solid var(--border-strong);
            border-radius: var(--radius-lg); overflow: hidden;
        }
        .video-box img { width: 100%; height: auto; display: block; }
        .video-hud {
            position: absolute; bottom: 10px; left: 10px; right: 10px;
            display: flex; justify-content: space-between; align-items: center;
            background: rgba(10, 13, 18, 0.85); border: 1px solid var(--border-strong);
            border-radius: var(--radius-sm); padding: 6px 12px; font-size: 11px;
            font-family: var(--font-mono); color: var(--text-muted);
        }

        /* Vessel List & Cards */
        .vessel-list { display: flex; flex-direction: column; gap: 8px; max-height: 480px; overflow-y: auto; }
        .vessel-card {
            background: var(--bg-inset); border: 1px solid var(--border);
            border-radius: var(--radius-md); padding: 10px; transition: all 0.15s;
        }
        .vessel-card:hover { border-color: var(--accent-cyan); background: var(--bg-card-hover); }
        .vessel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .vessel-id { font-size: 12px; font-weight: 700; color: var(--accent-cyan); font-family: var(--font-mono); }
        .vessel-stat { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 3px; }
        .vessel-stat.nav { background: rgba(0, 240, 255, 0.15); color: #00f0ff; }
        .vessel-stat.stop { background: rgba(0, 230, 118, 0.15); color: #00e676; }
        .vessel-details { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px; color: var(--text-muted); }
        .vessel-details strong { color: var(--text-main); }

        /* History Table */
        .hist-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 6px; }
        .hist-table th, .hist-table td { padding: 5px 8px; text-align: left; border-bottom: 1px solid var(--border); }
        .hist-table th { color: var(--text-muted); font-size: 10px; text-transform: uppercase; background: var(--bg-inset); }

        /* Toast */
        #toast {
            position: fixed; bottom: 20px; right: 20px;
            background: var(--bg-card); border: 1px solid var(--accent-green);
            color: var(--text-main); padding: 10px 16px; border-radius: 6px;
            font-size: 12px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            opacity: 0; transform: translateY(10px); transition: all 0.25s ease;
            z-index: 9999; pointer-events: none;
        }
        #toast.show { opacity: 1; transform: translateY(0); }
    </style>
</head>
<body>
    <div class="topbar">
        <div class="brand">
            <div class="brand-mark">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </div>
            <div class="brand-text">
                <h1>Painel Naval Inteligente</h1>
                <div class="sub">Porto de Santos • Vigilância Neural &amp; Acoplamento de Modelos</div>
            </div>
        </div>
        <div class="topbar-right">
            <div class="status-chip">
                <span class="status-dot"></span>
                <span id="top-status">ONLINE</span>
            </div>
            <div class="gpu-meta">DirectML</div>
            <a href="/anotar" class="topbar-btn highlight" title="Estúdio de Anotação e Segmentação CVAT">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                Anotar (CVAT)
            </a>
            <a href="/sobre" class="topbar-btn" title="Arquitetura e Documentação">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
                Sobre
            </a>
        </div>
    </div>

    <div class="grid">
        <!-- COLUNA ESQUERDA: ACOPLAMENTO DE MODELOS & CONTROLES -->
        <div class="col-stack">
            <!-- PAINEL DE ARQUITETURA ACOPLÁVEL -->
            <div class="card" style="border-color: rgba(76,159,176,0.4);">
                <div class="panel-title">
                    <h3><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px; margin-right:4px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Arquitetura &amp; Modelos</h3>
                    <span class="badge blue" id="active-model-badge">Ensemble</span>
                </div>

                <div class="form-group" style="background:rgba(24,144,255,0.08); padding:8px; border-radius:4px; border:1px solid rgba(24,144,255,0.25); margin-bottom:10px;">
                    <label class="form-label" style="color:var(--accent-cyan);"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:3px;"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>Preset de Arquitetura</label>
                    <select class="select-input" id="arch-preset-select" style="font-weight:600;">
                        <option value="pre_arch_production">Arquitetura de Produção: Ensemble Multi-Domínio (WBF + BoT-SORT + DINOv2 + IMO OCR)</option>
                        <option value="test_arch_experimental">Arquitetura de Teste: YOLO11n + YOLO26n Edge Ultra-Rápido</option>
                    </select>
                </div>

                <div class="form-group">
                    <label class="form-label">Modelo / Pipeline Individual</label>
                    <select class="select-input" id="model-select">
                        <option value="ensemble_full">Ensemble Multi-Domínio (SAR + Naval + COCO)</option>
                        <option value="mewan2808_sar">MeWan2808 YOLOv8 SAR (Fluvial &amp; Radar)</option>
                        <option value="sixopen_y8naval">SixOpen Y8Naval (ONNX Aéreo 50 Classes)</option>
                        <option value="yolo11n">YOLO11n Baseline (Ultralytics v11)</option>
                        <option value="yolo26n">YOLO26n Baseline (Ultralytics v26)</option>
                        <option value="yolov8n">YOLOv8n Geral (COCO)</option>
                        <option value="mayrajeo_marine">Mayrajeo Marine Vessel (Porto Cais)</option>
                        <option value="vessel_perception_net">VesselPerceptionNet (PyTorch)</option>
                    </select>
                </div>

                <!-- Sliders -->
                <div style="margin-top:10px;">
                    <div class="slider-row">
                        <span class="form-label" style="margin-bottom:0;">Confiança Mínima:</span>
                        <strong id="conf-val" style="font-family:var(--font-mono); color:var(--accent-cyan);">15%</strong>
                    </div>
                    <input type="range" class="range-slider" id="conf-slider" min="0.05" max="0.80" step="0.05" value="0.15">

                    <div class="slider-row">
                        <span class="form-label" style="margin-bottom:0;">Limiar IoU / NMS:</span>
                        <strong id="iou-val" style="font-family:var(--font-mono); color:var(--accent-cyan);">45%</strong>
                    </div>
                    <input type="range" class="range-slider" id="iou-slider" min="0.10" max="0.80" step="0.05" value="0.45">
                </div>

                <!-- Toggles Modulares -->
                <div style="margin-top:6px;">
                    <label class="form-label" style="margin-bottom:6px;">Submódulos Ativos</label>
                    <div class="switch-row">
                        <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>Visão Noturna (CLAHE)</span>
                        <label class="switch">
                            <input type="checkbox" id="toggle-night" checked>
                            <span class="switch-slider"></span>
                        </label>
                    </div>
                    <div class="switch-row">
                        <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/></svg>Segmentação Água (eWaSR)</span>
                        <label class="switch">
                            <input type="checkbox" id="toggle-water" checked>
                            <span class="switch-slider"></span>
                        </label>
                    </div>
                    <div class="switch-row">
                        <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>Memória Espacial &amp; Rastro</span>
                        <label class="switch">
                            <input type="checkbox" id="toggle-spatial" checked>
                            <span class="switch-slider"></span>
                        </label>
                    </div>
                    <div class="switch-row">
                        <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>Classificador ViT &amp; Re-ID</span>
                        <label class="switch">
                            <input type="checkbox" id="toggle-vit" checked>
                            <span class="switch-slider"></span>
                        </label>
                    </div>
                    <div class="switch-row">
                        <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>OCR de Casco (EasyOCR)</span>
                        <label class="switch">
                            <input type="checkbox" id="toggle-ocr" checked>
                            <span class="switch-slider"></span>
                        </label>
                    </div>
                </div>

                <!-- Upload de Modelo Customizado -->
                <div style="margin-top:12px;">
                    <input type="file" id="model-upload-input" accept=".pt,.onnx" style="display:none;">
                    <button class="btn outline-cyan" onclick="document.getElementById('model-upload-input').click()">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Acoplar Novo Modelo (.pt / .onnx)
                    </button>
                </div>
            </div>

            <!-- FONTE DE VÍDEO -->
            <div class="card">
                <div class="panel-title">
                    <h3>Fonte de Transmissão</h3>
                </div>
                <div class="form-group">
                    <select class="select-input" id="stream-source-select">
                        <option value="LIVE">Transmissão ao Vivo (YouTube)</option>
                        <option value="LOCAL">Vídeo Gravado (Porto de Santos 3min)</option>
                    </select>
                </div>
                <div class="form-group" id="yt-url-group">
                    <label class="form-label">URL do YouTube</label>
                    <input type="text" class="text-input" id="yt-url-input" value="https://www.youtube.com/watch?v=5BxqzvR6TgM">
                    <button class="btn" style="margin-top:6px;" id="btn-update-yt">Aplicar Nova URL</button>
                </div>
            </div>
        </div>

        <!-- COLUNA CENTRAL: VÍDEO AO VIVO & STATUS -->
        <div class="col-stack">
            <div class="video-box">
                <img id="video-stream" src="/video_feed" alt="Stream Naval do Porto de Santos">
                <div class="video-hud">
                    <span id="hud-model-info">MODELO: ENSEMBLE MULTI-DOMÍNIO</span>
                    <span id="hud-latency">LATÊNCIA: ~38ms</span>
                    <span id="hud-count">0 EMBARCAÇÕES</span>
                </div>
            </div>

            <!-- Telemetria Rápida -->
            <div class="card">
                <div class="panel-title">
                    <h3>Telemetria de Canal &amp; Navegação</h3>
                    <span class="badge green" id="channel-status-badge">NORMAL</span>
                </div>
                <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:8px; text-align:center;">
                    <div style="background:var(--bg-inset); padding:8px; border-radius:4px; border:1px solid var(--border);">
                        <div style="font-size:18px; font-weight:700; color:var(--accent-cyan);" id="stat-active-vessels">0</div>
                        <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Na Tela</div>
                    </div>
                    <div style="background:var(--bg-inset); padding:8px; border-radius:4px; border:1px solid var(--border);">
                        <div style="font-size:18px; font-weight:700; color:var(--accent-green);" id="stat-stationary-vessels">0</div>
                        <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Atracados / Parados</div>
                    </div>
                    <div style="background:var(--bg-inset); padding:8px; border-radius:4px; border:1px solid var(--border);">
                        <div style="font-size:18px; font-weight:700; color:var(--accent-orange);" id="stat-moving-vessels">0</div>
                        <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Navegando</div>
                    </div>
                    <div style="background:var(--bg-inset); padding:8px; border-radius:4px; border:1px solid var(--border);">
                        <div style="font-size:18px; font-weight:700; color:var(--accent-purple);" id="stat-total-seen">0</div>
                        <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Total na Sessão</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- COLUNA DIREITA: EMBARCAÇÕES ATIVAS & HISTÓRICO -->
        <div class="col-stack">
            <!-- EMBARCAÇÕES NA TELA -->
            <div class="card">
                <div class="panel-title">
                    <h3>Embarcações Rastreadas (<span id="vessels-count-title">0</span>)</h3>
                </div>
                <div class="vessel-list" id="active-vessels-list">
                    <div style="color:var(--text-faint); font-size:11px; padding:12px; text-align:center;">
                        Aguardando detecção no fluxo de vídeo...
                    </div>
                </div>
            </div>

            <!-- HISTÓRICO DA SESSÃO -->
            <div class="card">
                <div class="panel-title">
                    <h3>Histórico de Tráfego</h3>
                </div>
                <table class="hist-table">
                    <thead>
                        <tr><th>ID</th><th>Visto às</th><th>Status</th></tr>
                    </thead>
                    <tbody id="history-table-body">
                        <tr><td colspan="3" style="text-align:center; color:var(--text-faint);">Nenhum registro ainda.</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div id="toast">Notificação</div>

    <script>
        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }

        // Carrega Lista de Modelos e Presets Acoplados
        async function loadModelsCatalog() {
            try {
                const res = await fetch('/api/models');
                const d = await res.json();
                const sel = document.getElementById('model-select');
                sel.innerHTML = '';
                d.catalog.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.id;
                    opt.text = `${m.name} (${m.framework})`;
                    if (m.id === d.active_model_id) opt.selected = true;
                    sel.appendChild(opt);
                });

                const presetSel = document.getElementById('arch-preset-select');
                if (d.presets && d.presets.length > 0) {
                    presetSel.innerHTML = '';
                    d.presets.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.id;
                        opt.text = p.name;
                        if (p.id === d.active_preset_id) opt.selected = true;
                        presetSel.appendChild(opt);
                    });
                }

                document.getElementById('active-model-badge').innerText = d.active_model_id;
                document.getElementById('hud-model-info').innerText = `MODELO: ${d.active_model_id.toUpperCase()}`;
            } catch (e) {
                console.error("Erro ao carregar catálogo de modelos:", e);
            }
        }

        // Aplicação de Preset de Arquitetura
        document.getElementById('arch-preset-select').addEventListener('change', async (e) => {
            const pid = e.target.value;
            showToast(`Aplicando arquitetura: ${pid}...`);
            try {
                const res = await fetch('/api/architectures/apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ preset_id: pid })
                });
                const d = await res.json();
                if (d.status === 'ok') {
                    showToast(`Arquitetura aplicada: ${d.preset_name || pid}`);
                    const cfg = d.pipeline_status.config;
                    document.getElementById('model-select').value = cfg.active_model_id;
                    document.getElementById('conf-slider').value = cfg.conf_threshold;
                    document.getElementById('conf-val').innerText = `${Math.round(cfg.conf_threshold * 100)}%`;
                    document.getElementById('iou-slider').value = cfg.iou_threshold;
                    document.getElementById('iou-val').innerText = `${Math.round(cfg.iou_threshold * 100)}%`;
                    document.getElementById('toggle-night').checked = cfg.enable_night_enhancement;
                    document.getElementById('toggle-water').checked = cfg.enable_water_segmentation;
                    document.getElementById('toggle-spatial').checked = cfg.enable_spatial_memory;
                    document.getElementById('toggle-vit').checked = cfg.enable_vit_reid;
                    document.getElementById('toggle-ocr').checked = cfg.enable_ocr;
                    document.getElementById('active-model-badge').innerText = cfg.active_model_id;
                    document.getElementById('hud-model-info').innerText = `MODELO: ${cfg.active_model_id.toUpperCase()}`;
                }
            } catch (err) {
                showToast(`Erro ao aplicar arquitetura: ${err}`);
            }
        });

        // Atualização de Configuração do Pipeline
        async function updatePipelineConfig() {
            const modelId = document.getElementById('model-select').value;
            const conf = parseFloat(document.getElementById('conf-slider').value);
            const iou = parseFloat(document.getElementById('iou-slider').value);
            const night = document.getElementById('toggle-night').checked;
            const water = document.getElementById('toggle-water').checked;
            const spatial = document.getElementById('toggle-spatial').checked;
            const vit = document.getElementById('toggle-vit').checked;
            const ocr = document.getElementById('toggle-ocr').checked;

            document.getElementById('conf-val').innerText = `${Math.round(conf * 100)}%`;
            document.getElementById('iou-val').innerText = `${Math.round(iou * 100)}%`;

            try {
                const res = await fetch('/api/models/set_active', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        active_model_id: modelId,
                        conf_threshold: conf,
                        iou_threshold: iou,
                        enable_night_enhancement: night,
                        enable_water_segmentation: water,
                        enable_spatial_memory: spatial,
                        enable_vit_reid: vit,
                        enable_ocr: ocr
                    })
                });
                const d = await res.json();
                if (d.status === 'ok') {
                    document.getElementById('active-model-badge').innerText = modelId;
                    document.getElementById('hud-model-info').innerText = `MODELO: ${modelId.toUpperCase()}`;
                    showToast(`Pipeline atualizado: ${modelId}`);
                }
            } catch (e) {
                showToast(`Erro ao atualizar pipeline: ${e}`);
            }
        }

        document.getElementById('model-select').addEventListener('change', updatePipelineConfig);
        document.getElementById('conf-slider').addEventListener('input', (e) => {
            document.getElementById('conf-val').innerText = `${Math.round(e.target.value * 100)}%`;
        });
        document.getElementById('conf-slider').addEventListener('change', updatePipelineConfig);
        document.getElementById('iou-slider').addEventListener('input', (e) => {
            document.getElementById('iou-val').innerText = `${Math.round(e.target.value * 100)}%`;
        });
        document.getElementById('iou-slider').addEventListener('change', updatePipelineConfig);
        ['toggle-night', 'toggle-water', 'toggle-spatial', 'toggle-vit', 'toggle-ocr'].forEach(id => {
            document.getElementById(id).addEventListener('change', updatePipelineConfig);
        });

        // Upload de Modelo Customizado
        document.getElementById('model-upload-input').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            showToast('Acoplando modelo...');
            try {
                const res = await fetch('/api/models/upload', { method: 'POST', body: formData });
                const d = await res.json();
                if (d.status === 'ok') {
                    showToast(`Modelo acoplado com sucesso: ${d.filename}`);
                    await loadModelsCatalog();
                    updatePipelineConfig();
                } else {
                    showToast(`Erro: ${d.error || 'Falha ao carregar modelo'}`);
                }
            } catch (err) {
                showToast(`Erro no envio: ${err}`);
            }
        });

        // Fonte de Stream
        document.getElementById('stream-source-select').addEventListener('change', async (e) => {
            const src = e.target.value;
            const ytUrl = document.getElementById('yt-url-input').value;
            await fetch('/api/set_stream_source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: src, youtube_url: ytUrl })
            });
            document.getElementById('video-stream').src = `/video_feed?source=${src}&t=${Date.now()}`;
            showToast(`Fonte alterada para: ${src}`);
        });
        document.getElementById('btn-update-yt').onclick = async () => {
            const ytUrl = document.getElementById('yt-url-input').value;
            await fetch('/api/set_stream_source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: 'LIVE', youtube_url: ytUrl })
            });
            document.getElementById('video-stream').src = `/video_feed?source=LIVE&t=${Date.now()}`;
            showToast('URL do YouTube atualizada!');
        };

        // Telemetria Periódica
        async function fetchTelemetry() {
            try {
                const res = await fetch('/api/live_telemetry');
                const d = await res.json();

                document.getElementById('top-status').innerText = d.status || 'VIGILÂNCIA ATIVA';
                const vessels = d.vessels || [];
                document.getElementById('vessels-count-title').innerText = vessels.length;
                document.getElementById('stat-active-vessels').innerText = vessels.length;
                document.getElementById('hud-count').innerText = `${vessels.length} EMBARCAÇÃO(ÕES)`;

                const moving = vessels.filter(v => !v.is_stationary).length;
                const stationary = vessels.filter(v => v.is_stationary).length;
                document.getElementById('stat-moving-vessels').innerText = moving;
                document.getElementById('stat-stationary-vessels').innerText = stationary;

                const history = d.vessel_history || [];
                document.getElementById('stat-total-seen').innerText = history.length;

                // Renderiza Lista Ativa
                const vList = document.getElementById('active-vessels-list');
                if (vessels.length === 0) {
                    vList.innerHTML = '<div style="color:var(--text-faint); font-size:11px; padding:12px; text-align:center;">Canal livre — nenhuma embarcação na tela.</div>';
                } else {
                    vList.innerHTML = '';
                    vessels.forEach(v => {
                        const card = document.createElement('div');
                        card.className = 'vessel-card';
                        const statusClass = v.is_stationary ? 'stop' : 'nav';
                        const statusText = v.is_stationary ? 'PARADO' : `NAVEGANDO (${(v.speed || 0).toFixed(1)} nós)`;
                        const ocrInfo = v.fingerprint?.texto_ocr ? `<div>Inscrição/IMO: <strong>${v.fingerprint.texto_ocr}</strong></div>` : '';
                        card.innerHTML = `
                            <div class="vessel-header">
                                <span class="vessel-id">${v.vessel_id}</span>
                                <span class="vessel-stat ${statusClass}">${statusText}</span>
                            </div>
                            <div class="vessel-details">
                                <div>Tipo: <strong>${v.name || 'Embarcação'}</strong></div>
                                <div>Destino: <strong>${v.destination || 'Canal de Santos'}</strong></div>
                                <div>Confiança: <strong>${v.score_ensemble || 85}%</strong></div>
                                <div>Rumo: <strong>${v.cardinal || 'Proa Fixa'} (${Math.round(v.heading_deg || 0)}°)</strong></div>
                                <div>Cor Casco: <strong>${v.fingerprint?.cor_casco || 'N/D'}</strong></div>
                                ${ocrInfo}
                            </div>
                        `;
                        vList.appendChild(card);
                    });
                }

                // Renderiza Histórico
                const hTable = document.getElementById('history-table-body');
                if (history.length > 0) {
                    hTable.innerHTML = '';
                    history.slice(0, 10).forEach(h => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td><strong style="color:var(--accent-cyan); font-family:var(--font-mono);">${h.vessel_id}</strong></td>
                            <td>${h.last_seen || '--:--'}</td>
                            <td style="color:var(--text-muted); font-size:10px;">${h.last_destination || 'Porto'}</td>
                        `;
                        hTable.appendChild(row);
                    });
                }
            } catch (e) {
                // Ignore silent network jitter
            }
        }

        loadModelsCatalog();
        setInterval(fetchTelemetry, 1500);
    </script>
</body>
</html>"""
