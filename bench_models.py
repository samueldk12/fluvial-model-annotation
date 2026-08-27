"""
Benchmark comparativo dos detectores de embarcacoes disponiveis no repositorio
+ baselines genericos mais recentes da Ultralytics (YOLO11n / YOLO26n).
"""
import time
import glob
from ultralytics import YOLO

IMAGES = [
    "data/santos_live_snapshot.jpg",
    "data/extracted_dataset/iwhr/IWHR_Floater_V1/IWHR_AI_Lable_Floater_V1-package1/JPEGImages/0051.jpg",
    "data/extracted_dataset/sar/sar-ship-detection/000302.jpg",
]

MODELS = [
    ("yolov8n.pt (COCO generico, classe 'boat')", "yolov8n.pt", [8]),
    ("mayrajeo YOLOv8n Marine Vessel (fine-tuned)", "models/02_sar_radar_and_edge/mayrajeo_YOLOv8_Marine_Vessel/YOLOv8n/yolov8n.pt", None),
    ("MeWan2808 YOLOv8 SAR (fine-tuned, 38ms)", "models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR/unquantized/best.pt", None),
    ("YOLO11n (COCO generico, classe 'boat')", "yolo11n.pt", [8]),
    ("YOLO26n (COCO generico, classe 'boat')", "yolo26n.pt", [8]),
]

print(f"{'MODELO':50s} {'IMAGEM':40s} {'DETECCOES':10s} {'CONF MAX':9s} {'TEMPO(ms)':10s}")
print("-" * 125)

for label, weight_path, classes in MODELS:
    try:
        model = YOLO(weight_path)
    except Exception as e:
        print(f"{label:50s} FALHOU AO CARREGAR: {e}")
        continue

    for img_path in IMAGES:
        t0 = time.time()
        kwargs = {"conf": 0.15, "verbose": False}
        if classes is not None:
            kwargs["classes"] = classes
        results = model.predict(img_path, **kwargs)
        elapsed_ms = (time.time() - t0) * 1000

        n_det = 0
        max_conf = 0.0
        for r in results:
            n_det += len(r.boxes)
            if len(r.boxes) > 0:
                max_conf = max(max_conf, float(r.boxes.conf.max()))

        img_short = img_path.split("/")[-1]
        print(f"{label:50s} {img_short:40s} {n_det:<10d} {max_conf:<9.3f} {elapsed_ms:<10.1f}")
    print()
