with open('scripts/p_html_part1.txt', 'r', encoding='utf-8') as f:
    p1 = f.read()
with open('scripts/p_html_part2.txt', 'r', encoding='utf-8') as f:
    p2 = f.read()
with open('scripts/p_html_part3.txt', 'r', encoding='utf-8') as f:
    p3 = f.read()

new_html_def = p1 + p2 + p3

with open('src/web/app.py', 'r', encoding='utf-8') as f:
    app_text = f.read()

idx_start = app_text.find('HTML_PAGE = """')
idx_end = app_text.find('@app.route("/")')

if idx_start != -1 and idx_end != -1:
    app_text = app_text[:idx_start] + new_html_def + '\n\n' + app_text[idx_end:]
    with open('src/web/app.py', 'w', encoding='utf-8') as f:
        f.write(app_text)
    print('Successfully replaced HTML_PAGE in app.py!')
else:
    print('Failed to find HTML boundaries')
