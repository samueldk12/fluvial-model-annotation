with open('src/web/app.py', 'r', encoding='utf-8') as f:
    t = f.read()

t = t.replace('\ncurrent_live_vessels.append({', '\n                current_live_vessels.append({')

with open('src/web/app.py', 'w', encoding='utf-8') as f:
    f.write(t)
print('Fixed indentation')
