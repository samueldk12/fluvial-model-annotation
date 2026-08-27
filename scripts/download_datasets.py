"""
Script Utilitario para Download e Gerenciamento de Datasets Maritimos, Navais e Fluviais
Permite baixar datasets do Hugging Face, Roboflow Universe e consultar benchmarks maritimos e fluviais.
"""

import argparse
import json
import os
import sys
from huggingface_hub import snapshot_download

MARITIME_MANIFEST_PATH = os.path.join(os.path.dirname(__file__), '..', 'datasets', 'bifrost_benchmarks', 'benchmark_manifest.json')
FLUVIAL_MANIFEST_PATH = os.path.join(os.path.dirname(__file__), '..', 'datasets', 'fluvial', 'fluvial_manifest.json')

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def list_datasets(domain='all'):
    if domain in ['all', 'maritime', 'naval']:
        data_mar = load_json(MARITIME_MANIFEST_PATH)
        print("=" * 85)
        print("DATASETS MARITIMOS E NAVAIS (BENCHMARK BIFROST & SEA-AI)")
        print("=" * 85)
        for ds in data_mar.get('datasets', []):
            scores = ds.get('scores', {})
            print(f"[{ds['id']}] {ds['name']} ({ds['year']}) - Score: {scores.get('total', 'N/A')}/15")
            print(f"   Tarefa: {ds['task']}")
            print(f"   Sensores: {', '.join(ds['sensors'])}")
            print(f"   URL: {ds['url']}")
            print(f"   Uso: {ds['use_case']}")
            print("-" * 85)

    if domain in ['all', 'fluvial', 'river']:
        data_fluv = load_json(FLUVIAL_MANIFEST_PATH)
        print("\n" + "=" * 85)
        print("DATASETS FLUVIAIS E HIDROVIAS INTERIORES (RIVER & INLAND WATERWAY AI)")
        print("=" * 85)
        for ds in data_fluv.get('datasets', []):
            print(f"[{ds['id']}] {ds['name']} ({ds['year']}) - Venue: {ds.get('venue', 'N/A')}")
            print(f"   Tarefa: {ds['task']}")
            print(f"   Sensores: {', '.join(ds['sensors'])}")
            print(f"   URL: {ds['url']}")
            print(f"   Uso: {ds['use_case']}")
            print("-" * 85)

def download_hf_dataset(repo_id, dest_dir):
    print(f"Baixando dataset do Hugging Face: {repo_id} para {dest_dir}...")
    os.makedirs(dest_dir, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        repo_type='dataset',
        local_dir=dest_dir
    )
    print(f"Download de {repo_id} finalizado com sucesso.")

def download_hf_model(repo_id, dest_dir):
    print(f"Baixando modelo do Hugging Face: {repo_id} para {dest_dir}...")
    os.makedirs(dest_dir, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        local_dir=dest_dir
    )
    print(f"Download de {repo_id} finalizado com sucesso.")

def main():
    parser = argparse.ArgumentParser(description='Gerenciador de Download de Datasets Maritimos e Fluviais')
    parser.add_argument('--list', action='store_true', help='Listar todos os datasets registrados')
    parser.add_argument('--domain', type=str, choices=['all', 'maritime', 'naval', 'fluvial'], default='all',
                        help='Dominio para listagem (maritime, fluvial ou all)')
    parser.add_argument('--dataset', type=str, choices=['seanet', 'crowdsourced', 'y8naval', 'sar_vessel', 'all_hf'],
                        help='Baixar um conjunto de dados especifico')
    parser.add_argument('--custom-hf-dataset', type=str, help='Baixar qualquer dataset HF especificando o repo_id')
    parser.add_argument('--custom-hf-model', type=str, help='Baixar qualquer modelo HF especificando o repo_id')
    args = parser.parse_args()

    if args.list or (len(sys.argv) == 1 and not args.dataset):
        list_datasets(args.domain)
        return

    if args.dataset == 'seanet':
        download_hf_dataset('SEA-AI/SEANet', 'datasets/sea_ai/SEANet')
    elif args.dataset == 'crowdsourced':
        download_hf_dataset('SEA-AI/crowdsourced-sea-images-v2', 'datasets/sea_ai/crowdsourced_sea_images_v2')
    elif args.dataset == 'y8naval':
        download_hf_model('SixOpen/Y8NavalONNX', 'models/SixOpen_Y8NavalONNX')
    elif args.dataset == 'sar_vessel':
        download_hf_model('MeWan2808/yolov8n-sar-vessel-detection', 'models/fluvial_and_radar/MeWan2808_YOLOv8_SAR_Vessel')
    elif args.dataset == 'all_hf':
        download_hf_model('SixOpen/Y8NavalONNX', 'models/SixOpen_Y8NavalONNX')
        download_hf_model('MeWan2808/yolov8n-sar-vessel-detection', 'models/fluvial_and_radar/MeWan2808_YOLOv8_SAR_Vessel')
        download_hf_dataset('SEA-AI/SEANet', 'datasets/sea_ai/SEANet')
        
    if args.custom_hf_dataset:
        repo_name = args.custom_hf_dataset.replace('/', '_')
        download_hf_dataset(args.custom_hf_dataset, f'datasets/{repo_name}')
        
    if args.custom_hf_model:
        repo_name = args.custom_hf_model.replace('/', '_')
        download_hf_model(args.custom_hf_model, f'models/{repo_name}')

if __name__ == '__main__':
    main()
