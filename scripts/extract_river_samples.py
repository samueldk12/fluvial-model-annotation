"""
Script para extracao e visualizacao de amostras do Dataset Fluvial Elwha (stodoran/elwha-segmentation-v1)
Extrai imagens reais de rios e suas mascaras de segmentacao semantica da calha do rio e margens.
"""

import os
import io
import pandas as pd
from PIL import Image

def main():
    data_dir = 'datasets/fluvial/elwha_river_segmentation/data'
    output_dir = 'datasets/fluvial/elwha_river_segmentation/extracted_samples'
    os.makedirs(output_dir, exist_ok=True)
    
    parquet_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.parquet')]
    if not parquet_files:
        print("Nenhum arquivo parquet encontrado em", data_dir)
        return
        
    print(f"Carregando {len(parquet_files)} arquivos parquet...")
    total_samples = 0
    
    for p_idx, p_file in enumerate(parquet_files):
        df = pd.read_parquet(p_file)
        total_samples += len(df)
        # Extrair 3 amostras por arquivo
        for i in range(min(3, len(df))):
            row = df.iloc[i]
            name = str(row.get('name', f"sample_p{p_idx}_{i}")).replace('/', '_').replace('\\', '_')
            
            # Imagem
            img_data = row['image']
            if isinstance(img_data, dict) and 'bytes' in img_data:
                img = Image.open(io.BytesIO(img_data['bytes']))
            elif hasattr(img_data, 'save'):
                img = img_data
            else:
                img = Image.open(io.BytesIO(img_data))
                
            img_save_path = os.path.join(output_dir, f"{name}_image.jpg")
            img.save(img_save_path)
            
            # Mascara
            mask_data = row['label']
            if isinstance(mask_data, dict) and 'bytes' in mask_data:
                mask = Image.open(io.BytesIO(mask_data['bytes']))
            elif hasattr(mask_data, 'save'):
                mask = mask_data
            else:
                mask = Image.open(io.BytesIO(mask_data))
                
            mask_save_path = os.path.join(output_dir, f"{name}_mask.png")
            mask.save(mask_save_path)
            
            print(f" -> Salva amostra fluvial: {img_save_path} e {mask_save_path}")
            
    print(f"\nTotal de amostras fluviais no dataset: {total_samples}")
    print(f"Amostras visuais extraidas em: {output_dir}")

if __name__ == '__main__':
    main()
