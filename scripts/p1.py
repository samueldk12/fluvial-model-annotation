import os, sys, re

with open('src/tracking/vessel_spatial_memory.py', 'r', encoding='utf-8') as f:
    sm_text = f.read()

if 'entry_sector' not in sm_text:
    sm_text = sm_text.replace(
        '"destination": "Atracado no Píer / Fundeado",',
        '"destination": "Atracado no Péer / Fundeado",\n                        "entry_time": time.strftime("%H:%M:%S"),\n                        "entry_sector": "Canal Central",\n                        "origin_story": f"Está fundeado/atracado no píer desde as {time.strftime(%H:%M:%S)}.",'
    )
    with open('src/tracking/vessel_spatial_memory.py', 'w', encoding='utf-8') as f:
        f.write(sm_text)
print('Spatial memory checked')
