import urllib.request
import re

def main():
    url = 'https://lojzezust.github.io/lars-dataset/'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        print(f"HTML downloaded ({len(html)} bytes)")
        
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        for l in set(links):
            print("Link:", l)
            
        # Find download section
        d_match = re.search(r'id=[\'"]download[\'"].*?</section>', html, re.DOTALL | re.I)
        if d_match:
            print("\nDownload section:")
            print(d_match.group(0))
        else:
            print("\nSearching for download text:")
            for line in html.splitlines():
                if 'download' in line.lower() or 'box.vicos' in line or 'zip' in line.lower():
                    print(' ', line.strip())
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
