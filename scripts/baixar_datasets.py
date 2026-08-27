#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT PARA DOWNLOAD COMPLETO DE DATASETS (IMAGENS/ANOTACOES) E MODELOS AQUATICOS
================================================================================
A Opcao 1 (--tracking) baixa TODOS os conjuntos de dados necessarios para:
1. DETECTAR BARCOS (Imagens reais de barcos, rios, satelite, radar e drones).
2. IDENTIFICAR UNICAMENTE CADA BARCO (Re-ID, embeddings finos e metadados IMO).
3. ANALISAR TRAJETORIAS E RUMO (Sequencias de video, Radar 4D e telemetria).
================================================================================
"""

import concurrent.futures
import json
import os
import shutil
import sys
import time
import urllib.request
import zipfile

# Forçar codificação UTF-8 no Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# BASE DE DADOS COMPLETA: DATASETS PESADOS (IMAGENS) + MODELOS DEEP LEARNING
# ==============================================================================
DATASETS = {
    # --------------------------------------------------------------------------
    # 01. PANÓPTICOS E MULTIMODAIS (IMAGENS COMPLETAS DE BARCOS E RIOS)
    # --------------------------------------------------------------------------
    "lars": {
        "name": "LaRS - Imagens e Anotacoes Completas (ICCV 2023)",
        "folder": "01_panoptic_and_multimodal/LaRS",
        "short": "LaRS",
        "size": "~988 MB (Dataset Completo com Imagens)",
        "is_dataset": True,
        "is_top": True,
        "is_tracking": True,
        "role": "Dataset Completo: Fotos de Barcos em Rios, Lagos e Mar com Segmentacao Panoptica",
        "urls": [
            ("https://box.vicos.si/lars/lars_v1.0.0_images.zip", "lars_v1.0.0_images.zip"),
            ("https://box.vicos.si/lars/lars_v1.0.0_annotations.zip", "lars_v1.0.0_annotations.zip"),
            ("https://github.com/lojzezust/lars_evaluator/archive/refs/heads/master.zip", "LaRS_evaluator.zip")
        ]
    },
    "waterscenes": {
        "name": "WaterScenes Multi-Task 4D Radar-Camera Benchmark",
        "folder": "01_panoptic_and_multimodal/WaterScenes_4DRadar",
        "short": "WaterScenes_4DRadar",
        "size": "~7.8 MB (DevKit & Ferramentas 4D)",
        "is_dataset": True,
        "is_top": True,
        "is_tracking": True,
        "role": "Dataset/DevKit: Fusao Radar 4D Doppler + Cameras para Rastreamento e Rumo",
        "urls": [
            ("https://github.com/WaterScenes/WaterScenes/archive/refs/heads/main.zip", "WaterScenes_DevKit.zip")
        ]
    },

    # --------------------------------------------------------------------------
    # 02. FLUVIAIS E HIDROVIAS (IMAGENS DE RIOS E CALHAS NAVEGÁVEIS)
    # --------------------------------------------------------------------------
    "elwha_river": {
        "name": "Elwha River - Dataset de Imagens em Alta Resolucao",
        "folder": "02_fluvial_and_inland_waterways/Elwha_River_Segmentation",
        "short": "Elwha_River_Segmentation",
        "size": "~1.38 GB (1.508 Imagens e Mascaras)",
        "is_dataset": True,
        "is_top": True,
        "is_tracking": True,
        "role": "Dataset Completo: Mapeamento de Rios, Calhas de Navegacao e Bancos de Areia",
        "urls": [
            ("https://huggingface.co/datasets/stodoran/elwha-segmentation-v1/resolve/main/data/train-00000-of-00003.parquet", "Elwha_train_part1.parquet"),
            ("https://huggingface.co/datasets/stodoran/elwha-segmentation-v1/resolve/main/data/train-00001-of-00003.parquet", "Elwha_train_part2.parquet"),
            ("https://huggingface.co/datasets/stodoran/elwha-segmentation-v1/resolve/main/data/train-00002-of-00003.parquet", "Elwha_train_part3.parquet"),
            ("https://huggingface.co/datasets/stodoran/elwha-segmentation-v1/resolve/main/data/validation-00000-of-00001.parquet", "Elwha_val.parquet"),
            ("https://huggingface.co/datasets/stodoran/elwha-segmentation-v1/resolve/main/README.md", "README.md")
        ]
    },
    "iwhr_floater": {
        "name": "IWHR Floater V1 - Toolkit e Amostras de Barcos Fluviais",
        "folder": "02_fluvial_and_inland_waterways/IWHR_Floater_V1",
        "short": "IWHR_Floater_V1",
        "size": "~0.01 MB (Toolkit Fluvial)",
        "is_dataset": True,
        "is_top": True,
        "is_tracking": True,
        "role": "Dataset/Toolkit: Deteccao de Embarcacoes e Objetos Flutuantes em Rios",
        "urls": [
            ("https://github.com/sunjiaen/WSODD/archive/refs/heads/main.zip", "IWHR_Floater_Toolkit.zip")
        ]
    },

    # --------------------------------------------------------------------------
    # 03. ESTEREOSCOPIA E DISTÂNCIA MÉTRICA DE EMBARCAÇÕES
    # --------------------------------------------------------------------------
    "modd2": {
        "name": "MODD2 - 28 Sequencias de Video Estereo + GPS",
        "folder": "03_coastal_and_stereo_usv/MODD2_Stereo",
        "short": "MODD2_Stereo",
        "size": "~7.0 MB (Anotacoes, Mascaras e GPS)",
        "is_dataset": True,
        "is_top": False,
        "is_tracking": True,
        "role": "Dataset de Sequencias Temporais: Medicao Metrica de Distancia e Vetor de Rota",
        "urls": [
            ("https://box.vicos.si/borja/modd2_dataset/MODD2_annotations_v2.zip", "MODD2_annotations_v2.zip"),
            ("https://box.vicos.si/borja/modd2_dataset/MODD2_GPS_data.zip", "MODD2_GPS_data.zip"),
            ("https://box.vicos.si/borja/modd2_dataset/MODD2_USVparts_masks.zip", "MODD2_USVparts_masks.zip")
        ]
    },

    # --------------------------------------------------------------------------
    # 04. RE-ID (IMO) E RADAR SAR (IMAGENS REAIS DE NAVIOS)
    # --------------------------------------------------------------------------
    "sar_ship_detection": {
        "name": "SAR Ship Detection - 2.320 Imagens de Radar SAR",
        "folder": "04_thermal_and_offshore/SAR_Ship_Detection",
        "short": "SAR_Ship_Detection",
        "size": "~88 MB (2.320 Imagens de Navios e JSONs)",
        "is_dataset": True,
        "is_top": True,
        "is_tracking": True,
        "role": "Dataset Completo: 2.320 Fotos de Navios em Radar SAR para Deteccao Noturna",
        "hf_dataset": "agungpambudi/sar-ship-detection",
        "zip_name": "sar_ship_detection.zip",
        "urls": [
            ("https://huggingface.co/datasets/agungpambudi/sar-ship-detection/resolve/main/README.md", "README.md")
        ]
    },
    "marvel_2016": {
        "name": "MARVEL 2016 - Identificacao Unica de Barcos (IMO Re-ID)",
        "folder": "04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval",
        "short": "MARVEL_2016_Vessel_Retrieval",
        "size": "~8.3 MB (Metadados IMO e Ferramentas)",
        "is_dataset": True,
        "is_top": True,
        "is_tracking": True,
        "role": "Dataset de Re-ID: Associacao de Fotos com Numero IMO Unico de Cada Embarcacao",
        "urls": [
            ("https://github.com/avaapm/marveldataset2016/archive/refs/heads/master.zip", "MARVEL_2016_dataset.zip")
        ]
    },

    # --------------------------------------------------------------------------
    # 05. ROBOFLOW UNIVERSE (10 DATASETS DE BARCOS PRONTOS PARA YOLO)
    # --------------------------------------------------------------------------
    "roboflow_suite": {
        "name": "Roboflow Universe - 10 Datasets Individuais de Barcos",
        "folder": "05_roboflow_universe_catalog",
        "short": "Roboflow_Universe_Suite",
        "size": "~0.05 MB (Configs e Estrutura dos 10 Datasets)",
        "is_dataset": True,
        "is_top": False,
        "is_tracking": True,
        "role": "10 Datasets de Barcos: Coruna (12 classes), Drones Aereos, Cameras NIR e Portuarias",
        "urls": []
    },

    # --------------------------------------------------------------------------
    # 06. MODELOS DE DEEP LEARNING PRÉ-TREINADOS
    # --------------------------------------------------------------------------
    "model_y8naval": {
        "name": "Modelo: SixOpen Y8Naval ONNX (50 Classes Navais Satélite)",
        "folder": "models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX",
        "short": "SixOpen_Y8NavalONNX",
        "size": "~101 MB (Pesos Neurais ONNX)",
        "is_dataset": False,
        "is_top": True,
        "is_tracking": True,
        "role": "Modelo: Deteccao de 50 Tipos de Barcos em Fotos Orbitais e Aereas",
        "urls": [
            ("https://huggingface.co/SixOpen/Y8NavalONNX/resolve/main/Y8Naval.onnx", "Y8Naval.onnx"),
            ("https://huggingface.co/SixOpen/Y8NavalONNX/resolve/main/config.json", "config.json"),
            ("https://huggingface.co/SixOpen/Y8NavalONNX/resolve/main/README.md", "README.md")
        ]
    },
    "model_sar_vessel": {
        "name": "Modelo: MeWan2808 YOLOv8 SAR Vessel (38 ms Borda)",
        "folder": "models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR",
        "short": "MeWan2808_YOLOv8_SAR",
        "size": "~12 MB (Pesos ONNX + PyTorch)",
        "is_dataset": False,
        "is_top": True,
        "is_tracking": True,
        "role": "Modelo: Deteccao Ultra-Rapida (38 ms) para Rastreamento de Rota em Tempo Real",
        "urls": [
            ("https://huggingface.co/MeWan2808/yolov8n-sar-vessel-detection/resolve/main/quantized/best.onnx", "best.onnx"),
            ("https://huggingface.co/MeWan2808/yolov8n-sar-vessel-detection/resolve/main/unquantized/best.pt", "best.pt"),
            ("https://huggingface.co/MeWan2808/yolov8n-sar-vessel-detection/resolve/main/README.md", "README.md")
        ]
    },
    "model_marine_vessel": {
        "name": "Modelo: mayrajeo YOLOv8n Marine Vessel Detection",
        "folder": "models/02_sar_radar_and_edge/mayrajeo_YOLOv8_Marine_Vessel",
        "short": "mayrajeo_YOLOv8_Marine_Vessel",
        "size": "~6 MB (Pesos PyTorch)",
        "is_dataset": False,
        "is_top": False,
        "is_tracking": True,
        "role": "Modelo: Monitoramento de Fluxo de Embarcacoes em Cameras Costeiras e Fluviais",
        "urls": [
            ("https://huggingface.co/mayrajeo/marine-vessel-detection-yolov8/resolve/main/YOLOv8n/yolov8n.pt", "yolov8n.pt"),
            ("https://huggingface.co/mayrajeo/marine-vessel-detection-yolov8/resolve/main/README.md", "README.md")
        ]
    },
    "model_river_seg": {
        "name": "Modelo: beaunix River Semantic Segmentation (PyTorch)",
        "folder": "models/02_sar_radar_and_edge/beaunix_River_Segmentation",
        "short": "beaunix_River_Segmentation",
        "size": "~104 MB (Checkpoints PyTorch)",
        "is_dataset": False,
        "is_top": True,
        "is_tracking": True,
        "role": "Modelo: Segmentacao da Calha Fluvial e Borda da Agua para Corredores de Rota",
        "urls": [
            ("https://huggingface.co/beaunix/river-segmentation/resolve/main/best_model.pt", "best_model.pt"),
            ("https://huggingface.co/beaunix/river-segmentation/resolve/main/README.md", "README.md")
        ]
    },
    "model_vit_vessel": {
        "name": "Modelo: dima806 ViT Vessel Classifier (Vision Transformer)",
        "folder": "models/03_vessel_transformers/dima806_ViT_Vessel_Classification",
        "short": "dima806_ViT_Vessel_Classification",
        "size": "~327 MB (Safetensors + Configs)",
        "is_dataset": False,
        "is_top": True,
        "is_tracking": True,
        "role": "Modelo: Extracao de Impressao Digital de 768 dimensoes para Re-ID Unico de Barcos",
        "urls": [
            ("https://huggingface.co/dima806/vessel_ship_types_image_detection/resolve/main/model.safetensors", "model.safetensors"),
            ("https://huggingface.co/dima806/vessel_ship_types_image_detection/resolve/main/config.json", "config.json"),
            ("https://huggingface.co/dima806/vessel_ship_types_image_detection/resolve/main/preprocessor_config.json", "preprocessor_config.json"),
            ("https://huggingface.co/dima806/vessel_ship_types_image_detection/resolve/main/README.md", "README.md")
        ]
    }
}

# ==============================================================================
# MOTOR DE DOWNLOAD E GERENCIAMENTO
# ==============================================================================
def download_file(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    temp_path = dest_path + ".download"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()
            last_print = start_time
            last_downloaded = 0
            with open(temp_path, "wb") as out_file:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_print >= 0.5:
                        speed = (downloaded - last_downloaded) / (now - last_print) / (1024 * 1024)
                        dl_mb = downloaded / (1024 * 1024)
                        if total_size > 0:
                            pct = (downloaded / total_size * 100)
                            tot_mb = total_size / (1024 * 1024)
                            print(f"  -> Progresso: {pct:.1f}% ({dl_mb:.1f}/{tot_mb:.1f} MB) | Velocidade: {speed:.2f} MB/s", end="\r")
                        else:
                            print(f"  -> Baixado: {dl_mb:.1f} MB | Velocidade: {speed:.2f} MB/s", end="\r")
                        last_print = now
                        last_downloaded = downloaded
            print()
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(temp_path, dest_path)
        return True
    except Exception as e:
        print(f"\n[ERRO no Download] {url}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def process_download(item_key, base_dest=".", single_mode=False):
    info = DATASETS[item_key]
    category_type = "📦 DATASET DE IMAGENS/DADOS" if info.get("is_dataset") else "🧠 MODELO DE DEEP LEARNING"
    
    print("\n" + "=" * 85)
    print(f"Iniciando: [{category_type}] {info['name']}")
    print(f"Finalidade: {info['role']}")
    print(f"Tamanho estimado: {info['size']}")
    print("=" * 85)
    
    if single_mode:
        target_dir = os.path.join(base_dest, info["short"])
    else:
        target_dir = os.path.join(base_dest, "datasets" if not info["folder"].startswith("models") else "", info["folder"])
        
    os.makedirs(target_dir, exist_ok=True)
    
    # Se for HF dataset com snapshot ou links diretos
    if "hf_dataset" in info:
        print(f"Baixando pacote completo de imagens ({info['hf_dataset']})...")
        try:
            from huggingface_hub import snapshot_download
            temp_hf = os.path.join(target_dir, "hf_temp")
            snapshot_download(repo_id=info["hf_dataset"], repo_type="dataset", local_dir=temp_hf)
            dest_zip = os.path.join(target_dir, info.get("zip_name", "dataset.zip"))
            print("Compactando em arquivo .zip padronizado...")
            with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_hf):
                    for f in files:
                        fp = os.path.join(root, f)
                        zf.write(fp, os.path.relpath(fp, temp_hf))
            shutil.rmtree(temp_hf, ignore_errors=True)
            print(f"[OK] {info['zip_name']} gerado com sucesso!")
        except Exception:
            pass

    # Roboflow suite
    if item_key == "roboflow_suite":
        print("Configurando as 10 pastas dedicadas com arquivos .zip e data.yaml do Roboflow...")
        try:
            from scripts.setup_roboflow_individual_datasets import main as setup_rf
            setup_rf()
            print("[OK] 10 Datasets do Roboflow configurados!")
        except Exception:
            pass
            
    success_count = 0
    for url, filename in info.get("urls", []):
        dest_file = os.path.join(target_dir, filename)
        print(f"Baixando [{filename}]...")
        if download_file(url, dest_file):
            sz_mb = os.path.getsize(dest_file) / (1024 * 1024)
            print(f"[OK] {filename} salvo com sucesso ({sz_mb:.2f} MB)")
            success_count += 1
            
    print(f"Concluido: {info['name']} -> Salvo em '{target_dir}'")
    return success_count > 0

# ==============================================================================
# INTERFACE E LISTAGENS
# ==============================================================================
def list_available():
    print("=" * 100)
    print(f"{'#':<3} | {'Tipo':<9} | {'ID':<18} | {'Nome do Dataset / Modelo':<40} | {'Tamanho'}")
    print("-" * 100)
    for idx, (k, info) in enumerate(DATASETS.items(), 1):
        tipo = "DATASET" if info.get("is_dataset") else "MODELO"
        print(f"{idx:<3} | {tipo:<9} | {k:<18} | {info['name'][:38]:<40} | {info['size']}")
        print(f"    └─ Papel: {info['role']}\n")
    print("=" * 100)

def interactive_menu():
    while True:
        print("\n" + "=" * 75)
        print("CENTRAL DE DOWNLOAD DE DATASETS E MODELOS AQUATICOS (PYTHON PURO)")
        print("=" * 75)
        print("1. 🎯 Baixar Suite COMPLETA: DATASETS DE IMAGENS + MODELOS + RE-ID + TRAJETORIA")
        print("2. 📦 Baixar Apenas os DATASETS DE IMAGENS E ANOTACOES (LaRS, Elwha, SAR, etc.)")
        print("3. 🧠 Baixar Apenas os MODELOS DE DEEP LEARNING (ONNX, PyTorch, YOLO, ViT)")
        print("4. ⭐ Baixar os 10 PRINCIPAIS (Top Tier)")
        print("5. 🔍 Baixar UM Dataset Especifico (Direto na pasta, sem aninhamento)")
        print("6. 📋 Listar Todos os Datasets e Modelos Disponiveis")
        print("0. Sair")
        print("=" * 75)
        
        opt = input("Escolha uma opcao (0-6): ").strip()
        if opt == "1":
            keys = [k for k, v in DATASETS.items() if v.get("is_tracking")]
            print(f"\nIniciando download da Suíte Completa ({len(keys)} componentes: Datasets + Modelos)...")
            for k in keys:
                process_download(k)
        elif opt == "2":
            keys = [k for k, v in DATASETS.items() if v.get("is_dataset")]
            print(f"\nIniciando download de {len(keys)} Datasets de Imagens...")
            for k in keys:
                process_download(k)
        elif opt == "3":
            keys = [k for k, v in DATASETS.items() if not v.get("is_dataset")]
            print(f"\nIniciando download de {len(keys)} Modelos de Deep Learning...")
            for k in keys:
                process_download(k)
        elif opt == "4":
            keys = [k for k, v in DATASETS.items() if v.get("is_top")]
            print(f"\nIniciando download de {len(keys)} itens principais...")
            for k in keys:
                process_download(k)
        elif opt == "5":
            list_available()
            item_id = input("Digite o ID desejado (ex: lars, elwha_river, model_sar_vessel): ").strip()
            if item_id in DATASETS:
                process_download(item_id, single_mode=True)
            else:
                print(f"[ERRO] ID '{item_id}' invalido!")
        elif opt == "6":
            list_available()
        elif opt == "0":
            print("Encerrando.")
            break
        else:
            print("Opcao invalida. Tente novamente.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Downloader 100% em Python Puro para Datasets de Imagens e Modelos Aquáticos")
    parser.add_argument("--all", action="store_true", help="Baixar todos os datasets e modelos cadastrados")
    parser.add_argument("--tracking", "--reid", action="store_true", help="Baixar a suite completa (Datasets de Imagens + Modelos de Re-ID e Trajetoria)")
    parser.add_argument("--datasets-only", action="store_true", help="Baixar apenas os datasets de imagens/anotações")
    parser.add_argument("--models-only", action="store_true", help="Baixar apenas os modelos neurais")
    parser.add_argument("--top", action="store_true", help="Baixar apenas os principais")
    parser.add_argument("--dataset", type=str, help="Baixar apenas UM dataset/modelo diretamente (ex: --dataset lars)")
    parser.add_argument("--list", action="store_true", help="Listar todos os datasets e modelos cadastrados")
    parser.add_argument("--dest", type=str, default=".", help="Diretorio de destino (padrao: pasta atual)")
    args = parser.parse_args()

    if args.list:
        list_available()
        return

    if args.dataset:
        if args.dataset not in DATASETS:
            print(f"[ERRO] ID '{args.dataset}' nao encontrado!")
            print("IDs disponiveis:", ", ".join(DATASETS.keys()))
            return
        process_download(args.dataset, base_dest=args.dest, single_mode=True)
    elif args.datasets_only:
        keys = [k for k, v in DATASETS.items() if v.get("is_dataset")]
        for k in keys:
            process_download(k, base_dest=args.dest)
    elif args.models_only:
        keys = [k for k, v in DATASETS.items() if not v.get("is_dataset")]
        for k in keys:
            process_download(k, base_dest=args.dest)
    elif args.tracking:
        keys = [k for k, v in DATASETS.items() if v.get("is_tracking")]
        for k in keys:
            process_download(k, base_dest=args.dest)
    elif args.top:
        keys = [k for k, v in DATASETS.items() if v.get("is_top")]
        for k in keys:
            process_download(k, base_dest=args.dest)
    elif args.all:
        for k in DATASETS:
            process_download(k, base_dest=args.dest)
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
