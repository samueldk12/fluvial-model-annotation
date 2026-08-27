# -*- coding: utf-8 -*-
"""Template HTML da página de documentação técnica /sobre com suporte aos 7 domínios de IA."""

from src.domains.domain_config import DOMAINS_CONFIG

def get_docs_html(domain_id="naval"):
    config = DOMAINS_CONFIG.get(domain_id, DOMAINS_CONFIG["naval"])
    dom_id = config["id"]
    dom_name = config["name"]
    dom_icon = config["icon"]
    dom_badge = config["badge"]

    # Constrói opções da barra de navegação entre domínios
    domain_nav_items = ""
    for d_k, d_v in DOMAINS_CONFIG.items():
        is_active = "active" if d_k == dom_id else ""
        domain_nav_items += f"""
        <a href="/{d_k}/sobre" class="domain-tab {is_active}" style="--tab-color: {d_v['accent_color']};">
            <span>{d_v['icon']}</span>
            <span>{d_v['name'].split('&')[0].strip()}</span>
        </a>
        """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentação Técnica &amp; Arquitetura — {dom_icon} {dom_name}</title>
    <style>
        :root {{
            --bg-canvas: #06080b;
            --bg-card: #0d1117;
            --bg-card-hover: #131822;
            --bg-inset: #090c10;
            --border: #1b222d;
            --border-strong: #283344;
            --accent-primary: {config['accent_color']};
            --accent-glow: {config['accent_rgba']};
            --text-main: #e6edf3;
            --text-muted: #8b949e;
            --text-faint: #484f58;
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            --font-mono: 'Cascadia Mono', Consolas, 'Liberation Mono', monospace;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-canvas);
            color: var(--text-main);
            font-family: var(--font-sans);
            font-size: 14px;
            line-height: 1.6;
            padding: 20px;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            max-width: 1140px;
            margin: 0 auto;
        }}
        /* Navigation */
        .domain-navbar {{
            display: flex;
            align-items: center;
            gap: 6px;
            overflow-x: auto;
            padding: 8px 12px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .home-tab {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--border-strong);
            border-radius: 4px;
            color: #ffffff;
            text-decoration: none;
            font-size: 12px;
            font-weight: 700;
            margin-right: 8px;
            flex-shrink: 0;
        }}
        .domain-tab {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: var(--bg-inset);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text-muted);
            text-decoration: none;
            font-size: 11.5px;
            font-weight: 600;
            white-space: nowrap;
        }}
        .domain-tab.active {{
            background: rgba(255,255,255,0.04);
            color: #ffffff;
            border-color: var(--tab-color);
            box-shadow: 0 0 10px var(--accent-glow);
            font-weight: 700;
        }}

        .page {{
            display: grid;
            grid-template-columns: 240px 1fr;
            gap: 28px;
            align-items: start;
        }}
        .toc {{
            position: sticky;
            top: 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            font-size: 12.5px;
        }}
        .toc-title {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-muted);
            margin-bottom: 10px;
        }}
        .toc a {{
            display: block;
            color: var(--text-muted);
            text-decoration: none;
            padding: 5px 8px;
            border-radius: 4px;
            margin-bottom: 2px;
        }}
        .toc a:hover {{ color: var(--text-main); background: var(--bg-inset); }}

        .hero {{ margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }}
        .eyebrow {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--accent-primary);
            margin-bottom: 4px;
        }}
        .hero h1 {{ font-size: 22px; font-weight: 800; color: #ffffff; margin-bottom: 6px; }}
        .hero p {{ font-size: 13.5px; color: var(--text-muted); }}

        .nav-links {{ display: flex; gap: 10px; margin-top: 14px; }}
        .nav-link {{
            display: inline-flex; align-items: center; gap: 6px;
            padding: 6px 12px; border-radius: 4px;
            background: var(--bg-card); border: 1px solid var(--border);
            color: var(--text-main); text-decoration: none; font-size: 12px; font-weight: 600;
        }}
        .nav-link:hover {{ border-color: var(--accent-primary); background: var(--bg-card-hover); }}

        section {{ margin-bottom: 32px; }}
        section h2 {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
            border-bottom: 1px solid var(--border);
            padding-bottom: 6px;
            margin-bottom: 12px;
            display: flex; align-items: center; gap: 8px;
        }}
        section h2::before {{
            content: ''; display: inline-block; width: 4px; height: 14px; background: var(--accent-primary); border-radius: 2px;
        }}
        p {{ margin-bottom: 10px; color: var(--text-muted); }}
        ul, ol {{ padding-left: 20px; margin-bottom: 12px; color: var(--text-muted); }}
        li {{ margin-bottom: 4px; }}

        .card-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }}
        .card-box h3 {{ font-size: 13px; color: #ffffff; margin-bottom: 6px; }}

        table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 14px; }}
        th {{ background: var(--bg-inset); color: var(--text-muted); padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border-strong); }}
        td {{ padding: 8px 10px; border-bottom: 1px solid var(--border); color: var(--text-main); }}
        code {{ font-family: var(--font-mono); background: var(--bg-inset); padding: 2px 6px; border-radius: 4px; font-size: 11.5px; color: var(--accent-primary); }}
    </style>
