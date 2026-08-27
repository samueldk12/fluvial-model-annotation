"""
Download paralelo e robusto do dataset agungpambudi/sar-ship-detection do Hugging Face.
Baixa com 16 threads paralelas, retries e empacota automaticamente em .zip.
"""

import concurrent.futures
import json
import os
import shutil
import urllib.request
import zipfile

REPO_ID = "agungpambudi/sar-ship-detection"
TEMP_DIR = "temp_sar_ship"
TARGET_DIR = "datasets/04_thermal_and_offshore/SAR_Ship_Detection"
TARGET_ZIP = os.path.join(TARGET_DIR, "sar_ship_detection.zip")
ARCHIVE_ZIP = os.path.join("datasets/archives", "sar_ship_detection.zip")

def get_file_list():
    url = f"https://huggingface.co/api/datasets/{REPO_ID}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return [s.get("rfilename") for s in data.get("siblings", []) if s.get("rfilename") not in [".gitattributes", "README.md"]]

def download_one(filename):
    local_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return True
    
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    url = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/{filename}"
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp, open(local_path, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            return True
        except Exception:
            pass
    return False

def main():
    print("=" * 80)
    print("DOWNLOAD PARALELO DO DATASET SAR SHIP DETECTION")
    print("=" * 80)
    
    os.makedirs(TEMP_DIR, exist_ok=True)
    files = get_file_list()
    total = len(files)
    print(f"Total de arquivos no dataset: {total}")
    
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(download_one, f): f for f in files}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                completed += 1
            if completed % 250 == 0 or completed == total:
                print(f"Progresso: {completed}/{total} arquivos baixados ({(completed/total)*100:.1f}%)")
                
    print(f"\n[OK] Todos os {completed} arquivos foram baixados com sucesso!")
    
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"Compactando arquivos para {TARGET_ZIP}...")
    with zipfile.ZipFile(TARGET_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, f_list in os.walk(TEMP_DIR):
            for f in f_list:
                fp = os.path.join(root, f)
                arcname = os.path.relpath(fp, TEMP_DIR)
                zf.write(fp, arcname)
                
    sz_mb = os.path.getsize(TARGET_ZIP) / (1024 * 1024)
    print(f"[CONCLUIDO] Arquivo ZIP gerado: {TARGET_ZIP} ({sz_mb:.2f} MB)")
    
    # Backup em archives
    os.makedirs("datasets/archives", exist_ok=True)
    shutil.copy2(TARGET_ZIP, ARCHIVE_ZIP)
    print(f"[COPIADO] {ARCHIVE_ZIP}")
    
    # Limpeza
    shutil.rmtree(TEMP_DIR)
    print("[LIMPEZA] Diretorio temporario removido com sucesso!")

if __name__ == "__main__":
    main()
