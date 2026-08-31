# -*- coding: utf-8 -*-
"""Gerador de Template HTML dinâmico para os Painéis de Monitoramento de cada um dos 7 Domínios."""

from src.domains.domain_config import DOMAINS_CONFIG

def get_domain_monitoring_html(domain_id="naval"):
    config = DOMAINS_CONFIG.get(domain_id, DOMAINS_CONFIG["naval"])
    dom_id = config["id"]
    dom_name = config["name"]
    dom_icon = config["icon"]
    dom_badge = config["badge"]
    dom_tagline = config["tagline"]
    accent_color = config["accent_color"]
    accent_rgba = config["accent_rgba"]
    registry_title = config["registry_title"]
    default_stream_title = config["default_stream_title"]
    default_youtube_url = config["default_youtube_url"]

    # Constrói opções da barra de navegação entre domínios
    domain_nav_items = ""
    for d_k, d_v in DOMAINS_CONFIG.items():
        is_active = "active" if d_k == dom_id else ""
        domain_nav_items += f"""
        <a href="/{d_k}" class="domain-tab {is_active}" style="--tab-color: {d_v['accent_color']};">
            <span class="tab-icon">{d_v['icon']}</span>
            <span class="tab-label">{d_v['name'].split('&')[0].strip()}</span>
        </a>
        """

    # Constrói campos de semântica
    sem_boxes_html = ""
    for sem in config.get("semantics_keys", []):
        sem_boxes_html += f"""
        <div class="meta-row">
            <span class="meta-label">{sem['label']}:</span>
            <span class="meta-val" id="sem_{sem['key']}" style="color: {sem['color']};">{sem['default']}</span>
        </div>
        """

    # Constrói campos do alvo selecionado
    target_boxes_html = ""
    for tgt in config.get("target_keys", []):
        target_boxes_html += f"""
        <div class="meta-row">
            <span class="meta-label">{tgt['label']}:</span>
            <span class="meta-val" id="tgt_{tgt['key']}">{tgt['default']}</span>
        </div>
        """

    # Constrói colunas da tabela de registros
    table_headers_html = ""
    for col in config.get("registry_columns", []):
        table_headers_html += f"""<th style="width: {col['width']};">{col['label']}</th>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dom_icon} {dom_name} — Monitoramento &amp; Telemetria</title>
    <style>
        :root {{
            --bg-dark: #090c10;
            --bg-canvas: #06080b;
            --bg-card: #0d1117;
            --bg-card-hover: #131822;
            --bg-inset: #090c10;
            --border: #1b222d;
            --border-strong: #283344;
            --accent-primary: {accent_color};
            --accent-glow: {accent_rgba};
            --text-main: #e6edf3;
            --text-muted: #8b949e;
            --text-faint: #484f58;
            --radius-sm: 4px;
            --radius-md: 6px;
            --radius-lg: 8px;
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            --font-mono: 'Cascadia Mono', Consolas, 'Liberation Mono', monospace;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-canvas);
            color: var(--text-main);
            font-family: var(--font-sans);
            padding: 14px;
            -webkit-font-smoothing: antialiased;
        }}
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: var(--border-strong); border-radius: 4px; }}

        /* ===== DOMAIN NAV BAR ===== */
        .domain-navbar {{
            display: flex;
            align-items: center;
            gap: 6px;
            overflow-x: auto;
            padding: 8px 12px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            margin-bottom: 12px;
        }}
        .home-tab {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-sm);
            color: #ffffff;
            text-decoration: none;
            font-size: 12px;
            font-weight: 700;
            margin-right: 8px;
            flex-shrink: 0;
            transition: all 0.15s ease;
        }}
        .home-tab:hover {{ background: rgba(255,255,255,0.15); border-color: #ffffff; }}

        .domain-tab {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: var(--bg-inset);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text-muted);
            text-decoration: none;
            font-size: 11.5px;
            font-weight: 600;
            white-space: nowrap;
            transition: all 0.15s ease;
        }}
        .domain-tab:hover {{
            background: var(--bg-card-hover);
            color: var(--text-main);
            border-color: var(--tab-color);
        }}
        .domain-tab.active {{
            background: rgba(255,255,255,0.04);
            color: #ffffff;
            border-color: var(--tab-color);
            box-shadow: 0 0 10px var(--accent-glow);
            font-weight: 700;
        }}

        /* ===== TOPBAR ===== */
        .topbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 18px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            margin-bottom: 12px;
        }}
        .brand {{ display: flex; align-items: center; gap: 12px; }}
        .brand-mark {{
            width: 36px; height: 36px;
            display: flex; align-items: center; justify-content: center;
            border-radius: var(--radius-sm);
            background: var(--accent-primary);
            color: #000;
            font-size: 20px;
            font-weight: bold;
        }}
        .brand-text h1 {{ font-size: 15px; font-weight: 800; color: #ffffff; display: flex; align-items: center; gap: 8px; }}
        .brand-badge {{
            font-size: 10px; font-weight: 700; text-transform: uppercase;
            padding: 2px 7px; border-radius: 4px;
            background: var(--accent-glow); color: var(--accent-primary); border: 1px solid var(--accent-primary);
        }}
        .brand-text .sub {{ font-size: 11.5px; color: var(--text-muted); margin-top: 2px; }}
        .topbar-right {{ display: flex; align-items: center; gap: 8px; }}
        .status-chip {{
            display: flex; align-items: center; gap: 6px;
            padding: 5px 10px; border-radius: var(--radius-sm);
            font-size: 11px; font-weight: 600;
            background: var(--bg-inset); color: var(--text-main);
            border: 1px solid var(--border-strong);
        }}
        .status-dot {{ width: 7px; height: 7px; border-radius: 50%; background: #52c41a; }}
        .topbar-btn {{
            display: inline-flex; align-items: center; gap: 6px;
            padding: 6px 12px; font-size: 11.5px; font-weight: 600;
            color: var(--text-main); background: var(--bg-inset);
            border: 1px solid var(--border-strong); border-radius: var(--radius-sm);
            text-decoration: none; cursor: pointer; transition: all 0.15s ease;
        }}
        .topbar-btn:hover {{ background: var(--bg-card-hover); border-color: var(--accent-primary); }}
        .topbar-btn.primary {{ background: var(--accent-primary); color: #000000; font-weight: 700; border-color: var(--accent-primary); }}

        /* ===== MAIN LAYOUT ===== */
        .grid {{ display: grid; grid-template-columns: 320px 1fr 380px; gap: 12px; align-items: start; }}
        .col-stack {{ display: flex; flex-direction: column; gap: 12px; }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 14px;
        }}
        .card-header {{
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border);
        }}
        .card-title {{
            font-size: 11.5px; font-weight: 700; color: var(--text-muted);
            text-transform: uppercase; letter-spacing: 0.5px;
        }}

        .meta-row {{
            display: flex; justify-content: space-between; align-items: center;
            font-size: 11.5px; margin-bottom: 6px; padding: 4px 6px;
            background: var(--bg-inset); border-radius: 4px;
        }}
        .meta-label {{ color: var(--text-muted); }}
        .meta-val {{ font-weight: 700; color: var(--text-main); font-family: var(--font-mono); }}

        /* Form Controls */
        .form-group {{ margin-bottom: 8px; }}
        .form-label {{ font-size: 10.5px; font-weight: 600; color: var(--text-muted); margin-bottom: 3px; display: block; }}
        .text-input, .select-input {{
            width: 100%; padding: 6px 8px; background: var(--bg-inset); border: 1px solid var(--border-strong);
            border-radius: 4px; color: var(--text-main); font-size: 11px; outline: none;
        }}
        .text-input:focus {{ border-color: var(--accent-primary); }}

        .btn-action {{
            width: 100%; padding: 7px; font-size: 11.5px; font-weight: 700;
            background: var(--bg-inset); border: 1px solid var(--border-strong);
            border-radius: 4px; color: var(--text-main); cursor: pointer; transition: all 0.15s ease;
            margin-top: 4px;
        }}
        .btn-action:hover {{ background: var(--bg-card-hover); border-color: var(--accent-primary); color: #fff; }}
        .btn-action.highlight {{ background: var(--accent-primary); color: #000; border-color: var(--accent-primary); }}

        /* Center Video Canvas */
        .video-container {{
            position: relative;
            background: #000;
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-lg);
            overflow: hidden;
            aspect-ratio: 16/9;
            display: flex; align-items: center; justify-content: center;
        }}
        .video-stream {{
            width: 100%; height: 100%; object-fit: contain;
        }}
        .video-controls {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 8px 12px; background: var(--bg-card);
            border: 1px solid var(--border); border-radius: var(--radius-md);
            margin-top: 8px; font-size: 11px;
        }}

        /* Table */
        .table-wrap {{
            max-height: 480px; overflow-y: auto;
            border: 1px solid var(--border); border-radius: 4px;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        th {{
            background: var(--bg-inset); color: var(--text-muted);
            padding: 8px 6px; text-align: left; font-weight: 700;
            border-bottom: 1px solid var(--border-strong); position: sticky; top: 0;
        }}
        td {{
            padding: 7px 6px; border-bottom: 1px solid var(--border);
            color: var(--text-main);
        }}
        tr:hover td {{ background: var(--bg-card-hover); }}
        .tag-auto {{ background: rgba(250,140,22,0.15); color: #fa8c16; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 9.5px; }}
        .tag-manual {{ background: rgba(24,144,255,0.15); color: #1890ff; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 9.5px; }}

        .status-alert-box {{
            padding: 10px; border-radius: var(--radius-md); font-size: 11.5px; font-weight: 700;
            text-align: center; margin-top: 8px;
            background: rgba(0, 240, 255, 0.1); border: 1px solid var(--accent-primary); color: var(--accent-primary);
        }}
    </style>
</head>
<body>
    <!-- DOMAIN NAVIGATION TABS -->
    <nav class="domain-navbar">
        <a href="/" class="home-tab"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>Hub Inicial</a>
        {domain_nav_items}
    </nav>

    <!-- TOPBAR -->
    <header class="topbar">
        <div class="brand">
            <div class="brand-mark">{dom_icon}</div>
            <div class="brand-text">
                <h1>
                    <span>{dom_name.upper()}</span>
                    <span class="brand-badge">{dom_badge}</span>
                </h1>
                <div class="sub">{dom_tagline}</div>
            </div>
        </div>
        <div class="topbar-right">
            <div class="status-chip">
                <span class="status-dot"></span>
                <span id="system_status">VIGILÂNCIA ATIVA</span>
            </div>
            <a href="/{dom_id}/anotar" class="topbar-btn primary"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>Estúdio CVAT ({dom_name.split('&')[0].strip()})</a>
            <a href="/{dom_id}/sobre" class="topbar-btn"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>Documentação</a>
        </div>
    </header>

    <!-- MAIN GRID -->
    <div class="grid">
        <!-- LEFT COLUMN: CONTROLS & SCENE SEMANTICS -->
        <div class="col-stack">
            <!-- Fonte de Vídeo -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px; margin-right:4px;"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12" y2="20.01"/></svg>Fonte de Transmissão</span>
                </div>
                <div class="form-group">
                    <label class="form-label">Stream YouTube / Câmera IP:</label>
                    <input type="text" id="stream_url" class="text-input" value="{default_youtube_url}">
                </div>
                <button class="btn-action highlight" onclick="switchStream()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Conectar Câmera / Stream</button>
                <button class="btn-action" onclick="takeSnapshot()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>Capturar Snapshot HD</button>
                
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border);">
                    <label class="form-label">Analisar Foto Local:</label>
                    <input type="file" id="file_upload" accept="image/*,video/*" style="display:none;" onchange="uploadMedia(this)">
                    <button class="btn-action" onclick="document.getElementById('file_upload').click()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px; margin-right:4px;"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>Carregar Arquivo de Imagem</button>
                </div>
            </div>

            <!-- Semântica da Cena -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px; margin-right:4px;"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>Semântica da Cena</span>
                </div>
                {sem_boxes_html}
            </div>

            <!-- Alvo em Foco -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px; margin-right:4px;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>Alvo / Entidade em Foco</span>
                </div>
                {target_boxes_html}
                <div class="status-alert-box" id="reid_status_box">
                    RASTREAMENTO CINEMÁTICO ATIVO
                </div>
            </div>
        </div>

        <!-- CENTER COLUMN: VIDEO STREAM HUD -->
        <div class="col-stack">
            <div class="video-container">
                <img id="main_stream_img" class="video-stream" src="/video_feed?domain={dom_id}" alt="Stream ao Vivo">
            </div>
            <div class="video-controls">
                <div style="display: flex; gap: 14px; align-items: center;">
                    <span>● <strong id="stream_title_display">{default_stream_title}</strong></span>
                    <span style="color: var(--text-muted);">| Latência: <strong id="latency_display" style="color: #52c41a;">12 ms</strong></span>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <label><input type="checkbox" id="chk_night_vision" onchange="toggleNightVision()"> Visão Noturna</label>
                    <label><input type="range" id="conf_range" min="0.05" max="0.9" step="0.05" value="0.25" onchange="updateConfidence(this.value)"> Conf: <span id="conf_val">25%</span></label>
                </div>
            </div>
        </div>

        <!-- RIGHT COLUMN: REGISTRY & CATALOG -->
        <div class="col-stack">
            <div class="card">
                <div class="card-header">
                    <span class="card-title"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px; margin-right:4px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>{registry_title}</span>
                    <button class="topbar-btn" style="padding: 2px 6px; font-size: 10px;" onclick="refreshRegistry()"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg></button>
                </div>
                <div class="form-group">
                    <input type="text" id="filter_registry" class="text-input" placeholder="Filtrar registros por ID ou nome..." onkeyup="filterTable()">
                </div>
                <div class="table-wrap">
                    <table id="registry_table">
                        <thead>
                            <tr>
                                {table_headers_html}
                            </tr>
                        </thead>
                        <tbody id="registry_tbody">
                            <tr><td colspan="5" style="text-align:center; color: var(--text-muted);">Carregando registros...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        const CURRENT_DOMAIN = "{dom_id}";

        function switchStream() {{
            const url = document.getElementById('stream_url').value;
            fetch(`/api/${{CURRENT_DOMAIN}}/set_stream_source`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ source: 'LIVE', youtube_url: url }})
            }}).then(r => r.json()).then(data => {{
                document.getElementById('main_stream_img').src = `/video_feed?domain=${{CURRENT_DOMAIN}}&t=` + new Date().getTime();
            }});
        }}

        function takeSnapshot() {{
            window.open(`/api/${{CURRENT_DOMAIN}}/live_raw_snapshot.jpg?t=` + new Date().getTime(), '_blank');
        }}

        function uploadMedia(input) {{
            if (!input.files || !input.files[0]) return;
            const formData = new FormData();
            formData.append('file', input.files[0]);
            fetch(`/api/${{CURRENT_DOMAIN}}/analyze_image`, {{
                method: 'POST',
                body: formData
            }}).then(r => r.json()).then(data => {{
                alert(`Imagem analisada com sucesso! ${{data.targets ? data.targets.length : 0}} entidades detectadas.`);
                refreshRegistry();
            }});
        }}

        function updateConfidence(val) {{
            document.getElementById('conf_val').innerText = Math.round(val * 100) + '%';
        }}

        function toggleNightVision() {{
            const isNight = document.getElementById('chk_night_vision').checked;
            fetch(`/api/${{CURRENT_DOMAIN}}/toggle_night_vision`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ night_vision: isNight }})
            }});
        }}

        function refreshRegistry() {{
            fetch(`/api/${{CURRENT_DOMAIN}}/registry`).then(r => r.json()).then(data => {{
                const tbody = document.getElementById('registry_tbody');
                tbody.innerHTML = '';
                const items = data.items || [];
                if (items.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted);">Nenhum registro encontrado</td></tr>';
                    return;
                }}
                items.forEach(item => {{
                    const tr = document.createElement('tr');
                    const isAuto = item.origin === 'AUTO';
                    const tagClass = isAuto ? 'tag-auto' : 'tag-manual';
                    tr.innerHTML = `
                        <td><strong>${{item.id}}</strong></td>
                        <td>${{item.name}}</td>
                        <td>${{item.type}}</td>
                        <td><span class="${{tagClass}}">${{item.origin}}</span></td>
                        <td style="text-align:center;">${{item.sightings || 1}}</td>
                    `;
                    tbody.appendChild(tr);
                }});
            }});
        }}

        function filterTable() {{
            const query = document.getElementById('filter_registry').value.toLowerCase();
            const rows = document.querySelectorAll('#registry_tbody tr');
            rows.forEach(r => {{
                r.style.display = r.innerText.toLowerCase().includes(query) ? '' : 'none';
            }});
        }}

        // Telemetria Periódica
        setInterval(() => {{
            fetch(`/api/${{CURRENT_DOMAIN}}/live_telemetry`).then(r => r.json()).then(data => {{
                if (data.status) document.getElementById('system_status').innerText = data.status;
                if (data.latency_ms) document.getElementById('latency_display').innerText = data.latency_ms + ' ms';
                
                // Atualiza semântica se disponível
                if (data.semantica_cena) {{
                    for (const [k, v] of Object.entries(data.semantica_cena)) {{
                        const el = document.getElementById('sem_' + k);
                        if (el) el.innerText = v;
                    }}
                }}
                // Atualiza primeiro alvo
                if (data.targets && data.targets.length > 0) {{
                    const t = data.targets[0];
                    const idEl = document.getElementById('tgt_target_id');
                    if (idEl) idEl.innerText = t.target_id;
                    const modEl = document.getElementById('tgt_model');
                    if (modEl) modEl.innerText = t.model;
                    const crgEl = document.getElementById('tgt_cargo');
                    if (crgEl) crgEl.innerText = t.cargo;
                    const hdEl = document.getElementById('tgt_heading');
                    if (hdEl) hdEl.innerText = typeof t.heading === 'object' ? `${{t.heading.graus}}° (${{t.heading.cardeal}})` : t.heading;
                }}
            }}).catch(() => {{}});
        }}, 2000);

        // Carga inicial
        refreshRegistry();
    </script>
</body>
</html>
"""
