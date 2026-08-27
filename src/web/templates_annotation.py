# -*- coding: utf-8 -*-
"""Template HTML/CSS/JS do Estúdio de Anotação no Padrão CVAT com suporte a BBox, Segmentação Poligonal, Presets de Classes e Importação de Datasets."""

ANNOTATION_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CVAT Naval Studio — Anotação &amp; Segmentação de Datasets</title>
    <style>
        :root {
            --cvat-bg-main: #141414;
            --cvat-bg-panel: #1f1f1f;
            --cvat-bg-surface: #2a2a2a;
            --cvat-bg-hover: #333333;
            --cvat-border: #383838;
            --cvat-text-primary: #e6e6e6;
            --cvat-text-secondary: #999999;
            --cvat-text-disabled: #555555;
            --cvat-accent: #1890ff;
            --cvat-accent-hover: #40a9ff;
            --cvat-danger: #ff4d4f;
            --cvat-success: #52c41a;
            --cvat-warning: #faad14;
            --cvat-cyan: #13c2c2;
            --font-main: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            --font-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background-color: var(--cvat-bg-main);
            color: var(--cvat-text-primary);
            font-family: var(--font-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            user-select: none;
        }

        /* ===== TOP HEADER (CLEAN MINIMALIST CVAT) ===== */
        .cvat-header {
            height: 44px;
            background: #181818;
            border-bottom: 1px solid #282828;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 14px;
            z-index: 100;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .cvat-logo {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 700;
            font-size: 13px;
            color: #fff;
            text-decoration: none;
        }
        .cvat-logo-badge {
            background: var(--cvat-accent);
            color: #fff;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.5px;
        }
        .task-file-badge {
            font-size: 11px;
            color: var(--cvat-text-secondary);
            background: #222;
            border: 1px solid #2e2e2e;
            padding: 3px 8px;
            border-radius: 4px;
            max-width: 220px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Compact Segmented Mode Switcher */
        .source-mode-toggle {
            display: flex;
            background: #111;
            border: 1px solid #2a2a2a;
            border-radius: 4px;
            padding: 2px;
            gap: 2px;
        }
        .mode-btn {
            background: transparent;
            border: none;
            color: var(--cvat-text-secondary);
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
            font-family: inherit;
            border-radius: 3px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: all 0.12s ease;
        }
        .mode-btn:hover { color: #fff; background: #262626; }
        .mode-btn.active {
            background: var(--cvat-accent);
            color: #fff;
        }
        .mode-btn.live-active {
            background: #cf1322;
            color: #fff;
        }

        .header-center {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .frame-nav {
            display: flex;
            align-items: center;
            background: #222;
            border: 1px solid #2e2e2e;
            border-radius: 4px;
            padding: 2px;
            gap: 1px;
        }
        .nav-icon-btn {
            background: transparent;
            border: none;
            color: var(--cvat-text-primary);
            width: 24px;
            height: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
            transition: background 0.1s;
        }
        .nav-icon-btn:hover { background: #333; color: #fff; }
        .nav-icon-btn:disabled { color: var(--cvat-text-disabled); cursor: not-allowed; }
        .frame-counter {
            font-family: var(--font-mono);
            font-size: 11px;
            padding: 0 6px;
            color: var(--cvat-text-primary);
            min-width: 75px;
            text-align: center;
        }
        .zoom-indicator {
            font-family: var(--font-mono);
            font-size: 10.5px;
            padding: 0 5px;
            color: var(--cvat-text-secondary);
            min-width: 40px;
            text-align: center;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .cvat-btn {
            background: #242424;
            border: 1px solid #333;
            color: var(--cvat-text-primary);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: all 0.12s ease;
            text-decoration: none;
        }
        .cvat-btn:hover { background: #2f2f2f; border-color: #444; color: #fff; }
        .cvat-btn.primary { background: #1677ff; border-color: #1677ff; color: #fff; }
        .cvat-btn.primary:hover { background: #4096ff; }
        .cvat-btn.success { background: #237804; border-color: #389e0d; color: #fff; font-weight: 700; }
        .cvat-btn.success:hover { background: #389e0d; }
        .cvat-btn.ai { background: #531dab; border-color: #722ed1; color: #fff; }
        .cvat-btn.ai:hover { background: #722ed1; }
        .cvat-btn.danger { background: #a8071a; border-color: #cf1322; color: #fff; font-weight: 700; }
        .cvat-btn.danger:hover { background: #cf1322; border-color: #f5222d; }
        .cvat-btn.icon-only { padding: 4px 7px; }

        .model-selector-group {
            display: flex;
            align-items: center;
            gap: 5px;
            background: #191424;
            border: 1px solid #531dab;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .ai-active-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            font-weight: 700;
            color: #d3adf7;
        }

        /* ===== MAIN WORKSPACE BODY ===== */
        .cvat-body {
            flex: 1;
            display: flex;
            overflow: hidden;
            position: relative;
        }

        /* ===== LEFT TOOLS STRIP (CVAT) ===== */
        .cvat-left-toolbar {
            width: 44px;
            background: var(--cvat-bg-panel);
            border-right: 1px solid var(--cvat-border);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px 0;
            gap: 6px;
            z-index: 50;
        }
        .tool-icon {
            width: 34px; height: 34px; border-radius: 4px; display: flex; align-items: center; justify-content: center;
            background: transparent; border: 1px solid transparent; color: var(--cvat-text-secondary);
            cursor: pointer; transition: all 0.12s; position: relative;
        }
        .tool-icon:hover { background: var(--cvat-bg-surface); color: #fff; }
        .tool-icon.active { background: rgba(24, 144, 255, 0.2); border-color: var(--cvat-accent); color: var(--cvat-accent); }
        .tool-divider { width: 28px; height: 1px; background: var(--cvat-border); margin: 4px 0; }

        /* ===== CENTER CANVAS WORKSPACE ===== */
        .cvat-canvas-container {
            flex: 1;
            position: relative;
            background: #080808;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: default;
        }
        .cvat-canvas-container.tool-rect { cursor: crosshair; }
        .cvat-canvas-container.tool-polygon { cursor: crosshair; }
        .cvat-canvas-container.tool-hand { cursor: grab; }
        .cvat-canvas-container.tool-hand:active { cursor: grabbing; }

        #stage-wrapper {
            position: absolute;
            transform-origin: 0 0;
            box-shadow: 0 0 20px rgba(0,0,0,0.8);
        }
        #video-element {
            display: block;
            pointer-events: none;
        }
        #live-image-element {
            display: none;
            pointer-events: none;
            width: 1280px;
            height: 720px;
            object-fit: contain;
            background: #000;
        }
        #cvat-canvas {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: all;
        }

        /* Canvas HUD Badges */
        .canvas-coords-badge {
            position: absolute; bottom: 12px; left: 12px;
            background: rgba(20,20,20,0.85); border: 1px solid var(--cvat-border);
            padding: 3px 8px; border-radius: 3px; font-family: var(--font-mono);
            font-size: 10.5px; color: var(--cvat-text-secondary); pointer-events: none; z-index: 40;
        }
        .canvas-tools-floating {
            position: absolute; top: 12px; left: 12px;
            background: rgba(26,26,26,0.9); border: 1px solid var(--cvat-border);
            border-radius: 4px; padding: 4px 8px; display: flex; align-items: center; gap: 8px;
            z-index: 40; font-size: 11px;
        }
        .live-pulse-badge {
            position: absolute; top: 12px; right: 12px;
            background: rgba(168, 7, 26, 0.85); border: 1px solid #ff4d4f;
            border-radius: 4px; padding: 4px 10px; display: none; align-items: center; gap: 6px;
            z-index: 40; font-size: 11px; font-weight: 700; color: #fff;
        }
        .live-dot {
            width: 8px; height: 8px; background: #fff; border-radius: 50%;
            animation: pulse-live 1.2s infinite ease-in-out;
        }
        @keyframes pulse-live {
            0% { transform: scale(0.9); opacity: 0.7; }
            50% { transform: scale(1.3); opacity: 1.0; }
            100% { transform: scale(0.9); opacity: 0.7; }
        }

        /* ===== RIGHT SIDEBAR ===== */
        .cvat-right-sidebar {
            width: 340px;
            background: var(--cvat-bg-panel);
            border-left: 1px solid var(--cvat-border);
            display: flex;
            flex-direction: column;
            z-index: 50;
        }
        .sidebar-tabs {
            display: flex;
            background: var(--cvat-bg-surface);
            border-bottom: 1px solid var(--cvat-border);
        }
        .sidebar-tab {
            flex: 1; padding: 8px 6px; text-align: center; font-size: 11px; font-weight: 600;
            color: var(--cvat-text-secondary); cursor: pointer; border-bottom: 2px solid transparent;
            transition: all 0.15s;
        }
        .sidebar-tab:hover { color: #fff; }
        .sidebar-tab.active { color: var(--cvat-accent); border-bottom-color: var(--cvat-accent); background: var(--cvat-bg-panel); }

        .sidebar-content {
            flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px;
        }
        .tab-pane { display: none; }
        .tab-pane.active { display: block; }

        /* Object Layer Item */
        .object-item {
            background: var(--cvat-bg-surface);
            border: 1px solid var(--cvat-border);
            border-radius: 4px;
            padding: 6px 8px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: all 0.12s;
        }
        .object-item:hover { background: var(--cvat-bg-hover); }
        .object-item.selected { border-color: var(--cvat-accent); background: rgba(24, 144, 255, 0.12); }
        .obj-left { display: flex; align-items: center; gap: 8px; }
        .obj-color-dot { width: 10px; height: 10px; border-radius: 2px; }
        .obj-title { font-size: 11.5px; font-weight: 600; }
        .obj-type-badge { font-size: 9.5px; padding: 1px 4px; border-radius: 2px; background: rgba(255,255,255,0.1); color: var(--cvat-text-secondary); }
        .obj-coords { font-size: 10px; color: var(--cvat-text-secondary); font-family: var(--font-mono); }
        .obj-actions { display: flex; align-items: center; gap: 4px; }
        .obj-btn {
            background: transparent; border: none; color: var(--cvat-text-secondary);
            cursor: pointer; padding: 2px 4px; border-radius: 3px; font-size: 11px;
        }
        .obj-btn:hover { color: #fff; background: rgba(255,255,255,0.1); }
        .obj-btn.del:hover { color: var(--cvat-danger); }

        /* Class Selector Chips */
        .class-chip {
            display: flex; align-items: center; justify-content: space-between;
            padding: 6px 10px; border-radius: 4px; background: var(--cvat-bg-surface);
            border: 1px solid var(--cvat-border); cursor: pointer; margin-bottom: 5px;
            font-size: 11.5px; font-weight: 500; transition: all 0.12s;
        }
        .class-chip:hover { background: var(--cvat-bg-hover); }
        .class-chip.active { border-color: var(--cvat-accent); background: rgba(24,144,255,0.15); font-weight: 700; }
        .class-color-badge { width: 12px; height: 12px; border-radius: 2px; margin-right: 8px; }
        .class-hotkey { font-family: var(--font-mono); font-size: 10px; color: var(--cvat-text-secondary); }

        /* Form Controls */
        .cvat-select, .cvat-input {
            width: 100%; background: var(--cvat-bg-surface); border: 1px solid var(--cvat-border);
            color: var(--cvat-text-primary); padding: 6px 8px; border-radius: 3px; font-size: 11.5px;
            font-family: inherit; outline: none; margin-bottom: 6px;
        }
        .cvat-select:focus, .cvat-input:focus { border-color: var(--cvat-accent); }
        .setting-row { display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; color: var(--cvat-text-secondary); margin-bottom: 6px; }

        /* ===== BOTTOM FILMSTRIP (HORIZONTAL GALLERY) ===== */
        .cvat-bottom-filmstrip {
            height: 72px;
            background: #141414;
            border-top: 1px solid #282828;
            display: flex;
            align-items: center;
            padding: 0 12px;
            gap: 10px;
            z-index: 90;
            overflow-x: auto;
            white-space: nowrap;
        }
        .filmstrip-label {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--cvat-text-secondary);
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 75px;
            border-right: 1px solid #282828;
            padding-right: 8px;
        }
        .filmstrip-label strong { color: var(--cvat-accent); font-size: 12px; font-family: var(--font-mono); }
        .filmstrip-list {
            display: flex;
            align-items: center;
            gap: 8px;
            overflow-x: auto;
            flex: 1;
            padding: 4px 0;
        }
        .filmstrip-item {
            position: relative;
            width: 86px;
            height: 52px;
            border-radius: 4px;
            overflow: hidden;
            background: #1f1f1f;
            border: 1px solid #333;
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.15s ease;
        }
        .filmstrip-item:hover {
            border-color: var(--cvat-accent);
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }
        .filmstrip-item.active {
            border-color: var(--cvat-success);
            box-shadow: 0 0 8px rgba(82,196,26,0.5);
        }
        .filmstrip-thumb {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        .filmstrip-badge {
            position: absolute;
            bottom: 2px;
            right: 2px;
            background: rgba(0,0,0,0.75);
            color: #fff;
            font-size: 9px;
            font-weight: 700;
            padding: 1px 4px;
            border-radius: 2px;
            font-family: var(--font-mono);
        }
        .filmstrip-item:hover .filmstrip-del {
            display: flex;
        }
        .filmstrip-del {
            position: absolute;
            top: 2px;
            right: 2px;
            width: 16px;
            height: 16px;
            background: rgba(255,77,79,0.85);
            color: #fff;
            border: none;
            border-radius: 50%;
            font-size: 10px;
            display: none;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }
        .filmstrip-del:hover { background: #ff4d4f; }

        /* ===== BOTTOM PLAYER BAR (CVAT) ===== */
        .cvat-player-bar {
            height: 44px;
            background: var(--cvat-bg-panel);
            border-top: 1px solid var(--cvat-border);
            display: flex;
            align-items: center;
            padding: 0 16px;
            gap: 12px;
            z-index: 100;
        }
        .player-controls { display: flex; align-items: center; gap: 4px; }
        .play-btn {
            background: var(--cvat-accent); border: none; color: #fff; width: 32px; height: 28px;
            border-radius: 3px; cursor: pointer; display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: bold;
        }
        .play-btn:hover { background: var(--cvat-accent-hover); }

        .timeline-slider-wrap { flex: 1; display: flex; align-items: center; position: relative; }
        .cvat-timeline {
            width: 100%; -webkit-appearance: none; height: 6px; background: var(--cvat-bg-surface);
            border-radius: 3px; outline: none; cursor: pointer;
        }
        .cvat-timeline::-webkit-slider-thumb {
            -webkit-appearance: none; width: 12px; height: 12px; border-radius: 2px;
            background: var(--cvat-accent); border: 1px solid #fff; cursor: pointer;
        }
        .timecode-label { font-family: var(--font-mono); font-size: 11px; color: var(--cvat-text-secondary); min-width: 125px; text-align: right; }

        /* Live Control Bar Overlay */
        .live-player-bar {
            display: none;
            align-items: center;
            gap: 12px;
            width: 100%;
        }

        /* Toast */
        #cvat-toast {
            position: fixed; bottom: 50px; right: 20px;
            background: #262626; border: 1px solid var(--cvat-success);
            color: #fff; padding: 8px 14px; border-radius: 4px; font-size: 11.5px;
            font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.5); opacity: 0;
            transform: translateY(10px); transition: all 0.2s ease; z-index: 9999; pointer-events: none;
        }
        #cvat-toast.show { opacity: 1; transform: translateY(0); }

        /* Modals */
        .modal-backdrop {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7); z-index: 2000; display: none;
            align-items: center; justify-content: center;
        }
        .modal-box {
            background: var(--cvat-bg-panel); border: 1px solid var(--cvat-border);
            border-radius: 6px; width: 440px; padding: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.6);
        }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--cvat-border); font-weight: 700; font-size: 13px; }
        .shortcut-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; }
        .sc-key { background: var(--cvat-bg-surface); border: 1px solid var(--cvat-border); padding: 1px 5px; border-radius: 3px; font-family: var(--font-mono); color: var(--cvat-accent); }
    </style>
</head>
<body>

    <!-- 1. TOP HEADER (CLEAN MINIMALIST CVAT COM MODELO ATRELADO) -->
    <div class="cvat-header">
        <div class="header-left">
            <div class="cvat-logo">
                <span class="cvat-logo-badge">CVAT</span>
                <span id="header-domain-badge">Naval</span>
            </div>

            <!-- SELETOR DE MODO COMPACTO -->
            <div class="source-mode-toggle">
                <button class="mode-btn active" id="mode-btn-video" title="Vídeo Gravado (.mp4)">📁 Gravado</button>
                <button class="mode-btn" id="mode-btn-live" title="Transmissão ao Vivo">🔴 Ao Vivo</button>
            </div>

            <span class="task-file-badge" id="current-video-title" title="Fonte Ativa">teste_santos_3minutos_completo.mp4</span>

            <!-- SELETOR DE MODELO DE IA ATRELADO NO HEADER -->
            <div class="model-selector-group" title="Modelo de IA Atrelado para Percepção e Auto-Rotulagem">
                <span class="ai-active-indicator">🤖 Modelo:</span>
                <select class="cvat-select" id="select-ai-model-header" style="width:auto; margin:0; padding:2px 6px; font-size:11px; font-weight:600; background:#221b33; border:1px solid #722ed1; color:#fff; border-radius:3px;">
                    <option value="domain_default">Modelo Especialista</option>
                </select>
                <button class="mode-btn active" id="btn-toggle-auto-ai" style="padding:2px 6px; font-size:10px; border-radius:3px;" title="Executar Detecção Automaticamente ao Pausar ou Mudar de Frame">⚡ Auto-IA: ON</button>
            </div>
        </div>

        <div class="header-center">
            <!-- NAVEGADOR DE FRAMES COMPACTO -->
            <div class="frame-nav" id="header-frame-nav">
                <button class="nav-icon-btn" id="btn-first" title="Primeiro frame (Home)">|◀</button>
                <button class="nav-icon-btn" id="btn-prev" title="Frame anterior (D / [)">◀</button>
                <span class="frame-counter" id="header-frame-counter">0 / 0</span>
                <button class="nav-icon-btn" id="btn-next" title="Próximo frame (F / ])">▶</button>
                <button class="nav-icon-btn" id="btn-last" title="Último frame (End)">▶|</button>
            </div>

            <!-- ZOOM & FIT COMPACTO -->
            <div class="frame-nav">
                <button class="nav-icon-btn" id="btn-zoom-out" title="Zoom -">-</button>
                <span class="zoom-indicator" id="zoom-level">100%</span>
                <button class="nav-icon-btn" id="btn-zoom-in" title="Zoom +">+</button>
                <button class="nav-icon-btn" id="btn-fit-screen" title="Ajustar à Tela (Ctrl+0)">⛶</button>
            </div>
        </div>

        <div class="header-right">
            <button class="cvat-btn ai" id="btn-ai-auto" title="Executar Inferência do Modelo de IA no Frame Atual (A)">
                🤖 Auto-IA
            </button>
            <button class="cvat-btn danger" id="btn-delete-all-boxes" title="Deletar TODAS as anotações deste frame para refazer do zero (Alt+C)">
                🗑️ Deletar Tudo
            </button>
            <button class="cvat-btn success" id="btn-save-yolo" title="Salvar Anotações Corrigidas no Dataset YOLO (Ctrl+S)">
                💾 Salvar
            </button>
            <a href="/api/annotation/export_zip" class="cvat-btn" id="btn-export-zip" title="Exportar Dataset YOLO (.ZIP)">
                📦 Exportar
            </a>
            <button class="cvat-btn icon-only" id="btn-open-shortcuts" title="Atalhos de Teclado">
                ⌨
            </button>
            <a href="/" class="cvat-btn primary" title="Painel Principal">
                ⚓ Painel
            </a>
        </div>
    </div>

    <!-- 2. MAIN WORKSPACE -->
    <div class="cvat-body">
        <!-- LEFT TOOLS STRIP -->
        <div class="cvat-left-toolbar">
            <button class="tool-icon active" id="tool-cursor" title="Selecionar / Mover Objeto (S / Esc)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3l7 18 3-7 7-3L3 3z"/></svg>
            </button>
            <button class="tool-icon" id="tool-rectangle" title="Desenhar Bounding Box Retangular (N / R)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>
            </button>
            <button class="tool-icon" id="tool-polygon" title="Desenhar Polígono / Segmentação (P)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l8 6-3 12H7L4 8z"/></svg>
            </button>
            <button class="tool-icon" id="tool-hand" title="Mover Canvas / Pan (H / Barra de Espaço + Arrastar)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v6M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8M6 14v-2a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v6a7 7 0 0 0 7 7h3a7 7 0 0 0 7-7v-6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/></svg>
            </button>
            <div class="tool-divider"></div>
            <button class="tool-icon" id="tool-run-ai-left" title="Executar Modelo de IA no Frame (A)">
                <span style="font-size:14px;">🤖</span>
            </button>
            <button class="tool-icon" id="tool-del-box" title="Excluir Objeto Selecionado (Del / Backspace)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
            <button class="tool-icon" id="tool-clear-all" title="Limpar TODAS as anotações deste frame (Alt+C)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            </button>
        </div>

        <!-- CANVAS STAGE -->
        <div class="cvat-canvas-container tool-rect" id="canvas-container">
            <div class="canvas-tools-floating">
                <span>Classe Ativa:</span>
                <strong id="active-class-indicator" style="color:var(--cvat-cyan);">embarcacao (1)</strong>
                <span style="color:var(--cvat-text-disabled);">|</span>
                <span id="canvas-active-tool-badge" style="color:var(--cvat-accent);">Retângulo (N)</span>
                <span style="color:var(--cvat-text-disabled);">|</span>
                <span id="canvas-ai-badge" style="color:#b37feb; font-weight:700; cursor:pointer;" title="Clique para rodar inferência da IA">🤖 IA: YOLO11n (0.20)</span>
                <button class="cvat-btn ai" id="btn-hud-run-ai" style="padding:2px 7px; font-size:10px;" title="Executar Modelo no Frame (A)">🤖 Rodar IA</button>
                <button class="cvat-btn danger" id="btn-hud-clear-all" style="padding:2px 7px; font-size:10px;" title="Limpar Todas as Anotações (Alt+C)">🗑️ Limpar Tudo</button>
            </div>

            <!-- LIVE BADGE -->
            <div class="live-pulse-badge" id="live-indicator-badge">
                <span class="live-dot"></span>
                <span>AO VIVO — PORTO DE SANTOS</span>
            </div>

            <div id="stage-wrapper">
                <!-- 1. VÍDEO GRAVADO -->
                <video id="video-element" playsinline crossorigin="anonymous" style="display:block;">
                    <source src="/media/video/teste_santos_3minutos_completo.mp4" type="video/mp4">
                </video>

                <!-- 2. STREAM AO VIVO -->
                <img id="live-image-element" crossorigin="anonymous" src="/video_feed_raw" alt="Transmissão ao vivo">

                <!-- 3. CANVAS DE ANOTAÇÃO -->
                <canvas id="cvat-canvas"></canvas>
            </div>

            <div class="canvas-coords-badge" id="cursor-coords">X: 0 | Y: 0</div>
        </div>

        <!-- RIGHT SIDEBAR (CVAT OBJECTS, LABELS, IA & DATASET) -->
        <div class="cvat-right-sidebar">
            <div class="sidebar-tabs">
                <div class="sidebar-tab active" data-tab="objects">Objetos (<span id="count-objects">0</span>)</div>
                <div class="sidebar-tab" data-tab="labels">Classes</div>
                <div class="sidebar-tab" data-tab="ai">🤖 IA &amp; Correção</div>
                <div class="sidebar-tab" data-tab="dataset">Dataset</div>
            </div>

            <div class="sidebar-content">
                <!-- TAB 1: OBJETOS NO FRAME (LAYERS) -->
                <div class="tab-pane active" id="pane-objects">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="color:var(--cvat-text-secondary); font-size:10.5px; text-transform:uppercase;">Camadas do Frame</span>
                        <span style="font-size:10.5px; color:var(--cvat-accent);" id="active-tool-name">Ferramenta: Retângulo</span>
                    </div>

                    <div id="objects-list-wrap" style="display:flex; flex-direction:column; gap:6px; max-height:calc(100vh - 280px); overflow-y:auto;">
                        <div style="color:var(--cvat-text-disabled); font-size:11px; text-align:center; padding:20px 0;">
                            Nenhum objeto neste frame.<br>Pressione <strong>N</strong> (Retângulo), <strong>P</strong> (Polígono) ou <strong>A</strong> (Auto-IA).
                        </div>
                    </div>

                    <!-- AJUSTES DE VISUALIZAÇÃO CVAT -->
                    <div style="margin-top:auto; padding-top:10px; border-top:1px solid var(--cvat-border); display:flex; flex-direction:column; gap:8px;">
                        <div class="setting-row">
                            <span>Opacidade do Fill:</span>
                            <input type="range" id="slider-opacity" min="0" max="0.6" step="0.05" value="0.18" style="width:100px;">
                        </div>
                        <div class="setting-row">
                            <span>Espessura da Borda:</span>
                            <input type="range" id="slider-thickness" min="1" max="4" step="1" value="2" style="width:100px;">
                        </div>
                    </div>
                </div>

                <!-- TAB 2: CLASSES & CONJUNTOS PRESETS -->
                <div class="tab-pane" id="pane-labels">
                    <!-- SELETOR DE CONJUNTOS DE CLASSES -->
                    <div style="background:rgba(24,144,255,0.08); padding:8px; border-radius:4px; border:1px solid rgba(24,144,255,0.25); margin-bottom:10px;">
                        <span style="color:var(--cvat-accent); font-size:10.5px; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">
                            Conjunto de Classes Ativo
                        </span>
                        <select class="cvat-select" id="select-class-set">
                            <option value="nautical_default">Classes Náuticas (Padrão)</option>
                            <option value="environment_segmentation">Segmentação de Ambiente &amp; Cenário (Água, Porto, Floresta)</option>
                            <option value="port_security_people">Segurança Portuária &amp; Pessoas (EPI)</option>
                            <option value="port_infrastructure">Infraestrutura &amp; Cais Portuário</option>
                        </select>
                        <button class="cvat-btn" id="btn-create-class-set" style="width:100%; justify-content:center; margin-top:2px;">
                            + Criar Novo Conjunto de Classes
                        </button>
                    </div>

                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="color:var(--cvat-text-secondary); font-size:10.5px; text-transform:uppercase;">
                            Classes Disponíveis (1 a 9)
                        </span>
                        <button class="obj-btn" id="btn-add-single-class" style="color:var(--cvat-accent); font-weight:600;">+ Adicionar</button>
                    </div>
                    <div id="classes-list-wrap" style="display:flex; flex-direction:column; gap:6px; max-height:calc(100vh - 340px); overflow-y:auto;">
                        <!-- Classes geradas via JS -->
                    </div>
                </div>

                <!-- TAB 3: MODELO DE IA & ACTIVE LEARNING / CORREÇÃO -->
                <div class="tab-pane" id="pane-ai">
                    <!-- MODELO ATRELADO -->
                    <div style="background:#1b1528; border:1px solid #722ed1; border-radius:4px; padding:10px; margin-bottom:10px;">
                        <span style="color:#d3adf7; font-size:11px; font-weight:700; text-transform:uppercase; display:flex; align-items:center; gap:6px;">
                            🤖 Modelo de IA Atrelado
                        </span>
                        <select class="cvat-select" id="select-ai-model-sidebar" style="border-color:#722ed1; margin-top:6px;">
                            <option value="domain_default">Modelo Especialista do Domínio</option>
                            <option value="yolo11n">YOLO11n Baseline Edge</option>
                            <option value="mayrajeo_marine">Mayrajeo YOLOv8 Marine Vessel</option>
                            <option value="mewan2808_sar">MeWan2808 YOLOv8 SAR Radar</option>
                            <option value="sixopen_y8naval">SixOpen Y8Naval (Aéreo/Satélite)</option>
                            <option value="ensemble_full">Ensemble Multi-Domínio Completo</option>
                        </select>
                        <span id="ai-model-description" style="font-size:10px; color:#b37feb; display:block; margin-top:4px;">
                            Detector acoplado para auto-rotular alvos no frame.
                        </span>
                    </div>

                    <!-- PARÂMETROS DE DETECÇÃO -->
                    <div style="background:var(--cvat-bg-surface); padding:10px; border-radius:4px; border:1px solid var(--cvat-border); margin-bottom:10px; display:flex; flex-direction:column; gap:8px;">
                        <span style="color:var(--cvat-text-primary); font-size:11px; font-weight:700; text-transform:uppercase;">
                            ⚙️ Parâmetros de Inferência
                        </span>
                        <div class="setting-row">
                            <span>Limiar de Confiança:</span>
                            <span id="display-ai-conf" style="font-family:var(--font-mono); color:var(--cvat-accent); font-weight:700;">20%</span>
                        </div>
                        <input type="range" id="slider-ai-conf" min="0.05" max="0.90" step="0.05" value="0.20" style="width:100%;">

                        <div style="display:flex; align-items:center; justify-content:space-between; margin-top:4px;">
                            <span style="font-size:11px; color:var(--cvat-text-secondary);">Auto-IA ao pausar frame:</span>
                            <input type="checkbox" id="check-auto-ai-pause" checked style="cursor:pointer; transform:scale(1.15);">
                        </div>
                    </div>

                    <!-- AÇÕES HUMAN-IN-THE-LOOP & CORREÇÃO -->
                    <div style="display:flex; flex-direction:column; gap:6px;">
                        <button class="cvat-btn ai" id="btn-run-ai-sidebar" style="width:100%; justify-content:center; padding:8px 0; font-size:11.5px;">
                            🤖 Executar Inferência da IA no Frame (A)
                        </button>
                        <button class="cvat-btn danger" id="btn-clear-all-ai" style="width:100%; justify-content:center; padding:8px 0; font-size:11.5px;">
                            🗑️ Deletar Todas as Anotações (Limpar Frame)
                        </button>
                        <button class="cvat-btn success" id="btn-save-corrected-sidebar" style="width:100%; justify-content:center; padding:8px 0; font-size:11.5px;">
                            💾 Salvar Frame Corrigido no Dataset (Ctrl+S)
                        </button>
                    </div>

                    <!-- DICA DE ACTIVE LEARNING -->
                    <div style="background:rgba(250,173,20,0.08); border:1px solid rgba(250,173,20,0.3); border-radius:4px; padding:8px; margin-top:10px; font-size:10px; color:#d48806; line-height:1.4;">
                        💡 <strong>Fluxo Human-in-the-Loop</strong>:<br>
                        1. Pause o vídeo no frame com erros da IA.<br>
                        2. A IA gera as caixas previstas.<br>
                        3. Edite as caixas erradas ou clique em <em>Deletar Todas</em> para refazer do zero.<br>
                        4. Pressione <em>Salvar (Ctrl+S)</em> para gravar o Ground Truth e re-treinar a IA.
                    </div>
                </div>

                <!-- TAB 4: DATASET & FONTES (VÍDEO GRAVADO vs AO VIVO vs IMPORTAÇÃO) -->
                <div class="tab-pane" id="pane-dataset">
                    <!-- IMPORTAR DATASET EXISTENTE -->
                    <div style="background:rgba(82,196,26,0.08); padding:10px; border-radius:4px; border:1px solid rgba(82,196,26,0.3); margin-bottom:8px;">
                        <span style="color:var(--cvat-success); font-size:11px; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">
                            📥 Continuar Dataset Existente
                        </span>
                        <input type="file" id="input-import-dataset-zip" accept=".zip" style="display:none;">
                        <button class="cvat-btn success" style="width:100%; justify-content:center;" onclick="document.getElementById('input-import-dataset-zip').click()">
                            📦 Puxar Dataset (.ZIP)
                        </button>
                        <span style="font-size:9.5px; color:var(--cvat-text-secondary); display:block; margin-top:4px;">
                            Carrega imagens, anotações de BBox e polígonos para continuar rotulando.
                        </span>
                    </div>

                    <!-- SEÇÃO: MODO VÍDEO GRAVADO -->
                    <div id="section-recorded-video" style="display:flex; flex-direction:column; gap:6px; background:var(--cvat-bg-surface); padding:10px; border-radius:4px; border:1px solid var(--cvat-border);">
                        <span style="color:var(--cvat-accent); font-size:11px; font-weight:700; text-transform:uppercase;">📁 Arquivo de Vídeo Gravado</span>
                        <select class="cvat-select" id="select-video-source">
                            <option value="teste_santos_3minutos_completo.mp4">Porto de Santos - 3 Minutos Completo (MP4)</option>
                            <option value="teste_porto_santos_1min.mp4">Porto de Santos - 1 Minuto (MP4)</option>
                        </select>
                        <input type="file" id="input-upload-video" accept="video/mp4,video/webm" style="display:none;">
                        <button class="cvat-btn" style="width:100%; justify-content:center; margin-top:2px;" onclick="document.getElementById('input-upload-video').click()">
                            📁 Carregar Outro Vídeo (.mp4)
                        </button>
                    </div>

                    <!-- SEÇÃO: MODO AO VIVO (YOUTUBE / RTSP) -->
                    <div id="section-live-video" style="display:none; flex-direction:column; gap:6px; background:rgba(211,32,41,0.08); padding:10px; border-radius:4px; border:1px solid rgba(211,32,41,0.35);">
                        <span style="color:#ff4d4f; font-size:11px; font-weight:700; text-transform:uppercase;">🔴 Transmissão ao Vivo (YouTube / RTSP)</span>
                        <input type="text" class="cvat-input" id="input-youtube-live-url" value="https://www.youtube.com/watch?v=5BxqzvR6TgM" placeholder="URL da Live do YouTube">
                        <div style="display:flex; gap:6px;">
                            <button class="cvat-btn primary" id="btn-update-live-url" style="flex:1; justify-content:center;">
                                📡 Atualizar Live
                            </button>
                            <button class="cvat-btn live-freeze" id="btn-live-freeze-sidebar" style="flex:1; justify-content:center;">
                                📸 Congelar
                            </button>
                        </div>
                    </div>

                    <!-- ESTATÍSTICAS DO DATASET -->
                    <div style="margin-top:10px; padding-top:10px; border-top:1px solid var(--cvat-border);">
                        <span style="color:var(--cvat-text-secondary); font-size:10.5px; text-transform:uppercase; display:block; margin-bottom:6px;">Estatísticas do Dataset</span>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; text-align:center;">
                            <div style="background:var(--cvat-bg-surface); padding:8px; border-radius:3px; border:1px solid var(--cvat-border);">
                                <div style="font-size:16px; font-weight:700; color:var(--cvat-success);" id="ds-images-count">0</div>
                                <div style="font-size:9.5px; color:var(--cvat-text-secondary);">Frames Salvos</div>
                            </div>
                            <div style="background:var(--cvat-bg-surface); padding:8px; border-radius:3px; border:1px solid var(--cvat-border);">
                                <div style="font-size:16px; font-weight:700; color:var(--cvat-accent);" id="ds-boxes-count">0</div>
                                <div style="font-size:9.5px; color:var(--cvat-text-secondary);">Objetos (BBox/Seg)</div>
                            </div>
                        </div>
                    </div>

                    <!-- MINIATURAS DO DATASET -->
                    <div style="margin-top:10px;">
                        <span style="color:var(--cvat-text-secondary); font-size:10.5px; text-transform:uppercase; display:block; margin-bottom:6px;">
                            Frames Salvos (Clique para editar/continuar)
                        </span>
                        <div id="dataset-gallery" style="display:grid; grid-template-columns:1fr 1fr; gap:6px; max-height:160px; overflow-y:auto;">
                            <!-- Miniaturas -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 2.5 BOTTOM FILMSTRIP (HORIZONTAL GALLERY OF SAVED ANNOTATIONS) -->
    <div class="cvat-bottom-filmstrip" id="bottom-filmstrip-wrap">
        <div class="filmstrip-label">
            <span>Anotados</span>
            <strong id="filmstrip-count">0 frames</strong>
        </div>
        <div class="filmstrip-list" id="bottom-filmstrip-list">
            <span style="font-size:11px; color:var(--cvat-text-disabled); padding-left:6px;">Nenhum frame salvo ainda. Pressione Salvar (Ctrl+S) após anotar.</span>
        </div>
    </div>

    <!-- 3. BOTTOM PLAYER & TIMELINE BAR -->
    <div class="cvat-player-bar">
        <!-- BARRA DO MODO VÍDEO GRAVADO -->
        <div id="player-bar-recorded" style="display:flex; align-items:center; width:100%; gap:12px;">
            <div class="player-controls">
                <button class="play-btn" id="btn-play-pause" title="Reproduzir / Pausar (Espaço)">▶</button>
                <button class="nav-icon-btn" id="btn-step-prev" title="Frame anterior (D / [)">⏮</button>
                <button class="nav-icon-btn" id="btn-step-next" title="Próximo frame (F / ])">⏭</button>
            </div>

            <div class="timeline-slider-wrap">
                <input type="range" class="cvat-timeline" id="cvat-timeline" min="0" max="100" value="0" step="0.05">
            </div>

            <div class="timecode-label" id="timecode-display">00:00.00 / 00:00.00</div>
        </div>

        <!-- BARRA DO MODO AO VIVO -->
        <div id="player-bar-live" class="live-player-bar">
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="live-dot" style="background:#ff4d4f;"></span>
                <span style="font-weight:700; font-size:11.5px; color:#ff4d4f;">TRANSMISSÃO AO VIVO</span>
            </div>

            <button class="cvat-btn live-freeze" id="btn-toggle-live-freeze">
                📸 Congelar Frame para Anotação (Espaço)
            </button>

            <span style="font-size:11px; color:var(--cvat-text-secondary); margin-left:auto;" id="live-stream-status-msg">
                Transmitindo em tempo real do Porto de Santos
            </span>
        </div>
    </div>

    <!-- TOAST NOTIFICATION -->
    <div id="cvat-toast">Notificação</div>

    <!-- MODAL: CRIAR CONJUNTO DE CLASSES -->
    <div class="modal-backdrop" id="modal-class-set">
        <div class="modal-box">
            <div class="modal-header">
                <span>Criar Novo Conjunto de Classes</span>
                <button class="obj-btn" onclick="document.getElementById('modal-class-set').style.display='none'">✕</button>
            </div>
            <div style="display:flex; flex-direction:column; gap:8px; font-size:11.5px;">
                <div>
                    <label style="color:var(--cvat-text-secondary); display:block; margin-bottom:3px;">Nome do Conjunto:</label>
                    <input type="text" class="cvat-input" id="input-new-set-name" placeholder="ex: Inspeção de Pessoas e Barcos">
                </div>
                <div>
                    <label style="color:var(--cvat-text-secondary); display:block; margin-bottom:3px;">Classes (separadas por vírgula):</label>
                    <textarea class="cvat-input" id="input-new-set-classes" rows="4" placeholder="pessoa, operador_porto, colete, capacete, barco_apoio"></textarea>
                </div>
                <div style="display:flex; gap:8px; justify-content:flex-end; margin-top:8px;">
                    <button class="cvat-btn" onclick="document.getElementById('modal-class-set').style.display='none'">Cancelar</button>
                    <button class="cvat-btn primary" id="btn-save-new-class-set">Salvar &amp; Ativar Conjunto</button>
                </div>
            </div>
        </div>
    </div>

    <!-- SHORTCUTS MODAL -->
    <div class="modal-backdrop" id="shortcuts-modal">
        <div class="modal-box">
            <div class="modal-header">
                <span>Atalhos de Teclado (CVAT Mode)</span>
                <button class="obj-btn" onclick="document.getElementById('shortcuts-modal').style.display='none'">✕</button>
            </div>
            <div class="shortcut-grid">
                <div><span class="sc-key">Espaço</span> Play/Pause (Vídeo) ou Congelar/Retomar (Ao Vivo)</div>
                <div><span class="sc-key">D / [</span> Frame Anterior (-1)</div>
                <div><span class="sc-key">F / ]</span> Próximo Frame (+1)</div>
                <div><span class="sc-key">N / R</span> Modo Retângulo (BBox)</div>
                <div><span class="sc-key">P</span> Modo Polígono (Segmentação)</div>
                <div><span class="sc-key">Enter</span> Fechar Polígono Atual</div>
                <div><span class="sc-key">S / Esc</span> Modo Seleção / Cursor</div>
                <div><span class="sc-key">H</span> Modo Mão (Pan)</div>
                <div><span class="sc-key">Delete</span> Excluir Objeto Selecionado</div>
                <div><span class="sc-key">Ctrl + S</span> Salvar no Dataset YOLO</div>
                <div><span class="sc-key">Ctrl + 0</span> Ajustar à Tela (Fit)</div>
                <div><span class="sc-key">1 a 9</span> Selecionar Classe</div>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT CVAT LOGIC -->
    <script>
        let CVAT_CLASSES = [
            { id: 0, name: "embarcacao", color: "#00f0ff" },
            { id: 1, name: "navio_cargueiro", color: "#1890ff" },
            { id: 2, name: "rebocador", color: "#fa8c16" },
            { id: 3, name: "balsa", color: "#52c41a" },
            { id: 4, name: "lancha", color: "#722ed1" },
            { id: 5, name: "veleiro", color: "#eb2f96" },
            { id: 6, name: "boia_sinalizacao", color: "#fadb14" },
            { id: 7, name: "outro", color: "#8c8c8c" }
        ];

        let sourceMode = 'video'; // 'video' ou 'live'
        let isLiveFrozen = false;
        let frozenLiveImage = null;

        let activeClassId = 0;
        let activeTool = 'rect'; // 'rect', 'polygon', 'cursor', 'hand'
        let boxes = []; // [{id, type: 'bbox', class_id, x1, y1, x2, y2, hidden}]
        let polygons = []; // [{id, type: 'polygon', class_id, points: [{x,y},...], hidden}]
        let selectedItem = null; // {type: 'bbox'|'polygon', index: int}
        let activeHandle = null; // 'nw', 'ne', 'se', 'sw', 'vertex_0', 'body', etc.
        let activeVertexIndex = -1;

        // Current Polygon in Creation
        let currentPolygonPoints = [];

        // Pan & Zoom Transform State
        let scale = 1.0;
        let panX = 0, panY = 0;
        let isPanning = false;
        let panStartX = 0, panStartY = 0;

        // Drawing State
        let isDrawingBox = false;
        let drawStartX = 0, drawStartY = 0;

        // Resizing / Dragging State
        let isTransforming = false;
        let transformStartX = 0, transformStartY = 0;
        let initialCoords = null;

        // DOM Elements
        const video = document.getElementById('video-element');
        const liveImg = document.getElementById('live-image-element');
        const canvas = document.getElementById('cvat-canvas');
        const ctx = canvas.getContext('2d');
        const stageWrapper = document.getElementById('stage-wrapper');
        const canvasContainer = document.getElementById('canvas-container');
        const timeline = document.getElementById('cvat-timeline');
        const timeDisplay = document.getElementById('timecode-display');
        const frameCounter = document.getElementById('header-frame-counter');
        const btnPlay = document.getElementById('btn-play-pause');

        function showToast(msg) {
            const t = document.getElementById('cvat-toast');
            t.innerText = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2500);
        }

        function formatTimecode(sec) {
            if (isNaN(sec)) return "00:00.00";
            const m = Math.floor(sec / 60);
            const s = (sec % 60).toFixed(2);
            return `${m.toString().padStart(2, '0')}:${s.padStart(5, '0')}`;
        }

        // Switch Mode: Video Gravado vs Ao Vivo
        function setSourceMode(mode) {
            sourceMode = mode;
            if (mode === 'live') {
                document.getElementById('mode-btn-video').classList.remove('active');
                document.getElementById('mode-btn-live').classList.add('active', 'live-active');
                
                video.style.display = 'none';
                liveImg.style.display = 'block';
                document.getElementById('live-indicator-badge').style.display = 'flex';
                document.getElementById('header-frame-nav').style.display = 'none';
                document.getElementById('player-bar-recorded').style.display = 'none';
                document.getElementById('player-bar-live').style.display = 'flex';
                document.getElementById('section-recorded-video').style.display = 'none';
                document.getElementById('section-live-video').style.display = 'flex';
                document.getElementById('breadcrumb-label').innerText = 'Transmissão:';
                document.getElementById('current-video-title').innerText = 'Câmera ao Vivo - Porto de Santos';

                resumeLiveStream();
            } else {
                document.getElementById('mode-btn-live').classList.remove('active', 'live-active');
                document.getElementById('mode-btn-video').classList.add('active');

                liveImg.style.display = 'none';
                video.style.display = 'block';
                document.getElementById('live-indicator-badge').style.display = 'none';
                document.getElementById('header-frame-nav').style.display = 'flex';
                document.getElementById('player-bar-recorded').style.display = 'flex';
                document.getElementById('player-bar-live').style.display = 'none';
                document.getElementById('section-recorded-video').style.display = 'flex';
                document.getElementById('section-live-video').style.display = 'none';
                document.getElementById('breadcrumb-label').innerText = 'Vídeo:';
                document.getElementById('current-video-title').innerText = document.getElementById('select-video-source').value;

                isLiveFrozen = false;
                fitToScreen();
            }
        }

        document.getElementById('mode-btn-video').onclick = () => setSourceMode('video');
        document.getElementById('mode-btn-live').onclick = () => setSourceMode('live');

        // Apply Transform (Zoom & Pan)
        function applyTransform() {
            stageWrapper.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
            document.getElementById('zoom-level').innerText = `${Math.round(scale * 100)}%`;
        }

        function fitToScreen() {
            const cw = canvasContainer.clientWidth - 40;
            const ch = canvasContainer.clientHeight - 40;
            let vw = 1280, vh = 720;

            if (sourceMode === 'video') {
                vw = video.videoWidth || 1280;
                vh = video.videoHeight || 720;
            } else {
                vw = liveImg.naturalWidth || 1280;
                vh = liveImg.naturalHeight || 720;
            }

            canvas.width = vw;
            canvas.height = vh;
            if (sourceMode === 'video') {
                video.width = vw; video.height = vh;
            } else {
                liveImg.width = vw; liveImg.height = vh;
            }

            const scaleX = cw / vw;
            const scaleY = ch / vh;
            scale = Math.min(scaleX, scaleY, 1.0);

            const scaledW = vw * scale;
            const scaledH = vh * scale;

            panX = (canvasContainer.clientWidth - scaledW) / 2;
            panY = (canvasContainer.clientHeight - scaledH) / 2;
            applyTransform();
        }

        video.addEventListener('loadedmetadata', () => {
            if (sourceMode === 'video') {
                fitToScreen();
                updateFrameStats();
            }
        });

        liveImg.addEventListener('load', () => {
            if (sourceMode === 'live' && canvas.width !== liveImg.naturalWidth && liveImg.naturalWidth > 0) {
                fitToScreen();
            }
        });

        // Set Active Tool
        function setTool(toolName) {
            // Se estava desenhando polígono e mudou de ferramenta, finaliza
            if (activeTool === 'polygon' && currentPolygonPoints.length >= 3) {
                finishCurrentPolygon();
            } else {
                currentPolygonPoints = [];
            }

            activeTool = toolName;
            ['tool-cursor', 'tool-rectangle', 'tool-polygon', 'tool-hand'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.remove('active');
            });
            canvasContainer.classList.remove('tool-rect', 'tool-polygon', 'tool-hand');

            if (toolName === 'rect') {
                document.getElementById('tool-rectangle').classList.add('active');
                canvasContainer.classList.add('tool-rect');
                document.getElementById('active-tool-name').innerText = 'Ferramenta: Retângulo (BBox)';
                document.getElementById('canvas-active-tool-badge').innerText = 'Retângulo (N)';
            } else if (toolName === 'polygon') {
                document.getElementById('tool-polygon').classList.add('active');
                canvasContainer.classList.add('tool-polygon');
                document.getElementById('active-tool-name').innerText = 'Ferramenta: Polígono / Segmentação';
                document.getElementById('canvas-active-tool-badge').innerText = 'Polígono (P)';
                showToast('⬟ Modo Polígono: Clique para adicionar vértices. Enter ou Duplo Clique para fechar.');
            } else if (toolName === 'hand') {
                document.getElementById('tool-hand').classList.add('active');
                canvasContainer.classList.add('tool-hand');
                document.getElementById('active-tool-name').innerText = 'Ferramenta: Mão / Pan';
                document.getElementById('canvas-active-tool-badge').innerText = 'Mão (H)';
            } else {
                document.getElementById('tool-cursor').classList.add('active');
                document.getElementById('active-tool-name').innerText = 'Ferramenta: Seleção';
                document.getElementById('canvas-active-tool-badge').innerText = 'Cursor (S)';
            }
            redrawCanvas();
        }

        document.getElementById('tool-rectangle').onclick = () => setTool('rect');
        document.getElementById('tool-polygon').onclick = () => setTool('polygon');
        document.getElementById('tool-cursor').onclick = () => setTool('cursor');
        document.getElementById('tool-hand').onclick = () => setTool('hand');

        // Video Frame Navigation (Modo Vídeo Gravado)
        function togglePlay() {
            if (sourceMode === 'live') {
                toggleLiveFreeze();
                return;
            }
            if (video.paused) {
                video.play();
                btnPlay.innerText = '⏸';
            } else {
                video.pause();
                btnPlay.innerText = '▶';
            }
        }
        btnPlay.onclick = togglePlay;

        function stepFrame(frames) {
            if (sourceMode === 'live') {
                showToast('Navegação de frames disponível no modo Vídeo Gravado');
                return;
            }
            video.pause();
            btnPlay.innerText = '▶';
            const fps = 30.0;
            video.currentTime = Math.max(0, Math.min(video.duration, video.currentTime + (frames / fps)));
        }

        const bindClick = (id, fn) => { const el = document.getElementById(id); if (el) el.onclick = fn; };
        bindClick('btn-prev', () => stepFrame(-1));
        bindClick('btn-next', () => stepFrame(1));
        bindClick('btn-step-prev', () => stepFrame(-1));
        bindClick('btn-step-next', () => stepFrame(1));
        bindClick('btn-step-back-10', () => stepFrame(-10));
        bindClick('btn-step-fwd-10', () => stepFrame(10));
        bindClick('btn-first', () => { video.currentTime = 0; });
        bindClick('btn-last', () => { video.currentTime = video.duration || 0; });

        video.addEventListener('timeupdate', () => {
            if (!video.duration || sourceMode !== 'video') return;
            timeline.value = (video.currentTime / video.duration) * 100;
            updateFrameStats();
        });

        timeline.addEventListener('input', () => {
            if (!video.duration || sourceMode !== 'video') return;
            video.currentTime = (timeline.value / 100) * video.duration;
            updateFrameStats();
        });

        function updateFrameStats() {
            const fps = 30.0;
            const currentF = Math.floor(video.currentTime * fps);
            const totalF = Math.floor((video.duration || 0) * fps);
            frameCounter.innerText = `${currentF} / ${totalF}`;
            timeDisplay.innerText = `${formatTimecode(video.currentTime)} / ${formatTimecode(video.duration)}`;
        }

        // CONTROLES DE TRANSMISSÃO AO VIVO
        async function freezeLiveFrame() {
            showToast('📸 Congelando frame ao vivo para anotação...');
            try {
                const res = await fetch('/api/live_raw_snapshot');
                const d = await res.json();
                if (d.status === 'ok') {
                    frozenLiveImage = d.image_base64;
                    liveImg.src = d.image_base64;
                    isLiveFrozen = true;

                    document.getElementById('btn-toggle-live-freeze').innerText = '▶ Retomar Transmissão ao Vivo';
                    document.getElementById('btn-toggle-live-freeze').className = 'cvat-btn primary';
                    document.getElementById('live-stream-status-msg').innerText = '⏸ Frame Congelado — Pronto para Anotação';
                    document.getElementById('live-stream-status-msg').style.color = 'var(--cvat-accent)';
                    showToast('✔ Frame congelado! Desenhe retângulos ou polígonos.');
                }
            } catch (e) {
                showToast(`Erro ao congelar frame: ${e}`);
            }
        }

        async function resumeLiveStream() {
            // Se houver anotações feitas no frame congelado/carregado, salva automaticamente no dataset
            if (boxes.length > 0 || polygons.length > 0) {
                showToast('💾 Salvando anotações do frame no dataset...');
                try {
                    const base64Data = frozenLiveImage || await getCurrentFrameBase64();
                    const res = await fetch('/api/annotation/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            image_base64: base64Data,
                            boxes: boxes,
                            polygons: polygons,
                            source_video: 'live_santos_camera',
                            frame_timestamp: Date.now() / 1000
                        })
                    });
                    const d = await res.json();
                    if (d.status === 'ok') {
                        showToast(`✔ Frame salvo no rodapé! Transmissão ao vivo retomada.`);
                    }
                } catch (e) {
                    console.error("Erro ao auto-salvar ao retomar live:", e);
                }

                // Limpa o canvas para o próximo frame
                boxes = [];
                polygons = [];
                currentPolygonPoints = [];
                selectedItem = null;
                renderObjectsList();
                redrawCanvas();
                await loadDatasetStats();
            }

            // Descongela a transmissão ao vivo e força reconexão do stream MJPEG
            isLiveFrozen = false;
            frozenLiveImage = null;

            liveImg.src = '';
            setTimeout(() => {
                liveImg.src = `/video_feed_raw?t=${Date.now()}`;
            }, 30);

            document.getElementById('btn-toggle-live-freeze').innerText = '📸 Congelar Frame para Anotação (Espaço)';
            document.getElementById('btn-toggle-live-freeze').className = 'cvat-btn live-freeze';
            document.getElementById('live-stream-status-msg').innerText = 'Transmitindo em tempo real do Porto de Santos';
            document.getElementById('live-stream-status-msg').style.color = 'var(--cvat-text-secondary)';
            document.getElementById('current-video-title').innerText = 'Câmera ao Vivo - Porto de Santos';
            showToast('▶ Transmissão ao vivo retomada.');
        }

        async function toggleLiveFreeze() {
            if (isLiveFrozen) {
                await resumeLiveStream();
            } else {
                await freezeLiveFrame();
            }
        }

        document.getElementById('btn-toggle-live-freeze').onclick = toggleLiveFreeze;
        document.getElementById('btn-live-freeze-sidebar').onclick = toggleLiveFreeze;

        // ZOOM & PAN CONTROLS
        document.getElementById('btn-zoom-in').onclick = () => { scale = Math.min(scale * 1.25, 6.0); applyTransform(); };
        document.getElementById('btn-zoom-out').onclick = () => { scale = Math.max(scale / 1.25, 0.2); applyTransform(); };
        document.getElementById('btn-fit-screen').onclick = fitToScreen;

        canvasContainer.addEventListener('wheel', (e) => {
            e.preventDefault();
            const rect = canvasContainer.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
            const newScale = Math.max(0.2, Math.min(scale * zoomFactor, 6.0));

            panX = mouseX - (mouseX - panX) * (newScale / scale);
            panY = mouseY - (mouseY - panY) * (newScale / scale);
            scale = newScale;
            applyTransform();
        }, { passive: false });

        // MOUSE / CANVAS EVENT HANDLERS
        function getCanvasCoords(e) {
            const rect = stageWrapper.getBoundingClientRect();
            const x = (e.clientX - rect.left) / scale;
            const y = (e.clientY - rect.top) / scale;
            return {
                x: Math.max(0, Math.min(canvas.width, Math.round(x))),
                y: Math.max(0, Math.min(canvas.height, Math.round(y)))
            };
        }

        canvasContainer.addEventListener('mousemove', (e) => {
            const pt = getCanvasCoords(e);
            document.getElementById('cursor-coords').innerText = `X: ${pt.x} | Y: ${pt.y}`;

            if (isPanning) {
                panX += (e.clientX - panStartX);
                panY += (e.clientY - panStartY);
                panStartX = e.clientX;
                panStartY = e.clientY;
                applyTransform();
                return;
            }

            if (isTransforming && selectedItem) {
                const dx = pt.x - transformStartX;
                const dy = pt.y - transformStartY;

                if (selectedItem.type === 'bbox') {
                    const b = boxes[selectedItem.index];
                    if (activeHandle === 'body') {
                        const w = initialCoords.x2 - initialCoords.x1;
                        const h = initialCoords.y2 - initialCoords.y1;
                        b.x1 = Math.max(0, Math.min(canvas.width - w, initialCoords.x1 + dx));
                        b.y1 = Math.max(0, Math.min(canvas.height - h, initialCoords.y1 + dy));
                        b.x2 = b.x1 + w;
                        b.y2 = b.y1 + h;
                    } else if (activeHandle === 'nw') {
                        b.x1 = Math.min(initialCoords.x2 - 10, initialCoords.x1 + dx);
                        b.y1 = Math.min(initialCoords.y2 - 10, initialCoords.y1 + dy);
                    } else if (activeHandle === 'se') {
                        b.x2 = Math.max(initialCoords.x1 + 10, initialCoords.x2 + dx);
                        b.y2 = Math.max(initialCoords.y1 + 10, initialCoords.y2 + dy);
                    } else if (activeHandle === 'ne') {
                        b.x2 = Math.max(initialCoords.x1 + 10, initialCoords.x2 + dx);
                        b.y1 = Math.min(initialCoords.y2 - 10, initialCoords.y1 + dy);
                    } else if (activeHandle === 'sw') {
                        b.x1 = Math.min(initialCoords.x2 - 10, initialCoords.x1 + dx);
                        b.y2 = Math.max(initialCoords.y1 + 10, initialCoords.y2 + dy);
                    }
                } else if (selectedItem.type === 'polygon') {
                    const poly = polygons[selectedItem.index];
                    if (activeVertexIndex >= 0 && activeVertexIndex < poly.points.length) {
                        poly.points[activeVertexIndex].x = pt.x;
                        poly.points[activeVertexIndex].y = pt.y;
                    } else if (activeHandle === 'body') {
                        poly.points.forEach((p, idx) => {
                            p.x = initialCoords.points[idx].x + dx;
                            p.y = initialCoords.points[idx].y + dy;
                        });
                    }
                }
                redrawCanvas();
                renderObjectsList();
                return;
            }

            if (isDrawingBox) {
                redrawCanvas();
                ctx.strokeStyle = CVAT_CLASSES[activeClassId % CVAT_CLASSES.length].color;
                ctx.lineWidth = 2;
                ctx.fillStyle = hexToRgba(CVAT_CLASSES[activeClassId % CVAT_CLASSES.length].color, 0.25);
                const w = pt.x - drawStartX;
                const h = pt.y - drawStartY;
                ctx.fillRect(drawStartX, drawStartY, w, h);
                ctx.strokeRect(drawStartX, drawStartY, w, h);
            } else if (activeTool === 'polygon' && currentPolygonPoints.length > 0) {
                redrawCanvas();
                // Linha elástica temporária até a posição do mouse
                const lastPt = currentPolygonPoints[currentPolygonPoints.length - 1];
                ctx.strokeStyle = CVAT_CLASSES[activeClassId % CVAT_CLASSES.length].color;
                ctx.lineWidth = 1.5;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(lastPt.x, lastPt.y);
                ctx.lineTo(pt.x, pt.y);
                ctx.stroke();
                ctx.setLineDash([]);
            }
        });

        canvas.addEventListener('mousedown', (e) => {
            if (activeTool === 'hand' || e.button === 1 || e.spaceKey) {
                isPanning = true;
                panStartX = e.clientX;
                panStartY = e.clientY;
                return;
            }

            const pt = getCanvasCoords(e);

            // MODO POLÍGONO
            if (activeTool === 'polygon') {
                if (sourceMode === 'live' && !isLiveFrozen) {
                    freezeLiveFrame();
                }

                // Verifica se clicou perto do ponto inicial para fechar o polígono
                if (currentPolygonPoints.length >= 3) {
                    const startP = currentPolygonPoints[0];
                    if (Math.hypot(pt.x - startP.x, pt.y - startP.y) <= 12) {
                        finishCurrentPolygon();
                        return;
                    }
                }

                currentPolygonPoints.push({ x: pt.x, y: pt.y });
                redrawCanvas();
                return;
            }

            // MODO RETÂNGULO OU CURSOR
            if (activeTool === 'cursor' || selectedItem) {
                // Checa alças do objeto selecionado
                if (selectedItem) {
                    if (selectedItem.type === 'polygon') {
                        const poly = polygons[selectedItem.index];
                        for (let vIdx = 0; vIdx < poly.points.length; vIdx++) {
                            const p = poly.points[vIdx];
                            if (Math.hypot(pt.x - p.x, pt.y - p.y) <= 8) {
                                isTransforming = true;
                                activeVertexIndex = vIdx;
                                transformStartX = pt.x;
                                transformStartY = pt.y;
                                return;
                            }
                        }
                    } else if (selectedItem.type === 'bbox') {
                        const hnd = getBoxHandleAt(pt.x, pt.y);
                        if (hnd) {
                            isTransforming = true;
                            activeHandle = hnd;
                            transformStartX = pt.x;
                            transformStartY = pt.y;
                            const b = boxes[selectedItem.index];
                            initialCoords = { x1: b.x1, y1: b.y1, x2: b.x2, y2: b.y2 };
                            return;
                        }
                    }
                }

                // Checa se clicou em algum objeto
                const hit = getObjectAt(pt.x, pt.y);
                if (hit) {
                    selectedItem = hit;
                    isTransforming = true;
                    activeHandle = 'body';
                    transformStartX = pt.x;
                    transformStartY = pt.y;
                    if (hit.type === 'bbox') {
                        const b = boxes[hit.index];
                        initialCoords = { x1: b.x1, y1: b.y1, x2: b.x2, y2: b.y2 };
                    } else {
                        const p = polygons[hit.index];
                        initialCoords = { points: JSON.parse(JSON.stringify(p.points)) };
                    }
                    renderObjectsList();
                    redrawCanvas();
                    return;
                } else {
                    selectedItem = null;
                    renderObjectsList();
                    redrawCanvas();
                }
            }

            if (activeTool === 'rect') {
                if (sourceMode === 'live' && !isLiveFrozen) {
                    freezeLiveFrame();
                }
                isDrawingBox = true;
                drawStartX = pt.x;
                drawStartY = pt.y;
            }
        });

        // Fechar Polígono no duplo clique
        canvas.addEventListener('dblclick', () => {
            if (activeTool === 'polygon' && currentPolygonPoints.length >= 3) {
                finishCurrentPolygon();
            }
        });

        function finishCurrentPolygon() {
            if (currentPolygonPoints.length >= 3) {
                const cls = CVAT_CLASSES[activeClassId % CVAT_CLASSES.length];
                polygons.push({
                    id: 'poly_' + Date.now().toString().slice(-5),
                    type: 'polygon',
                    class_id: activeClassId,
                    class_name: cls.name,
                    points: [...currentPolygonPoints],
                    hidden: false
                });
                selectedItem = { type: 'polygon', index: polygons.length - 1 };
                currentPolygonPoints = [];
                renderObjectsList();
                redrawCanvas();
                showToast('✔ Polígono de segmentação adicionado!');
            }
        }

        window.addEventListener('mouseup', (e) => {
            if (isPanning) { isPanning = false; return; }
            if (isTransforming) {
                isTransforming = false;
                activeHandle = null;
                activeVertexIndex = -1;
                return;
            }

            if (isDrawingBox) {
                isDrawingBox = false;
                const pt = getCanvasCoords(e);
                const x1 = Math.min(drawStartX, pt.x);
                const y1 = Math.min(drawStartY, pt.y);
                const x2 = Math.max(drawStartX, pt.x);
                const y2 = Math.max(drawStartY, pt.y);

                if ((x2 - x1) >= 8 && (y2 - y1) >= 8) {
                    const cls = CVAT_CLASSES[activeClassId % CVAT_CLASSES.length];
                    boxes.push({
                        id: 'box_' + Date.now().toString().slice(-5),
                        type: 'bbox',
                        class_id: activeClassId,
                        class_name: cls.name,
                        x1: x1, y1: y1, x2: x2, y2: y2,
                        hidden: false
                    });
                    selectedItem = { type: 'bbox', index: boxes.length - 1 };
                    renderObjectsList();
                }
                redrawCanvas();
            }
        });

        // REDRAW CANVAS (BBOXES + POLÍGONOS + PONTOS EM CRIAÇÃO)
        function redrawCanvas() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const fillAlpha = parseFloat(document.getElementById('slider-opacity').value) || 0.18;
            const lineThickness = parseInt(document.getElementById('slider-thickness').value) || 2;

            // 1. Renderiza Polígonos de Segmentação
            polygons.forEach((poly, idx) => {
                if (poly.hidden || poly.points.length < 3) return;
                const isSel = selectedItem && selectedItem.type === 'polygon' && selectedItem.index === idx;
                const color = CVAT_CLASSES[poly.class_id % CVAT_CLASSES.length].color;

                ctx.beginPath();
                ctx.moveTo(poly.points[0].x, poly.points[0].y);
                for (let i = 1; i < poly.points.length; i++) {
                    ctx.lineTo(poly.points[i].x, poly.points[i].y);
                }
                ctx.closePath();

                ctx.fillStyle = isSel ? 'rgba(255,255,255,0.22)' : hexToRgba(color, fillAlpha);
                ctx.fill();

                ctx.strokeStyle = isSel ? '#ffffff' : color;
                ctx.lineWidth = isSel ? lineThickness + 1 : lineThickness;
                ctx.stroke();

                // Tag
                const tagText = `${idx + 1}. [Seg] ${poly.class_name || CVAT_CLASSES[poly.class_id % CVAT_CLASSES.length].name}`;
                ctx.font = 'bold 11px -apple-system, sans-serif';
                const tagW = ctx.measureText(tagText).width;
                const p0 = poly.points[0];

                ctx.fillStyle = isSel ? '#1890ff' : color;
                ctx.fillRect(p0.x, Math.max(16, p0.y) - 16, tagW + 8, 16);
                ctx.fillStyle = '#000';
                ctx.fillText(tagText, p0.x + 4, Math.max(16, p0.y) - 4);

                // Se selecionado, desenha vértices editáveis
                if (isSel) {
                    poly.points.forEach(p => drawVertex(p.x, p.y));
                }
            });

            // 2. Renderiza Bounding Boxes
            boxes.forEach((b, idx) => {
                if (b.hidden) return;
                const isSel = selectedItem && selectedItem.type === 'bbox' && selectedItem.index === idx;
                const color = CVAT_CLASSES[b.class_id % CVAT_CLASSES.length].color;
                const bw = b.x2 - b.x1;
                const bh = b.y2 - b.y1;

                ctx.fillStyle = isSel ? 'rgba(255,255,255,0.2)' : hexToRgba(color, fillAlpha);
                ctx.fillRect(b.x1, b.y1, bw, bh);

                ctx.strokeStyle = isSel ? '#ffffff' : color;
                ctx.lineWidth = isSel ? lineThickness + 1 : lineThickness;
                ctx.strokeRect(b.x1, b.y1, bw, bh);

                const tagText = `${idx + 1}. ${b.class_name || CVAT_CLASSES[b.class_id % CVAT_CLASSES.length].name}`;
                ctx.font = 'bold 11px -apple-system, sans-serif';
                const tagW = ctx.measureText(tagText).width;
                const tagY = Math.max(16, b.y1);

                ctx.fillStyle = isSel ? '#1890ff' : color;
                ctx.fillRect(b.x1, tagY - 16, tagW + 8, 16);
                ctx.fillStyle = '#000';
                ctx.fillText(tagText, b.x1 + 4, tagY - 4);

                if (isSel) {
                    drawHandle(b.x1, b.y1);
                    drawHandle(b.x2, b.y1);
                    drawHandle(b.x2, b.y2);
                    drawHandle(b.x1, b.y2);
                }
            });

            // 3. Renderiza Polígono que está sendo criado agora
            if (activeTool === 'polygon' && currentPolygonPoints.length > 0) {
                const color = CVAT_CLASSES[activeClassId % CVAT_CLASSES.length].color;
                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(currentPolygonPoints[0].x, currentPolygonPoints[0].y);
                for (let i = 1; i < currentPolygonPoints.length; i++) {
                    ctx.lineTo(currentPolygonPoints[i].x, currentPolygonPoints[i].y);
                }
                ctx.stroke();

                currentPolygonPoints.forEach((p, idx) => {
                    drawVertex(p.x, p.y, idx === 0 ? '#52c41a' : '#1890ff');
                });
            }
        }

        function drawHandle(x, y) {
            ctx.fillStyle = '#1890ff';
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            ctx.fillRect(x - 4, y - 4, 8, 8);
            ctx.strokeRect(x - 4, y - 4, 8, 8);
        }

        function drawVertex(x, y, color = '#1890ff') {
            ctx.fillStyle = color;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.arc(x, y, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
        }

        function hexToRgba(hex, alpha) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }

        // Render Objects List
        function renderObjectsList() {
            const container = document.getElementById('objects-list-wrap');
            const totalCount = boxes.length + polygons.length;
            document.getElementById('count-objects').innerText = totalCount;

            if (totalCount === 0) {
                container.innerHTML = '<div style="color:var(--cvat-text-disabled); font-size:11px; text-align:center; padding:20px 0;">Nenhum objeto neste frame.<br>Pressione <strong>N</strong> (Retângulo) ou <strong>P</strong> (Polígono) para desenhar.</div>';
                return;
            }

            container.innerHTML = '';

            // Caixas BBox
            boxes.forEach((b, idx) => {
                const item = document.createElement('div');
                const isSel = selectedItem && selectedItem.type === 'bbox' && selectedItem.index === idx;
                item.className = `object-item ${isSel ? 'selected' : ''}`;
                const color = CVAT_CLASSES[b.class_id % CVAT_CLASSES.length].color;
                const bw = Math.round(b.x2 - b.x1);
                const bh = Math.round(b.y2 - b.y1);

                item.innerHTML = `
                    <div class="obj-left">
                        <div class="obj-color-dot" style="background:${color};"></div>
                        <div>
                            <div class="obj-title">${b.class_name || CVAT_CLASSES[b.class_id % CVAT_CLASSES.length].name} <span class="obj-type-badge">BBox</span></div>
                            <div class="obj-coords">${bw}×${bh} px</div>
                        </div>
                    </div>
                    <div class="obj-actions">
                        <button class="obj-btn" title="Ocultar/Exibir" onclick="event.stopPropagation(); toggleHideItem('bbox', ${idx})">${b.hidden ? '👁️‍🗨️' : '👁️'}</button>
                        <button class="obj-btn del" title="Excluir" onclick="event.stopPropagation(); deleteItem('bbox', ${idx})">✕</button>
                    </div>
                `;
                item.onclick = () => {
                    selectedItem = { type: 'bbox', index: idx };
                    renderObjectsList();
                    redrawCanvas();
                };
                container.appendChild(item);
            });

            // Polígonos de Segmentação
            polygons.forEach((poly, idx) => {
                const item = document.createElement('div');
                const isSel = selectedItem && selectedItem.type === 'polygon' && selectedItem.index === idx;
                item.className = `object-item ${isSel ? 'selected' : ''}`;
                const color = CVAT_CLASSES[poly.class_id % CVAT_CLASSES.length].color;

                item.innerHTML = `
                    <div class="obj-left">
                        <div class="obj-color-dot" style="background:${color};"></div>
                        <div>
                            <div class="obj-title">${poly.class_name || CVAT_CLASSES[poly.class_id % CVAT_CLASSES.length].name} <span class="obj-type-badge" style="background:rgba(24,144,255,0.2); color:var(--cvat-accent);">Segmentação</span></div>
                            <div class="obj-coords">${poly.points.length} vértices</div>
                        </div>
                    </div>
                    <div class="obj-actions">
                        <button class="obj-btn" title="Ocultar/Exibir" onclick="event.stopPropagation(); toggleHideItem('polygon', ${idx})">${poly.hidden ? '👁️‍🗨️' : '👁️'}</button>
                        <button class="obj-btn del" title="Excluir" onclick="event.stopPropagation(); deleteItem('polygon', ${idx})">✕</button>
                    </div>
                `;
                item.onclick = () => {
                    selectedItem = { type: 'polygon', index: idx };
                    renderObjectsList();
                    redrawCanvas();
                };
                container.appendChild(item);
            });
        }

        function toggleHideItem(type, idx) {
            if (type === 'bbox') boxes[idx].hidden = !boxes[idx].hidden;
            else polygons[idx].hidden = !polygons[idx].hidden;
            renderObjectsList();
            redrawCanvas();
        }

        function deleteItem(type, idx) {
            if (type === 'bbox') {
                boxes.splice(idx, 1);
            } else {
                polygons.splice(idx, 1);
            }
            if (selectedItem && selectedItem.type === type && selectedItem.index === idx) {
                selectedItem = null;
            }
            renderObjectsList();
            redrawCanvas();
        }

        document.getElementById('tool-del-box').onclick = () => {
            if (selectedItem) deleteItem(selectedItem.type, selectedItem.index);
        };
        document.getElementById('tool-clear-all').onclick = () => {
            if ((boxes.length > 0 || polygons.length > 0) && confirm('Limpar todos os objetos deste frame?')) {
                boxes = [];
                polygons = [];
                currentPolygonPoints = [];
                selectedItem = null;
                renderObjectsList();
                redrawCanvas();
            }
        };

        function getBoxHandleAt(x, y) {
            if (!selectedItem || selectedItem.type !== 'bbox') return null;
            const b = boxes[selectedItem.index];
            const tol = 7;
            if (Math.abs(x - b.x1) <= tol && Math.abs(y - b.y1) <= tol) return 'nw';
            if (Math.abs(x - b.x2) <= tol && Math.abs(y - b.y1) <= tol) return 'ne';
            if (Math.abs(x - b.x2) <= tol && Math.abs(y - b.y2) <= tol) return 'se';
            if (Math.abs(x - b.x1) <= tol && Math.abs(y - b.y2) <= tol) return 'sw';
            return null;
        }

        function getObjectAt(x, y) {
            // Checa polígonos
            for (let i = polygons.length - 1; i >= 0; i--) {
                const poly = polygons[i];
                if (isPointInPoly(x, y, poly.points)) return { type: 'polygon', index: i };
            }
            // Checa caixas
            for (let i = boxes.length - 1; i >= 0; i--) {
                const b = boxes[i];
                if (x >= b.x1 && x <= b.x2 && y >= b.y1 && y <= b.y2) return { type: 'bbox', index: i };
            }
            return null;
        }

        function isPointInPoly(x, y, pts) {
            let inside = false;
            for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
                const xi = pts[i].x, yi = pts[i].y;
                const xj = pts[j].x, yj = pts[j].y;
                const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
                if (intersect) inside = !inside;
            }
            return inside;
        }

        // CARREGA E GESTÃO DE CONJUNTOS DE CLASSES
        async function loadClassSets() {
            try {
                const res = await fetch('/api/class_sets');
                const d = await res.json();
                const sel = document.getElementById('select-class-set');
                const previousVal = sel.value;
                sel.innerHTML = '';
                d.presets.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.text = p.name;
                    sel.appendChild(opt);
                });

                if (previousVal && d.presets.some(p => p.id === previousVal)) {
                    sel.value = previousVal;
                    const activeP = d.presets.find(p => p.id === previousVal);
                    if (activeP) {
                        CVAT_CLASSES = activeP.classes;
                        renderClassesList();
                    }
                } else if (d.presets.length > 0) {
                    const activeP = d.presets[0];
                    CVAT_CLASSES = activeP.classes;
                    renderClassesList();
                }
            } catch (err) {
                console.error("Erro ao carregar conjuntos de classes:", err);
            }
        }

        document.getElementById('select-class-set').addEventListener('change', async (e) => {
            const pid = e.target.value;
            try {
                const res = await fetch('/api/class_sets/set_active', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ preset_id: pid })
                });
                const d = await res.json();
                if (d.status === 'ok' && d.active_preset) {
                    CVAT_CLASSES = d.active_preset.classes;
                    activeClassId = 0;
                    renderClassesList();
                    showToast(`Conjunto ativado: ${d.active_preset.name}`);
                }
            } catch (err) {
                showToast(`Erro ao ativar conjunto: ${err}`);
            }
        });

        document.getElementById('btn-create-class-set').onclick = () => {
            document.getElementById('modal-class-set').style.display = 'flex';
        };

        document.getElementById('btn-save-new-class-set').onclick = async () => {
            const name = document.getElementById('input-new-set-name').value.trim();
            const rawClasses = document.getElementById('input-new-set-classes').value.trim();
            if (!name || !rawClasses) {
                showToast('Preencha o nome e as classes do conjunto!');
                return;
            }

            const classNames = rawClasses.split(',').map(s => s.trim()).filter(Boolean);
            const classesArr = classNames.map((cName, idx) => ({ id: idx, name: cName }));

            try {
                const res = await fetch('/api/class_sets/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        id: 'set_' + Date.now().toString().slice(-6),
                        name: name,
                        classes: classesArr,
                        set_as_active: true
                    })
                });
                const d = await res.json();
                if (d.status === 'ok') {
                    document.getElementById('modal-class-set').style.display = 'none';
                    showToast(`Novo conjunto "${name}" criado e ativado!`);
                    await loadClassSets();
                }
            } catch (err) {
                showToast(`Erro ao salvar conjunto: ${err}`);
            }
        };

        document.getElementById('btn-add-single-class').onclick = () => {
            const newClassName = prompt('Nome da nova classe:');
            if (!newClassName || !newClassName.trim()) return;
            const newId = CVAT_CLASSES.length;
            const colors = ["#ff4d4f", "#1890ff", "#52c41a", "#faad14", "#722ed1", "#13c2c2", "#eb2f96"];
            CVAT_CLASSES.push({
                id: newId,
                name: newClassName.trim().toLowerCase().replace(/\s+/g, '_'),
                color: colors[newId % colors.length]
            });
            renderClassesList();
            showToast(`Classe "${newClassName}" adicionada!`);
        };

        // Render Classes List
        function renderClassesList() {
            const container = document.getElementById('classes-list-wrap');
            container.innerHTML = '';
            CVAT_CLASSES.forEach((cls, idx) => {
                const chip = document.createElement('div');
                chip.className = `class-chip ${idx === activeClassId ? 'active' : ''}`;
                chip.innerHTML = `
                    <div style="display:flex; align-items:center;">
                        <div class="class-color-badge" style="background:${cls.color};"></div>
                        <span>${cls.name}</span>
                    </div>
                    <span class="class-hotkey">[${idx + 1}]</span>
                `;
                chip.onclick = () => {
                    activeClassId = idx;
                    document.getElementById('active-class-indicator').innerText = `${cls.name} (${idx + 1})`;
                    document.getElementById('active-class-indicator').style.color = cls.color;
                    renderClassesList();
                    if (selectedItem) {
                        if (selectedItem.type === 'bbox') {
                            boxes[selectedItem.index].class_id = idx;
                            boxes[selectedItem.index].class_name = cls.name;
                        } else {
                            polygons[selectedItem.index].class_id = idx;
                            polygons[selectedItem.index].class_name = cls.name;
                        }
                        renderObjectsList();
                        redrawCanvas();
                    }
                };
                container.appendChild(chip);
            });

            if (CVAT_CLASSES[activeClassId]) {
                document.getElementById('active-class-indicator').innerText = `${CVAT_CLASSES[activeClassId].name} (${activeClassId + 1})`;
                document.getElementById('active-class-indicator').style.color = CVAT_CLASSES[activeClassId].color;
            }
        }

        // Sidebar Tabs Switcher
        document.querySelectorAll('.sidebar-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                const target = tab.getAttribute('data-tab');
                document.getElementById(`pane-${target}`).classList.add('active');
            });
        });

        document.getElementById('slider-opacity').addEventListener('input', redrawCanvas);
        document.getElementById('slider-thickness').addEventListener('input', redrawCanvas);

        // EXTRAÇÃO DE IMAGEM BASE64 DO FRAME ATUAL
        async function getCurrentFrameBase64() {
            if (sourceMode === 'live') {
                if (isLiveFrozen && frozenLiveImage) return frozenLiveImage;
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';
                const res = await fetch(`/api/${currentDomain}/live_raw_snapshot`);
                const d = await res.json();
                if (d.status === 'ok') {
                    frozenLiveImage = d.image_base64;
                    liveImg.src = d.image_base64;
                    isLiveFrozen = true;
                    return d.image_base64;
                }
            }

            const offCanvas = document.createElement('canvas');
            offCanvas.width = video.videoWidth || 1280;
            offCanvas.height = video.videoHeight || 720;
            const offCtx = offCanvas.getContext('2d');
            offCtx.drawImage(video, 0, 0, offCanvas.width, offCanvas.height);
            return offCanvas.toDataURL('image/jpeg', 0.95);
        }

        // ====================================================
        // GESTÃO DO MODELO DE IA ATRELADO & ACTIVE LEARNING
        // ====================================================
        let availableAiModels = [];
        let activeModelId = 'yolo11n';
        let aiConfThreshold = 0.20;
        let autoAiOnPause = true;
        let isAiInferring = false;

        async function loadAiModels() {
            try {
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';
                const res = await fetch(`/api/annotation/models?domain=${currentDomain}`);
                const d = await res.json();
                if (d.status === 'ok') {
                    availableAiModels = d.models || [];
                    activeModelId = d.active_model_id || (availableAiModels.length > 0 ? availableAiModels[0].id : 'yolo11n');

                    const selHeader = document.getElementById('select-ai-model-header');
                    const selSidebar = document.getElementById('select-ai-model-sidebar');

                    [selHeader, selSidebar].forEach(sel => {
                        if (!sel) return;
                        sel.innerHTML = '';
                        availableAiModels.forEach(m => {
                            const opt = document.createElement('option');
                            opt.value = m.id;
                            opt.text = `${m.name} (${m.framework || 'PyTorch'})`;
                            if (m.id === activeModelId) opt.selected = true;
                            sel.appendChild(opt);
                        });
                    });

                    updateAiModelDisplay();
                }
            } catch (err) {
                console.error("Erro ao carregar modelos de IA:", err);
            }
        }

        function updateAiModelDisplay() {
            const m = availableAiModels.find(item => item.id === activeModelId);
            const mName = m ? m.name : activeModelId;
            const badge = document.getElementById('canvas-ai-badge');
            if (badge) badge.innerText = `🤖 IA: ${mName.slice(0, 16)} (${Math.round(aiConfThreshold * 100)}%)`;
            const desc = document.getElementById('ai-model-description');
            if (desc && m) desc.innerText = m.description || `Modelo ${m.name} acoplado para auto-rotulagem de alvos.`;
        }

        function onAiModelChanged(newModelId) {
            activeModelId = newModelId;
            const selH = document.getElementById('select-ai-model-header');
            const selS = document.getElementById('select-ai-model-sidebar');
            if (selH && selH.value !== newModelId) selH.value = newModelId;
            if (selS && selS.value !== newModelId) selS.value = newModelId;
            updateAiModelDisplay();
            showToast(`🤖 Modelo de IA selecionado: ${newModelId}`);
        }

        if (document.getElementById('select-ai-model-header')) {
            document.getElementById('select-ai-model-header').addEventListener('change', (e) => onAiModelChanged(e.target.value));
        }
        if (document.getElementById('select-ai-model-sidebar')) {
            document.getElementById('select-ai-model-sidebar').addEventListener('change', (e) => onAiModelChanged(e.target.value));
        }

        // Slider de Confiança
        const sliderConf = document.getElementById('slider-ai-conf');
        const displayConf = document.getElementById('display-ai-conf');
        if (sliderConf) {
            sliderConf.addEventListener('input', (e) => {
                aiConfThreshold = parseFloat(e.target.value) || 0.20;
                if (displayConf) displayConf.innerText = `${Math.round(aiConfThreshold * 100)}%`;
                updateAiModelDisplay();
            });
        }

        // Toggle Auto-IA ao Pausar
        function toggleAutoAi() {
            autoAiOnPause = !autoAiOnPause;
            const btn = document.getElementById('btn-toggle-auto-ai');
            const chk = document.getElementById('check-auto-ai-pause');
            if (btn) {
                btn.className = `mode-btn ${autoAiOnPause ? 'active' : ''}`;
                btn.innerText = autoAiOnPause ? '⚡ Auto-IA: ON' : '⚡ Auto-IA: OFF';
            }
            if (chk) chk.checked = autoAiOnPause;
            showToast(`Auto-IA ao pausar frame: ${autoAiOnPause ? 'ATIVADA' : 'DESATIVADA'}`);
        }

        if (document.getElementById('btn-toggle-auto-ai')) {
            document.getElementById('btn-toggle-auto-ai').onclick = toggleAutoAi;
        }
        if (document.getElementById('check-auto-ai-pause')) {
            document.getElementById('check-auto-ai-pause').addEventListener('change', (e) => {
                autoAiOnPause = e.target.checked;
                const btn = document.getElementById('btn-toggle-auto-ai');
                if (btn) {
                    btn.className = `mode-btn ${autoAiOnPause ? 'active' : ''}`;
                    btn.innerText = autoAiOnPause ? '⚡ Auto-IA: ON' : '⚡ Auto-IA: OFF';
                }
                showToast(`Auto-IA ao pausar frame: ${autoAiOnPause ? 'ATIVADA' : 'DESATIVADA'}`);
            });
        }

        // INFERÊNCIA DO MODELO DE IA NO FRAME
        async function runAiAutoDetect(isAutomated = false) {
            if (isAiInferring) return;
            // Se for automatizado ao pausar e já houver anotações feitas/editadas, não sobrepõe
            if (isAutomated && (boxes.length > 0 || polygons.length > 0)) {
                return;
            }

            isAiInferring = true;
            if (!isAutomated) {
                showToast(`🤖 Executando inferência do modelo [${activeModelId}] no frame...`);
            }

            try {
                const base64Data = await getCurrentFrameBase64();
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';

                const res = await fetch('/api/annotation/auto_detect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image_base64: base64Data,
                        model_id: activeModelId,
                        conf: aiConfThreshold,
                        domain: currentDomain
                    })
                });
                const d = await res.json();
                if (d.status === 'ok' && d.detections && d.detections.length > 0) {
                    boxes = [];
                    polygons = [];
                    d.detections.forEach(det => {
                        const [x1, y1, x2, y2] = det.bbox;
                        let cid = det.class_id !== undefined ? det.class_id : activeClassId;
                        let cname = det.class_name || (CVAT_CLASSES[cid] ? CVAT_CLASSES[cid].name : 'objeto');

                        boxes.push({
                            id: 'box_' + Date.now().toString().slice(-5) + '_' + Math.floor(Math.random()*1000),
                            type: 'bbox',
                            class_id: cid,
                            class_name: cname,
                            x1: Math.round(x1),
                            y1: Math.round(y1),
                            x2: Math.round(x2),
                            y2: Math.round(y2),
                            confidence: det.confidence || 0.85,
                            source_model: det.source_model || activeModelId,
                            hidden: false
                        });
                    });

                    selectedItem = { type: 'bbox', index: 0 };
                    renderObjectsList();
                    redrawCanvas();
                    showToast(`🤖 IA [${activeModelId}]: ${d.detections.length} objeto(s) detectado(s)! Edite ou limpe para corrigir erros.`);
                } else {
                    if (!isAutomated) {
                        showToast(`Nenhuma detecção encontrada pelo modelo [${activeModelId}] com confiança ≥ ${Math.round(aiConfThreshold * 100)}%.`);
                    }
                }
            } catch (err) {
                console.error("Erro na inferência da IA:", err);
                if (!isAutomated) {
                    showToast(`Erro na inferência da IA: ${err}`);
                }
            } finally {
                isAiInferring = false;
            }
        }

        // DELETAR TODAS AS ANOTAÇÕES DO FRAME
        function deleteAllAnnotations() {
            const count = boxes.length + polygons.length;
            if (count === 0) {
                showToast('Nenhuma anotação neste frame para deletar.');
                return;
            }
            if (confirm(`Deletar todas as ${count} anotações deste frame e refazer do zero?`)) {
                boxes = [];
                polygons = [];
                currentPolygonPoints = [];
                selectedItem = null;
                renderObjectsList();
                redrawCanvas();
                showToast('🗑️ Todas as anotações foram removidas! Frame limpo para corrigir os erros da IA.');
            }
        }

        // Conecta eventos de botões
        const bindEl = (id, fn) => { const el = document.getElementById(id); if (el) el.onclick = fn; };
        bindEl('btn-ai-auto', () => runAiAutoDetect(false));
        bindEl('btn-run-ai-sidebar', () => runAiAutoDetect(false));
        bindEl('btn-hud-run-ai', () => runAiAutoDetect(false));
        bindEl('tool-run-ai-left', () => runAiAutoDetect(false));
        bindEl('canvas-ai-badge', () => runAiAutoDetect(false));

        bindEl('btn-delete-all-boxes', deleteAllAnnotations);
        bindEl('btn-clear-all-ai', deleteAllAnnotations);
        bindEl('btn-hud-clear-all', deleteAllAnnotations);
        bindEl('tool-clear-all', deleteAllAnnotations);

        // SALVAR ANOTAÇÃO (BBOX + POLÍGONOS) NO DATASET YOLO & CONTINUAR VÍDEO
        async function saveAnnotationYOLO() {
            if (boxes.length === 0 && polygons.length === 0) {
                showToast('Desenhe ao menos um objeto ou execute a IA antes de salvar!');
                return;
            }

            showToast('💾 Gravando frame corrigido no dataset YOLO para re-treinamento da IA...');
            try {
                const base64Data = await getCurrentFrameBase64();
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';
                const srcLabel = (sourceMode === 'live') ? 'live_santos_camera' : document.getElementById('select-video-source').value;
                const ts = (sourceMode === 'live') ? Date.now() / 1000 : video.currentTime;

                const res = await fetch('/api/annotation/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image_base64: base64Data,
                        boxes: boxes,
                        polygons: polygons,
                        domain: currentDomain,
                        source_video: srcLabel,
                        frame_timestamp: ts,
                        model_used: activeModelId,
                        is_ai_assisted: true,
                        human_corrected: true,
                        notes: `Anotação com auxílio do modelo ${activeModelId} corrigida pelo operador humano.`
                    })
                });
                const d = await res.json();
                if (d.status === 'ok') {
                    // 1. Limpa o canvas para o próximo frame
                    boxes = [];
                    polygons = [];
                    currentPolygonPoints = [];
                    selectedItem = null;
                    renderObjectsList();
                    redrawCanvas();

                    // 2. Atualiza a galeria inferior e contadores
                    await loadDatasetStats();

                    // 3. CONTINUAR O VÍDEO AUTOMATICAMENTE
                    if (sourceMode === 'live') {
                        resumeLiveStream();
                        showToast(`✔ Frame Ground Truth salvo no dataset! Transmissão ao vivo retomada.`);
                    } else {
                        video.play();
                        btnPlay.innerText = '⏸';
                        showToast(`✔ Frame Ground Truth salvo no dataset! Reprodução continuada.`);
                    }
                } else {
                    showToast(`Erro ao salvar: ${d.message || 'Falha'}`);
                }
            } catch (err) {
                showToast(`Erro de rede: ${err}`);
            }
        }
        bindEl('btn-save-yolo', saveAnnotationYOLO);
        bindEl('btn-save-corrected-sidebar', saveAnnotationYOLO);

        // PUXAR / IMPORTAR DATASET EXISTENTE (.ZIP)
        document.getElementById('input-import-dataset-zip').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            const pathParts = window.location.pathname.split('/').filter(Boolean);
            const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';
            formData.append('domain', currentDomain);
            showToast('📦 Importando dataset ZIP e reconstruindo anotações...');

            try {
                const res = await fetch('/api/annotation/import_zip', { method: 'POST', body: formData });
                const d = await res.json();
                if (d.status === 'ok') {
                    showToast(`✔ Dataset importado com sucesso: ${d.imported_images} imagens!`);
                    await loadClassSets();
                    await loadDatasetStats();
                } else {
                    showToast(`Erro na importação: ${d.error || 'Falha ao processar ZIP'}`);
                }
            } catch (err) {
                showToast(`Erro de rede ao importar: ${err}`);
            }
        });

        // EXCLUIR ITEM DO DATASET
        async function deleteAnnotationItem(imageId) {
            if (!confirm('Excluir este frame anotado do dataset?')) return;
            try {
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';
                const res = await fetch(`/api/annotation/delete/${imageId}?domain=${currentDomain}`, { method: 'DELETE' });
                const d = await res.json();
                if (d.status === 'ok') {
                    showToast('✔ Frame excluído do dataset.');
                    await loadDatasetStats();
                }
            } catch (err) {
                showToast(`Erro ao excluir: ${err}`);
            }
        }

        // CARREGA ESTATÍSTICAS E GALERIA DO DATASET (SIDEBAR & FILMSTRIP INFERIOR)
        async function loadDatasetStats() {
            try {
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';
                const res = await fetch(`/api/annotation/list?domain=${currentDomain}`);
                const d = await res.json();
                const totalImgs = d.total_images || 0;
                const totalObjs = (d.total_boxes || 0) + (d.total_polygons || 0);

                document.getElementById('ds-images-count').innerText = totalImgs;
                document.getElementById('ds-boxes-count').innerText = totalObjs;
                document.getElementById('filmstrip-count').innerText = `${totalImgs} frames`;

                // 1. Galeria Inferior (Filmstrip Horizontal)
                const filmstrip = document.getElementById('bottom-filmstrip-list');
                if (filmstrip) {
                    if (!d.items || d.items.length === 0) {
                        filmstrip.innerHTML = '<span style="font-size:11px; color:var(--cvat-text-disabled); padding-left:6px;">Nenhum frame salvo ainda. Pressione Salvar (Ctrl+S) após anotar ou corrigir.</span>';
                    } else {
                        filmstrip.innerHTML = '';
                        d.items.forEach((item, idx) => {
                            const card = document.createElement('div');
                            card.className = 'filmstrip-item';
                            card.title = `Frame #${idx + 1} (${item.filename}) - Clique para continuar editando`;
                            card.innerHTML = `
                                <img class="filmstrip-thumb" src="/media/annotated/${item.filename}" alt="Frame">
                                <span class="filmstrip-badge">${(item.num_boxes||0) + (item.num_polygons||0)} obj</span>
                                <button class="filmstrip-del" title="Excluir" onclick="event.stopPropagation(); deleteAnnotationItem('${item.id}')">✕</button>
                            `;
                            card.onclick = () => loadExistingAnnotation(item.id);
                            filmstrip.appendChild(card);
                        });
                    }
                }

                // 2. Galeria da Sidebar
                const gallery = document.getElementById('dataset-gallery');
                if (gallery) {
                    if (!d.items || d.items.length === 0) {
                        gallery.innerHTML = '<div style="color:var(--cvat-text-disabled); font-size:10px; grid-column:1/-1; text-align:center; padding:10px;">Nenhum frame salvo ainda.</div>';
                    } else {
                        gallery.innerHTML = '';
                        d.items.forEach(item => {
                            const el = document.createElement('div');
                            el.style.cssText = 'position:relative; background:var(--cvat-bg-surface); border:1px solid var(--cvat-border); border-radius:3px; overflow:hidden; cursor:pointer;';
                            el.title = `Clique para editar o frame ${item.filename}`;
                            el.innerHTML = `
                                <img src="/media/annotated/${item.filename}" style="width:100%; height:60px; object-fit:cover; display:block;">
                                <div style="padding:3px 5px; font-size:9.5px; display:flex; justify-content:space-between; color:var(--cvat-text-secondary);">
                                    <span><strong>${(item.num_boxes||0) + (item.num_polygons||0)}</strong> obj</span>
                                    <span style="color:var(--cvat-accent);">Editar ✎</span>
                                </div>
                            `;
                            el.onclick = () => loadExistingAnnotation(item.id);
                            gallery.appendChild(el);
                        });
                    }
                }
            } catch (err) {
                console.error("Erro ao carregar estatísticas do dataset:", err);
            }
        }

        // CARREGA ANOTAÇÃO EXISTENTE NO CANVAS PARA CONTINUAR / REVISAR
        async function loadExistingAnnotation(imageId) {
            showToast('Carregando frame salvo para edição...');
            try {
                const pathParts = window.location.pathname.split('/').filter(Boolean);
                const currentDomain = (pathParts.length > 0 && pathParts[0] !== 'anotar' && pathParts[0] !== 'hub') ? pathParts[0] : 'naval';
                const res = await fetch(`/api/annotation/load/${imageId}?domain=${currentDomain}`);
                const d = await res.json();
                if (d.status === 'ok') {
                    // Configura visualizador no modo imagem do frame salvo
                    if (sourceMode !== 'live') {
                        document.getElementById('mode-btn-video').classList.remove('active');
                        document.getElementById('mode-btn-live').classList.add('active', 'live-active');
                        video.style.display = 'none';
                        liveImg.style.display = 'block';
                        document.getElementById('header-frame-nav').style.display = 'none';
                        document.getElementById('player-bar-recorded').style.display = 'none';
                        document.getElementById('player-bar-live').style.display = 'flex';
                        document.getElementById('section-recorded-video').style.display = 'none';
                        document.getElementById('section-live-video').style.display = 'flex';
                        sourceMode = 'live';
                    }

                    liveImg.src = d.image_url;
                    frozenLiveImage = d.image_url;
                    isLiveFrozen = true;

                    // Restaura caixas e polígonos
                    boxes = (d.boxes || []).map((b, idx) => ({ ...b, id: `box_${idx}`, type: 'bbox', hidden: false }));
                    polygons = (d.polygons || []).map((p, idx) => ({ ...p, id: `poly_${idx}`, type: 'polygon', hidden: false }));
                    selectedItem = null;

                    renderObjectsList();
                    redrawCanvas();

                    document.getElementById('btn-toggle-live-freeze').innerText = '▶ Retomar Transmissão ao Vivo';
                    document.getElementById('btn-toggle-live-freeze').className = 'cvat-btn primary';
                    document.getElementById('live-stream-status-msg').innerText = `⏸ Frame #${imageId} Carregado (${d.filename})`;
                    document.getElementById('live-stream-status-msg').style.color = 'var(--cvat-accent)';
                    document.getElementById('current-video-title').innerText = `Dataset: ${d.filename}`;
                    showToast(`✔ Frame carregado: ${boxes.length} caixas, ${polygons.length} polígonos.`);
                }
            } catch (err) {
                showToast(`Erro ao carregar frame: ${err}`);
            }
        }

        // Troca de Vídeo Gravado
        document.getElementById('select-video-source').addEventListener('change', (e) => {
            const vname = e.target.value;
            video.src = `/media/video/${vname}`;
            video.load();
            document.getElementById('current-video-title').innerText = vname;
            boxes = [];
            polygons = [];
            currentPolygonPoints = [];
            selectedItem = null;
            redrawCanvas();
            renderObjectsList();
        });

        // Upload de Vídeo
        document.getElementById('input-upload-video').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            showToast('Enviando vídeo...');
            try {
                const res = await fetch('/api/upload_video', { method: 'POST', body: formData });
                const d = await res.json();
                if (d.status === 'ok') {
                    showToast('Vídeo carregado com sucesso!');
                    const opt = document.createElement('option');
                    opt.value = d.filename;
                    opt.text = `Upload: ${d.filename}`;
                    opt.selected = true;
                    document.getElementById('select-video-source').appendChild(opt);
                    video.src = d.url;
                    video.load();
                    document.getElementById('current-video-title').innerText = d.filename;
                }
            } catch (err) {
                showToast(`Erro no envio: ${err}`);
            }
        });

        // ATALHOS DE TECLADO (CVAT MODE)
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

            if (e.code === 'Space') {
                e.preventDefault();
                togglePlay();
            } else if (e.code === 'KeyA') {
                e.preventDefault();
                runAiAutoDetect(false);
            } else if ((e.altKey && e.code === 'KeyC') || (e.ctrlKey && e.shiftKey && e.code === 'Delete')) {
                e.preventDefault();
                deleteAllAnnotations();
            } else if (e.code === 'KeyD' || e.code === 'BracketLeft') {
                stepFrame(-1);
            } else if (e.code === 'KeyF' || e.code === 'BracketRight') {
                stepFrame(1);
            } else if (e.code === 'KeyN' || e.code === 'KeyR') {
                setTool('rect');
            } else if (e.code === 'KeyP') {
                setTool('polygon');
            } else if (e.code === 'Enter') {
                if (activeTool === 'polygon' && currentPolygonPoints.length >= 3) {
                    finishCurrentPolygon();
                }
            } else if (e.code === 'KeyS' || e.code === 'Escape') {
                setTool('cursor');
            } else if (e.code === 'KeyH') {
                setTool('hand');
            } else if (e.code === 'Delete' || e.code === 'Backspace') {
                if (selectedItem) deleteItem(selectedItem.type, selectedItem.index);
            } else if (e.ctrlKey && e.code === 'KeyS') {
                e.preventDefault();
                saveAnnotationYOLO();
            } else if (e.ctrlKey && e.code === 'Digit0') {
                e.preventDefault();
                fitToScreen();
            } else if (e.key >= '1' && e.key <= '9') {
                const idx = parseInt(e.key) - 1;
                if (idx < CVAT_CLASSES.length) {
                    activeClassId = idx;
                    document.getElementById('active-class-indicator').innerText = `${CVAT_CLASSES[idx].name} (${idx+1})`;
                    document.getElementById('active-class-indicator').style.color = CVAT_CLASSES[idx].color;
                    renderClassesList();
                }
            }
        });

        document.getElementById('btn-open-shortcuts').onclick = () => {
            document.getElementById('shortcuts-modal').style.display = 'flex';
        };

        // Auto-execução ao pausar vídeo
        video.addEventListener('pause', () => {
            if (sourceMode === 'video' && autoAiOnPause && boxes.length === 0 && polygons.length === 0) {
                setTimeout(() => runAiAutoDetect(true), 150);
            }
        });

        // Inicialização
        loadAiModels();
        loadClassSets();
        renderObjectsList();
        loadDatasetStats();
    </script>
</body>
</html>"""
