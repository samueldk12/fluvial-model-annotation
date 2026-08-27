"""
Módulo de Rastreamento de Embarcações com Cálculo de Trajetória, ID Único e Direção de Movimento (Heading/Vetor de Curso).

Demonstra como combinar:
1. Detecção YOLO de embarcações
2. Rastreamento Temporal com IDs Persistentes (Multi-Object Tracking)
3. Cálculo de Vetor de Movimento (dx, dy), Velocidade Aparente e Ângulo de Curso/Navegação (0° a 360°)
4. Histórico da esteira de navegação (Trajectory Trail)
"""

import math
import cv2
import numpy as np

class VesselTrajectoryTracker:
    def __init__(self, max_history=30):
        self.max_history = max_history
        self.tracks = {} # track_id -> {'history': [(x, y)], 'heading': float, 'speed': float, 'class_name': str}

    def update(self, detections):
        """
        detections: lista de tuplas (track_id, x1, y1, x2, y2, class_name, conf)
        """
        current_ids = set()
        for track_id, x1, y1, x2, y2, class_name, conf in detections:
            current_ids.add(track_id)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            if track_id not in self.tracks:
                self.tracks[track_id] = {
                    "history": [(cx, cy)],
                    "heading_deg": 0.0,
                    "heading_cardinal": "N/D",
                    "speed_pixels": 0.0,
                    "class_name": class_name
                }
            else:
                hist = self.tracks[track_id]["history"]
                hist.append((cx, cy))
                if len(hist) > self.max_history:
                    hist.pop(0)
                    
                # Calcular vetor de deslocamento recente
                if len(hist) >= 3:
                    p_old = hist[-3]
                    p_new = hist[-1]
                    dx = p_new[0] - p_old[0]
                    dy = p_new[1] - p_old[1] # Em coordenadas de imagem, Y cresce para baixo
                    
                    speed = math.hypot(dx, dy)
                    self.tracks[track_id]["speed_pixels"] = speed
                    
                    if speed > 2.0: # Movimento significativo
                        # Ângulo náutico: 0 = Norte (para cima na imagem), 90 = Leste (direita), 180 = Sul (baixo), 270 = Oeste (esquerda)
                        angle_rad = math.atan2(dx, -dy)
                        angle_deg = (math.degrees(angle_rad) + 360) % 360
                        self.tracks[track_id]["heading_deg"] = angle_deg
                        self.tracks[track_id]["heading_cardinal"] = self._degrees_to_cardinal(angle_deg)
                        
        # Limpar rastros de barcos perdidos
        for tid in list(self.tracks.keys()):
            if tid not in current_ids and len(self.tracks[tid]["history"]) > 0:
                pass # Pode manter temporariamente se desejar

    def _degrees_to_cardinal(self, deg):
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        ix = int((deg + 11.25) / 22.5) % 16
        return dirs[ix]

    def draw_trajectories(self, image, detections):
        """
        Desenha as caixas delimitadoras, IDs únicos, trilha de trajetória e vetor de direção (seta de curso).
        """
        annotated = image.copy()
        for track_id, x1, y1, x2, y2, class_name, conf in detections:
            t_data = self.tracks.get(track_id, {})
            hist = t_data.get("history", [])
            heading_deg = t_data.get("heading_deg", 0.0)
            cardinal = t_data.get("heading_cardinal", "N/D")
            
            # 1. Bounding Box
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # 2. Rastro de Trajetória (Trail)
            for i in range(1, len(hist)):
                thickness = int(np.sqrt(64 / float(len(hist) - i + 1)) * 1.5)
                alpha = i / len(hist)
                color = (int(255 * (1 - alpha)), int(255 * alpha), 255)
                cv2.line(annotated, hist[i - 1], hist[i], color, thickness)
                
            # 3. Vetor de Direção de Navegação (Seta de Rota)
            if len(hist) >= 2 and t_data.get("speed_pixels", 0) > 2.0:
                cx, cy = hist[-1]
                rad = math.radians(heading_deg)
                arrow_len = 45
                end_x = int(cx + arrow_len * math.sin(rad))
                end_y = int(cy - arrow_len * math.cos(rad))
                cv2.arrowedLine(annotated, (cx, cy), (end_x, end_y), (0, 0, 255), 3, tipLength=0.3)
                
            # 4. Painel de Identificação Única e Telemetria de Curso
            label = f"Barco ID #{track_id} | {class_name} | Rumo: {cardinal} ({heading_deg:.0f} deg)"
            cv2.putText(annotated, label, (int(x1), max(20, int(y1) - 10)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(annotated, label, (int(x1), max(20, int(y1) - 10)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
                        
        return annotated

def simulate_vessel_tracking_demo():
    """
    Demonstracao visual gerando uma simulacao com 3 embarcacoes navegando em direcoes distintas.
    """
    print("Executando simulacao de rastreamento de barco, ID unico e vetor de rumo (Heading)...")
    h, w = 600, 800
    tracker = VesselTrajectoryTracker(max_history=25)
    
    # 3 barcos com trajetorias simuladas
    vessels = [
        {"id": 101, "x": 100, "y": 150, "vx": 4.0, "vy": 1.2, "name": "Cargueiro"},
        {"id": 102, "x": 700, "y": 450, "vx": -3.5, "vy": -2.0, "name": "Balsa Fluvial"},
        {"id": 103, "x": 400, "y": 500, "vx": 0.5, "vy": -4.5, "name": "Lancha Patrulha"}
    ]
    
    frames = []
    for step in range(30):
        # Fundo azul (Agua de rio/mar)
        frame = np.full((h, w, 3), (120, 80, 20), dtype=np.uint8)
        
        detections = []
        for v in vessels:
            v["x"] += v["vx"]
            v["y"] += v["vy"]
            bw, bh = 70, 40
            x1, y1 = v["x"] - bw/2, v["y"] - bh/2
            x2, y2 = v["x"] + bw/2, v["y"] + bh/2
            detections.append((v["id"], x1, y1, x2, y2, v["name"], 0.95))
            
        tracker.update(detections)
        annotated = tracker.draw_trajectories(frame, detections)
        frames.append(annotated)
        
    output_path = "scripts/simulacao_rastreamento_rumo.png"
    cv2.imwrite(output_path, frames[-1])
    print(f"[SUCESSO] Demonstracao gerada e salva em: {output_path}")

if __name__ == "__main__":
    simulate_vessel_tracking_demo()
