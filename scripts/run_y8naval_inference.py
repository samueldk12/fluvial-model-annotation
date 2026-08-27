"""
Script de Inferencia para o Modelo SixOpen/Y8NavalONNX
Detecta e rastreia embarcacoes navais e navios militares/comerciais a partir de imagens aereas e de satelite.
"""

import argparse
import json
import os
import sys
import time
import cv2
import numpy as np
import onnxruntime as ort

def parse_args():
    parser = argparse.ArgumentParser(description='Inferencia YOLOv8 Naval ONNX')
    parser.add_argument('--model', type=str, default='models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/Y8Naval.onnx',
                        help='Caminho para o arquivo ONNX')
    parser.add_argument('--config', type=str, default='models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/config.json',
                        help='Caminho para o arquivo de configuracao com id2label')
    parser.add_argument('--image', type=str, default='models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/examples/Y8Nex3.PNG',
                        help='Caminho da imagem para inferencia')
    parser.add_argument('--conf', type=float, default=0.25,
                        help='Limiar de confianca minimo')
    parser.add_argument('--iou', type=float, default=0.45,
                        help='Limiar de IoU para Non-Maximum Suppression (NMS)')
    parser.add_argument('--output', type=str, default='output_detection.png',
                        help='Caminho para salvar a imagem com os bounding boxes')
    return parser.parse_args()

def load_classes(config_path):
    if not os.path.exists(config_path):
        print(f"Aviso: {config_path} nao encontrado. Usando indices numericos.")
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    return cfg.get('id2label', {})

def nms(boxes, scores, iou_threshold):
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(ovr <= iou_threshold)[0]
        order = order[inds + 1]
    return keep

def main():
    args = parse_args()
    
    if not os.path.exists(args.model):
        print(f"Erro: Modelo {args.model} nao encontrado.")
        sys.exit(1)
        
    if not os.path.exists(args.image):
        print(f"Erro: Imagem {args.image} nao encontrada.")
        sys.exit(1)

    id2label = load_classes(args.config)
    
    print(f"Carregando modelo ONNX: {args.model}...")
    sess_opts = ort.SessionOptions()
    sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(args.model, sess_opts)
    
    input_name = session.get_inputs()[0].name
    print(f"Input: {input_name}, Shape: {session.get_inputs()[0].shape}")
    
    orig_img = cv2.imread(args.image)
    if orig_img is None:
        print(f"Erro ao abrir imagem {args.image}")
        sys.exit(1)
        
    orig_h, orig_w = orig_img.shape[:2]
    
    # Pre-processamento
    img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (640, 640))
    tensor = (img_resized.astype(np.float32) / 255.0).transpose(2, 0, 1)[None, ...]
    
    t0 = time.time()
    outputs = session.run(None, {input_name: tensor})
    infer_time = (time.time() - t0) * 1000
    
    raw_out = outputs[0][0] # Shape (55, 8400)
    print(f"Inferencia concluida em {infer_time:.2f} ms. Output shape: {raw_out.shape}")
    
    # Parse das predicoes:
    # raw_out[:4] sao as coordenadas normalizadas (cx, cy, w, h)
    # raw_out[4:54] sao as pontuacoes das 50 classes navais
    boxes_norm = raw_out[:4, :].T # (8400, 4)
    class_scores = raw_out[4:54, :].T # (8400, 50)
    
    if class_scores.max() > 1.0 or class_scores.min() < 0.0:
        scores = 1.0 / (1.0 + np.exp(-class_scores))
    else:
        scores = class_scores
        
    best_classes = np.argmax(scores, axis=1)
    best_scores = np.max(scores, axis=1)
    
    # Filtrar por limiar de confianca
    mask = best_scores >= args.conf
    filtered_boxes = boxes_norm[mask]
    filtered_scores = best_scores[mask]
    filtered_classes = best_classes[mask]
    
    if len(filtered_scores) == 0:
        print(f"Nenhum alvo detectado com confianca >= {args.conf}.")
        return
        
    gain_x = orig_w / 640.0
    gain_y = orig_h / 640.0
    
    cx = filtered_boxes[:, 0] * gain_x
    cy = filtered_boxes[:, 1] * gain_y
    w = filtered_boxes[:, 2] * gain_x
    h = filtered_boxes[:, 3] * gain_y
    
    x1 = np.clip(cx - w / 2.0, 0, orig_w)
    y1 = np.clip(cy - h / 2.0, 0, orig_h)
    x2 = np.clip(cx + w / 2.0, 0, orig_w)
    y2 = np.clip(cy + h / 2.0, 0, orig_h)
    
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)
    
    # Aplicar NMS por classe
    final_detections = []
    unique_classes = np.unique(filtered_classes)
    for c in unique_classes:
        c_mask = filtered_classes == c
        c_boxes = boxes_xyxy[c_mask]
        c_scores = filtered_scores[c_mask]
        keep = nms(c_boxes, c_scores, args.iou)
        for k in keep:
            final_detections.append({
                'class_id': int(c),
                'class_name': id2label.get(str(c), f"Class_{c}"),
                'score': float(c_scores[k]),
                'box': [int(c_boxes[k][0]), int(c_boxes[k][1]), int(c_boxes[k][2]), int(c_boxes[k][3])]
            })
            
    print(f"Total de alvos detectados apos NMS: {len(final_detections)}")
    
    annotated = orig_img.copy()
    for det in final_detections:
        bx = det['box']
        label = f"{det['class_name']}: {det['score']:.2f}"
        print(f" -> {label} em {bx}")
        
        cv2.rectangle(annotated, (bx[0], bx[1]), (bx[2], bx[3]), (0, 255, 0), 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(annotated, (bx[0], max(0, bx[1] - th - 6)), (bx[0] + tw + 4, bx[1]), (0, 255, 0), -1)
        cv2.putText(annotated, label, (bx[0] + 2, max(12, bx[1] - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2, cv2.LINE_AA)
                    
    cv2.imwrite(args.output, annotated)
    print(f"Imagem anotada salva em: {args.output}")

if __name__ == '__main__':
    main()
