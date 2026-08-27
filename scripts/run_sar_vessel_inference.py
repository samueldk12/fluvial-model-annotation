"""
Script de Inferencia para Deteccao de Embarcacoes com YOLOv8 SAR / Fluvial (ONNX)
Modelo otimizado para deteccao em imagens de radar de abertura sintetica (SAR) e condicoes fluviais adversas.
"""

import argparse
import os
import sys
import time
import cv2
import numpy as np
import onnxruntime as ort

def parse_args():
    parser = argparse.ArgumentParser(description='Inferencia YOLOv8 SAR/Fluvial Vessel Detection')
    parser.add_argument('--model', type=str,
                        default='models/02_sar_radar_and_edge/MeWan2808_YOLOv8_SAR/quantized/best.onnx',
                        help='Caminho para o modelo ONNX')
    parser.add_argument('--image', type=str,
                        default='models/01_satellite_and_aerial_naval/SixOpen_Y8NavalONNX/examples/Y8Nex3.PNG',
                        help='Caminho para a imagem de teste')
    parser.add_argument('--conf', type=float, default=0.25,
                        help='Limiar de confianca minimo')
    parser.add_argument('--iou', type=float, default=0.45,
                        help='Limiar de IoU para NMS')
    parser.add_argument('--output', type=str, default='output_sar_detection.png',
                        help='Arquivo de saida para a imagem anotada')
    return parser.parse_args()

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

    print(f"Carregando modelo ONNX: {args.model}...")
    sess = ort.InferenceSession(args.model)
    input_name = sess.get_inputs()[0].name
    
    orig_img = cv2.imread(args.image)
    if orig_img is None:
        print(f"Erro ao abrir {args.image}")
        sys.exit(1)
        
    orig_h, orig_w = orig_img.shape[:2]
    
    img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (640, 640))
    tensor = (img_resized.astype(np.float32) / 255.0).transpose(2, 0, 1)[None, ...]
    
    t0 = time.time()
    outputs = sess.run(None, {input_name: tensor})
    infer_time = (time.time() - t0) * 1000
    
    raw_out = outputs[0][0] # Shape (5, 8400)
    print(f"Inferencia concluida em {infer_time:.2f} ms. Output shape: {raw_out.shape}")
    
    boxes_norm = raw_out[:4, :].T # (8400, 4) in (cx, cy, w, h)
    scores = raw_out[4, :].T      # (8400,)
    
    if scores.max() > 1.0 or scores.min() < 0.0:
        scores = 1.0 / (1.0 + np.exp(-scores))
        
    mask = scores >= args.conf
    filtered_boxes = boxes_norm[mask]
    filtered_scores = scores[mask]
    
    if len(filtered_scores) == 0:
        print(f"Nenhuma embarcacao detectada com confianca >= {args.conf}.")
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
    keep = nms(boxes_xyxy, filtered_scores, args.iou)
    
    print(f"Total de embarcacoes detectadas apos NMS: {len(keep)}")
    annotated = orig_img.copy()
    for idx in keep:
        bx = [int(v) for v in boxes_xyxy[idx]]
        score = float(filtered_scores[idx])
        label = f"Vessel: {score:.2f}"
        print(f" -> {label} em {bx}")
        
        cv2.rectangle(annotated, (bx[0], bx[1]), (bx[2], bx[3]), (255, 128, 0), 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(annotated, (bx[0], max(0, bx[1] - th - 6)), (bx[0] + tw + 4, bx[1]), (255, 128, 0), -1)
        cv2.putText(annotated, label, (bx[0] + 2, max(12, bx[1] - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
                    
    cv2.imwrite(args.output, annotated)
    print(f"Resultado salvo em: {args.output}")

if __name__ == '__main__':
    main()
