"""
Script para baixar o devkit oficial do WaterScenes e scripts do WSODD
"""

import os
import urllib.request
import base64
import json

def fetch_github_file(repo, file_path, save_path):
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        content = base64.b64decode(data['content'])
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(content)
        print(f"[OK] Baixado: {save_path}")
    except Exception as e:
        print(f"Erro ao baixar {repo}/{file_path}:", e)

def main():
    # 1. WSODD
    wsodd_dir = 'datasets/fluvial/WSODD'
    os.makedirs(wsodd_dir, exist_ok=True)
    fetch_github_file('sunjiaen/WSODD', 'VOC2COCO.py', os.path.join(wsodd_dir, 'VOC2COCO.py'))
    fetch_github_file('sunjiaen/WSODD', 'README.md', os.path.join(wsodd_dir, 'README.md'))
    
    # 2. WaterScenes DevKit
    ws_dir = 'datasets/fluvial/WaterScenes/devkit'
    os.makedirs(ws_dir, exist_ok=True)
    ws_files = ['Config.py', 'DataLoader.py', 'Transformation.py', 'WaterScenes.py', '__init__.py', 'api.py']
    for f in ws_files:
        fetch_github_file('WaterScenes/WaterScenes', f'WaterScenes/{f}', os.path.join(ws_dir, f))
    fetch_github_file('WaterScenes/WaterScenes', 'requirements.txt', os.path.join(ws_dir, 'requirements.txt'))

if __name__ == '__main__':
    main()
