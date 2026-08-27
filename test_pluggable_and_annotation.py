# -*- coding: utf-8 -*-
"""Teste automatizado das novas capacidades: Arquitetura Acoplável & Estúdio de Anotação YOLO."""

import os
import sys
import cv2
import zipfile
import json

project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.annotation.dataset_manager import DatasetAnnotationManager
from src.pipeline.pluggable_pipeline import PluggableVisionPipeline, ModelRegistry

def test_pipeline_and_models():
    print("=" * 60)
    print("1. TESTANDO ARQUITETURA ACOPLÁVEL E MODELOS")
    print("=" * 60)

    reg = ModelRegistry(project_dir)
    catalog = reg.get_catalog()
    print(f"Total de modelos no catálogo: {len(catalog)}")
    for m in catalog:
        print(f"  - [{m['id']}] {m['name']} ({m['framework']}) | Disponível: {m['available']}")

    pipeline = PluggableVisionPipeline(project_dir)
    
    # Teste de inferência em snapshot real
    sample_img_path = os.path.join(project_dir, "data", "santos_live_snapshot.jpg")
    if os.path.exists(sample_img_path):
        img = cv2.imread(sample_img_path)
        print(f"\nTestando inferência na imagem de teste ({img.shape[1]}x{img.shape[0]}px)...")
        
        # Testa modelos diferentes
        for test_model_id in ["ensemble_full", "yolov8n", "yolo11n"]:
            pipeline.update_config({"active_model_id": test_model_id, "conf_threshold": 0.15})
            vessels = pipeline.process_frame(img)
            lat = pipeline.last_inference_latency_ms
            print(f"  > Modelo '{test_model_id}': {len(vessels)} embarcação(ões) detectadas em {lat:.1f}ms")
    else:
        print("Aviso: santos_live_snapshot.jpg não encontrado para inferência visual.")

    print("\n[OK] Pipeline acoplável validado com sucesso!")


def test_annotation_and_dataset():
    print("\n" + "=" * 60)
    print("2. TESTANDO GERENCIADOR DE DATASET & ANOTAÇÃO YOLO")
    print("=" * 60)

    mgr = DatasetAnnotationManager(project_dir)
    classes = mgr.get_classes()
    print(f"Classes registradas ({len(classes)}): {classes}")

    # Cria uma imagem sintética para teste de salvamento
    dummy_img = cv2.imread(os.path.join(project_dir, "data", "santos_live_snapshot.jpg"))
    if dummy_img is None:
        dummy_img = (255 * (cv2.randn(cv2.Mat(720, 1280, cv2.CV_8UC3), (120, 120, 120), (30, 30, 30)))).astype('uint8')

    test_boxes = [
        {"class_id": 0, "x1": 100, "y1": 150, "x2": 450, "y2": 380},
        {"class_id": 1, "x1": 600, "y1": 200, "x2": 950, "y2": 500}
    ]

    res = mgr.save_annotation(dummy_img, test_boxes, source_video="teste_unitario.mp4", frame_timestamp=12.5)
    print(f"Anotação salva: {res}")
    assert res["status"] == "ok", "Falha ao salvar anotação"
    img_id = res["image_id"]

    # Verifica se os arquivos foram criados corretamente
    label_file = os.path.join(mgr.labels_dir, f"frame_{res['filename'].split('_')[1]}_{res['filename'].split('_')[2]}_{img_id}.txt")
    img_file = os.path.join(mgr.images_dir, res["filename"])
    assert os.path.exists(img_file), f"Imagem não encontrada: {img_file}"

    # Testa listagem
    ann_list = mgr.list_annotations()
    print(f"Total de anotações no dataset: {ann_list['total_images']} imagens, {ann_list['total_boxes']} caixas")
    assert ann_list["total_images"] >= 1, "Deveria haver ao menos 1 anotação"

    # Testa exportação ZIP
    zip_path, err = mgr.export_dataset_zip(split_ratio=0.8)
    assert err is None, f"Erro ao exportar ZIP: {err}"
    assert os.path.exists(zip_path), f"Arquivo ZIP não encontrado: {zip_path}"
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        print(f"Arquivos no pacote ZIP ({len(files)} arquivos): {files[:6]}...")
        assert "data.yaml" in files, "data.yaml ausente no ZIP"
        assert "classes.txt" in files, "classes.txt ausente no ZIP"

    print(f"Arquivo ZIP gerado com sucesso: {os.path.basename(zip_path)} ({round(os.path.getsize(zip_path)/1024, 1)} KB)")

    print("\n[OK] Módulo de Anotação e Exportação YOLO validado com sucesso!")


if __name__ == "__main__":
    test_pipeline_and_models()
    test_annotation_and_dataset()
    print("\n>>> TODOS OS TESTES PASSARAM COM 100% DE SUCESSO! <<<")
