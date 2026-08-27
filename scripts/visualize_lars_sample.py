"""
Script para Inspecao e Visualizacao de Amostras do Dataset LaRS (ICCV 2023)
Carrega uma imagem real e sobrepoe sua mascara semantica de agua, ceu e obstaculos com transparencia.
"""

import os
import json
import cv2
import numpy as np

def main():
    lars_dir = 'datasets/LaRS'
    train_dir = os.path.join(lars_dir, 'train')
    img_dir = os.path.join(train_dir, 'images')
    mask_dir = os.path.join(train_dir, 'semantic_masks')
    out_dir = os.path.join(lars_dir, 'visualized_samples')
    os.makedirs(out_dir, exist_ok=True)
    
    if not os.path.exists(img_dir) or not os.path.exists(mask_dir):
        print("Diretorios do LaRS nao encontrados em", train_dir)
        return
        
    img_files = sorted(os.listdir(img_dir))
    print(f"Total de imagens de treino no LaRS: {len(img_files)}")
    
    # Paleta de cores para LaRS (ID -> BGR)
    # 1: Static Obstacle (Amarelo)
    # 3: Water (Azul Claro)
    # 5: Sky (Roxo)
    # 11+: Dynamic Obstacles / Boats (Vermelho / Laranja)
    palette = {
        0: (0, 0, 0),          # Background / Void
        1: (0, 212, 255),      # Static Obstacle (BGR: Amarelo)
        3: (255, 245, 70),      # Water (BGR: Ciano/Azul)
        5: (255, 0, 170),      # Sky (BGR: Roxo)
        11: (43, 39, 255),     # Boat/Ship (BGR: Vermelho)
        12: (0, 128, 255),     # Row boats (BGR: Laranja)
        13: (0, 255, 255),     # Paddle board (BGR: Amarelo)
        14: (255, 0, 255),     # Buoy (BGR: Magenta)
        15: (0, 255, 0),       # Swimmer (BGR: Verde)
        16: (128, 0, 128),     # Animal
        17: (255, 128, 0),     # Float
        19: (128, 128, 128)    # Other
    }
    
    for i in range(min(5, len(img_files))):
        img_name = img_files[i]
        mask_name = os.path.splitext(img_name)[0] + '.png'
        
        img_path = os.path.join(img_dir, img_name)
        mask_path = os.path.join(mask_dir, mask_name)
        
        if not os.path.exists(mask_path):
            continue
            
        img = cv2.imread(img_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None or mask is None:
            continue
            
        color_mask = np.zeros_like(img)
        for class_id, color in palette.items():
            color_mask[mask == class_id] = color
            
        # Blending com transparencia 50%
        blended = cv2.addWeighted(img, 0.65, color_mask, 0.35, 0)
        
        # Salvar lado a lado
        combined = np.hstack([img, blended])
        save_path = os.path.join(out_dir, f"lars_sample_{i+1}_{img_name}")
        cv2.imwrite(save_path, combined)
        print(f"[OK] Amostra LaRS visualizada e salva: {save_path}")
        
    print(f"\nAmostras salvas em: {out_dir}")

if __name__ == '__main__':
    main()
