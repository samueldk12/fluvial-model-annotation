"""
Script de Download e Extracao do Dataset LaRS (ICCV 2023 / University of Ljubljana)
Panoptic Maritime and Fluvial Obstacle Detection Dataset and Benchmark
Website: https://lojzezust.github.io/lars-dataset/
"""

import os
import urllib.request
import zipfile
import time

def download_file(url, target_path, desc):
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        print(f"[JA EXISTE] {desc}: {target_path} ({os.path.getsize(target_path) / (1024*1024):.2f} MB)")
        return
    print(f"Baixando {desc} de {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp, open(target_path, 'wb') as out_f:
        total = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        chunk_size = 1024 * 1024
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                percent = (downloaded / total) * 100
                print(f"\r  Progresso: {percent:.1f}% ({downloaded / (1024*1024):.1f}/{total / (1024*1024):.1f} MB)", end='', flush=True)
        print()
    print(f"[OK] {desc} salvo em: {target_path}")

def extract_zip(zip_path, target_dir):
    print(f"Extraindo {zip_path} em {target_dir}...")
    t0 = time.time()
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(target_dir)
    print(f"[OK] Extraido com sucesso em {time.time() - t0:.2f} s.")

def main():
    dest_dir = 'datasets/LaRS'
    os.makedirs(dest_dir, exist_ok=True)
    
    # 1. Anotacoes
    ann_url = 'https://box.vicos.si/lars/lars_v1.0.0_annotations.zip'
    ann_zip = os.path.join(dest_dir, 'lars_v1.0.0_annotations.zip')
    download_file(ann_url, ann_zip, 'LaRS Annotations (v1.0.0)')
    extract_zip(ann_zip, dest_dir)
    
    # 2. Imagens
    img_url = 'https://box.vicos.si/lars/lars_v1.0.0_images.zip'
    img_zip = os.path.join(dest_dir, 'lars_v1.0.0_images.zip')
    download_file(img_url, img_zip, 'LaRS Single-Frame Images (v1.0.0 - 966 MB)')
    extract_zip(img_zip, dest_dir)
    
    print("\n[SUCESSO] Dataset LaRS completamente instalado e pronto para treino/avaliacao.")

if __name__ == '__main__':
    main()
