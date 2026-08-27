"""
Motor Cinemático Robusto com Filtro de Zona Morta (Deadzone) contra Jitter Neural,
Detecção Estrita de Embarcações Paradas/Atracadas e Destino Náutico 100% Dinâmico.
"""

import math
import numpy as np

class KinematicVesselTracker:
    def __init__(self, deadzone_pixels=8.0, min_motion_frames=5):
        self.deadzone_pixels = deadzone_pixels
        self.min_motion_frames = min_motion_frames
        self.tracks = {}

    def update_vessel(self, vessel_id, cx, cy, timestamp):
        """
        Atualiza a posição do barco e calcula velocidade, rumo real e status de movimento
        eliminando falso movimento causado por jitter de bounding box.
        """
        if vessel_id not in self.tracks:
            self.tracks[vessel_id] = {
                "history": [(cx, cy, timestamp)],
                "anchor_pos": (cx, cy),
                "consecutive_motion": 0,
                "is_stationary": True,
                "speed": 0.0,
                "vx": 0.0,
                "vy": 0.0,
                "heading_deg": 0.0,
                "cardinal": "Proa Fixa (Atracado)",
                "destination": "Atracado no Píer / Fundeado",
                "last_seen": timestamp
            }
            return self.tracks[vessel_id]

        track = self.tracks[vessel_id]
        track["history"].append((cx, cy, timestamp))
        if len(track["history"]) > 35:
            track["history"].pop(0)

        track["last_seen"] = timestamp

        # Calcular mediana das últimas 10 posições para filtrar trepidação de pixels
        recent_pts = np.array([(p[0], p[1]) for p in track["history"][-10:]])
        med_x, med_y = float(np.median(recent_pts[:, 0])), float(np.median(recent_pts[:, 1]))

        # Distância em relação à posição âncora
        dist_from_anchor = math.hypot(med_x - track["anchor_pos"][0], med_y - track["anchor_pos"][1])

        # Se o deslocamento acumulado for menor que a zona morta (ex: 8 pixels)
        if dist_from_anchor < self.deadzone_pixels:
            track["consecutive_motion"] = max(0, track["consecutive_motion"] - 1)
            track["is_stationary"] = True
            track["speed"] = 0.0
            track["vx"] = 0.0
            track["vy"] = 0.0
            track["cardinal"] = "Proa Fixa (Fundeado)"
            track["destination"] = "Atracado no Píer / Fundeado"
        else:
            # Deslocamento consistente observado
            first_x, first_y, first_t = track["history"][0]
            dt = max(0.25, timestamp - first_t)
            vx = (med_x - first_x) / dt
            vy = (med_y - first_y) / dt
            speed = math.hypot(vx, vy)

            # Velocidade mínima para navegação real (2.5 px/s)
            if speed > 2.5:
                track["consecutive_motion"] += 1
                if track["consecutive_motion"] >= self.min_motion_frames:
                    track["is_stationary"] = False
                    track["speed"] = speed
                    track["vx"] = vx
                    track["vy"] = vy
                    
                    # Rumo Náutico Verdadeiro: atan2(dx, -dy)
                    heading_rad = math.atan2(vx, -vy)
                    heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0
                    track["heading_deg"] = heading_deg

                    track["cardinal"] = self._degrees_to_cardinal(heading_deg)
                    track["destination"] = self._compute_dynamic_destination(heading_deg, cx, cy)
                    track["anchor_pos"] = (med_x, med_y)
            else:
                track["is_stationary"] = True
                track["speed"] = 0.0
                track["cardinal"] = "Proa Fixa (Atracado)"
                track["destination"] = "Atracado no Píer / Fundeado"

        return track

    def _degrees_to_cardinal(self, degrees):
        dirs = [
            "Norte (N)", "Norte-Nordeste (NNE)", "Nordeste (NE)", "Leste-Nordeste (ENE)",
            "Leste (E)", "Leste-Sudeste (ESE)", "Sudeste (SE)", "Sul-Sudeste (SSE)",
            "Sul (S)", "Sul-Sudoeste (SSW)", "Sudoeste (SW)", "Oeste-Sudoeste (WSW)",
            "Oeste (W)", "Oeste-Noroeste (WNW)", "Noroeste (NW)", "Norte-Noroeste (NNW)"
        ]
        idx = int((degrees + 11.25) / 22.5) % 16
        return dirs[idx]

    def _compute_dynamic_destination(self, heading_deg, cx, cy):
        """
        Calcula o destino dinâmico real baseado no vetor de deslocamento.
        """
        if 45.0 <= heading_deg < 135.0:
            return "Entrada do Canal -> Bacia de Manobra / Cais 02"
        elif 135.0 <= heading_deg < 225.0:
            return "Sul do Canal -> Travessia da Balsa / Ponta da Praia"
        elif 225.0 <= heading_deg < 315.0:
            return "Saída do Canal -> Barra de Santos / Mar Aberto"
        else:
            return "Norte do Canal -> Terminal Alemoa / Saboó"

    def predict_future_positions(self, track, seconds_ahead=[5.0, 10.0]):
        """
        Retorna as coordenadas futuras apenas se o barco estiver em movimento real.
        """
        if track["is_stationary"]:
            return []

        cx, cy, _ = track["history"][-1]
        preds = []
        for s in seconds_ahead:
            pred_x = int(cx + track["vx"] * s)
            pred_y = int(cy + track["vy"] * s)
            preds.append({
                "seconds": s,
                "x": pred_x,
                "y": pred_y
            })
        return preds
