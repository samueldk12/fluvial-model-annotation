"""
Script de Conversao de Caminhos Absolutos para Relativos a Pasta Raiz.
Garante que todas as documentacoes (.md), configuracoes (.yaml), listas (.txt) e manifestos (.json)
utilizem exclusivamente caminhos relativos portateis (ex: datasets/..., models/..., scripts/...).
"""

import os

REPLACEMENTS = [
    ("./", "./"),
    ("./", "./"),
    ("./", "./"),
    ("./", "./"),
    ("c:\\Users\\samue\\Documents\\antigravity\\goofy-raman\\", ""),
    ("C:\\Users\\samue\\Documents\\antigravity\\goofy-raman\\", ""),
    (".", "."),
    (".", ".")
]

def main():
    print("=" * 80)
    print("CONVERTENDO TODOS OS CAMINHOS ABSOLUTOS PARA RELATIVOS A RAIZ")
    print("=" * 80)
    
    modified_files = []
    
    for root, dirs, files in os.walk("."):
        if any(p in root for p in [".git", "archives", ".cache"]):
            continue
        for f in files:
            if f.endswith((".md", ".json", ".py", ".yaml", ".txt", ".dat", ".cff")):
                fp = os.path.join(root, f)
                try:
                    with open(fp, "r", encoding="utf-8") as f_in:
                        content = f_in.read()
                    
                    new_content = content
                    for old_pat, new_pat in REPLACEMENTS:
                        new_content = new_content.replace(old_pat, new_pat)
                        
                    if new_content != content:
                        with open(fp, "w", encoding="utf-8") as f_out:
                            f_out.write(new_content)
                        modified_files.append(fp)
                        print(f"[ATUALIZADO] {fp}")
                except Exception as e:
                    print(f"[ERRO] {fp}: {e}")
                    
    print(f"\n[SUCESSO] Total de arquivos convertidos para caminhos relativos: {len(modified_files)}")

if __name__ == "__main__":
    main()
