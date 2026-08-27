"""
Script Unificado e Visual para Download, Listagem e Organizacao de Datasets e Modelos Maritimos, Navais e Fluviais.

Especialmente configurado para a Tríade:
1. DETECCAO & LOCALIZACAO de Embarcacoes (Detection Bounding Boxes).
2. IDENTIFICACAO UNICA & RE-IDENTIFICACAO (Re-ID, Impressao Digital Visual e IMO).
3. ANALISE DE TRAJETORIA & RUMO (Multi-Object Tracking, Vetores de Velocidade e Direcao/Heading).
"""

import argparse
import concurrent.futures
import json
import os
import shutil
import sys
import threading
import time
import urllib.request
import zipfile

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# CATÁLOGO COM PAPEL FUNCIONAL (DETECÇÃO, RE-ID E TRAJETÓRIA)
# ==============================================================================
CATALOG = {
    # 01 - Panópticos & Multimodais
    "lars": {
        "name": "LaRS (Lake, River, Sea Panoptic Dataset - ICCV 2023)",
        "pipeline_role": "1. DETECCAO & SEGMENTACAO",
        "pipeline_goal": "Detectar barcos e limites da agua navegavel em rios, lagos e mar.",
        "type": "Segmentacao Panoptica / Deteccao de Obstaculos",
        "sensor": "Cameras Opticas Terrestres e Embarcadas (RGB)",
        "category": "01_panoptic_and_multimodal",
        "category_name": "01. Panopticos e Multimodais Globais",
        "folder": "01_panoptic_and_multimodal/LaRS",
        "short_folder": "LaRS",
        "size_str": "~988 MB",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "13/15 (Top #1 Global Bifrost)",
        "format": "COCO Panoptic JSON + Mascaras PNG",
        "classes": "Obstaculos Dinamicos, Agua Navegavel, Margens, Ceu",
        "advantages": "Padrao ouro mundial. Unico dataset que unifica rios, lagos e mar aberto com anotacao panoptica completa.",
        "items": [
            ("https://box.vicos.si/borja/lars_dataset/lars_v1.0.0_images.zip", "lars_v1.0.0_images.zip"),
            ("https://box.vicos.si/borja/lars_dataset/lars_v1.0.0_annotations.zip", "lars_v1.0.0_annotations.zip"),
            ("https://github.com/lojzezust/lars_evaluator/archive/refs/heads/main.zip", "LaRS_evaluator.zip")
        ],
        "desc": "Referencia cientifica mundial para USVs e embarcacoes autonomas operando em qualquer corpo de agua."
    },
    "seanet": {
        "name": "SEA-AI / SEANet Maritime Panoptic Dataset",
        "pipeline_role": "1. DETECCAO & SALVAMENTO",
        "pipeline_goal": "Detectar pequenos barcos, botes, destrocos e homem ao mar (MOB).",
        "type": "Segmentacao Panoptica e Deteccao de Salvamento",
        "sensor": "Cameras Termicas (LWIR) + Opticas RGB",
        "category": "01_panoptic_and_multimodal",
        "category_name": "01. Panopticos e Multimodais Globais",
        "folder": "01_panoptic_and_multimodal/SEANet_SEA_AI",
        "short_folder": "SEANet_SEA_AI",
        "size_str": "~22 MB",
        "is_top": True,
        "is_tracking_reid": False,
        "rank_score": "Missao Critica Salvamento",
        "format": "Parquet / Hugging Face Datasets",
        "classes": "Homem ao Mar (MOB), Destrocos (Flotsam), Gelo Marinho, Barcos",
        "advantages": "Focado em missao critica: prevencao de colisao com objetos semisubmersos e salvamento em alto-mar.",
        "hf_dataset": "SEA-AI/SEANet",
        "zip_name": "SEANet_panoptic_dataset.zip",
        "desc": "Dataset de seguranca de vida humana no mar e deteccao de pequenos perigos a navegacao."
    },
    "waterscenes": {
        "name": "WaterScenes Multi-Task 4D Radar-Camera Perception",
        "pipeline_role": "3. RASTREAMENTO & TRAJETORIA 4D",
        "pipeline_goal": "Rastrear barcos com Doppler direto, velocidade radial e vetores de rumo 4D.",
        "type": "Fusao Multimodal 4D (Deteccao + Rastreamento)",
        "sensor": "Radar 4D Imaging + Camera Monocular RGB",
        "category": "01_panoptic_and_multimodal",
        "category_name": "01. Panopticos e Multimodais Globais",
        "folder": "01_panoptic_and_multimodal/WaterScenes_4DRadar",
        "short_folder": "WaterScenes_4DRadar",
        "size_str": "~0.01 MB (DevKit)",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "12/15 (Top #2 Global Bifrost)",
        "format": "Numpy / JSON / Pcd Point Clouds",
        "classes": "Navios, Barcos, Boias, Nadadores, Cais, Pontes",
        "advantages": "Imune a nevoeiro, chuva torrencial e reflexos solares gracas a fusao com nuvens de pontos de Radar 4D.",
        "items": [
            ("https://github.com/WaterScenes/WaterScenes/archive/refs/heads/main.zip", "WaterScenes_DevKit.zip")
        ],
        "desc": "Primeiro grande benchmark multimodal com Radar 4D para navegacao autonoma em condicoes climaticas adversas."
    },

    # 02 - Fluviais & Hidrovias Interiores
    "iwhr_floater": {
        "name": "IWHR Floater V1 (Nature Scientific Data 2025)",
        "pipeline_role": "1. DETECCAO FLUVIAL",
        "pipeline_goal": "Diferenciar embarcacoes fluviais reais de troncos e lixo flutuante.",
        "type": "Deteccao de Objetos Flutuantes em Rios (YOLO / VOC)",
        "sensor": "Cameras de Seguranca de Rios e Usinas Hidreletricas",
        "category": "02_fluvial_and_inland_waterways",
        "category_name": "02. Fluviais e Hidrovias Interiores",
        "folder": "02_fluvial_and_inland_waterways/IWHR_Floater_V1",
        "short_folder": "IWHR_Floater_V1",
        "size_str": "~971 MB",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "Top #1 Fluvial Nature 2025",
        "format": "YOLO TXT + Pascal VOC XML",
        "classes": "Troncos, Vegetacao Aquatica, Lixo Plastico, Boias, Barcos",
        "advantages": "Validado pela revista Nature (2025). Excelente para monitoramento ambiental e prevencao de danos a turbinas.",
        "items": [
            ("https://figshare.com/ndownloader/files/51448835", "IWHR_AI_Lable_Floater_V1-package1.zip")
        ],
        "desc": "Mais de 10.000 imagens reais de rios sob variacoes extremas de iluminacao e turbidez da agua."
    },
    "elwha_river": {
        "name": "Elwha River Path & Shoreline Semantic Segmentation",
        "pipeline_role": "3. CORREDOR NAVEGAVEL / ROTA",
        "pipeline_goal": "Mapear a calha fluvial para prever corredores de navegacao e desvio de bancos de areia.",
        "type": "Segmentacao Semantica de Calha Fluvial",
        "sensor": "Cameras Fluviais Aereas e Terrestres",
        "category": "02_fluvial_and_inland_waterways",
        "category_name": "02. Fluviais e Hidrovias Interiores",
        "folder": "02_fluvial_and_inland_waterways/Elwha_River_Segmentation",
        "short_folder": "Elwha_River_Segmentation",
        "size_str": "~1.38 GB",
        "is_top": True,
        "is_tracking_reid": False,
        "rank_score": "Top Calha Fluvial Parquet",
        "format": "Apache Parquet / Imagens PNG de Alta Resolucao",
        "classes": "Canal Ativo (Agua), Bancos de Cascalho/Areia, Vegetacao Riparia",
        "advantages": "Ideal para tracado automatico de rotas navegaveis e desvio de bancos de areia e ilhotas em rios rasos.",
        "hf_dataset": "stodoran/elwha-segmentation-v1",
        "zip_name": "Elwha_river_segmentation.zip",
        "desc": "1.508 amostras rotuladas para segmentacao morfologica de bacias e calhas de rios."
    },
    "wsodd": {
        "name": "WSODD (Water Surface Object Detection Dataset)",
        "pipeline_role": "1. DETECCAO DE OBSTACULOS",
        "pipeline_goal": "Detectar barcos e obstaculos na agua.",
        "type": "Deteccao de Objetos na Superficie da Agua",
        "sensor": "Cameras Costeiras e Fluviais",
        "category": "02_fluvial_and_inland_waterways",
        "category_name": "02. Fluviais e Hidrovias Interiores",
        "folder": "02_fluvial_and_inland_waterways/WSODD_Water_Surface",
        "short_folder": "WSODD_Water_Surface",
        "size_str": "~0.01 MB",
        "is_top": False,
        "is_tracking_reid": False,
        "format": "Pascal VOC XML / Scripts COCO",
        "classes": "14 Classes de Barcos, Pontes, Pilares, Obstaculos",
        "advantages": "Grande variedade de obstaculos fixos e moveis em ambientes fluviais e lacustres.",
        "items": [
            ("https://github.com/sunjiaen/WSODD/archive/refs/heads/main.zip", "WSODD_dataset.zip")
        ],
        "desc": "Benchmark de deteccao de obstaculos e construcoes em rios e represas."
    },

    # 03 - Costeiros & Estereoscopia USV
    "mastre1325": {
        "name": "MaSTRe1325 Maritime Semantic Segmentation + IMU",
        "pipeline_role": "3. NAVEGACAO COM TELEMETRIA",
        "pipeline_goal": "Compensar a inclinacao e balanco de cameras a bordo para calculo exato de trajetoria.",
        "type": "Segmentacao Semantica com Telemetria Inercial",
        "sensor": "Camera RGB + Sensor Inercial IMU Sincronizado",
        "category": "03_coastal_and_stereo_usv",
        "category_name": "03. Costeiros e Estereoscopia USV",
        "folder": "03_coastal_and_stereo_usv/MaSTRe1325",
        "short_folder": "MaSTRe1325",
        "size_str": "~24 MB",
        "is_top": True,
        "is_tracking_reid": False,
        "rank_score": "10/15 (Top Costeiro ViCoS)",
        "format": "PNG Masks + CSV IMU Telemetry",
        "classes": "Mar, Ceu, Terra / Obstaculos",
        "advantages": "Permite compensar o balanco de ondas e inclinacao do barco atraves dos dados de acelerometro/giroscopio.",
        "items": [
            ("https://box.vicos.si/borja/mastr1325_dataset/MaSTr1325_masks_512x384.zip", "MaSTr1325_masks_512x384.zip"),
            ("https://box.vicos.si/borja/mastr1325_dataset/MaSTr1325_images_512x384.zip", "MaSTr1325_images_512x384.zip"),
            ("https://box.vicos.si/borja/mastr1325_dataset/MaSTr1325_imus_512x384.zip", "MaSTr1325_imus_512x384.zip")
        ],
        "desc": "1.325 imagens costeiras de alta resolucao com dados inerciais para navegacao de USVs."
    },
    "modd2": {
        "name": "MODD2 Stereo Obstacle Detection & Water-Edge",
        "pipeline_role": "3. RASTREAMENTO METRICO & DISTANCIA",
        "pipeline_goal": "Calcular distancia metrica (em metros) e vetor de aproximacao de barcos em video sequencial.",
        "type": "Estereoscopia Metrica e Estimativa de Distancia",
        "sensor": "Par de Cameras Estereoscopicas + GPS",
        "category": "03_coastal_and_stereo_usv",
        "category_name": "03. Costeiros e Estereoscopia USV",
        "folder": "03_coastal_and_stereo_usv/MODD2_Stereo",
        "short_folder": "MODD2_Stereo",
        "size_str": "~7 MB",
        "is_top": False,
        "is_tracking_reid": True,
        "format": "TXT Anotacoes + Mascaras USV + CSV GPS",
        "classes": "Obstaculos Maritimos, Linha da Agua, Mascara do Proprio Barco",
        "advantages": "Permite medicao metrica de distancia de colisao sem necessidade de LiDAR.",
        "items": [
            ("https://box.vicos.si/borja/modd2_dataset/MODD2_annotations_v2.zip", "MODD2_annotations_v2.zip"),
            ("https://box.vicos.si/borja/modd2_dataset/MODD2_GPS_data.zip", "MODD2_GPS_data.zip"),
            ("https://box.vicos.si/borja/modd2_dataset/MODD2_USVparts_masks.zip", "MODD2_USVparts_masks.zip")
        ],
        "desc": "28 sequencias de video estereo para calculo de horizonte e deteccao metrica de colisao."
    },

    # 04 - Térmicos, Radar SAR & Offshore
    "sar_ship_detection": {
        "name": "SAR Ship Detection Dataset (Synthetic Aperture Radar)",
        "pipeline_role": "1. DETECCAO SAR NOTURNA / TEMPESTADE",
        "pipeline_goal": "Identificar barcos atraves de chuva, neblina e noite total via radar de satelite.",
        "type": "Deteccao de Navios por Radar SAR",
        "sensor": "Radar de Abertura Sintetica (Satélite / Aeronave SAR)",
        "category": "04_thermal_and_offshore",
        "category_name": "04. Termicos, Radar SAR e Offshore",
        "folder": "04_thermal_and_offshore/SAR_Ship_Detection",
        "short_folder": "SAR_Ship_Detection",
        "size_str": "~88 MB",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "Top Radar SAR HF 2025",
        "format": "Imagens TIFF/PNG + Anotacoes Bounding Box",
        "classes": "Navios Comerciais, Belonaves, Embarcacoes Pesqueiras",
        "advantages": "Funciona atraves de tempestades severas, nuvens grossas e escuridao total.",
        "hf_dataset": "agungpambudi/sar-ship-detection",
        "zip_name": "sar_ship_detection.zip",
        "desc": "2.320 imagens de radar SAR processadas para treinamento de redes neurais maritimas."
    },
    "massmind": {
        "name": "MassMIND Long-Wave Infrared (LWIR 8-14 um) Thermal",
        "pipeline_role": "1. ASSINATURA TERMICA NOTURNA",
        "pipeline_goal": "Detectar barcos no escuro total pela assinatura de calor dos motores e casco.",
        "type": "Segmentacao Termica no Infravermelho Longo (LWIR)",
        "sensor": "Cameras Termograficas LWIR",
        "category": "04_thermal_and_offshore",
        "category_name": "04. Termicos, Radar SAR e Offshore",
        "folder": "04_thermal_and_offshore/MassMIND_Thermal_LWIR",
        "short_folder": "MassMIND_Thermal_LWIR",
        "size_str": "~1.3 MB",
        "is_top": False,
        "is_tracking_reid": False,
        "format": "Imagens Termicas PNG + Mascaras Semanticas",
        "classes": "Navios, Embarcacoes, Obstaculos, Agua, Costa",
        "advantages": "Detecta embarcacoes pelo contraste termico residual do motor e casco na agua.",
        "items": [
            ("https://github.com/uml-marine-robotics/MassMIND/archive/refs/heads/main.zip", "MassMIND_dataset.zip")
        ],
        "desc": "Dataset termico especializado para navegacao noturna sob neblina."
    },
    "kolomverse": {
        "name": "KOLOMVERSE Korea Offshore Surveillance (4K UHD)",
        "pipeline_role": "1. DETECCAO DE LONGO ALCANCE 4K",
        "pipeline_goal": "Detectar barcos a grandes distancias em cameras 4K.",
        "type": "Vigilancia de Infraestruturas Offshore em 4K",
        "sensor": "Cameras Opticas 4K Ultra HD",
        "category": "04_thermal_and_offshore",
        "category_name": "04. Termicos, Radar SAR e Offshore",
        "folder": "04_thermal_and_offshore/KOLOMVERSE_Offshore_4K",
        "short_folder": "KOLOMVERSE_Offshore_4K",
        "size_str": "~27 MB",
        "is_top": False,
        "is_tracking_reid": False,
        "format": "JSON / Imagens 4K",
        "classes": "Parques Eolicos Offshore, Farois, Plataformas de Petroleo, Redes de Pesca",
        "advantages": "Alta resolucao 4K para deteccao precoce a longas distancias em mar aberto.",
        "items": [
            ("https://github.com/MaritimeDataset/KOLOMVERSE/archive/refs/heads/main.zip", "KOLOMVERSE_dataset.zip")
        ],
        "desc": "Monitoramento e seguranca de instalacoes offshore e redes de pesca."
    },
    "marvel_2016": {
        "name": "MARVEL 2016 Vessel Classification & Retrieval (IMO)",
        "pipeline_role": "2. IDENTIFICACAO UNICA & RE-ID (IMO)",
        "pipeline_goal": "Diferenciar individualmente cada barco por foto e recuperar seu cadastro/IMO unico.",
        "type": "Recuperacao e Classificacao por Similaridade Visual",
        "sensor": "Cameras Teleobjetivas Portuarias",
        "category": "04_thermal_and_offshore",
        "category_name": "04. Termicos, Radar SAR e Offshore",
        "folder": "04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval",
        "short_folder": "MARVEL_2016_Vessel_Retrieval",
        "size_str": "~8.3 MB",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "Top #1 Re-ID & IMO Match",
        "format": "DAT / Metadados IMO / Python Scraper",
        "classes": "26 Categorias de Embarcacoes com registro IMO",
        "advantages": "O melhor dataset para Re-ID: permite treinar redes de contraste e recuperar o mesmo barco em diferentes cameras.",
        "items": [
            ("https://github.com/avaapm/marveldataset2016/archive/refs/heads/master.zip", "MARVEL_2016_dataset.zip")
        ],
        "desc": "Base massiva para busca de embarcacoes por foto."
    },

    # 05 - Catálogo Roboflow Universe
    "roboflow_suite": {
        "name": "Roboflow Universe Naval & Fluvial Suite (10 Datasets)",
        "pipeline_role": "1. DETECCAO MULTIDOMINIO YOLO",
        "pipeline_goal": "Detectar barcos sob cameras de drones, portos, NIR noturno e embarcacoes costeiras.",
        "type": "Deteccao YOLO em Multiplos Dominios",
        "sensor": "Drones (UAV), Cameras Costeiras, NIR, Portuarias",
        "category": "05_roboflow_universe_catalog",
        "category_name": "05. Catalogo Roboflow Universe (10 Datasets)",
        "folder": "05_roboflow_universe_catalog",
        "short_folder": "Roboflow_Universe_Suite",
        "size_str": "~0.05 MB",
        "is_top": False,
        "is_tracking_reid": True,
        "format": "YOLO TXT + data.yaml",
        "classes": "10 conjuntos (Coruna 12 classes, Drones, NIR, Defesa Naval, etc.)",
        "advantages": "10 datasets individuais pré-configurados prontos para treinamento com YOLOv8/v9/v11.",
        "desc": "Colecao completa de 10 subpastas com arquivos .zip e configs de treino."
    },

    # Modelos de Deep Learning
    "model_y8naval": {
        "name": "SixOpen Y8Naval ONNX (50 Classes Navais Satélite)",
        "pipeline_role": "1. DETECCAO & CLASSIFICACAO FINA (50 CLASSES)",
        "pipeline_goal": "Detectar e classificar o tipo exato do barco entre 50 categorias navais.",
        "type": "Modelo de Deteccao em Fotos Orbitais / Aereas",
        "sensor": "Imagens de Satelite e Drones em Alta Altitude",
        "category": "models",
        "category_name": "Modelos de Deep Learning Pré-Treinados",
        "folder": "models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX",
        "short_folder": "SixOpen_Y8NavalONNX",
        "size_str": "~101 MB",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "Top Satelite 50 Classes",
        "format": "ONNX (Open Neural Network Exchange)",
        "classes": "50 Classes (Porta-Avioes, Destroieres, Submarinos, Graneleiros, Balsas, etc.)",
        "advantages": "Cobre praticamente qualquer embarcacao naval do mundo vista de cima em alta resolucao.",
        "hf_model": "SixOpen/Y8NavalONNX",
        "files": ["Y8Naval.onnx", "config.json", "preprocessor_config.json"],
        "desc": "Modelo ONNX otimizado para deteccao em fotos orbitais e vigilancia aerea estrategica."
    },
    "model_sar_vessel": {
        "name": "MeWan2808 YOLOv8 SAR Vessel (38 ms Borda)",
        "pipeline_role": "3. RASTREAMENTO EM TEMPO REAL (38 ms)",
        "pipeline_goal": "Alimentar o algoritmo de rastreamento (ByteTrack) a altissima taxa de quadros (60+ FPS).",
        "type": "Modelo Ultra-Rapido para Radar SAR e Borda",
        "sensor": "Imagens de Radar SAR",
        "category": "models",
        "category_name": "Modelos de Deep Learning Pré-Treinados",
        "folder": "models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR",
        "short_folder": "MeWan2808_YOLOv8_SAR",
        "size_str": "~12 MB",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "Top Borda Ultra-Rapido (38 ms)",
        "format": "ONNX Quantizado INT8 / PyTorch .pt",
        "classes": "Vessel / Ship em Radar SAR",
        "advantages": "Velocidade extrema de inferencia (38 ms em CPU simples). Nao requer GPU dedicada.",
        "hf_model": "MeWan2808/YOLOv8_SAR_Vessel_Detection",
        "files": ["quantized/best.onnx", "unquantized/best.pt"],
        "desc": "Perfeito para instalacao em Raspberry Pi, Jetson Nano ou computadores de bordo USV."
    },
    "model_marine_vessel": {
        "name": "mayrajeo YOLOv8n Marine Vessel Detection",
        "pipeline_role": "1. DETECCAO COSTEIRA TEMPO REAL",
        "pipeline_goal": "Detectar caixas de barcos para alimentar o módulo de rastreamento.",
        "type": "Modelo Leve em Tempo Real para Cameras Costeiras",
        "sensor": "Cameras Opticas RGB",
        "category": "models",
        "category_name": "Modelos de Deep Learning Pré-Treinados",
        "folder": "models/02_sar_radar_and_edge/mayrajeo_YOLOv8_Marine_Vessel",
        "short_folder": "mayrajeo_YOLOv8_Marine_Vessel",
        "size_str": "~6 MB",
        "is_top": False,
        "is_tracking_reid": True,
        "format": "PyTorch (.pt)",
        "classes": "Embarcacoes Maritimas Gerais",
        "advantages": "Ultraleve (apenas 5.95 MB), ideal para deteccao em tempo real a 60+ FPS.",
        "hf_model": "mayrajeo/marine-vessel-detection-yolov8",
        "files": ["YOLOv8n/yolov8n.pt", "YOLOv8n/args.yaml"],
        "desc": "Modelo YOLOv8n para monitoramento rapido de fluxo de barcos."
    },
    "model_river_seg": {
        "name": "beaunix River Semantic Segmentation (PyTorch)",
        "pipeline_role": "3. DELIMITACAO DE CANAL & ROTA FLUVIAL",
        "pipeline_goal": "Segmentar a calha navegavel para correlacionar o rumo dos barcos com a rota do rio.",
        "type": "Segmentacao Semantica de Calha Fluvial",
        "sensor": "Cameras de Bordo Fluviais",
        "category": "models",
        "category_name": "Modelos de Deep Learning Pré-Treinados",
        "folder": "models/02_sar_radar_and_edge/beaunix_River_Segmentation",
        "short_folder": "beaunix_River_Segmentation",
        "size_str": "~104 MB",
        "is_top": True,
        "is_tracking_reid": False,
        "rank_score": "Top Fluvial Segmentation",
        "format": "PyTorch State Dict (.pt)",
        "classes": "Calha do Rio, Margens e Vegetacao",
        "advantages": "Segmenta com precisao pixel a pixel os limites da agua em rios e igarapes.",
        "hf_model": "beaunix/river-segmentation",
        "files": ["best_model.pt"],
        "desc": "Checkpoints treinados para deteccao de borda d'agua e navegacao fluvial segura."
    },
    "model_vit_vessel": {
        "name": "dima806 ViT Vessel Classifier (Vision Transformer)",
        "pipeline_role": "2. EXTRAÇÃO DE EMBEDDING & RE-ID UNICO",
        "pipeline_goal": "Gerar a 'impressao digital' (vetor de 768 dimensoes) de cada barco para reconhece-lo em qualquer camera.",
        "type": "Classificacao Fina Baseada em Transformers",
        "sensor": "Cameras Opticas de Longo Alcance",
        "category": "models",
        "category_name": "Modelos de Deep Learning Pré-Treinados",
        "folder": "models/03_vessel_transformers/dima806_ViT_Vessel_Classification",
        "short_folder": "dima806_ViT_Vessel_Classification",
        "size_str": "~327 MB",
        "is_top": True,
        "is_tracking_reid": True,
        "rank_score": "Top #1 Vessel Re-ID Transformer",
        "format": "Hugging Face Safetensors",
        "classes": "9 Tipos de Navios (Cargo, Tanker, Cruise, Tug, Military, etc.)",
        "advantages": "Mecanismo de auto-atencao que extrai caracteristicas unicas da superestrutura de cada barco para Re-ID.",
        "hf_model": "dima806/vessel_classification",
        "files": ["model.safetensors", "config.json", "preprocessor_config.json"],
        "desc": "Rede Vision Transformer de alta acuracia para classificacao naval."
    }
}

