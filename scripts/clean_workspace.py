"""
Script de Limpeza do Workspace:
Remove arquivos e pastas temporarias, caches, checkpoints intermediarios de treino
e duplicatas descompactadas, deixando o repositorio limpo e enxuto para compactacao.
"""

import os
import shutil

def safe_remove_dir(path):
    if os.path.exists(path) and os.path.isdir(path):
        print(f"Removendo diretorio: {path}")
        shutil.rmtree(path, ignore_errors=True)

def safe_remove_file(path):
    if os.path.exists(path) and os.path.isfile(path):
        print(f"Removendo arquivo: {path}")
        os.remove(path)

def main():
    print("=" * 80)
    print("INICIANDO LIMPEZA DE ARQUIVOS DESNECESSARIOS")
    print("=" * 80)
    
    # 1. Remover pastas .cache em todo o workspace
    for root, dirs, files in os.walk(".", topdown=False):
        for d in dirs:
            if d in [".cache", "__pycache__", ".pytest_cache"]:
                dp = os.path.join(root, d)
                safe_remove_dir(dp)
                
    # 2. Remover checkpoints intermediarios de treinamento pesados
    dima_dir = "models/03_vessel_transformers/dima806_ViT_Vessel_Classification"
    for cp in ["checkpoint-266", "checkpoint-2793", "checkpoint-6650"]:
        safe_remove_dir(os.path.join(dima_dir, cp))
        
    # 3. Remover subpastas duplicadas em datasets que ja estao em .zip
    safe_remove_dir("datasets/01_panoptic_and_multimodal/LaRS/evaluator")
    safe_remove_dir("datasets/01_panoptic_and_multimodal/WaterScenes_4DRadar/devkit")
    safe_remove_dir("datasets/05_roboflow_universe_catalog/seaships_sample")
    
    # 4. Remover pastas vazias residuais se houver
    safe_remove_dir("datasets/LaRS")
    safe_remove_dir("temp_sar_ship")
    
    # 5. Remover arquivos temporarios de saida de teste
    for f in [
        "resultado_naval.png",
        "resultado_sar.png",
        "output_detection.png",
        "output_sar_detection.png",
        "models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/output_test_detection.png",
        "models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/output_test_detection_ex1.png"
    ]:
        safe_remove_file(f)
        
    # 6. Remover pasta onnx duplicada em SixOpen
    safe_remove_dir("models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/onnx")

    print("\n[SUCESSO] Limpeza de arquivos desnecessarios concluida!")

if __name__ == "__main__":
    main()