</head>
<body>
    <div class="container">
        <!-- DOMAIN NAV -->
        <nav class="domain-navbar">
            <a href="/" class="home-tab">🏠 Hub Inicial</a>
            {domain_nav_items}
        </nav>

        <div class="page">
            <!-- TOC -->
            <aside class="toc">
                <div class="toc-title">Navegação Técnica</div>
                <a href="#visao-geral">1. Visão Geral</a>
                <a href="#pipeline-ia">2. Pipeline de IA &amp; YOLO</a>
                <a href="#semantica">3. Análise Semântica</a>
                <a href="#classes">4. Presets de Classes</a>
                <a href="#dataset-yolo">5. Estúdio &amp; Dataset YOLO</a>
                <a href="#hardware">6. Hardware &amp; DirectML</a>
            </aside>

            <!-- MAIN CONTENT -->
            <main>
                <div class="hero">
                    <div class="eyebrow">{dom_badge} &bull; ARQUITETURA DE VISÃO COMPUTACIONAL</div>
                    <h1>{dom_icon} {dom_name} — Especificação Técnica</h1>
                    <p>{config['tagline']}</p>
                    <div class="nav-links">
                        <a href="/{dom_id}" class="nav-link">📹 Abrir Monitoramento em Tempo Real</a>
                        <a href="/{dom_id}/anotar" class="nav-link">✏️ Abrir Estúdio CVAT</a>
                    </div>
                </div>

                <!-- 1. VISÃO GERAL -->
                <section id="visao-geral">
                    <h2>1. Visão Geral do Domínio</h2>
                    <p>
                        O módulo <strong>{dom_name}</strong> é projetado para operar com inferência de ultra baixa latência (&lt; 15 ms),
                        combinando redes neurais convolucionais e Vision Transformers para detecção de objetos, rastreamento cinemático,
                        segmentação espacial e análise semântica em tempo real.
                    </p>
                </section>

                <!-- 2. PIPELINE DE IA -->
                <section id="pipeline-ia">
                    <h2>2. Pipeline de IA &amp; Modelos Neurais</h2>
                    <div class="card-box">
                        <h3>Modelos Neurais Acoplados</h3>
                        <ul>
                            <li><strong>Detector Principal:</strong> Ultralytics YOLOv8 / YOLOv11 otimizado para inferência DirectML na GPU.</li>
                            <li><strong>Extrator de Features &amp; Re-ID:</strong> Embeddings de alta dimensionalidade para identificação e persistência temporal de alvos.</li>
                            <li><strong>Memória Espacial Cinemática:</strong> Estimador de velocidade, direção vetorial (rumo cardeal) e projeção de trajetórias a 5s e 10s.</li>
                        </ul>
                    </div>
                </section>

                <!-- 3. ANÁLISE SEMÂNTICA -->
                <section id="semantica">
                    <h2>3. Análise Semântica da Cena</h2>
                    <p>
                        A cada frame processado, o pipeline extrai indicadores quantitativos e qualitativos da cena:
                    </p>
                    <table>
                        <thead>
                            <tr>
                                <th>Indicador Semântico</th>
                                <th>Tipo de Medição</th>
                                <th>Ação no Sistema</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(f"<tr><td><code>{s['key']}</code></td><td>{s['label']}</td><td>Monitoramento contínuo &amp; Telemetria HUD</td></tr>" for s in config.get("semantics_keys", []))}
                        </tbody>
                    </table>
                </section>

                <!-- 4. CLASSES DE ANOTAÇÃO -->
                <section id="classes">
                    <h2>4. Presets de Classes para Anotação</h2>
                    <p>
                        O domínio possui classes pré-configuradas prontas para uso no estúdio de rotulagem:
                    </p>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nome da Classe</th>
                                <th>Cor Padrão</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(f"<tr><td>{c['id']}</td><td><code>{c['name']}</code></td><td><span style='display:inline-block; width:12px; height:12px; background:{c['color']}; border-radius:2px; vertical-align:middle; margin-right:6px;'></span>{c['color']}</td></tr>" for c in config.get("classes", []))}
                        </tbody>
                    </table>
                </section>

                <!-- 5. ESTÚDIO YOLO -->
                <section id="dataset-yolo">
                    <h2>5. Estúdio de Anotação &amp; Dataset YOLO</h2>
                    <p>
                        O Estúdio CVAT integrado permite rotulagem manual de caixas delimitadoras e polígonos de segmentação,
                        além de pré-anotação automática via <em>Active Learning</em>. Todos os datasets gerados são exportados no
                        formato padrão Ultralytics YOLO com <code>data.yaml</code>, divisão <code>train/val</code> e compactação <code>.ZIP</code>.
                    </p>
                </section>

                <!-- 6. HARDWARE -->
                <section id="hardware">
                    <h2>6. Aceleração de Hardware &amp; DirectML</h2>
                    <p>
                        A plataforma suporta aceleração nativa via PyTorch DirectML, permitindo execução de alto desempenho
                        em GPUs AMD Radeon, NVIDIA GeForce, Intel Arc e fallback em CPU com precisão FP16/FP32.
                    </p>
                </section>
            </main>
        </div>
    </div>
</body>
</html>
"""

DOCS_PAGE = get_docs_html("naval")
