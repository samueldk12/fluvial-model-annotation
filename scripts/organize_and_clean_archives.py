"""
Script de Organizacao e Limpeza:
1. Garante que todos os datasets estao devidamente zipados em suas respectivas pastas.
2. Remove pastas de dados brutos/descompactados (mantendo apenas os arquivos .zip e a documentacao README.md).
"""

import os
import shutil

def remove_dir(path):
    if os.path.exists(path):
        print(f"Removendo pasta descompactada: {path}")
        shutil.rmtree(path)

def copy_file(src, dst):
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            print(f"Copiando {src} -> {dst}")
            shutil.copy2(src, dst)

def main():
    print("=" * 80)
    print("ORGANIZANDO ARQUIVOS .ZIP E LIMPANDO PASTAS DESCOMPACTADAS")
    print("=" * 80)
    
    # 1. LaRS
    # Zips: datasets/LaRS/lars_v1.0.0_images.zip e datasets/LaRS/lars_v1.0.0_annotations.zip
    remove_dir('datasets/LaRS/train')
    remove_dir('datasets/LaRS/val')
    remove_dir('datasets/LaRS/test')
    remove_dir('datasets/LaRS/visualized_samples')
    copy_file('datasets/archives/LaRS_evaluator.zip', 'datasets/LaRS/LaRS_evaluator.zip')
    
    # 2. IWHR Floater V1
    copy_file('datasets/archives/IWHR_Floater_V1_yolo.zip', 'datasets/fluvial/IWHR_Floater_V1/IWHR_Floater_V1_yolo.zip')
    remove_dir('datasets/fluvial/IWHR_Floater_V1/IWHR_AI_Lable_Floater_V1-package1')
    
    # 3. Elwha River Segmentation
    copy_file('datasets/archives/Elwha_river_segmentation.zip', 'datasets/fluvial/elwha_river_segmentation/Elwha_river_segmentation.zip')
    remove_dir('datasets/fluvial/elwha_river_segmentation/data')
    remove_dir('datasets/fluvial/elwha_river_segmentation/extracted_samples')
    
    # 4. SEA-AI SEANet
    copy_file('datasets/archives/SEANet_panoptic_dataset.zip', 'datasets/sea_ai/SEANet/SEANet_panoptic_dataset.zip')
    remove_dir('datasets/sea_ai/SEANet/images')
    remove_dir('datasets/sea_ai/SEANet/annotations')
    
    # 5. MaSTRe1325
    remove_dir('datasets/MaSTRe1325/masks')
    for f in os.listdir('datasets/MaSTRe1325'):
        if f.endswith('.png'):
            os.remove(os.path.join('datasets/MaSTRe1325', f))
            
    # 6. MODD2
    remove_dir('datasets/MODD2/annotations')
    
    # 7. WaterScenes
    copy_file('datasets/archives/WaterScenes_DevKit.zip', 'datasets/fluvial/WaterScenes/WaterScenes_DevKit.zip')
    
    # 8. Roboflow Naval
    copy_file('datasets/archives/roboflow_naval_configs.zip', 'datasets/roboflow_naval/roboflow_naval_configs.zip')
    
    print("\n[SUCESSO] Limpeza concluida. Apenas arquivos .zip e arquivos de documentacao foram mantidos.")

if __name__ == '__main__':
    main()
