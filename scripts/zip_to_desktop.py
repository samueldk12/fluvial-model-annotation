"""
Script para Compactar o Repositorio Inteiro e Salvar na Area de Trabalho como 'fluvial_dataset.zip'.
Otimizado com caminhos relativos portateis e velocidade maxima de empacotamento.
"""

import os
import sys
import time
import zipfile

def main():
    root_dir = os.path.abspath(".")
    folder_name = "fluvial_dataset"
    desktop_dir = os.path.expanduser("~/Desktop")
    output_zip = os.path.join(desktop_dir, f"{folder_name}.zip")
    
    print("=" * 85)
    print(f"COMPACTANDO REPOSITORIO PARA A AREA DE TRABALHO: {output_zip}")
    print(f"Origem:  {root_dir}")
    print("=" * 85)
    
    files_to_zip = []
    total_uncompressed_bytes = 0
    
    ignore_dirs = {".git", ".cache", "__pycache__", ".pytest_cache"}
    ignore_exts = {".pyc", ".tmp"}
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ignore_exts:
                continue
            fp = os.path.join(root, f)
            arcname = os.path.relpath(fp, root_dir)
            sz = os.path.getsize(fp)
            files_to_zip.append((fp, arcname, sz))
            total_uncompressed_bytes += sz
            
    total_files = len(files_to_zip)
    print(f"Total de arquivos a empacotar: {total_files}")
    print(f"Tamanho total dos dados: {total_uncompressed_bytes / (1024 * 1024 * 1024):.2f} GB")
    
    t0 = time.time()
    written_bytes = 0
    
    with zipfile.ZipFile(output_zip, "w", allowZip64=True) as zf:
        for idx, (fp, arcname, sz) in enumerate(files_to_zip, 1):
            if fp.lower().endswith(".zip"):
                compress_type = zipfile.ZIP_STORED
            else:
                compress_type = zipfile.ZIP_DEFLATED
                
            zf.write(fp, arcname, compress_type=compress_type)
            written_bytes += sz
            
            if idx % 25 == 0 or idx == total_files:
                pct = (written_bytes / total_uncompressed_bytes) * 100
                print(f"[{idx}/{total_files}] ({pct:.1f}%) Empacotado: {arcname}")
                
    elapsed = time.time() - t0
    final_size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    final_size_gb = final_size_mb / 1024
    
    print("\n" + "=" * 85)
    print("COMPACTACAO CONCLUIDA COM SUCESSO!")
    print(f"Arquivo gerado: {output_zip}")
    print(f"Tamanho final:  {final_size_gb:.2f} GB ({final_size_mb:.2f} MB)")
    print(f"Tempo total:    {elapsed:.1f} segundos")
    print("=" * 85)

if __name__ == "__main__":
    main()
