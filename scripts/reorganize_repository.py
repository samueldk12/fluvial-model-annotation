"""
Script de Reorganizacao Arquitetural do Repositorio:
Reorganiza datasets e modelos em categorias logicas numeradas por dominio de aplicacao e modalidade sensorial.
"""

import os
import shutil
import time

def safe_copy_tree(src, dst):
    if os.path.exists(src):
        os.makedirs(dst, exist_ok=True)
        for root, dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            target_root = os.path.join(dst, rel)
            os.makedirs(target_root, exist_ok=True)
            for f in files:
                sf = os.path.join(root, f)
                tf = os.path.join(target_root, f)
                if not os.path.exists(tf):
                    shutil.copy2(sf, tf)
        print(f"[OK] Copiado diretorio: {src} -> {dst}")

def safe_remove_tree(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass
            for d in dirs:
                try:
                    os.rmdir(os.path.join(root, d))
                except Exception:
                    pass
        try:
            os.rmdir(path)
        except Exception:
            pass
        print(f"[OK] Removido diretorio antigo: {path}")

def main():
    print("=" * 90)
    print("INICIANDO REORGANIZACAO ESTRUTURAL DO REPOSITORIO")
    print("=" * 90)
    
    # -------------------------------------------------------------
    # 1. CATEGORIAS DE DATASETS
    # -------------------------------------------------------------
    d_panoptic = "datasets/01_panoptic_and_multimodal"
    d_fluvial = "datasets/02_fluvial_and_inland_waterways"
    d_coastal = "datasets/03_coastal_and_stereo_usv"
    d_thermal = "datasets/04_thermal_and_offshore"
    d_roboflow = "datasets/05_roboflow_universe_catalog"
    d_manifests = "datasets/benchmarks_manifest"
    d_archives = "datasets/archives"
    
    # 1.1 Panoptic & Multimodal
    safe_copy_tree("datasets/LaRS", f"{d_panoptic}/LaRS")
    safe_copy_tree("datasets/sea_ai/SEANet", f"{d_panoptic}/SEANet_SEA_AI")
    safe_copy_tree("datasets/fluvial/WaterScenes", f"{d_panoptic}/WaterScenes_4DRadar")
    
    # 1.2 Fluvial & Inland Waterways
    safe_copy_tree("datasets/fluvial/IWHR_Floater_V1", f"{d_fluvial}/IWHR_Floater_V1")
    safe_copy_tree("datasets/fluvial/elwha_river_segmentation", f"{d_fluvial}/Elwha_River_Segmentation")
    safe_copy_tree("datasets/fluvial/WSODD", f"{d_fluvial}/WSODD_Water_Surface")
    if os.path.exists("datasets/fluvial/fluvial_manifest.json"):
        os.makedirs(d_fluvial, exist_ok=True)
        shutil.copy2("datasets/fluvial/fluvial_manifest.json", f"{d_fluvial}/fluvial_manifest.json")
    
    # 1.3 Coastal & Stereo USV
    safe_copy_tree("datasets/MaSTRe1325", f"{d_coastal}/MaSTRe1325")
    safe_copy_tree("datasets/MODD2", f"{d_coastal}/MODD2_Stereo")
    
    # 1.4 Thermal & Offshore
    safe_copy_tree("datasets/MassMIND", f"{d_thermal}/MassMIND_Thermal_LWIR")
    safe_copy_tree("datasets/KOLOMVERSE", f"{d_thermal}/KOLOMVERSE_Offshore_4K")
    safe_copy_tree("datasets/MARVEL_2016", f"{d_thermal}/MARVEL_2016_Vessel_Retrieval")
    
    # 1.5 Roboflow Universe Catalog
    safe_copy_tree("datasets/roboflow_naval", d_roboflow)
    
    # 1.6 Manifestos
    if os.path.exists("datasets/bifrost_benchmarks/benchmark_manifest.json"):
        os.makedirs(d_manifests, exist_ok=True)
        shutil.copy2("datasets/bifrost_benchmarks/benchmark_manifest.json", f"{d_manifests}/bifrost_maritime_manifest.json")
        
    # -------------------------------------------------------------
    # 2. CATEGORIAS DE MODELOS
    # -------------------------------------------------------------
    m_sat = "models/01_satellite_and_aerial_naval"
    m_sar = "models/02_sar_radar_and_edge"
    m_vit = "models/03_vessel_transformers"
    
    safe_copy_tree("models/SixOpen_Y8NavalONNX", f"{m_sat}/SixOpen_Y8NavalONNX")
    safe_copy_tree("models/fluvial_and_radar/MeWan2808_YOLOv8_SAR_Vessel", f"{m_sar}/MeWan2808_YOLOv8_SAR")
    safe_copy_tree("models/fluvial_and_radar/dima806_ViT_Vessel_Classification", f"{m_vit}/dima806_ViT_Vessel_Classification")
    
    # -------------------------------------------------------------
    # 3. LIMPAR DIRETÓRIOS ANTIGOS
    # -------------------------------------------------------------
    for old_dir in [
        "datasets/LaRS", "datasets/sea_ai", "datasets/fluvial", "datasets/MaSTRe1325", 
        "datasets/MODD2", "datasets/MassMIND", "datasets/KOLOMVERSE", "datasets/MARVEL_2016",
        "datasets/bifrost_benchmarks", "datasets/roboflow_naval",
        "models/SixOpen_Y8NavalONNX", "models/fluvial_and_radar"
    ]:
        safe_remove_tree(old_dir)
        
    # -------------------------------------------------------------
    # 4. GARANTIR QUE datasets/archives/ CONTÉM TODOS OS .ZIP
    # -------------------------------------------------------------
    os.makedirs(d_archives, exist_ok=True)
    for z in [
        f"{d_panoptic}/LaRS/lars_v1.0.0_images.zip",
        f"{d_panoptic}/LaRS/lars_v1.0.0_annotations.zip",
        f"{d_panoptic}/LaRS/LaRS_evaluator.zip",
        f"{d_panoptic}/SEANet_SEA_AI/SEANet_panoptic_dataset.zip",
        f"{d_panoptic}/WaterScenes_4DRadar/WaterScenes_DevKit.zip",
        f"{d_fluvial}/IWHR_Floater_V1/IWHR_Floater_V1_yolo.zip",
        f"{d_fluvial}/IWHR_Floater_V1/IWHR_AI_Lable_Floater_V1-package1.zip",
        f"{d_fluvial}/Elwha_River_Segmentation/Elwha_river_segmentation.zip",
        f"{d_coastal}/MaSTRe1325/MaSTr1325_masks_512x384.zip",
        f"{d_coastal}/MODD2_Stereo/MODD2_annotations_v2.zip",
        f"{d_coastal}/MODD2_Stereo/MODD2_GPS_data.zip",
        f"{d_roboflow}/roboflow_naval_configs.zip"
    ]:
        if os.path.exists(z):
            dst = os.path.join(d_archives, os.path.basename(z))
            if not os.path.exists(dst):
                shutil.copy2(z, dst)

    print("\n[SUCESSO] Reorganizacao estrutural concluida com perfeicao!")

if __name__ == '__main__':
    main()
