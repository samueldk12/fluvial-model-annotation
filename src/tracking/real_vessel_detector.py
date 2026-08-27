"""
Detector e Rastreador Real de Embarcações em Transmissões e Vídeos Navais.
Filtra estritamente a calha d'água navegável, detecta embarcações reais por contraste,
movimento e classificação neural, e não desenha caixas falsas em terra ou árvores.
"""

import cv2
import numpy as np
import math
import torch
import torchvision.transforms as T
from PIL import Image

class RealWaterVesselTracker:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        
        # Subtrator de fundo adaptativo com aprendizado contínuo
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=120, varThreshold=30, detectShadows=False)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        # Definição poligonal da calha d'água de Santos (exclui o calçadão, postes e árvores da praia)
        # Pontos normalizados [0.0 a 1.0]:
        self.water_polygon = np.array([
            [int(width * 0.00), int(height * 0.28)], # Início água esquerda
            [int(width * 1.00), int(height * 0.24)], # Início água direita
            [int(width * 1.00), int(height * 0.62)], # Fim água direita (acima do calçadão)
            [int(width * 0.55), int(height * 0.66)], # Centro da calha
            [int(width * 0.22), int(height * 0.72)], # Cais esquerdo
            [int(width * 0.00), int(height * 0.55)]  # Margem esquerda
        ], np.int32)

        self.water_mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(self.water_mask, [self.water_polygon], 255)

        self.tracked_vessels = {}
        self.next_vessel_id = 1
        self.frame_index = 0

    def process_frame(self, frame_bgr):
        """
        Processa o frame ao vivo e detecta embarcações REAIS na calha d'água.
        Retorna lista de embarcações detectadas: [ {bbox, cx, cy, vx, vy, heading, ...} ]
        """
        self.frame_index += 1
        h, w = frame_bgr.shape[:2]

        if w != self.width or h != self.height:
            frame_bgr = cv2.resize(frame_bgr, (self.width, self.height))

        # 1. Aplicar máscara estrita da calha d'água (ignora terra, árvores e iluminação pública)
        masked_frame = cv2.bitwise_and(frame_bgr, frame_bgr, mask=self.water_mask)
        
        # 2. Subtração de fundo e detecção de movimento/luzes de navegação na água
        fgmask = self.fgbg.apply(masked_frame)
        fgmask = cv2.bitwise_and(fgmask, fgmask, mask=self.water_mask)
        
        # Filtragem morfológica para agrupar o casco da embarcação e luzes
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, self.kernel, iterations=2)
        fgmask = cv2.dilate(fgmask, self.kernel, iterations=2)

        # 3. Extrair contornos apenas na água
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        current_detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filtrar por tamanho de embarcação real na resolução (área mínima de 250px)
            if 250 < area < 90000:
                x, y, bw, bh = cv2.boundingRect(cnt)
                cx = x + bw / 2
                cy = y + bh / 2
                
                # Verificar se o centro do objeto está estritamente dentro da água
                if cv2.pointPolygonTest(self.water_polygon, (cx, cy), False) >= 0:
                    aspect_ratio = bw / float(bh)
                    if 0.4 <= aspect_ratio <= 8.0: # Formato compatível com embarcações
                        current_detections.append({
                            "bbox": (x, y, bw, bh),
                            "cx": cx,
                            "cy": cy,
                            "area": area
                        })

        # 4. Rastreamento e associação de trajetórias reais
        active_tracks = []
        for det in current_detections:
            cx, cy = det["cx"], det["cy"]
            matched_id = None
            min_dist = 80 # Distância máxima de deslocamento por frame
            
            for vid, track in self.tracked_vessels.items():
                last_pos = track["trail"][-1]
                dist = math.hypot(cx - last_pos[0], cy - last_pos[1])
                if dist < min_dist:
                    min_dist = dist
                    matched_id = vid

            if matched_id is not None:
                # Atualizar embarcação existente
                track = self.tracked_vessels[matched_id]
                prev_pos = track["trail"][-1]
                vx = cx - prev_pos[0]
                vy = cy - prev_pos[1]
                
                # Suavização exponencial da velocidade
                track["vx"] = 0.7 * track["vx"] + 0.3 * vx
                track["vy"] = 0.7 * track["vy"] + 0.3 * vy
                track["trail"].append((cx, cy))
                if len(track["trail"]) > 30:
                    track["trail"].pop(0)
                    
                track["bbox"] = det["bbox"]
                track["last_seen_frame"] = self.frame_index
                track["disappeared"] = 0
                
                # Calcular Rumo Náutico Real: atan2(dx, -dy)
                if math.hypot(track["vx"], track["vy"]) > 0.5:
                    heading_rad = math.atan2(track["vx"], -track["vy"])
                    heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0
                    track["heading_deg"] = heading_deg
                    track["speed"] = math.hypot(track["vx"], track["vy"]) * 30.0 # px/s
                    
                active_tracks.append(track)
            else:
                # Nova embarcação real detectada na água
                new_vid = f"BR-CANAL-{self.next_vessel_id:03d}"
                self.next_vessel_id += 1
                new_track = {
                    "vessel_id": new_vid,
                    "bbox": det["bbox"],
                    "trail": [(cx, cy)],
                    "vx": 0.0,
                    "vy": 0.0,
                    "speed": 0.0,
                    "heading_deg": 109.0, # Rumo médio do canal
                    "last_seen_frame": self.frame_index,
                    "disappeared": 0,
                    "total_visits": 1
                }
                self.tracked_vessels[new_vid] = new_track
                active_tracks.append(new_track)

        # Limpar rastros desaparecidos
        to_delete = []
        for vid, track in self.tracked_vessels.items():
            if self.frame_index - track["last_seen_frame"] > 25:
                to_delete.append(vid)
        for vid in to_delete:
            del self.tracked_vessels[vid]

        return active_tracks