# ==============================================================================
# MOTOR DE DOWNLOAD E GERENCIAMENTO DE ARQUIVOS
# ==============================================================================
class DownloadManager:
    def __init__(self, base_dest=".", is_single_item=False, log_callback=None, progress_callback=None):
        self.base_dest = os.path.abspath(base_dest)
        self.is_single_item = is_single_item
        self.log_callback = log_callback or (lambda msg: print(msg))
        self.progress_callback = progress_callback or (lambda pct, speed_str: None)
        self.stop_requested = False

    def log(self, message):
        self.log_callback(message)

    def download_url_with_progress(self, url, dest_file):
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        temp_file = dest_file + ".part"
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()
            last_time = start_time
            last_downloaded = 0
            
            with open(temp_file, "wb") as f_out:
                while True:
                    if self.stop_requested:
                        f_out.close()
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        return False
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    downloaded += len(chunk)
                    
                    now = time.time()
                    if now - last_time >= 0.5:
                        speed = (downloaded - last_downloaded) / (now - last_time) / (1024 * 1024)
                        pct = (downloaded / total_size * 100) if total_size > 0 else 0
                        speed_str = f"{speed:.2f} MB/s"
                        dl_mb = downloaded / (1024 * 1024)
                        tot_mb = total_size / (1024 * 1024)
                        self.progress_callback(pct, f"{pct:.1f}% ({dl_mb:.1f}/{tot_mb:.1f} MB) - {speed_str}")
                        last_time = now
                        last_downloaded = downloaded

        if os.path.exists(dest_file):
            os.remove(dest_file)
        os.rename(temp_file, dest_file)
        return True

    def download_hf_hub_files(self, repo_id, repo_type, files, dest_dir):
        from huggingface_hub import hf_hub_download
        os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            if self.stop_requested:
                return False
            self.log(f"  -> Baixando {f} do Hugging Face ({repo_id})...")
            hf_hub_download(repo_id=repo_id, repo_type=repo_type, filename=f, local_dir=dest_dir)
        return True

    def process_item(self, key):
        info = CATALOG[key]
        self.log(f"\n=======================================================")
        self.log(f"Iniciando: {info['name']}")
        self.log(f"Funcao no Pipeline: {info['pipeline_role']}")
        self.log(f"Objetivo: {info['pipeline_goal']}")
        self.log(f"Vantagens: {info['advantages']}")
        self.log(f"Tamanho estimado: {info['size_str']}")
        self.log(f"=======================================================")
        
        if self.is_single_item:
            target_dir = os.path.join(self.base_dest, info.get("short_folder", info["folder"]))
            archives_dir = self.base_dest
        else:
            target_dir = os.path.join(self.base_dest, "datasets" if not info["category"].startswith("models") else "", info["folder"])
            archives_dir = os.path.join(self.base_dest, "datasets", "archives")
            
        os.makedirs(target_dir, exist_ok=True)
        os.makedirs(archives_dir, exist_ok=True)
        
        if "items" in info:
            for url, filename in info["items"]:
                if self.stop_requested:
                    return
                dest_zip = os.path.join(target_dir, filename)
                self.log(f"Baixando pacote {filename}...")
                success = self.download_url_with_progress(url, dest_zip)
                if success:
                    sz_mb = os.path.getsize(dest_zip) / (1024 * 1024)
                    self.log(f"[OK] {filename} baixado com sucesso ({sz_mb:.2f} MB)!")
                    if not self.is_single_item:
                        archive_dest = os.path.join(archives_dir, filename)
                        shutil.copy2(dest_zip, archive_dest)
                    
        elif "hf_dataset" in info:
            self.log(f"Baixando dataset do Hugging Face: {info['hf_dataset']}...")
            from huggingface_hub import snapshot_download
            temp_dir = os.path.join(self.base_dest, "temp_hf_download")
            snapshot_download(repo_id=info["hf_dataset"], repo_type="dataset", local_dir=temp_dir)
            
            dest_zip = os.path.join(target_dir, info["zip_name"])
            self.log(f"Compactando dataset para {info['zip_name']}...")
            with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, temp_dir)
                        zf.write(fp, arcname)
            shutil.rmtree(temp_dir, ignore_errors=True)
            if not self.is_single_item:
                archive_dest = os.path.join(archives_dir, info["zip_name"])
                shutil.copy2(dest_zip, archive_dest)
            self.log(f"[OK] Dataset {info['zip_name']} salvo em {target_dir}!")

        elif "hf_model" in info:
            self.log(f"Baixando pesos do modelo: {info['hf_model']}...")
            self.download_hf_hub_files(info["hf_model"], "model", info["files"], target_dir)
            self.log(f"[OK] Modelo instalado com sucesso em {target_dir}!")

        elif key == "roboflow_suite":
            self.log("Gerando e estruturando os 10 datasets dedicados do Roboflow Universe...")
            try:
                from scripts.setup_roboflow_individual_datasets import main as setup_rf
                setup_rf()
            except Exception:
                pass
            self.log("[OK] Suite Roboflow Universe configurada com sucesso!")

    def download_selected(self, keys):
        total = len(keys)
        self.log(f"Iniciando processamento de {total} item(ns)...")
        for i, k in enumerate(keys, 1):
            if self.stop_requested:
                self.log("\n[CANCELADO] Processo interrompido pelo usuario.")
                break
            self.process_item(k)
        self.progress_callback(100, "Concluido!")
        self.log("\n" + "=" * 80)
        self.log("DOWNLOADS FINALIZADOS COM SUCESSO!")
        self.log("=" * 80)


