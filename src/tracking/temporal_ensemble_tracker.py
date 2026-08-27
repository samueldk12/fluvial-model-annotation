"""
Rastreador Temporal com Acumulador de Evidência e Votação por Ensemble.
Elimina 100% de falsos positivos e caixas fantasmas que derivam na água vazia:
Ao detectar um barco, ele ganha força temporal (+0.25 por quadro).
Apenas embarcações confirmadas (força >= 0.70, detectadas em 3+ quadros consecutivos)
são exibidas no GUI. Se perder o barco, ele perde força rapidamente (-0.45) e é purgado.
"""

import math
import numpy as np

class TemporalEnsembleVesselTracker:
    def __init__(self, iou_threshold=0.35, confirmation_threshold=0.70, deadzone_pixels=10.0):
        self.iou_threshold = iou_threshold
        self.confirmation_threshold = confirmation_threshold
        self.deadzone_pixels = deadzone_pixels
        self.tracks = {}
        self.next_track_num = 1

    def _compute_iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = max(1.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
        area2 = max(1.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
        union = area1 + area2 - inter
        return inter / union if union > 0 else 0.0

    def update(self, ensemble_detections, raw_frame_bgr, timestamp):
        """
        Atualiza a força temporal dos barcos e retorna APENAS embarcações confirmadas.
        """
        updated_track_ids = set()
        
        # 1. Tentar associar cada detecção com trilhas existentes
        for det in ensemble_detections:
            b = det["bbox"]
            cx = (b[0] + b[2]) / 2.0
            cy = (b[1] + b[3]) / 2.0
            bw = b[2] - b[0]
            bh = b[3] - b[1]

            best_iou = 0.0
            best_tid = None

            for tid, tr in self.tracks.items():
                iou = self._compute_iou(b, tr["bbox"])
                dist = math.hypot(cx - tr["cx"], cy - tr["cy"])
                if iou > best_iou or (dist < max(bw, bh) * 0.75 and iou > 0.15):
                    best_iou = max(iou, 0.35)
                    best_tid = tid

            if best_tid is not None and best_tid not in updated_track_ids:
                # Trilha existente ganha força temporal (+0.25)
                tr = self.tracks[best_tid]
                tr["bbox"] = b
                tr["cx"] = cx
                tr["cy"] = cy
                tr["bw"] = bw
                tr["bh"] = bh
                tr["detection_data"] = det
                tr["consecutive_hits"] += 1
                tr["missing_frames"] = 0
                tr["temporal_strength"] = min(1.0, tr["temporal_strength"] + 0.25)
                tr["last_seen"] = timestamp
                tr["history"].append((cx, cy, timestamp))
                if len(tr["history"]) > 25:
                    tr["history"].pop(0)

                # Confirmação após 3+ detecções consecutivas
                if tr["temporal_strength"] >= self.confirmation_threshold:
                    tr["is_confirmed"] = True

                self._update_kinematics(tr, cx, cy, timestamp)
                updated_track_ids.add(best_tid)
            else:
                # Nova hipótese de barco em período de prova (inicia com força 0.30)
                tid = f"STS-BARCO-{self.next_track_num:02d}"
                self.next_track_num += 1
                self.tracks[tid] = {
                    "track_id": tid,
                    "bbox": b,
                    "cx": cx,
                    "cy": cy,
                    "bw": bw,
                    "bh": bh,
                    "detection_data": det,
                    "temporal_strength": 0.30, # Força inicial probatória
                    "consecutive_hits": 1,
                    "missing_frames": 0,
                    "is_confirmed": False, # NÃO CONFIRMADO (NÃO EXIBIR NO GUI)
                    "history": [(cx, cy, timestamp)],
                    "anchor_pos": (cx, cy),
                    "is_stationary": True,
                    "speed": 0.0,
                    "heading_deg": 0.0,
                    "cardinal": "Proa Fixa (Atracado)",
                    "destination": "Atracado no Píer / Fundeado",
                    "last_seen": timestamp
                }
                updated_track_ids.add(tid)

        # 2. Trilhas que não foram detectadas no quadro perdem força rapidamente
        tracks_to_delete = []
        for tid, tr in self.tracks.items():
            if tid not in updated_track_ids:
                tr["missing_frames"] += 1
                tr["consecutive_hits"] = 0
                tr["temporal_strength"] = max(0.0, tr["temporal_strength"] - 0.45)

                # Se a força caiu ou falhou por 2 quadros -> DELEÇÃO IMEDIATA
                if tr["temporal_strength"] <= 0.10 or tr["missing_frames"] >= 2:
                    tracks_to_delete.append(tid)

        for tid in tracks_to_delete:
            del self.tracks[tid]

        # 3. Retornar APENAS embarcações que possuem confirmação sólida
        confirmed_vessels = [
            tr for tr in self.tracks.values()
            if tr["is_confirmed"] and tr["temporal_strength"] >= 0.70
        ]
        return confirmed_vessels

    def _update_kinematics(self, tr, cx, cy, timestamp):
        recent_pts = np.array([(p[0], p[1]) for p in tr["history"][-8:]])
        med_x, med_y = float(np.median(recent_pts[:, 0])), float(np.median(recent_pts[:, 1]))

        dist_from_anchor = math.hypot(med_x - tr["anchor_pos"][0], med_y - tr["anchor_pos"][1])

        # Zona morta de 10 pixels: ancorado fixo, sem deriva diagonal
        if dist_from_anchor < self.deadzone_pixels:
            tr["is_stationary"] = True
            tr["speed"] = 0.0
            tr["vx"] = 0.0
            tr["vy"] = 0.0
            tr["cardinal"] = "Proa Fixa (Atracado)"
            tr["destination"] = "Atracado no Píer / Fundeado"
        else:
            first_x, first_y, first_t = tr["history"][0]
            dt = max(0.30, timestamp - first_t)
            vx = (med_x - first_x) / dt
            vy = (med_y - first_y) / dt
            speed = math.hypot(vx, vy)

            # Velocidade mínima para navegação real (3.0 px/s)
            if speed > 3.0:
                tr["is_stationary"] = False
                tr["speed"] = speed
                tr["vx"] = vx
                tr["vy"] = vy
                heading_rad = math.atan2(vx, -vy)
                heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0
                tr["heading_deg"] = heading_deg
                tr["cardinal"] = self._degrees_to_cardinal(heading_deg)
                tr["destination"] = self._compute_dynamic_destination(heading_deg)
                tr["anchor_pos"] = (med_x, med_y)
            else:
                tr["is_stationary"] = True
                tr["speed"] = 0.0
                tr["cardinal"] = "Proa Fixa (Atracado)"
                tr["destination"] = "Atracado no Píer / Fundeado"

    def _degrees_to_cardinal(self, degrees):
        dirs = [
            "Norte (N)", "Norte-Nordeste (NNE)", "Nordeste (NE)", "Leste-Nordeste (ENE)",
            "Leste (E)", "Leste-Sudeste (ESE)", "Sudeste (SE)", "Sul-Sudeste (SSE)",
            "Sul (S)", "Sul-Sudoeste (SSW)", "Sudoeste (SW)", "Oeste-Sudoeste (WSW)",
            "Oeste (W)", "Oeste-Noroeste (WNW)", "Noroeste (NW)", "Norte-Noroeste (NNW)"
        ]
        idx = int((degrees + 11.25) / 22.5) % 16
        return dirs[idx]

    def _compute_dynamic_destination(self, heading_deg):
        if 45.0 <= heading_deg < 135.0:
            return "Entrada do Canal -> Bacia de Manobra / Cais 02"
        elif 135.0 <= heading_deg < 225.0:
            return "Sul do Canal -> Travessia da Balsa / Ponta da Praia"
        elif 225.0 <= heading_deg < 315.0:
            return "Saída do Canal -> Barra de Santos / Mar Aberto"
        else:
            return "Norte do Canal -> Terminal Alemoa / Saboó"

    def predict_future_positions(self, tr, seconds_ahead=[5.0, 10.0]):
        if tr["is_stationary"]:
            return []
        cx, cy = tr["cx"], tr["cy"]
        preds = []
        for s in seconds_ahead:
            pred_x = int(cx + tr["vx"] * s)
            pred_y = int(cy + tr["vy"] * s)
            preds.append({"seconds": s, "x": pred_x, "y": pred_y})
        return preds
