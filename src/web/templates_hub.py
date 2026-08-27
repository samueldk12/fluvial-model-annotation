# -*- coding: utf-8 -*-
"""Template HTML da Página Inicial (Portal Geral / Hub Multi-Domínio de Visão Computacional)."""

HUB_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Vision Hub — Plataforma Multi-Domínio de Visão Computacional &amp; IA</title>
    <style>
        :root {
            --bg-canvas: #06080b;
            --bg-card: #0d1117;
            --bg-card-hover: #131822;
            --bg-inset: #090c10;
            --border: #1b222d;
            --border-strong: #283344;
            --accent-cyan: #00f0ff;
            --accent-blue: #1890ff;
            --accent-purple: #722ed1;
            --accent-green: #52c41a;
            --accent-orange: #fa8c16;
            --accent-pink: #eb2f96;
            --accent-teal: #13c2c2;
            --accent-red: #ff4d4f;
            --text-main: #e6edf3;
            --text-muted: #8b949e;
            --text-faint: #484f58;
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            --font-mono: 'Cascadia Mono', Consolas, 'Liberation Mono', monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: var(--bg-canvas);
            color: var(--text-main);
            font-family: var(--font-sans);
            padding: 24px;
            -webkit-font-smoothing: antialiased;
            min-height: 100vh;
        }

        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-canvas); }
        ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }

        .container {
            max-width: 1380px;
            margin: 0 auto;
        }

        /* ===== TOPBAR ===== */
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .brand-mark {
            width: 44px;
            height: 44px;
            border-radius: var(--radius-md);
            background: linear-gradient(135deg, #1890ff, #722ed1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 16px rgba(24,144,255,0.4);
        }
        .brand-text h1 {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #ffffff, #00f0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-text .sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .topbar-meta {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: var(--radius-sm);
            background: var(--bg-inset);
            border: 1px solid var(--border-strong);
            font-size: 11.5px;
            font-weight: 600;
        }
        .chip.pulse .dot {
            width: 8px; height: 8px; border-radius: 50%; background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse-dot 2s infinite ease-in-out;
        }
        @keyframes pulse-dot {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.6; }
        }

        /* ===== HERO BANNER ===== */
        .hero {
            background: linear-gradient(180deg, #101620 0%, #0a0e14 100%);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 32px;
            margin-bottom: 28px;
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: -50%; right: -10%;
            width: 400px; height: 400px;
            background: radial-gradient(circle, rgba(0,240,255,0.08) 0%, transparent 70%);
            pointer-events: none;
        }
        .hero-title {
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 8px;
        }
        .hero-desc {
            font-size: 14px;
            color: var(--text-muted);
            max-width: 860px;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .hero-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
        }
        .stat-card {
            background: var(--bg-inset);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 12px 18px;
            min-width: 180px;
        }
        .stat-num {
            font-size: 20px;
            font-weight: 800;
            font-family: var(--font-mono);
            color: var(--accent-cyan);
        }
        .stat-lbl {
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 2px;
        }

        /* ===== DOMAINS GRID ===== */
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .section-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-title::before {
            content: '';
            display: inline-block;
            width: 4px;
            height: 16px;
            background: var(--accent-cyan);
            border-radius: 2px;
        }

        .domains-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
            margin-bottom: 36px;
        }

        .domain-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.25s ease;
            position: relative;
            overflow: hidden;
        }
        .domain-card:hover {
            transform: translateY(-4px);
            background: var(--bg-card-hover);
            border-color: var(--domain-color);
            box-shadow: 0 8px 28px rgba(0,0,0,0.5), 0 0 16px var(--domain-glow);
        }
        .domain-card-top {
            display: flex;
            align-items: flex-start;
            gap: 14px;
            margin-bottom: 14px;
        }
        .domain-icon {
            font-size: 32px;
            width: 52px;
            height: 52px;
            background: var(--bg-inset);
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .domain-info h2 {
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }
        .domain-badge {
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 8px;
            border-radius: 4px;
            background: var(--domain-glow);
            color: var(--domain-color);
            border: 1px solid var(--domain-color);
        }
        .domain-desc {
            font-size: 12.5px;
            color: var(--text-muted);
            line-height: 1.5;
            margin-bottom: 16px;
            flex-grow: 1;
        }

        .domain-features {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 20px;
        }
        .feat-tag {
            font-size: 10.5px;
            padding: 3px 8px;
            background: var(--bg-inset);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: #c9d1d9;
            font-family: var(--font-mono);
        }

        .domain-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            padding-top: 14px;
            border-top: 1px solid var(--border);
        }
        .domain-actions .btn-full {
            grid-column: span 2;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 600;
            border-radius: var(--radius-sm);
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s ease;
            text-align: center;
        }
        .btn-primary {
            background: var(--domain-color);
            color: #000000;
            border: 1px solid var(--domain-color);
            font-weight: 700;
        }
        .btn-primary:hover {
            filter: brightness(1.15);
            box-shadow: 0 0 12px var(--domain-color);
        }
        .btn-outline {
            background: var(--bg-inset);
            color: var(--text-main);
            border: 1px solid var(--border-strong);
        }
        .btn-outline:hover {
            background: var(--bg-card-hover);
            border-color: var(--domain-color);
            color: #ffffff;
        }

        /* ===== FOOTER ===== */
        .footer {
            text-align: center;
            padding: 24px;
            font-size: 12px;
            color: var(--text-faint);
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- TOPBAR -->
        <header class="topbar">
            <div class="brand">
                <div class="brand-mark">🧠</div>
                <div class="brand-text">
                    <h1>AI VISION HUB — PLATAFORMA MULTI-DOMÍNIO</h1>
                    <div class="sub">Suíte Unificada de Percepção Visual, Análise Semântica, Telemetria &amp; Estúdios de Anotação YOLO</div>
                </div>
            </div>
            <div class="topbar-meta">
                <div class="chip pulse">
                    <span class="dot"></span>
                    <span>7 DOMÍNIOS ONLINE</span>
                </div>
                <div class="chip" style="font-family: var(--font-mono); color: var(--accent-cyan);">
                    ● GPU: DirectML / PyTorch
                </div>
            </div>
        </header>

        <!-- HERO -->
        <section class="hero">
            <h2 class="hero-title">Central Inteligente de Visão Computacional Especializada</h2>
            <p class="hero-desc">
                Selecione um dos 7 domínios abaixo para acessar o painel de monitoramento em tempo real com telemetria cinemática,
                o estúdio de anotação de datasets YOLO/CVAT para treinamento de modelos de IA, ou a documentação técnica detalhada.
            </p>
            <div class="hero-stats">
                <div class="stat-card">
                    <div class="stat-num">7</div>
                    <div class="stat-lbl">Domínios Ativos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-num">YOLOv8 / v11</div>
                    <div class="stat-lbl">Motores Neurais</div>
                </div>
                <div class="stat-card">
                    <div class="stat-num">60+ Classes</div>
                    <div class="stat-lbl">Presets Prontos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-num">&lt; 15 ms</div>
                    <div class="stat-lbl">Latência Média</div>
                </div>
            </div>
        </section>

        <!-- DOMAINS GRID -->
        <div class="section-header">
            <div class="section-title">Domínios de Visão Computacional Disponíveis</div>
        </div>

        <div class="domains-grid">
            <!-- 1. NAVAL -->
            <div class="domain-card" style="--domain-color: #00f0ff; --domain-glow: rgba(0, 240, 255, 0.15);">
                <div>
                    <div class="domain-card-top">
                        <div class="domain-icon">🚢</div>
                        <div class="domain-info">
                            <h2>Naval &amp; Aquático</h2>
                            <span class="domain-badge">Porto de Santos &amp; SAR</span>
                        </div>
                    </div>
                    <p class="domain-desc">
                        Segmentação de superfície d'água (eWaSR), tráfego no canal portuário, identificação de embarcações, rumo náutico e radares SAR.
                    </p>
                    <div class="domain-features">
                        <span class="feat-tag">Navios &amp; Balsas</span>
                        <span class="feat-tag">eWaSR Water Seg</span>
                        <span class="feat-tag">Rumo Náutico</span>
                        <span class="feat-tag">Re-ID do Porto</span>
                    </div>
                </div>
                <div class="domain-actions">
                    <a href="/naval" class="btn btn-primary btn-full">📹 Acessar Monitoramento Naval</a>
                    <a href="/naval/anotar" class="btn btn-outline">✏️ Estúdio Anotação</a>
                    <a href="/naval/sobre" class="btn btn-outline">📖 Documentação</a>
                </div>
            </div>

            <!-- 2. URBANO -->
            <div class="domain-card" style="--domain-color: #1890ff; --domain-glow: rgba(24, 144, 255, 0.15);">
                <div>
                    <div class="domain-card-top">
                        <div class="domain-icon">🏙️</div>
                        <div class="domain-info">
                            <h2>Cidade Urbana &amp; Trânsito</h2>
                            <span class="domain-badge">Smart City &amp; Vias</span>
                        </div>
                    </div>
                    <p class="domain-desc">
                        Monitoramento de fluxo veicular, carros, ônibus, caminhões, motos, ciclistas, segurança de pedestres e cruzamentos semafóricos.
                    </p>
                    <div class="domain-features">
                        <span class="feat-tag">Fluxo de Tráfego</span>
                        <span class="feat-tag">Pedestres &amp; Faixas</span>
                        <span class="feat-tag">Velocidade Estimada</span>
                        <span class="feat-tag">LPR &amp; Placas</span>
                    </div>
                </div>
                <div class="domain-actions">
                    <a href="/urbano" class="btn btn-primary btn-full">📹 Acessar Monitoramento Urbano</a>
                    <a href="/urbano/anotar" class="btn btn-outline">✏️ Estúdio Anotação</a>
                    <a href="/urbano/sobre" class="btn btn-outline">📖 Documentação</a>
                </div>
            </div>

            <!-- 3. FECHADO -->
            <div class="domain-card" style="--domain-color: #722ed1; --domain-glow: rgba(114, 46, 209, 0.15);">
                <div>
                    <div class="domain-card-top">
                        <div class="domain-icon">🏢</div>
                        <div class="domain-info">
                            <h2>Ambientes Fechados (Indoor)</h2>
                            <span class="domain-badge">Ocupação &amp; Escritórios</span>
                        </div>
                    </div>
                    <p class="domain-desc">
                        Ocupação de salas, rastreamento de pessoas, estações de trabalho, mobília, controle de portas/janelas e segurança predial.
                    </p>
                    <div class="domain-features">
                        <span class="feat-tag">Taxa de Ocupação</span>
                        <span class="feat-tag">Portas &amp; Acessos</span>
                        <span class="feat-tag">Postura &amp; Quedas</span>
                        <span class="feat-tag">Controle Patrimonial</span>
                    </div>
                </div>
                <div class="domain-actions">
                    <a href="/fechado" class="btn btn-primary btn-full">📹 Acessar Monitoramento Indoor</a>
                    <a href="/fechado/anotar" class="btn btn-outline">✏️ Estúdio Anotação</a>
                    <a href="/fechado/sobre" class="btn btn-outline">📖 Documentação</a>
                </div>
            </div>

            <!-- 4. NATUREZA -->
            <div class="domain-card" style="--domain-color: #52c41a; --domain-glow: rgba(82, 196, 26, 0.15);">
                <div>
                    <div class="domain-card-top">
                        <div class="domain-icon">🌿</div>
                        <div class="domain-info">
                            <h2>Natureza &amp; Vida Selvagem</h2>
                            <span class="domain-badge">Fauna &amp; Ambiental</span>
                        </div>
                    </div>
                    <p class="domain-desc">
                        Identificação de fauna silvestre, aves, répteis, densidade de cobertura florestal, rios e alerta precoce de queimadas/fumaça.
                    </p>
                    <div class="domain-features">
                        <span class="feat-tag">Espécies Silvestres</span>
                        <span class="feat-tag">Câmeras de Trilha</span>
                        <span class="feat-tag">Copa &amp; Vegetação</span>
                        <span class="feat-tag">Detecção de Fogo</span>
                    </div>
                </div>
                <div class="domain-actions">
                    <a href="/natureza" class="btn btn-primary btn-full">📹 Acessar Monitoramento Natureza</a>
                    <a href="/natureza/anotar" class="btn btn-outline">✏️ Estúdio Anotação</a>
                    <a href="/natureza/sobre" class="btn btn-outline">📖 Documentação</a>
                </div>
            </div>

            <!-- 5. OBJETOS -->
            <div class="domain-card" style="--domain-color: #fa8c16; --domain-glow: rgba(250, 140, 22, 0.15);">
                <div>
                    <div class="domain-card-top">
                        <div class="domain-icon">📦</div>
                        <div class="domain-info">
                            <h2>Objetos &amp; Varejo / Indústria</h2>
                            <span class="domain-badge">Indústria &amp; Estoque</span>
                        </div>
                    </div>
                    <p class="domain-desc">
                        Detecção e contagem de itens em esteiras, caixas, ferramentas, pacotes, código de barras e controle de defeitos de qualidade.
                    </p>
                    <div class="domain-features">
                        <span class="feat-tag">Contagem de Peças</span>
                        <span class="feat-tag">Esteiras &amp; SKUs</span>
                        <span class="feat-tag">Controle de Qualidade</span>
                        <span class="feat-tag">Dimensões BBox</span>
                    </div>
                </div>
                <div class="domain-actions">
                    <a href="/objetos" class="btn btn-primary btn-full">📹 Acessar Monitoramento Objetos</a>
                    <a href="/objetos/anotar" class="btn btn-outline">✏️ Estúdio Anotação</a>
                    <a href="/objetos/sobre" class="btn btn-outline">📖 Documentação</a>
                </div>
            </div>

            <!-- 6. TATUAGENS -->
            <div class="domain-card" style="--domain-color: #eb2f96; --domain-glow: rgba(235, 47, 150, 0.15);">
                <div>
                    <div class="domain-card-top">
                        <div class="domain-icon">🎨</div>
                        <div class="domain-info">
                            <h2>Tatuagens &amp; Arte Corporal</h2>
                            <span class="domain-badge">Biometria &amp; Estilos</span>
                        </div>
                    </div>
                    <p class="domain-desc">
                        Segmentação dérmica, classificação estilística (Tribal, Oriental, Realismo, Old School, Blackwork), localização corporal e Re-ID.
                    </p>
                    <div class="domain-features">
                        <span class="feat-tag">Classificação de Estilo</span>
                        <span class="feat-tag">Mapeamento Corporal</span>
                        <span class="feat-tag">Complexidade do Traço</span>
                        <span class="feat-tag">Busca Biométrica</span>
                    </div>
                </div>
                <div class="domain-actions">
                    <a href="/tatuagens" class="btn btn-primary btn-full">📹 Acessar Estúdio Tatuagens</a>
                    <a href="/tatuagens/anotar" class="btn btn-outline">✏️ Estúdio Anotação</a>
                    <a href="/tatuagens/sobre" class="btn btn-outline">📖 Documentação</a>
                </div>
            </div>

            <!-- 7. DIGITAIS -->
            <div class="domain-card" style="--domain-color: #13c2c2; --domain-glow: rgba(19, 194, 194, 0.15);">
                <div>
                    <div class="domain-card-top">
                        <div class="domain-icon">🔍</div>
                        <div class="domain-info">
                            <h2>Digitais &amp; Forense Biométrico</h2>
                            <span class="domain-badge">Papiloscopia &amp; AFIS</span>
                        </div>
                    </div>
                    <p class="domain-desc">
                        Extração de cristas papilares, minúcias de Galton (bifurcações e terminações), classificação de padrões (Arco, Presilha, Verticilo) e documentos.
                    </p>
                    <div class="domain-features">
                        <span class="feat-tag">Minúcias de Galton</span>
                        <span class="feat-tag">Arco / Presilha / Verticilo</span>
                        <span class="feat-tag">Nitidez de Cristas</span>
                        <span class="feat-tag">Perícia Documental</span>
                    </div>
                </div>
                <div class="domain-actions">
                    <a href="/digitais" class="btn btn-primary btn-full">📹 Acessar Análise Papiloscópica</a>
                    <a href="/digitais/anotar" class="btn btn-outline">✏️ Estúdio Anotação</a>
                    <a href="/digitais/sobre" class="btn btn-outline">📖 Documentação</a>
                </div>
            </div>
        </div>

        <footer class="footer">
            AI Vision Hub &bull; Plataforma Multi-Domínio com PyTorch DirectML, YOLOv8/v11 e Estúdios CVAT de Anotação &bull; 2026
        </footer>
    </div>
</body>
</html>
"""
