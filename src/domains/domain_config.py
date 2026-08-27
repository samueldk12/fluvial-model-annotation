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
        "icon": "🚢",
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
            {"key": "cobertura_agua", "label": "Cobertura d'Água / Rio", "default": "42.5%", "color": "#00f0ff"},
            {"key": "margens_terra", "label": "Margens & Infraestrutura", "default": "57.5%", "color": "#c0d2e5"},
            {"key": "condicao", "label": "Navegabilidade", "default": "ÁGUAS CALMAS / SEGURA", "color": "#00e676"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Alvo", "default": "EMB-2026-01"},
            {"key": "model", "label": "Modelo / Tipo", "default": "Navio Porta-Contêineres"},
            {"key": "cargo", "label": "Categoria / Carga", "default": "Carga Geral / Contêiner"},
            {"key": "heading", "label": "Rumo Náutico", "default": "184° (Sul-Sudoeste)"}
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
        "yolo_filter_classes": [8] # COCO boat
    },

    "urbano": {
        "id": "urbano",
        "name": "Cidade Urbana & Trânsito",
        "icon": "🏙️",
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
            {"key": "densidade_trafego", "label": "Densidade da Via", "default": "MODERADA (68%)", "color": "#fa8c16"},
            {"key": "fluxo_pedestres", "label": "Segurança de Pedestres", "default": "FAIXA SEGURA (0 Alertas)", "color": "#00e676"},
            {"key": "estado_semaforo", "label": "Status da Vias", "default": "FLUXO CONTÍNUO (Verde)", "color": "#1890ff"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Veículo", "default": "VEI-SP-8942"},
            {"key": "model", "label": "Tipo / Modelo", "default": "Automóvel Sedan / SUV"},
            {"key": "cargo", "label": "Faixa / Sentido", "default": "Faixa 2 (Norte -> Sul)"},
            {"key": "heading", "label": "Velocidade Estimada", "default": "48.2 km/h (Permitida)"}
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
        "yolo_filter_classes": [0, 1, 2, 3, 5, 7, 9, 11] # person, bicycle, car, motorcycle, bus, truck, traffic light, stop sign
    },

    "fechado": {
        "id": "fechado",
        "name": "Ambientes Fechados & Indoor",
        "icon": "🏢",
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
            {"key": "taxa_ocupacao", "label": "Taxa de Ocupação", "default": "4 / 12 Pessoas (33%)", "color": "#52c41a"},
            {"key": "estado_portas", "label": "Acessos & Portas", "default": "PORTA PRINCIPAL: FECHADA", "color": "#722ed1"},
            {"key": "seguranca_indoor", "label": "Segurança Predial", "default": "NORMAL / SEM ANOMALIAS", "color": "#00e676"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Ocupante", "default": "USR-IND-104"},
            {"key": "model", "label": "Postura / Estado", "default": "Sentado em Estação de Trabalho"},
            {"key": "cargo", "label": "Zona Interna", "default": "Área de Desenvolvimento - Mesa 4"},
            {"key": "heading", "label": "Tempo de Permanência", "default": "01h 42m (Atividade Normal)"}
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
        "yolo_filter_classes": [0, 56, 57, 59, 60, 62, 63, 64, 65, 66] # person, chair, couch, bed, dining table, tv, laptop, mouse, remote, keyboard
    },

    "natureza": {
        "id": "natureza",
        "name": "Natureza & Vida Selvagem",
        "icon": "🌿",
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
            {"key": "cobertura_vegetal", "label": "Densidade de Vegetação", "default": "78.4% (Copa Fechada)", "color": "#52c41a"},
            {"key": "indice_biodiversidade", "label": "Índice de Biodiversidade", "default": "ALTO (Diversas Espécies)", "color": "#13c2c2"},
            {"key": "alerta_ambiental", "label": "Alerta Ambiental", "default": "NORMAL (Sem Focos de Fogo)", "color": "#00e676"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID do Espécime", "default": "FAU-2026-07"},
            {"key": "model", "label": "Espécie Identificada", "default": "Cervo-do-Pantanal (Blastocerus)"},
            {"key": "cargo", "label": "Comportamento", "default": "Alimentação / Pastagem"},
            {"key": "heading", "label": "Direção de Deslocamento", "default": "045° (Nordeste em Trilha)"}
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
        "yolo_filter_classes": [14, 15, 16, 17, 18, 19, 20, 21, 22, 23] # bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe
    },

    "objetos": {
        "id": "objetos",
        "name": "Objetos & Indústria / Varejo",
        "icon": "📦",
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
            {"key": "contagem_esteira", "label": "Taxa de Fluxo (Itens/min)", "default": "48 peças / min", "color": "#fa8c16"},
            {"key": "conformidade_qualidade", "label": "Controle de Qualidade", "default": "99.4% CONFORME", "color": "#52c41a"},
            {"key": "diversidade_estoque", "label": "Diversidade de Categorias", "default": "6 Categorias Ativas", "color": "#1890ff"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "SKU do Objeto", "default": "SKU-IND-7731"},
            {"key": "model", "label": "Tipo de Embalagem", "default": "Caixa de Papelão Reforçada"},
            {"key": "cargo", "label": "Dimensões Estimadas", "default": "32cm x 24cm x 18cm"},
            {"key": "heading", "label": "Status de Inspeção", "default": "APROVADO (Sem Defeito)"}
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
        "yolo_filter_classes": [24, 25, 26, 28, 39, 41, 42, 43, 44, 45, 67, 73, 76, 77, 79] # backpack, umbrella, handbag, suitcase, bottle, cup, fork, knife, spoon, bowl, cell phone, book, scissors, teddy bear, toothbrush
    },

    "tatuagens": {
        "id": "tatuagens",
        "name": "Tatuagens & Arte Corporal",
        "icon": "🎨",
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
            {"key": "cobertura_pele", "label": "Área de Cobertura Dérmica", "default": "34.2% da Superfície", "color": "#eb2f96"},
            {"key": "complexidade_traco", "label": "Complexidade do Traço", "default": "ALTA DENSIDADE (94.8%)", "color": "#722ed1"},
            {"key": "estilo_dominante", "label": "Estilo Predominante", "default": "ORIENTAL / BLACKWORK", "color": "#fa8c16"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID da Marca", "default": "TAT-BIO-509"},
            {"key": "model", "label": "Classificação de Estilo", "default": "Oriental (Dragão / Flor de Lótus)"},
            {"key": "cargo", "label": "Localização Anatômica", "default": "Antebraço Esquerdo / Bíceps"},
            {"key": "heading", "label": "Assinatura Biométrica", "default": "Hash Re-ID: 7f8a9e2c... (99.1%)"}
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
        "yolo_filter_classes": [0] # person
    },

    "digitais": {
        "id": "digitais",
        "name": "Digitais & Forense Biométrico",
        "icon": "🔍",
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
            {"key": "clareza_cristas", "label": "Nitidez das Cristas (Ridge)", "default": "96.7% EXCELENTE", "color": "#13c2c2"},
            {"key": "contagem_minucias", "label": "Minúcias de Galton Detectadas", "default": "48 Minúcias Válidas", "color": "#52c41a"},
            {"key": "padrao_primario", "label": "Classificação Henry/Vucetich", "default": "VERTICILO ESPIRAL (Whorl)", "color": "#00f0ff"}
        ],
        "target_keys": [
            {"key": "target_id", "label": "ID Biométrico", "default": "FP-FOR-9041"},
            {"key": "model", "label": "Padrão Papilar", "default": "Verticilo Espiral (2 Deltas + 1 Núcleo)"},
            {"key": "cargo", "label": "Dedo / Posição", "default": "Polegar Direito (Dedo 1)"},
            {"key": "heading", "label": "Score de Match AFIS", "default": "98.7% Confiança Forense"}
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
        "yolo_filter_classes": []
    }
}
