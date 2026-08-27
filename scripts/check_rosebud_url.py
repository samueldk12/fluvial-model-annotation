import urllib.request
import re

def main():
    url = 'https://purr.purdue.edu/publications/3860/1'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        print("HTML length:", len(html))
        
        matches = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        for m in matches:
            if 'download' in m.lower() or 'serve' in m.lower() or '.zip' in m.lower() or '3860' in m:
                print("Link:", m)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
