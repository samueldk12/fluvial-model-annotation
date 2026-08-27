"""
Download do dataset e scripts de benchmark IWHR_AI_Lable_Floater_V1 (Nature Scientific Data / Figshare)
Dataset para deteccao de detritos flutuantes e vegetacao em rios e hidrovias interiores.
"""

import os
import urllib.request
import zipfile

def download_file(url, target_path, desc):
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        print(f"[JA EXISTE] {desc}: {target_path}")
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

def main():
    dest_dir = 'datasets/fluvial/IWHR_Floater_V1'
    os.makedirs(dest_dir, exist_ok=True)
    
    # Scripts de treinamento e rotulagem VOC/YOLO
    scripts = [
        ('https://ndownloader.figshare.com/files/50253003', os.path.join(dest_dir, 'voc_label.py'), 'Script de Conversao VOC/YOLO'),
        ('https://ndownloader.figshare.com/files/50253006', os.path.join(dest_dir, 'split_train_val.py'), 'Script de Divisao Treino/Val'),
        ('https://ndownloader.figshare.com/files/50252958', os.path.join(dest_dir, 'ultralytics-main.zip'), 'Framework Ultralytics Benchmark')
    ]
    
    for url, path, desc in scripts:
        try:
            download_file(url, path, desc)
        except Exception as e:
            print(f"Erro ao baixar {desc}:", e)
            
    # Package 1 do dataset (~1 GB com imagens e anotações XML/VOC de detritos fluviais)
    pkg1_url = 'https://ndownloader.figshare.com/files/50111817'
    pkg1_zip = os.path.join(dest_dir, 'IWHR_AI_Lable_Floater_V1-package1.zip')
    try:
        download_file(pkg1_url, pkg1_zip, 'Package 1 (Imagens e Rotulos Fluviais)')
        print("Descompactando amostras do Package 1...")
        with zipfile.ZipFile(pkg1_zip, 'r') as zf:
            # Extrair os primeiros 100 arquivos para inspecao rapida
            members = zf.namelist()[:150]
            zf.extractall(dest_dir, members)
        print(f"[OK] Amostras extraidas em: {dest_dir}")
    except Exception as e:
        print("Erro ao baixar Package 1:", e)

if __name__ == '__main__':
    main()
