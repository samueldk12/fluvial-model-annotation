import urllib.request
import re
import json

def inspect_url(url, desc):
    print("=" * 80)
    print(f"Inspecionando {desc}: {url}")
    print("=" * 80)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
        print(f"HTML carregado ({len(html)} bytes)")
        matches = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        for m in set(matches):
            if any(k in m.lower() for k in ['.zip', '.tar', '.gz', 'download', 'drive.google', 'pan.baidu', 'github', 'doi', 'modd', 'mastr', 'spscd', 'kolom', 'massmind', 'marvel']):
                print("  ->", m)
    except Exception as e:
        print(f"Erro em {url}:", e)

def inspect_github(repo):
    print("=" * 80)
    print(f"GitHub Repo: {repo}")
    print("=" * 80)
    url = f"https://api.github.com/repos/{repo}/contents"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
        print("Arquivos no repo:", [d['name'] for d in data])
    except Exception as e:
        print("Erro:", e)

def main():
    inspect_url('https://box.vicos.si/borja/viamaro/index.html', 'ViCoS MODD2 / MaSTRe1325')
    inspect_url('https://labs.pfst.hr/maritime-dataset/', 'SPSCD Maritime Dataset')
    inspect_github('WaterScenes/WaterScenes')
    inspect_github('MaritimeDataset/KOLOMVERSE')
    inspect_github('uml-marine-robotics/MassMIND')
    inspect_github('avaapm/marveldataset2016')

if __name__ == '__main__':
    main()
