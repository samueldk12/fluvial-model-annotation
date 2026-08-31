# -*- coding: utf-8 -*-
"""
Configurações Mestras dos 7 Domínios de Visão Computacional:
1. Naval & Aquático (naval)
2. Cidade Urbana & Trânsito (urbano)
3. Ambientes Fechados / Indoor (fechado)
4. Natureza & Vida Selvagem (natureza)
5. Objetos & Indústria / Varejo (objetos)
6. Tatuagens & Arte Corporal (tatuagens)
7. Digitais & Forense Biométrico (digitais)
"""

DOMAINS_CONFIG = {
    "naval": {
        "id": "naval",
        "name": "Naval & Aquático",
        "icon": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 20a2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1 2.4 2.4 0 0 1 2-1 2.4 2.4 0 0 1 2 1 2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1 2.4 2.4 0 0 1 2-1 2.4 2.4 0 0 1 2 1 2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1"/><path d="M4 18L3 12h18l-1 6"/><path d="M6 12V4h12v8"/><line x1="12" y1="4" x2="12" y2="1"/></svg>',
        "badge": "Porto & Marítimo",
        "tagline": "Segmentação de águas, tráfego hidroviário, identificação de embarcações e radares SAR.",
        "accent_color": "#00f0ff",
        "accent_rgba": "rgba(0, 240, 255, 0.15)",
        "default_stream_title": "Porto de Santos — Ao Vivo",
        "default_youtube_url": "https://www.youtube.com/watch?v=5BxqzvR6TgM",
        "target_singular": "Embarcação",
        "target_plural": "Embarcações",
        "registry_title": "Embarcações Cadastradas no Porto",
        "registry_columns": [
            {"key": "id", "label": "ID / IMO", "width": "110px"},
            {"key": "name", "label": "Nome / Identificação", "width": "140px"},
            {"key": "type", "label": "Tipo / Carga", "width": "120px"},
            {"key": "origin", "label": "Origem", "width": "75px"},
            {"key": "sightings", "label": "Visitas", "width": "60px"}
        ],
        "semantics_keys": [
            {"key": "cobertura_agua", "label": "Cobertura d'Água / Rio", "default": "Aguardando dados...", "color": "#00f0ff"},
            {"key": "margens_terra", "label": "Margens & Infraestrutura", "default": "Aguardando dados...", "color": "#c0d2e5"},
            {"key": "condicao", "label": "Navegabilidade", "default": "Aguardando dados...", "color": "#00e676"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Alvo", "default": "Aguardando dados..."},
            {"key": "model", "label": "Modelo / Tipo", "default": "Aguardando dados..."},
            {"key": "cargo", "label": "Categoria / Carga", "default": "Aguardando dados..."},
            {"key": "heading", "label": "Rumo Náutico", "default": "Aguardando dados..."}
        ],
        "classes": [
            {"id": 0, "name": "embarcacao", "color": "#00f0ff"},
            {"id": 1, "name": "navio_cargueiro", "color": "#1890ff"},
            {"id": 2, "name": "rebocador", "color": "#fa8c16"},
            {"id": 3, "name": "balsa", "color": "#52c41a"},
            {"id": 4, "name": "lancha", "color": "#722ed1"},
            {"id": 5, "name": "veleiro", "color": "#eb2f96"},
            {"id": 6, "name": "boia_sinalizacao", "color": "#fadb14"},
            {"id": 7, "name": "operador_porto", "color": "#ff4d4f"},
            {"id": 8, "name": "outro", "color": "#8c8c8c"}
        ],
        "models": [
            {"id": "gemini_vision_naval", "name": "Google Gemini Vision (Naval Grounding)", "framework": "Google Multimodal", "description": "Auto-rotulagem zero-shot com Google Gemini 1.5 Flash/Pro para embarcações e elementos aquáticos.", "is_gemini": True, "default_conf": 0.20},
            {"id": "ensemble_naval", "name": "Ensemble Naval Consensual (SAR + SixOpen + eWaSR)", "framework": "PyTorch / ONNX", "description": "Fusão multi-detector consensual para alta precisão em águas e portos.", "is_gemini": False, "default_conf": 0.18},
            {"id": "sixopen_y8naval", "name": "SixOpen Y8Naval (50 Classes Navais)", "framework": "ONNX", "description": "Detecção de cargueiros, rebocadores, lanchas, veleiros e botes.", "is_gemini": False, "default_conf": 0.20},
            {"id": "mewan2808_sar", "name": "MeWan2808 SAR Ship (Fluvial/Radar)", "framework": "YOLOv8", "description": "Especialista em imagens de radar SAR e águas agitadas.", "is_gemini": False, "default_conf": 0.20},
            {"id": "mayrajeo_marine", "name": "Mayrajeo Marine (Cais & Porto)", "framework": "YOLOv8", "description": "Especialista em atracação e cais portuário.", "is_gemini": False, "default_conf": 0.20},
            {"id": "yolo11n_marine", "name": "Ultralytics YOLO11n (Naval Edge)", "framework": "Ultralytics", "description": "Modelo ultra-leve para alta taxa de quadros.", "is_gemini": False, "default_conf": 0.25}
        ],
        "yolo_filter_classes": [8] # COCO boat
    },

    "urbano": {
        "id": "urbano",
        "name": "Cidade Urbana & Trânsito",
        "icon": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="9" y1="6" x2="9" y2="6.01"/><line x1="15" y1="6" x2="15" y2="6.01"/><line x1="9" y1="10" x2="9" y2="10.01"/><line x1="15" y1="10" x2="15" y2="10.01"/><line x1="9" y1="14" x2="9" y2="14.01"/><line x1="15" y1="14" x2="15" y2="14.01"/><line x1="9" y1="18" x2="15" y2="18"/></svg>',
        "badge": "Smart City & Vias",
        "tagline": "Monitoramento de tráfego, veículos, pedestres, semáforos, cruzamentos e segurança pública.",
        "accent_color": "#1890ff",
        "accent_rgba": "rgba(24, 144, 255, 0.15)",
        "default_stream_title": "Avenida Paulista / Centro Urbano — Câmera de Trânsito",
        "default_youtube_url": "https://www.youtube.com/watch?v=1-iS7LArMPA",
        "target_singular": "Veículo / Pedestre",
        "target_plural": "Veículos & Pedestres",
        "registry_title": "Veículos & Pedestres Registrados na Via",
        "registry_columns": [
            {"key": "id", "label": "ID / Placa", "width": "110px"},
            {"key": "name", "label": "Tipo / Descrição", "width": "140px"},
            {"key": "type", "label": "Categoria", "width": "120px"},
            {"key": "origin", "label": "Origem", "width": "75px"},
            {"key": "sightings", "label": "Passagens", "width": "60px"}
        ],
        "semantics_keys": [
            {"key": "densidade_trafego", "label": "Densidade da Via", "default": "Aguardando dados...", "color": "#fa8c16"},
            {"key": "fluxo_pedestres", "label": "Segurança de Pedestres", "default": "Aguardando dados...", "color": "#00e676"},
            {"key": "estado_semaforo", "label": "Status da Vias", "default": "Aguardando dados...", "color": "#1890ff"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Veículo", "default": "Aguardando dados..."},
            {"key": "model", "label": "Tipo / Modelo", "default": "Aguardando dados..."},
            {"key": "cargo", "label": "Faixa / Sentido", "default": "Aguardando dados..."},
            {"key": "heading", "label": "Velocidade Estimada", "default": "Aguardando dados..."}
        ],
        "classes": [
            {"id": 0, "name": "carro", "color": "#1890ff"},
            {"id": 1, "name": "caminhao", "color": "#fa8c16"},
            {"id": 2, "name": "onibus", "color": "#722ed1"},
            {"id": 3, "name": "motocicleta", "color": "#eb2f96"},
            {"id": 4, "name": "bicicleta", "color": "#13c2c2"},
            {"id": 5, "name": "pedestre", "color": "#52c41a"},
            {"id": 6, "name": "semaforo", "color": "#fadb14"},
            {"id": 7, "name": "faixa_pedestre", "color": "#ffffff"},
            {"id": 8, "name": "placa_transito", "color": "#ff4d4f"}
        ],
        "models": [
            {"id": "gemini_vision_urbano", "name": "Google Gemini Vision (Trânsito & Vias)", "framework": "Google Multimodal", "description": "Auto-rotulagem zero-shot com Gemini para veículos, pedestres e infraestrutura viária.", "is_gemini": True, "default_conf": 0.20},
            {"id": "urban_traffic_detector", "name": "YOLOv8 Urban Traffic Specialist", "framework": "Ultralytics", "description": "Especialista em tráfego urbano, semáforos, cruzamentos e vias rápidas.", "is_gemini": False, "default_conf": 0.22},
            {"id": "yolo11n_urban", "name": "Ultralytics YOLO11n (Smart City Edge)", "framework": "Ultralytics", "description": "Detector leve para câmeras de trânsito em tempo real.", "is_gemini": False, "default_conf": 0.25}
        ],
        "yolo_filter_classes": [0, 1, 2, 3, 5, 7, 9, 11] # person, bicycle, car, motorcycle, bus, truck, traffic light, stop sign
    },

    "fechado": {
        "id": "fechado",
        "name": "Ambientes Fechados & Indoor",
        "icon": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/><line x1="9" y1="9" x2="9" y2="9.01"/><line x1="9" y1="13" x2="9" y2="13.01"/><line x1="9" y1="17" x2="9" y2="17.01"/></svg>',
        "badge": "Indoor & Edifícios",
        "tagline": "Ocupação de salas, escritórios, lojas, armazéns, mobília, portas e segurança predial.",
        "accent_color": "#722ed1",
        "accent_rgba": "rgba(114, 46, 209, 0.15)",
        "default_stream_title": "Escritório & Hub Corporativo — Câmera Interna",
        "default_youtube_url": "https://www.youtube.com/watch?v=eJ7Z4_239FM",
        "target_singular": "Ocupante / Ativo",
        "target_plural": "Ocupantes & Ativos",
        "registry_title": "Ocupantes & Objetos Monitorados no Prédio",
        "registry_columns": [
            {"key": "id", "label": "ID / Tag", "width": "110px"},
            {"key": "name", "label": "Nome / Identificação", "width": "140px"},
            {"key": "type", "label": "Zona / Sala", "width": "120px"},
            {"key": "origin", "label": "Origem", "width": "75px"},
            {"key": "sightings", "label": "Presenças", "width": "60px"}
        ],
        "semantics_keys": [
            {"key": "taxa_ocupacao", "label": "Taxa de Ocupação", "default": "Aguardando dados...", "color": "#52c41a"},
            {"key": "estado_portas", "label": "Acessos & Portas", "default": "Aguardando dados...", "color": "#722ed1"},
            {"key": "seguranca_indoor", "label": "Segurança Predial", "default": "Aguardando dados...", "color": "#00e676"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Ocupante", "default": "Aguardando dados..."},
            {"key": "model", "label": "Postura / Estado", "default": "Aguardando dados..."},
            {"key": "cargo", "label": "Zona Interna", "default": "Aguardando dados..."},
            {"key": "heading", "label": "Tempo de Permanência", "default": "Aguardando dados..."}
        ],
        "classes": [
            {"id": 0, "name": "pessoa", "color": "#ff4d4f"},
            {"id": 1, "name": "cadeira", "color": "#1890ff"},
            {"id": 2, "name": "mesa_trabalho", "color": "#fa8c16"},
            {"id": 3, "name": "sofa", "color": "#722ed1"},
            {"id": 4, "name": "porta", "color": "#52c41a"},
            {"id": 5, "name": "janela", "color": "#13c2c2"},
            {"id": 6, "name": "laptop_monitor", "color": "#eb2f96"},
            {"id": 7, "name": "camera_seguranca", "color": "#fadb14"},
            {"id": 8, "name": "extintor", "color": "#ff7875"}
        ],
        "models": [
            {"id": "gemini_vision_fechado", "name": "Google Gemini Vision (Indoor & Escritório)", "framework": "Google Multimodal", "description": "Auto-rotulagem zero-shot com Gemini para salas, postos de trabalho e mobília.", "is_gemini": True, "default_conf": 0.20},
            {"id": "indoor_occupancy_detector", "name": "Indoor Occupancy & Asset Detector", "framework": "Ultralytics", "description": "Detecção de pessoas, postos de trabalho e equipamentos de segurança.", "is_gemini": False, "default_conf": 0.22},
            {"id": "yolo11n_indoor", "name": "Ultralytics YOLO11n (Indoor Edge)", "framework": "Ultralytics", "description": "Detector leve para segurança patrimonial e contagem de ocupação.", "is_gemini": False, "default_conf": 0.25}
        ],
        "yolo_filter_classes": [0, 56, 57, 59, 60, 62, 63, 64, 65, 66] # person, chair, couch, bed, dining table, tv, laptop, mouse, remote, keyboard
    },

    "natureza": {
        "id": "natureza",
        "name": "Natureza & Vida Selvagem",
        "icon": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 21 2c-1 4.5-1.5 6-2.6 11.7A7 7 0 0 1 11 20z"/><path d="M2 21c0-3 1.8-6 5-7"/></svg>',
        "badge": "Fauna & Ambiental",
        "tagline": "Monitoramento de animais silvestres, aves, cobertura florestal, rios e prevenção de focos de incêndio.",
        "accent_color": "#52c41a",
        "accent_rgba": "rgba(82, 196, 26, 0.15)",
        "default_stream_title": "Reserva Natural & Bebedouro Selvagem — Câmera de Trilha",
        "default_youtube_url": "https://www.youtube.com/watch?v=ydYDqZQpim8",
        "target_singular": "Espécime / Animal",
        "target_plural": "Espécimes & Aves",
        "registry_title": "Fauna Catalogada na Reserva",
        "registry_columns": [
            {"key": "id", "label": "ID do Espécime", "width": "110px"},
            {"key": "name", "label": "Espécie / Nome", "width": "140px"},
            {"key": "type", "label": "Família / Grupo", "width": "120px"},
            {"key": "origin", "label": "Origem", "width": "75px"},
            {"key": "sightings", "label": "Registros", "width": "60px"}
        ],
        "semantics_keys": [
            {"key": "cobertura_vegetal", "label": "Densidade de Vegetação", "default": "Aguardando dados...", "color": "#52c41a"},
            {"key": "indice_biodiversidade", "label": "Índice de Biodiversidade", "default": "Aguardando dados...", "color": "#13c2c2"},
            {"key": "alerta_ambiental", "label": "Alerta Ambiental", "default": "Aguardando dados...", "color": "#00e676"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Espécime", "default": "Aguardando dados..."},
            {"key": "model", "label": "Espécie Identificada", "default": "Aguardando dados..."},
            {"key": "cargo", "label": "Comportamento", "default": "Aguardando dados..."},
            {"key": "heading", "label": "Direção de Deslocamento", "default": "Aguardando dados..."}
        ],
        "classes": [
            {"id": 0, "name": "mamifero_silvestre", "color": "#fa8c16"},
            {"id": 1, "name": "ave_passaro", "color": "#1890ff"},
            {"id": 2, "name": "reptil", "color": "#52c41a"},
            {"id": 3, "name": "arvore_copa", "color": "#389e0d"},
            {"id": 4, "name": "rio_corpo_dagua", "color": "#00f0ff"},
            {"id": 5, "name": "fogo_foco_calor", "color": "#ff4d4f"},
            {"id": 6, "name": "fumaca", "color": "#8c8c8c"},
            {"id": 7, "name": "pegada_rastro", "color": "#d48806"},
            {"id": 8, "name": "fauna_outro", "color": "#722ed1"}
        ],
        "models": [
            {"id": "gemini_vision_natureza", "name": "Google Gemini Vision (Fauna & Biomas)", "framework": "Google Multimodal", "description": "Reconhecimento zero-shot de espécies animais e flora nativa com Gemini.", "is_gemini": True, "default_conf": 0.20},
            {"id": "wildlife_nature_detector", "name": "Wildlife & Forestry YOLO Detector", "framework": "Ultralytics", "description": "Detector treinado para mamíferos silvestres, aves e focos de calor.", "is_gemini": False, "default_conf": 0.22},
            {"id": "yolo11n_natureza", "name": "Ultralytics YOLO11n (Fauna Edge)", "framework": "Ultralytics", "description": "Modelo rápido para armadilhas fotográficas e monitoramento ambiental.", "is_gemini": False, "default_conf": 0.25}
        ],
        "yolo_filter_classes": [14, 15, 16, 17, 18, 19, 20, 21, 22, 23] # bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe
    },

    "objetos": {
        "id": "objetos",
        "name": "Objetos & Indústria / Varejo",
        "icon": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>',
        "badge": "Indústria & Varejo",
        "tagline": "Reconhecimento de objetos gerais, contagem de estoque, ferramentas, esteiras e controle de qualidade.",
        "accent_color": "#fa8c16",
        "accent_rgba": "rgba(250, 140, 22, 0.15)",
        "default_stream_title": "Linha de Produção & Triagem de Pacotes — Câmera Industrial",
        "default_youtube_url": "https://www.youtube.com/watch?v=LXb3EKWsInQ",
        "target_singular": "Item / Objeto",
        "target_plural": "Itens & Produtos",
        "registry_title": "Itens e Produtos Catalogados no Inventário",
        "registry_columns": [
            {"key": "id", "label": "SKU / Código", "width": "110px"},
            {"key": "name", "label": "Descrição do Item", "width": "140px"},
            {"key": "type", "label": "Categoria / Linha", "width": "120px"},
            {"key": "origin", "label": "Origem", "width": "75px"},
            {"key": "sightings", "label": "Contagem", "width": "60px"}
        ],
        "semantics_keys": [
            {"key": "contagem_esteira", "label": "Taxa de Fluxo (Itens/min)", "default": "Aguardando dados...", "color": "#fa8c16"},
            {"key": "conformidade_qualidade", "label": "Controle de Qualidade", "default": "Aguardando dados...", "color": "#52c41a"},
            {"key": "diversidade_estoque", "label": "Diversidade de Categorias", "default": "Aguardando dados...", "color": "#1890ff"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "SKU do Objeto", "default": "Aguardando dados..."},
            {"key": "model", "label": "Tipo de Embalagem", "default": "Aguardando dados..."},
            {"key": "cargo", "label": "Dimensões Estimadas", "default": "Aguardando dados..."},
            {"key": "heading", "label": "Status de Inspeção", "default": "Aguardando dados..."}
        ],
        "classes": [
            {"id": 0, "name": "caixa_embalagem", "color": "#fa8c16"},
            {"id": 1, "name": "ferramenta", "color": "#1890ff"},
            {"id": 2, "name": "garrafa_frasco", "color": "#13c2c2"},
            {"id": 3, "name": "pacote_produto", "color": "#52c41a"},
            {"id": 4, "name": "componente_eletronico", "color": "#722ed1"},
            {"id": 5, "name": "defeito_superficie", "color": "#ff4d4f"},
            {"id": 6, "name": "codigo_barras_etiqueta", "color": "#fadb14"},
            {"id": 7, "name": "objeto_geral", "color": "#d9d9d9"}
        ],
        "models": [
            {"id": "gemini_vision_objetos", "name": "Google Gemini Vision (Indústria & EPI)", "framework": "Google Multimodal", "description": "Inspeção de conformidade, ferramentas e embalagens com Gemini.", "is_gemini": True, "default_conf": 0.20},
            {"id": "industrial_ppe_detector", "name": "Industrial Safety & PPE Detector", "framework": "Ultralytics", "description": "Detecção de capacetes, coletes, caixas e empilhadeiras em linha de produção.", "is_gemini": False, "default_conf": 0.22},
            {"id": "yolo11n_objetos", "name": "Ultralytics YOLO11n (Industrial Edge)", "framework": "Ultralytics", "description": "Inspeção e contagem ultra-rápida de pacotes em esteiras.", "is_gemini": False, "default_conf": 0.25}
        ],
        "yolo_filter_classes": [24, 25, 26, 28, 39, 41, 42, 43, 44, 45, 67, 73, 76, 77, 79] # backpack, umbrella, handbag, suitcase, bottle, cup, fork, knife, spoon, bowl, cell phone, book, scissors, teddy bear, toothbrush
    },

    "tatuagens": {
        "id": "tatuagens",
        "name": "Tatuagens & Arte Corporal",
        "icon": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.563-2.512 5.563-5.563C22 6.5 17.5 2 12 2z"/></svg>',
        "badge": "Biometria & Arte Corporal",
        "tagline": "Segmentação de tatuagens em pele, classificação de estilos artísticos, mapeamento anatômico e Re-ID.",
        "accent_color": "#eb2f96",
        "accent_rgba": "rgba(235, 47, 150, 0.15)",
        "default_stream_title": "Estúdio & Inspeção de Arte Corporal — Câmera Macro",
        "default_youtube_url": "https://www.youtube.com/watch?v=vVj4J68uBvo",
        "target_singular": "Tatuagem / Marca",
        "target_plural": "Tatuagens & Marcas",
        "registry_title": "Catálogo Biométrico de Tatuagens",
        "registry_columns": [
            {"key": "id", "label": "ID da Tatuagem", "width": "110px"},
            {"key": "name", "label": "Estilo Artístico", "width": "140px"},
            {"key": "type", "label": "Região do Corpo", "width": "120px"},
            {"key": "origin", "label": "Origem", "width": "75px"},
            {"key": "sightings", "label": "Correspondências", "width": "60px"}
        ],
        "semantics_keys": [
            {"key": "cobertura_pele", "label": "Área de Cobertura Dérmica", "default": "Aguardando dados...", "color": "#eb2f96"},
            {"key": "complexidade_traco", "label": "Complexidade do Traço", "default": "Aguardando dados...", "color": "#722ed1"},
            {"key": "estilo_dominante", "label": "Estilo Predominante", "default": "Aguardando dados...", "color": "#fa8c16"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID da Marca", "default": "Aguardando dados..."},
            {"key": "model", "label": "Classificação de Estilo", "default": "Aguardando dados..."},
            {"key": "cargo", "label": "Localização Anatômica", "default": "Aguardando dados..."},
            {"key": "heading", "label": "Assinatura Biométrica", "default": "Aguardando dados..."}
        ],
        "classes": [
            {"id": 0, "name": "tatuagem_tribal", "color": "#000000"},
            {"id": 1, "name": "tatuagem_oriental", "color": "#eb2f96"},
            {"id": 2, "name": "tatuagem_realismo", "color": "#1890ff"},
            {"id": 3, "name": "tatuagem_oldschool", "color": "#fa8c16"},
            {"id": 4, "name": "tatuagem_blackwork", "color": "#722ed1"},
            {"id": 5, "name": "tatuagem_fineline", "color": "#13c2c2"},
            {"id": 6, "name": "escrita_lettering", "color": "#52c41a"},
            {"id": 7, "name": "braco_pele", "color": "#ffc069"},
            {"id": 8, "name": "costas_pele", "color": "#d48806"},
            {"id": 9, "name": "perna_pele", "color": "#adc6ff"}
        ],
        "models": [
            {"id": "gemini_vision_tatuagens", "name": "Google Gemini Vision (Tatuagens & Arte)", "framework": "Google Multimodal", "description": "Segmentação e descrição semântica de arte corporal com Gemini.", "is_gemini": True, "default_conf": 0.20},
            {"id": "tattoo_feature_detector", "name": "Tattoo Segmentation & Feature Net", "framework": "PyTorch", "description": "Detector de traços, preenchimentos e contornos de tatuagens.", "is_gemini": False, "default_conf": 0.22}
        ],
        "yolo_filter_classes": [0] # person
    },

    "digitais": {
        "id": "digitais",
        "name": "Digitais & Forense Biométrico",
        "icon": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        "badge": "Papiloscopia & Forense",
        "tagline": "Extração de cristas e minúcias (bifurcações/terminações), classificação de padrões (Arco, Presilha, Verticilo) e documentos.",
        "accent_color": "#13c2c2",
        "accent_rgba": "rgba(19, 194, 194, 0.15)",
        "default_stream_title": "Scanner Papiloscópico & Análise Forense — Câmera Laboratório",
        "default_youtube_url": "https://www.youtube.com/watch?v=v64KOxKVLVg",
        "target_singular": "Impressão / Minúcia",
        "target_plural": "Impressões & Documentos",
        "registry_title": "Base Biométrica Papiloscópica & Documental",
        "registry_columns": [
            {"key": "id", "label": "ID Papiloscópico", "width": "110px"},
            {"key": "name", "label": "Tipo de Padrão", "width": "140px"},
            {"key": "type", "label": "Dedo / Documento", "width": "120px"},
            {"key": "origin", "label": "Origem", "width": "75px"},
            {"key": "sightings", "label": "Comparações", "width": "60px"}
        ],
        "semantics_keys": [
            {"key": "clareza_cristas", "label": "Nitidez das Cristas (Ridge)", "default": "Aguardando dados...", "color": "#13c2c2"},
            {"key": "contagem_minucias", "label": "Minúcias de Galton Detectadas", "default": "Aguardando dados...", "color": "#52c41a"},
            {"key": "padrao_primario", "label": "Classificação Henry/Vucetich", "default": "Aguardando dados...", "color": "#00f0ff"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID Biométrico", "default": "Aguardando dados..."},
            {"key": "model", "label": "Padrão Papilar", "default": "Aguardando dados..."},
            {"key": "cargo", "label": "Dedo / Posição", "default": "Aguardando dados..."},
            {"key": "heading", "label": "Score de Match AFIS", "default": "Aguardando dados..."}
        ],
        "classes": [
            {"id": 0, "name": "impressao_digital", "color": "#13c2c2"},
            {"id": 1, "name": "verticilo_whorl", "color": "#00f0ff"},
            {"id": 2, "name": "presilha_loop", "color": "#1890ff"},
            {"id": 3, "name": "arco_arch", "color": "#52c41a"},
            {"id": 4, "name": "minucia_bifurcacao", "color": "#fa8c16"},
            {"id": 5, "name": "minucia_terminacao", "color": "#ff4d4f"},
            {"id": 6, "name": "ponto_delta", "color": "#fadb14"},
            {"id": 7, "name": "nucleo_core", "color": "#eb2f96"},
            {"id": 8, "name": "documento_registro", "color": "#722ed1"}
        ],
        "models": [
            {"id": "gemini_vision_digitais", "name": "Google Gemini Vision (Papiloscopia & Cristas)", "framework": "Google Multimodal", "description": "Detecção assistida de deltas, núcleos e minúcias com Gemini.", "is_gemini": True, "default_conf": 0.20},
            {"id": "papillary_minutiae_detector", "name": "AFIS Papillary Minutiae Extractor", "framework": "OpenCV / PyTorch", "description": "Extração e contagem de cristas e bifurcações papilares.", "is_gemini": False, "default_conf": 0.20}
        ],
        "yolo_filter_classes": []
    }
}
