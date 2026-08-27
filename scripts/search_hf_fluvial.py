import urllib.request
import json

def search_hf(query, is_dataset=False):
    t = 'datasets' if is_dataset else 'models'
    url = f'https://huggingface.co/api/{t}?search={query}&limit=10'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        print(f'=== HF {t} for "{query}" ===')
        for item in res:
            print(' ', item['id'], item.get('tags', [])[:5])
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    search_hf('river', is_dataset=True)
    search_hf('water', is_dataset=True)
    search_hf('vessel', is_dataset=False)
    search_hf('water-segmentation', is_dataset=False)
    search_hf('sar-vessel', is_dataset=False)
