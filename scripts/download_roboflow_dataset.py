"""
Script Utilitario para Download de Datasets do Roboflow Universe via Roboflow Python API
Permite baixar qualquer um dos datasets do catalogo Roboflow Universe nos formatos YOLOv8, COCO ou Pascal VOC.
"""

import argparse
import os
import sys

def download_roboflow(workspace, project, version=1, model_format='yolov8', api_key=None, dest_dir=None):
    try:
        from roboflow import Roboflow
    except ImportError:
        print("[AVISO] Pacote 'roboflow' nao instalado. Instalando via pip...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'roboflow'], check=True)
        from roboflow import Roboflow
        
    if not api_key:
        api_key = os.environ.get('ROBOFLOW_API_KEY')
        
    if not api_key:
        print("Erro: Chave de API do Roboflow (ROBOFLOW_API_KEY) nao fornecida.")
        print("Obtenha sua chave gratuita em https://app.roboflow.com/")
        print(f"Exemplo de uso: python scripts/download_roboflow_dataset.py --workspace {workspace} --project {project} --api-key SUA_CHAVE")
        return False
        
    rf = Roboflow(api_key=api_key)
    proj = rf.workspace(workspace).project(project)
    print(f"Baixando dataset {workspace}/{project} (versao {version}) no formato {model_format}...")
    dataset = proj.version(version).download(model_format, location=dest_dir)
    print(f"[SUCESSO] Dataset baixado em: {dataset.location}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Roboflow Universe Dataset Downloader')
    parser.add_argument('--workspace', type=str, default='university-of-coruna', help='Nome do workspace no Roboflow')
    parser.add_argument('--project', type=str, default='ship-type-detection', help='Nome do projeto')
    parser.add_argument('--version', type=int, default=1, help='Versao do dataset')
    parser.add_argument('--format', type=str, default='yolov8', help='Formato (yolov8, coco, voc, etc.)')
    parser.add_argument('--api-key', type=str, help='Chave de API do Roboflow')
    parser.add_argument('--dest', type=str, help='Diretorio de destino')
    args = parser.parse_args()
    
    download_roboflow(args.workspace, args.project, args.version, args.format, args.api_key, args.dest)

if __name__ == '__main__':
    main()
