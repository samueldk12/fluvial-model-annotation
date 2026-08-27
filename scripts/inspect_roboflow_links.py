import urllib.request
import re
import json

roboflow_links = [
    ('goruntu_isleme', 'erturul/goruntu-isleme-jmzxd', 'https://universe.roboflow.com/erturul/goruntu-isleme-jmzxd'),
    ('ai_maritime_surveillance', 'mahedishuvro-aum0t/ai-for-maritime-surveillance', 'https://universe.roboflow.com/mahedishuvro-aum0t/ai-for-maritime-surveillance'),
    ('veli_boat', 'erturul/veli-mhsyk', 'https://universe.roboflow.com/erturul/veli-mhsyk'),
    ('nir_maritime', 'dinesh-singh-ambni/nir-0az0r', 'https://universe.roboflow.com/dinesh-singh-ambni/nir-0az0r'),
    ('ship_classification_pro', 'harshas-workspace-uaqsf/ship-classification-pro', 'https://universe.roboflow.com/harshas-workspace-uaqsf/ship-classification-pro'),
    ('teste_56_imagens', 'amaury-s0bxl/teste-56-imagens', 'https://universe.roboflow.com/amaury-s0bxl/teste-56-imagens'),
    ('detection_70xge', 'detection-nkkfd/detection-70xge', 'https://universe.roboflow.com/detection-nkkfd/detection-70xge'),
    ('aerial_view_drones', 'cheka-low-yel2d/aerialviewfromdrones', 'https://universe.roboflow.com/cheka-low-yel2d/aerialviewfromdrones'),
    ('ship_type_detection_coruna', 'university-of-coruna/ship-type-detection', 'https://universe.roboflow.com/university-of-coruna/ship-type-detection'),
    ('ob_detection_maritime', 'personal-9bsnr/ob_detection', 'https://universe.roboflow.com/personal-9bsnr/ob_detection')
]

def main():
    results = []
    for short_name, repo_id, url in roboflow_links:
        print("=" * 80)
        print(f"Buscando metadados: {repo_id}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
            title = re.search(r'<title>(.*?)</title>', html)
            title_str = title.group(1) if title else repo_id
            
            # Tentar extrair classes ou informacoes de imagem
            desc_match = re.search(r'<meta name=[\'"]description[\'"] content=[\'"](.*?)[\'"]', html)
            desc_str = desc_match.group(1) if desc_match else ''
            
            print(f"Title: {title_str}")
            print(f"Desc: {desc_str}")
            
            results.append({
                'id': short_name,
                'repo_id': repo_id,
                'title': title_str,
                'description': desc_str,
                'url': url
            })
        except Exception as e:
            print(f"Erro em {url}:", e)
            results.append({
                'id': short_name,
                'repo_id': repo_id,
                'title': repo_id,
                'description': 'Roboflow Universe Maritime/Naval Computer Vision Dataset',
                'url': url
            })
            
    with open('datasets/roboflow_naval/roboflow_inspected.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n[OK] Metadados salvos em datasets/roboflow_naval/roboflow_inspected.json")

if __name__ == '__main__':
    main()