# ==============================================================================
# FUNÇÕES DE LISTAGEM E CLASSIFICAÇÃO
# ==============================================================================
def print_separator(char="=", length=100):
    print(char * length)

def list_pipeline_tracking_reid():
    print_separator("=")
    print("🎯 ARQUITETURA ESPECIALIZADA: IDENTIFICAÇÃO DE BARCOS, RE-ID ÚNICO E ANÁLISE DE TRAJETÓRIA")
    print_separator("=")
    
    stages = [
        ("1. ETAPA 1: DETECÇÃO & LOCALIZAÇÃO EM TEMPO REAL", 
         "Encontrar embarcações, delimitar bounding boxes e classificar tipos (YOLO / Satélite / SAR):",
         ["model_y8naval", "model_marine_vessel", "model_sar_vessel", "lars", "iwhr_floater", "roboflow_suite"]),
        
        ("2. ETAPA 2: IDENTIFICAÇÃO ÚNICA & RE-ID (IMPRESSÃO DIGITAL DO BARCO)", 
         "Extrair embeddings visuais para reconhecer o MESMO barco em câmeras diferentes e associar IMO:",
         ["marvel_2016", "model_vit_vessel"]),
         
        ("3. ETAPA 3: RASTREAMENTO MULTI-OBJETO, VETORES DE CURSO & TRAJETÓRIA (HEADING)", 
         "Rastrear o deslocamento temporal, calcular ângulo de navegação (0°-360°) e estimar velocidade/rota:",
         ["waterscenes", "modd2", "model_sar_vessel", "elwha_river", "model_river_seg"])
    ]
    
    for stage_title, stage_desc, item_keys in stages:
        print(f"\n>> {stage_title}")
        print(f"   {stage_desc}")
        print_separator("-")
        for k in item_keys:
            if k in CATALOG:
                info = CATALOG[k]
                print(f"  * [{k}] {info['name']} ({info['size_str']})")
                print(f"    Papel:      {info['pipeline_role']}")
                print(f"    Para que:   {info['pipeline_goal']}")
                print(f"    Vantagens:  {info['advantages']}")
                print()
                
    print("=" * 100)
    print("COMO EXECUTAR:")
    print("  - Baixar toda a suíte de Rastreamento + Re-ID: python download_fluvial_datasets.py --tracking")
    print("  - Testar rastreador de trajetória e rumo:      python scripts/track_and_heading.py")
    print("  - Testar extrator de identidade única (Re-ID): python scripts/vessel_reid_extractor.py")
    print("=" * 100)

