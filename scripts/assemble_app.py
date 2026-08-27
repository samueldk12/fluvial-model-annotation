with open('scripts/py_backend.txt', 'r', encoding='utf-8') as f:
    p1 = f.read()
with open('scripts/p_html_chunk1.txt', 'r', encoding='utf-8') as f:
    p2 = f.read()
with open('scripts/p_html_chunk2.txt', 'r', encoding='utf-8') as f:
    p3 = f.read()
with open('scripts/py_routes.txt', 'r', encoding='utf-8') as f:
    p4 = f.read()

full_code = p1 + '\n\n' + p2 + p3 + '\n\n' + p4

with open('src/web/app.py', 'w', encoding='utf-8') as f:
    f.write(full_code)

print('Assembled src/web/app.py successfully!')
