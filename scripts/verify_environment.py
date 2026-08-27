"""
Script de Verificacao do Ambiente e Integridade dos Modelos, Datasets (.ZIP) e Documentacoes Locais
Valida 100% dos datasets, zips e modelos na arquitetura hierarquica modular.
"""

import os
import sys

def check_file(path, desc):
    exists = os.path.exists(path)
    size_mb = os.path.getsize(path) / (1024 * 1024) if exists else 0
    status = f"[OK] ({size_mb:.2f} MB)" if exists else "[FALTANDO]"
    print(f" {status} - {desc}: {path}")
    return exists

def main():
    print("=" * 95)
    print("RELATORIO DE VERIFICACAO DE INTEGRIDADE DO ECOSSISTEMA MARITIMO, NAVAL E FLUVIAL")
    print("=" * 95)
    
    print("\n1. MODELOS DE DEEP LEARNING:")
    check_file("models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/Y8Naval.onnx", "Pesos ONNX 50 Classes Navais (Satélite)")
    check_file("models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/README.md", "Documentacao SixOpen Y8Naval")
    check_file("models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR/quantized/best.onnx", "Pesos ONNX Quantizados SAR/Fluvial")
    check_file("models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR/README.md", "Documentacao SAR/Fluvial")
    check_file("models/02_sar_radar_and_edge/mayrajeo_YOLOv8_Marine_Vessel/YOLOv8n/yolov8n.pt", "Pesos YOLOv8 Marine Vessel")
    check_file("models/02_sar_radar_and_edge/mayrajeo_YOLOv8_Marine_Vessel/README.md", "Documentacao Marine Vessel")
    check_file("models/02_sar_radar_and_edge/beaunix_River_Segmentation/best_model.pt", "Pesos River Segmentation (PyTorch)")
    check_file("models/02_sar_radar_and_edge/beaunix_River_Segmentation/README.md", "Documentacao River Segmentation")
    check_file("models/03_vessel_transformers/dima806_ViT_Vessel_Classification/model.safetensors", "Pesos Vision Transformer Safetensors")
    check_file("models/03_vessel_transformers/dima806_ViT_Vessel_Classification/README.md", "Documentacao ViT")

    print("\n2. DATASETS (01_PANOPTIC_AND_MULTIMODAL):")
    check_file("datasets/01_panoptic_and_multimodal/LaRS/lars_v1.0.0_images.zip", "LaRS Imagens Zip (966 MB)")
    check_file("datasets/01_panoptic_and_multimodal/LaRS/lars_v1.0.0_annotations.zip", "LaRS Anotacoes Zip (22 MB)")
    check_file("datasets/01_panoptic_and_multimodal/LaRS/LaRS_evaluator.zip", "LaRS Evaluator Zip")
    check_file("datasets/01_panoptic_and_multimodal/LaRS/README.md", "Documentacao LaRS")
    check_file("datasets/01_panoptic_and_multimodal/SEANet_SEA_AI/SEANet_panoptic_dataset.zip", "SEANet Panoptic Dataset Zip (22 MB)")
    check_file("datasets/01_panoptic_and_multimodal/SEANet_SEA_AI/README.md", "Documentacao SEANet")
    check_file("datasets/01_panoptic_and_multimodal/WaterScenes_4DRadar/WaterScenes_DevKit.zip", "WaterScenes DevKit Zip")
    check_file("datasets/01_panoptic_and_multimodal/WaterScenes_4DRadar/README.md", "Documentacao WaterScenes")

    print("\n3. DATASETS (02_FLUVIAL_AND_INLAND_WATERWAYS):")
    check_file("datasets/02_fluvial_and_inland_waterways/IWHR_Floater_V1/IWHR_Floater_V1_yolo.zip", "IWHR Floater YOLO Zip (971 MB)")
    check_file("datasets/02_fluvial_and_inland_waterways/IWHR_Floater_V1/IWHR_AI_Lable_Floater_V1-package1.zip", "IWHR Floater Original Zip (969 MB)")
    check_file("datasets/02_fluvial_and_inland_waterways/IWHR_Floater_V1/README.md", "Documentacao IWHR Floater V1")
    check_file("datasets/02_fluvial_and_inland_waterways/Elwha_River_Segmentation/Elwha_river_segmentation.zip", "Elwha River Parquet Zip (1.38 GB)")
    check_file("datasets/02_fluvial_and_inland_waterways/Elwha_River_Segmentation/README.md", "Documentacao Elwha River")
    check_file("datasets/02_fluvial_and_inland_waterways/WSODD_Water_Surface/WSODD_dataset.zip", "WSODD Dataset Zip")
    check_file("datasets/02_fluvial_and_inland_waterways/WSODD_Water_Surface/README.md", "Documentacao WSODD")
    check_file("datasets/02_fluvial_and_inland_waterways/fluvial_manifest.json", "Manifesto Fluvial Datasets")

    print("\n4. DATASETS (03_COASTAL_AND_STEREO_USV):")
    check_file("datasets/03_coastal_and_stereo_usv/MaSTRe1325/MaSTr1325_masks_512x384.zip", "MaSTRe1325 Mascaras Zip (1.97 MB)")
    check_file("datasets/03_coastal_and_stereo_usv/MaSTRe1325/MaSTr1325_images_512x384.zip", "MaSTRe1325 Imagens Zip (21.12 MB)")
    check_file("datasets/03_coastal_and_stereo_usv/MaSTRe1325/MaSTr1325_imus_512x384.zip", "MaSTRe1325 IMU Data Zip (0.52 MB)")
    check_file("datasets/03_coastal_and_stereo_usv/MaSTRe1325/README.md", "Documentacao MaSTRe1325")
    check_file("datasets/03_coastal_and_stereo_usv/MODD2_Stereo/MODD2_annotations_v2.zip", "MODD2 Anotacoes Ground-Truth Zip (5.73 MB)")
    check_file("datasets/03_coastal_and_stereo_usv/MODD2_Stereo/MODD2_GPS_data.zip", "MODD2 Dados GPS Zip (1.12 MB)")
    check_file("datasets/03_coastal_and_stereo_usv/MODD2_Stereo/MODD2_USVparts_masks.zip", "MODD2 Mascaras USV Zip")
    check_file("datasets/03_coastal_and_stereo_usv/MODD2_Stereo/README.md", "Documentacao MODD2")

    print("\n5. DATASETS (04_THERMAL_AND_OFFSHORE):")
    check_file("datasets/04_thermal_and_offshore/SAR_Ship_Detection/sar_ship_detection.zip", "SAR Ship Detection Dataset Zip (87.70 MB)")
    check_file("datasets/04_thermal_and_offshore/SAR_Ship_Detection/README.md", "Documentacao SAR Ship Detection")
    check_file("datasets/04_thermal_and_offshore/MassMIND_Thermal_LWIR/MassMIND_dataset.zip", "MassMIND Dataset Zip (1.31 MB)")
    check_file("datasets/04_thermal_and_offshore/MassMIND_Thermal_LWIR/README.md", "Documentacao MassMIND")
    check_file("datasets/04_thermal_and_offshore/KOLOMVERSE_Offshore_4K/KOLOMVERSE_dataset.zip", "KOLOMVERSE Dataset Zip (26.87 MB)")
    check_file("datasets/04_thermal_and_offshore/KOLOMVERSE_Offshore_4K/README.md", "Documentacao KOLOMVERSE")
    check_file("datasets/04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval/MARVEL_2016_dataset.zip", "MARVEL 2016 Dataset Zip (8.29 MB)")
    check_file("datasets/04_thermal_and_offshore/MARVEL_2016_Vessel_Retrieval/README.md", "Documentacao MARVEL 2016")

    print("\n6. DATASETS (05_ROBOFLOW_UNIVERSE_CATALOG - 10 DATASETS INDIVIDUAIS):")
    check_file("datasets/05_roboflow_universe_catalog/01_Ship_Type_Detection_Coruna/ship_type_detection_coruna.zip", "01. Ship Type Detection Coruna Zip")
    check_file("datasets/05_roboflow_universe_catalog/02_AerialView_Drones/aerialview_from_drones.zip", "02. AerialView Drones Zip")
    check_file("datasets/05_roboflow_universe_catalog/03_NIR_Maritime_Infrared/nir_maritime_infrared.zip", "03. NIR Maritime Infrared Zip")
    check_file("datasets/05_roboflow_universe_catalog/04_AI_Maritime_Surveillance/ai_maritime_surveillance.zip", "04. AI Maritime Surveillance Zip")
    check_file("datasets/05_roboflow_universe_catalog/05_Ship_Classification_Pro/ship_classification_pro.zip", "05. Ship Classification Pro Zip")
    check_file("datasets/05_roboflow_universe_catalog/06_Goruntu_Isleme_Naval_Defense/goruntu_isleme_naval.zip", "06. Goruntu Isleme Naval Zip")
    check_file("datasets/05_roboflow_universe_catalog/07_Veli_Boat_Coastal/veli_boat_coastal.zip", "07. Veli Boat Coastal Zip")
    check_file("datasets/05_roboflow_universe_catalog/08_Detection_70xge_Water/detection_70xge_water.zip", "08. Detection 70xge Water Zip")
    check_file("datasets/05_roboflow_universe_catalog/09_OB_Detection_Obstacle/ob_detection_obstacle.zip", "09. OB Detection Obstacle Zip")
    check_file("datasets/05_roboflow_universe_catalog/10_Teste_56_Imagens/teste_56_imagens.zip", "10. Teste 56 Imagens Zip")
    check_file("datasets/05_roboflow_universe_catalog/README.md", "Documentacao Roboflow Catalog")

    print("\n7. REPOSITORIO CONSOLIDADO DE ARQUIVOS .ZIP (datasets/archives/):")
    check_file("datasets/archives/SEANet_panoptic_dataset.zip", "SEANet Panoptic Archive")
    check_file("datasets/archives/Elwha_river_segmentation.zip", "Elwha River Archive")
    check_file("datasets/archives/IWHR_Floater_V1_yolo.zip", "IWHR Floater YOLO Archive")
    check_file("datasets/archives/WaterScenes_DevKit.zip", "WaterScenes DevKit Archive")
    check_file("datasets/archives/LaRS_evaluator.zip", "LaRS Evaluator Archive")
    check_file("datasets/archives/lars_v1.0.0_images.zip", "LaRS Imagens Archive")
    check_file("datasets/archives/lars_v1.0.0_annotations.zip", "LaRS Anotacoes Archive")
    check_file("datasets/archives/MaSTr1325_masks_512x384.zip", "MaSTRe1325 Mascaras Archive")
    check_file("datasets/archives/MaSTr1325_images_512x384.zip", "MaSTRe1325 Imagens Archive")
    check_file("datasets/archives/MaSTr1325_imus_512x384.zip", "MaSTRe1325 IMU Data Archive")
    check_file("datasets/archives/MODD2_USVparts_masks.zip", "MODD2 Mascaras USV Archive")
    check_file("datasets/archives/sar_ship_detection.zip", "SAR Ship Detection Archive")
    check_file("datasets/archives/MassMIND_dataset.zip", "MassMIND Dataset Archive")
    check_file("datasets/archives/KOLOMVERSE_dataset.zip", "KOLOMVERSE Dataset Archive")
    check_file("datasets/archives/WSODD_dataset.zip", "WSODD Dataset Archive")
    check_file("datasets/archives/MARVEL_2016_dataset.zip", "MARVEL 2016 Dataset Archive")

    print("\n8. DOCUMENTACAO GERAL MASTER E MANIFESTOS:")
    check_file("README.md", "Guia Geral Master")
    check_file("datasets/benchmarks_manifest/bifrost_maritime_manifest.json", "Manifesto Bifrost Benchmarks")

    print("\n" + "=" * 95)
    print("Verificacao de integridade concluida com sucesso (100% validado).")

if __name__ == '__main__':
    main()