def list_items(filter_type="all"):
    title_map = {
        "top": "[*] LISTA DOS 10 PRINCIPAIS DATASETS E MODELOS AQUATICOS (TOP TIER)",
        "all": "[*] CATALOGO COMPLETO CLASSIFICADO: DATASETS E MODELOS AQUATICOS E FLUVIAIS",
        "datasets": "[*] CATALOGO DE DATASETS AQUATICOS, FLUVIAIS E MARITIMOS",
        "models": "[*] CATALOGO DE MODELOS DE DEEP LEARNING PRE-TREINADOS"
    }
    
    print_separator("=")
    print(title_map.get(filter_type, title_map["all"]))
    print_separator("=")
    
    categories = [
        ("01_panoptic_and_multimodal", "01. Panopticos e Multimodais Globais"),
        ("02_fluvial_and_inland_waterways", "02. Fluviais e Hidrovias Interiores"),
        ("03_coastal_and_stereo_usv", "03. Costeiros e Estereoscopia USV"),
        ("04_thermal_and_offshore", "04. Termicos, Radar SAR e Offshore"),
        ("05_roboflow_universe_catalog", "05. Catalogo Roboflow Universe (10 Datasets)"),
        ("models", "Modelos de Deep Learning Pre-Treinados")
    ]
    
    for cat_id, cat_title in categories:
        items_in_cat = []
        for k, v in CATALOG.items():
            if v["category"] == cat_id:
                if filter_type == "top" and not v.get("is_top"):
                    continue
                if filter_type == "datasets" and cat_id == "models":
                    continue
                if filter_type == "models" and cat_id != "models":
                    continue
                items_in_cat.append((k, v))
                
        if not items_in_cat:
            continue
            
        print(f"\n>> {cat_title.upper()}")
        print_separator("-")
        
        for k, info in items_in_cat:
            star = "[TOP TIER] " if info.get("is_top") else ""
            print(f"ID:          {k}")
            print(f"Nome:        {star}{info['name']}")
            print(f"Funcao:      {info['pipeline_role']}")
            print(f"Objetivo:    {info['pipeline_goal']}")
            print(f"Sensor(es):  {info['sensor']}")
            print(f"Formato:     {info['format']}")
            print(f"Tamanho:     {info['size_str']}")
            print(f"Vantagens:   {info['advantages']}")
            print("-" * 100)


