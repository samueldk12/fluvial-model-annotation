"""
Trajectory & Heading Engine em PyTorch (Tensor-Based).

Calcula vetores de deslocamento, velocidade aparente, ângulo de curso náutico (0° a 360°)
e esteira de trajetória utilizando operações puramente tensoriais.
"""

import math
import torch
import torch.nn as nn

class TensorTrajectoryTracker:
    def __init__(self, max_history=30, min_speed_threshold=2.0, ema_alpha=0.7):
        self.max_history = max_history
        self.min_speed_threshold = min_speed_threshold
        self.ema_alpha = ema_alpha
        # Dicionário de rastros ativos: track_id -> tensor de histórico [N, 2]
        self.tracks = {}
        self.headings = {}
        self.speeds = {}
        self.classes = {}

    def update(self, track_ids, bboxes_tensor, class_names=None):
        """
        Atualiza os rastros usando tensores.
        
        Parâmetros:
          track_ids: lista de inteiros identificando os barcos [ID_1, ID_2, ...]
          bboxes_tensor: Tensor PyTorch [N, 4] contendo caixas (cx, cy, w, h) ou (x1, y1, x2, y2)
          class_names: lista de strings com os nomes das classes
        """
        if len(track_ids) == 0 or bboxes_tensor.shape[0] == 0:
            return
            
        # Extrair centróides (cx, cy)
        if bboxes_tensor.shape[1] == 4:
            cx = bboxes_tensor[:, 0]
            cy = bboxes_tensor[:, 1]
        centroids = torch.stack([cx, cy], dim=1) # [N, 2]

        current_active = set(track_ids)

        for i, tid in enumerate(track_ids):
            point = centroids[i:i+1] # [1, 2]
            cname = class_names[i] if class_names else "Embarcacao"
            self.classes[tid] = cname

            if tid not in self.tracks:
                self.tracks[tid] = point
                self.headings[tid] = torch.tensor(0.0)
                self.speeds[tid] = torch.tensor(0.0)
            else:
                # Concatenar novo ponto no tensor de histórico
                hist = torch.cat([self.tracks[tid], point], dim=0)
                if hist.shape[0] > self.max_history:
                    hist = hist[-self.max_history:]
                self.tracks[tid] = hist

                # Calcular vetor de deslocamento recente (dx, dy)
                if hist.shape[0] >= 3:
                    p_prev = hist[-3]
                    p_curr = hist[-1]
                    delta = p_curr - p_prev # [2] -> [dx, dy]
                    dx = delta[0]
                    dy = delta[1]

                    # Velocidade aparente em pixels por passo temporal
                    speed = torch.hypot(dx, dy)
                    self.speeds[tid] = speed

                    if speed.item() > self.min_speed_threshold:
                        # Ângulo Náutico: 0° = Norte (topo), 90° = Leste (direita), 180° = Sul, 270° = Oeste
                        # Em sistemas de coordenadas de imagem: Y cresce para baixo
                        rad = torch.atan2(dx, -dy)
                        deg = (torch.rad2deg(rad) + 360.0) % 360.0
                        
                        # Suavização por Média Móvel Exponencial (EMA)
                        old_deg = self.headings[tid]
                        smoothed_deg = self.ema_alpha * deg + (1.0 - self.ema_alpha) * old_deg
                        self.headings[tid] = smoothed_deg

    def get_track_telemetry(self, track_id):
        """
        Retorna a telemetria náutica calculada para uma embarcação específica.
        """
        if track_id not in self.tracks:
            return None
            
        deg = self.headings[track_id].item()
        speed = self.speeds[track_id].item()
        history_points = self.tracks[track_id].cpu().tolist()
        cardinal = self.degrees_to_cardinal(deg)
        
        return {
            "track_id": track_id,
            "class_name": self.classes.get(track_id, "Embarcacao"),
            "heading_deg": deg,
            "heading_cardinal": cardinal,
            "speed_pixels": speed,
            "trail": history_points,
            "current_position": history_points[-1] if history_points else (0, 0)
        }

    @staticmethod
    def degrees_to_cardinal(deg):
        """Converte ângulo náutico em graus para direção da Rosa dos Ventos."""
        directions = ["Norte (N)", "Norte-Nordeste (NNE)", "Nordeste (NE)", "Leste-Nordeste (ENE)",
                      "Leste (L)", "Leste-Sudeste (ESE)", "Sudeste (SE)", "Sul-Sudeste (SSE)",
                      "Sul (S)", "Sul-Sudoeste (SSW)", "Sudoeste (SW)", "Oeste-Sudoeste (WSW)",
                      "Oeste (O)", "Oeste-Noroeste (WNW)", "Noroeste (NW)", "Norte-Noroeste (NNW)"]
        idx = int((deg + 11.25) / 22.5) % 16
        return directions[idx]
