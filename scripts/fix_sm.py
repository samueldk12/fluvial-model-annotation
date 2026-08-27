with open('src/tracking/vessel_spatial_memory.py', 'r', encoding='utf-8') as f:
    t = f.read()

t = t.replace('{time.strftime(%H:%M:%S)}', '{time.strftime(\'%H:%M:%S\')}')

with open('src/tracking/vessel_spatial_memory.py', 'w', encoding='utf-8') as f:
    f.write(t)
print('Fixed spatial memory syntax')
