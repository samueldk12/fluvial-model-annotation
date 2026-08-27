"""
Setup e Organizacao dos Benchmarks Maritimos e Fluviais (MODD2, MaSTRe1325, MassMIND, MARVEL 2016, KOLOMVERSE)
"""

import os
import zipfile
import urllib.request
import json
import base64

def extract_to_dir(zip_path, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(target_dir)
    print(f"[OK] Extraido {zip_path} -> {target_dir}")

def fetch_github_file(repo, file_path, save_path):
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        content = base64.b64decode(data['content'])
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(content)
        print(f"[OK] GitHub file salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao baixar {repo}/{file_path}:", e)

def main():
    # 1. MaSTRe1325
    mastr_zip = 'datasets/MaSTRe1325/MaSTr1325_masks_512x384.zip'
    if os.path.exists(mastr_zip):
        extract_to_dir(mastr_zip, 'datasets/MaSTRe1325/masks')
        
    # 2. MODD2
    modd_zip = 'datasets/MODD2/MODD2_annotations_v2.zip'
    if os.path.exists(modd_zip):
        extract_to_dir(modd_zip, 'datasets/MODD2/annotations')
        
    # 3. MassMIND (LWIR Thermal Segmentation)
    massmind_dir = 'datasets/MassMIND'
    os.makedirs(massmind_dir, exist_ok=True)
    for f in ['README.md', 'Piechart_class_instances.png', 'CITATION.cff']:
        fetch_github_file('uml-marine-robotics/MassMIND', f, os.path.join(massmind_dir, f))
        
    # 4. MARVEL 2016 (Ship Retrieval & Classification)
    marvel_dir = 'datasets/MARVEL_2016'
    os.makedirs(marvel_dir, exist_ok=True)
    for f in ['README.md', 'MARVEL_Download.py', 'ReadMe.txt', 'VesselClassification.dat']:
        fetch_github_file('avaapm/marveldataset2016', f, os.path.join(marvel_dir, f))
        
    # 5. KOLOMVERSE
    kolom_dir = 'datasets/KOLOMVERSE'
    os.makedirs(kolom_dir, exist_ok=True)
    fetch_github_file('MaritimeDataset/KOLOMVERSE', 'README.md', os.path.join(kolom_dir, 'README.md'))
    
    print("\n[SUCESSO] Benchmarks organizados e configurados localmente.")

if __name__ == '__main__':
    main()