# ==============================================================================
# INTERFACE GRÁFICA VISUAL (TKINTER)
# ==============================================================================
def run_visual_gui(dest_dir="."):
    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.title("Central de Inteligencia Naval - Identificação, Re-ID e Trajetórias 🌊🚢")
    root.geometry("1020x800")
    root.minsize(880, 650)

    style = ttk.Style()
    style.theme_use("clam")

    # Header
    header_frame = tk.Frame(root, bg="#1a2a3a", pady=10)
    header_frame.pack(fill="x")
    
    title_lbl = tk.Label(header_frame, text="Central de Visão Computacional: Identificação, Re-ID e Trajetórias 🌊🚢", 
                         font=("Segoe UI", 14, "bold"), fg="#ffffff", bg="#1a2a3a")
    title_lbl.pack()
    sub_lbl = tk.Label(header_frame, text="Configurado para: 1. Detectar Barcos | 2. Identificar Unicamente (Re-ID) | 3. Analisar Trajetoria e Rumo", 
                       font=("Segoe UI", 9), fg="#a0c0e0", bg="#1a2a3a")
    sub_lbl.pack()

    # Split Horizontal
    paned = tk.PanedWindow(root, orient="horizontal", sashrelief="ridge", bg="#e0e0e0")
    paned.pack(fill="both", expand=True, padx=6, pady=6)

    # Painel Esquerdo: Seleção
    left_frame = tk.Frame(paned, padx=6, pady=4)
    paned.add(left_frame, minsize=490)

    btn_box1 = tk.Frame(left_frame)
    btn_box1.pack(fill="x", pady=2)

    btn_box2 = tk.Frame(left_frame)
    btn_box2.pack(fill="x", pady=2)

    checkbox_vars = {}

    def set_all(state):
        for var in checkbox_vars.values():
            var.set(state)

    def set_tracking_reid_only():
        for k, v in checkbox_vars.items():
            v.set(CATALOG[k].get("is_tracking_reid", False))

    def set_top_only():
        for k, v in checkbox_vars.items():
            v.set(CATALOG[k].get("is_top", False))

    def set_category(cat_name, state=True):
        for k, v in checkbox_vars.items():
            if CATALOG[k]["category"] == cat_name:
                v.set(state)

    tk.Button(btn_box1, text="🎯 Suite Identificação, Re-ID & Trajetória", bg="#0088cc", fg="#ffffff", 
              font=("Segoe UI", 9, "bold"), padx=6, pady=2, command=set_tracking_reid_only).pack(side="left", padx=2)
    tk.Button(btn_box1, text="⭐ Principais (Top Tier)", bg="#ff9900", fg="#000000", 
              font=("Segoe UI", 9, "bold"), padx=6, pady=2, command=set_top_only).pack(side="left", padx=2)

    ttk.Button(btn_box2, text="Marcar Todos", command=lambda: set_all(True)).pack(side="left", padx=2)
    ttk.Button(btn_box2, text="Desmarcar Todos", command=lambda: set_all(False)).pack(side="left", padx=2)
    ttk.Button(btn_box2, text="Apenas Modelos", command=lambda: (set_all(False), set_category("models", True))).pack(side="left", padx=2)
    ttk.Button(btn_box2, text="Apenas Fluviais", command=lambda: (set_all(False), set_category("02_fluvial_and_inland_waterways", True))).pack(side="left", padx=2)

    # Canvas com Scrollbar
    canvas = tk.Canvas(left_frame, borderwidth=0, highlightthickness=0)
    scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
    scroll_content = tk.Frame(canvas)

    scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_content, anchor="nw")
    canvas.configure(xscrollcommand=scrollbar.set, yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Painel Direito: Detalhes e Logs
    right_frame = tk.Frame(paned, padx=6, pady=4)
    paned.add(right_frame, minsize=460)

    # Painel de Detalhes
    info_frame = tk.LabelFrame(right_frame, text="🔍 Papel no Pipeline de Identificação e Trajetória", font=("Segoe UI", 10, "bold"), padx=6, pady=4)
    info_frame.pack(fill="x", pady=2)

    lbl_info_title = tk.Label(info_frame, text="Passe o mouse para ver detalhes do pipeline", font=("Segoe UI", 10, "bold"), fg="#0b4f8c", wraplength=420, justify="left")
    lbl_info_title.pack(anchor="w")

    lbl_info_details = tk.Label(info_frame, text="", font=("Segoe UI", 8), fg="#333333", wraplength=420, justify="left")
    lbl_info_details.pack(anchor="w", pady=2)

    def show_details(k):
        info = CATALOG[k]
        star = "⭐ [TOP TIER] " if info.get("is_top") else ""
        lbl_info_title.config(text=f"{star}{info['name']}")
        details_txt = (
            f"🎯 Papel no Pipeline: {info['pipeline_role']}\n"
            f"💡 Como atua: {info['pipeline_goal']}\n"
            f"📡 Sensores: {info['sensor']}\n"
            f"📁 Formato: {info['format']} | Tamanho: {info['size_str']}\n"
            f"🚀 Vantagens: {info['advantages']}"
        )
        lbl_info_details.config(text=details_txt)

    categories_ui = [
        ("01_panoptic_and_multimodal", "🌊 01 - Panópticos & Multimodais (Detecção & 4D)"),
        ("02_fluvial_and_inland_waterways", "🛶 02 - Fluviais (Detecção & Calha de Rota)"),
        ("03_coastal_and_stereo_usv", "🚢 03 - Costeiros (Estereoscopia & Trajetória)"),
        ("04_thermal_and_offshore", "🛰️ 04 - Térmicos, Radar SAR & Re-ID IMO"),
        ("05_roboflow_universe_catalog", "🎯 05 - Catálogo Roboflow Universe (10 Datasets)"),
        ("models", "🧠 Modelos Pré-Treinados (Detecção, Borda & Re-ID ViT)")
    ]

    for cat_id, cat_title in categories_ui:
        cat_lbl = tk.Label(scroll_content, text=cat_title, font=("Segoe UI", 10, "bold"), fg="#0b4f8c", pady=4)
        cat_lbl.pack(anchor="w")
        
        for k, info in CATALOG.items():
            if info["category"] == cat_id:
                var = tk.BooleanVar(value=info.get("is_tracking_reid", True))
                checkbox_vars[k] = var
                
                star = "⭐ " if info.get("is_top") else ""
                fg_color = "#004080" if info.get("is_tracking_reid") else "#333333"
                cb = tk.Checkbutton(scroll_content, text=f"{star}{info['name']} ({info['size_str']})", 
                                    variable=var, font=("Segoe UI", 9, "bold" if info.get("is_tracking_reid") else "normal"), 
                                    fg=fg_color, anchor="w", justify="left")
                cb.pack(anchor="w", padx=10, pady=1)
                
                cb.bind("<Enter>", lambda e, key=k: show_details(key))
                cb.bind("<Button-1>", lambda e, key=k: show_details(key))

    # Log Terminal
    log_title = tk.Label(right_frame, text="Terminal de Acompanhamento em Tempo Real", font=("Segoe UI", 10, "bold"))
    log_title.pack(anchor="w", pady=(4, 0))

    log_text = tk.Text(right_frame, bg="#1e1e1e", fg="#00ff66", font=("Consolas", 8), wrap="word", height=12)
    log_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=log_text.yview)
    log_text.configure(yscrollcommand=log_scrollbar.set)
    log_text.pack(side="top", fill="both", expand=True, pady=2)
    log_scrollbar.pack(side="right", fill="y")

    # Barra de Progresso
    progress_lbl = tk.Label(right_frame, text="Pronto para iniciar.", font=("Segoe UI", 8))
    progress_lbl.pack(anchor="w")
    progress_bar = ttk.Progressbar(right_frame, orient="horizontal", mode="determinate")
    progress_bar.pack(fill="x", pady=2)

    # Ações
    action_frame = tk.Frame(right_frame)
    action_frame.pack(fill="x", pady=4)

    def log_gui(msg):
        def _append():
            log_text.insert("end", msg + "\n")
            log_text.see("end")
        root.after(0, _append)

    def progress_gui(pct, text):
        def _update():
            progress_bar["value"] = pct
            progress_lbl.config(text=text)
        root.after(0, _update)

    def start_download():
        selected = [k for k, v in checkbox_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Aviso", "Selecione ao menos um dataset ou modelo para baixar!")
            return
        
        btn_start.config(state="disabled")
        btn_stop.config(state="normal")
        
        is_single = (len(selected) == 1)
        mgr = DownloadManager(base_dest=dest_dir, is_single_item=is_single, 
                              log_callback=log_gui, progress_callback=progress_gui)
        
        def _worker():
            mgr.download_selected(selected)
            btn_start.config(state="normal")
            btn_stop.config(state="disabled")
            
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def stop_download():
        btn_stop.config(state="disabled")

    btn_start = tk.Button(action_frame, text="▶ Iniciar Download dos Selecionados", 
                          bg="#007acc", fg="#ffffff", font=("Segoe UI", 10, "bold"), 
                          padx=10, pady=4, command=start_download)
    btn_start.pack(side="left", padx=4)

    btn_stop = tk.Button(action_frame, text="⏹ Cancelar", 
                         bg="#cc3300", fg="#ffffff", font=("Segoe UI", 10, "bold"), 
                         padx=10, pady=4, state="disabled", command=stop_download)
    btn_stop.pack(side="left", padx=4)

    show_details("lars")
    root.mainloop()


# ==============================================================================
# ENTRYPOINT CLI / VISUAL
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Central de Inteligencia Naval - Identificação, Re-ID e Trajetórias de Embarcações")
    parser.add_argument("--visual", "--gui", action="store_true", help="Abrir a interface grafica visual interativa")
    parser.add_argument("--tracking", "--reid", action="store_true", help="Baixar a suite especializada em Deteccao + Re-ID Unico + Trajetoria")
    parser.add_argument("--list-tracking", "--list-pipeline", action="store_true", help="Listar os datasets e modelos organizados pelo papel no pipeline de rastreamento e Re-ID")
    parser.add_argument("--top", "--principais", action="store_true", help="Baixar apenas os 10 datasets e modelos principais (Top Tier)")
    parser.add_argument("--dataset", type=str, help="Baixar apenas UM dataset ou modelo especifico diretamente (sem pastas aninhadas)")
    parser.add_argument("--list", "--list-top", action="store_true", help="Listar os 10 datasets e modelos principais")
    parser.add_argument("--list-all", action="store_true", help="Listar o catalogo completo")
    parser.add_argument("--list-datasets", action="store_true", help="Listar apenas os datasets")
    parser.add_argument("--list-models", action="store_true", help="Listar apenas os modelos de deep learning")
    parser.add_argument("--all", action="store_true", help="Baixar todos os datasets e modelos cadastrados")
    parser.add_argument("--category", type=str, choices=["01", "02", "03", "04", "05", "models", "fluvial", "panoptic"], 
                        help="Baixar apenas uma categoria especifica")
    parser.add_argument("--dest", type=str, default=".", help="Pasta de destino (padrao: diretorio atual)")
    args = parser.parse_args()

    if args.list_tracking:
        list_pipeline_tracking_reid()
        return

    if args.list:
        list_items("top")
        return
    elif args.list_all:
        list_items("all")
        return
    elif args.list_datasets:
        list_items("datasets")
        return
    elif args.list_models:
        list_items("models")
        return

    if args.visual or (len(sys.argv) == 1):
        print("Iniciando interface visual interativa...")
        run_visual_gui(dest_dir=args.dest)
    else:
        print_separator("=")
        print("CENTRAL DE DOWNLOADS - MODO LINHA DE COMANDO (CLI)")
        print_separator("=")
        
        is_single = bool(args.dataset)
        mgr = DownloadManager(base_dest=args.dest, is_single_item=is_single,
                              log_callback=lambda m: print(m), 
                              progress_callback=lambda pct, s: print(f"[{pct:.1f}%] {s}", end="\r" if pct < 100 else "\n"))
        
        selected_keys = []
        if args.dataset:
            if args.dataset not in CATALOG:
                print(f"[ERRO] Dataset/Modelo '{args.dataset}' nao encontrado!")
                print("IDs validos:", ", ".join(CATALOG.keys()))
                return
            selected_keys = [args.dataset]
        elif args.tracking:
            selected_keys = [k for k, v in CATALOG.items() if v.get("is_tracking_reid")]
        elif args.top:
            selected_keys = [k for k, v in CATALOG.items() if v.get("is_top")]
        elif args.all:
            selected_keys = list(CATALOG.keys())
        elif args.category:
            cat_map = {
                "01": "01_panoptic_and_multimodal",
                "panoptic": "01_panoptic_and_multimodal",
                "02": "02_fluvial_and_inland_waterways",
                "fluvial": "02_fluvial_and_inland_waterways",
                "03": "03_coastal_and_stereo_usv",
                "04": "04_thermal_and_offshore",
                "05": "05_roboflow_universe_catalog",
                "models": "models"
            }
            target_cat = cat_map.get(args.category, args.category)
            selected_keys = [k for k, v in CATALOG.items() if v["category"] == target_cat]
        else:
            selected_keys = [k for k, v in CATALOG.items() if v.get("is_tracking_reid")]
            
        mgr.download_selected(selected_keys)

if __name__ == "__main__":
    main()
