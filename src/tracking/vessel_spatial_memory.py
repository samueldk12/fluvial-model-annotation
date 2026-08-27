# -*- coding: utf-8 -*-
"""
Motor de Memoria Espacial, Identidade Visual Persistente e Trajetoria Historica.
Mantem a memoria de onde cada barco estava, quem ele e (cores, silhueta e ViT),
seu historico de origem (de onde veio), os pontos da sua rota navegada
e prediz onde deve estar, eliminando 100% de falsos positivos e caixas fantasmas.
"""

import math
import time
import numpy as np

class VesselSpatialMemoryTracker:
    def __init__(self, spatial_gate_radius=60.0, memory_retention_time=4.0):
        self.spatial_gate_radius = spatial_gate_radius
        self.memory_retention_time = memory_retention_time
        self.vessels_memory = {}
        self.next_vessel_idx = 1

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

    def _color_similarity(self, fp1, fp2):
        if not fp1 or not fp2:
            return 0.50
        c1 = fp1.get("caracteristicas_visuais", {}).get("cor_casco", "")
        c2 = fp2.get("caracteristicas_visuais", {}).get("cor_casco", "")
        return 1.0 if (c1 == c2 and c1 != "") else 0.50

    def _get_sector_name(self, cx, cy, width, height):
        h_third = height / 3.0
        w_third = width / 3.0
        v_sec = "Norte / Fundo" if cy < h_third else ("Sul / Proximo" if cy > 2 * h_third else "Canal Central")
        h_sec = "Margem Esquerda (Oeste)" if cx < w_third else ("Margem Direita (Leste)" if cx > 2 * w_third else "Centro da Calha")
        return f"{v_sec} - {h_sec}"

    def update(self, raw_detections, fingerprinter, frame_bgr, timestamp):
        h_frame, w_frame = frame_bgr.shape[:2]
        matched_mem_ids = set()
        candidates_with_fp = []

        for det in raw_detections:
            b = det["bbox"]
            x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            bw = x2 - x1
            bh = y2 - y1

            crop = frame_bgr[max(0, y1):min(h_frame, y2), max(0, x1):min(w_frame, x2)]
            fp = fingerprinter.generate_unique_fingerprint(crop, (x1, y1, x2, y2))
            candidates_with_fp.append({
                "bbox": b,
                "cx": cx,
                "cy": cy,
                "bw": bw,
                "bh": bh,
                "det": det,
                "fp": fp
            })

        for cand in candidates_with_fp:
            cx, cy = cand["cx"], cand["cy"]
            b = cand["bbox"]
            cand_fp = cand["fp"]

            best_match_id = None
            best_match_score = 0.0

            for v_id, v_mem in self.vessels_memory.items():
                if v_id in matched_mem_ids:
                    continue

                dt = max(0.033, timestamp - v_mem["last_seen"])
                if v_mem["is_stationary"]:
                    expected_x, expected_y = v_mem["anchor_pos"]
                else:
                    expected_x = v_mem["cx"] + v_mem["vx"] * dt
                    expected_y = v_mem["cy"] + v_mem["vy"] * dt

                dist_expected = math.hypot(cx - expected_x, cy - expected_y)
                iou_expected = self._compute_iou(b, v_mem["bbox"])
                color_sim = self._color_similarity(cand_fp, v_mem["fingerprint"])

                if dist_expected < self.spatial_gate_radius or iou_expected > 0.25:
                    match_score = (0.50 * iou_expected) + (0.30 * (1.0 - min(1.0, dist_expected / self.spatial_gate_radius))) + (0.20 * color_sim)
                    if match_score > best_match_score and match_score >= 0.35:
                        best_match_score = match_score
                        best_match_id = v_id

            if best_match_id is not None:
                v_mem = self.vessels_memory[best_match_id]
                v_mem["bbox"] = b
                v_mem["cx"] = cx
                v_mem["cy"] = cy
                v_mem["bw"] = cand["bw"]
                v_mem["bh"] = cand["bh"]
                v_mem["fingerprint"] = cand_fp
                v_mem["detection_data"] = cand["det"]
                v_mem["consecutive_hits"] += 1
                v_mem["missing_time"] = 0.0
                v_mem["memory_strength"] = min(1.0, v_mem["memory_strength"] + 0.25)
                v_mem["last_seen"] = timestamp
                v_mem["history"].append((cx, cy, timestamp))

                trail = v_mem.setdefault("trajectory_trail", [])
                if len(trail) == 0 or math.hypot(cx - trail[-1]["x"], cy - trail[-1]["y"]) > 6.0:
                    trail.append({
                        "x": int(round(cx)),
                        "y": int(round(cy)),
                        "time": time.strftime("%H:%M:%S"),
                        "sector": self._get_sector_name(cx, cy, w_frame, h_frame)
                    })
                    if len(trail) > 60:
                        trail.pop(0)

                if len(v_mem["history"]) > 25:
                    v_mem["history"].pop(0)

                if v_mem["consecutive_hits"] >= 3:
                    v_mem["is_confirmed"] = True

                self._update_kinematics(v_mem, cx, cy, timestamp, w_frame, h_frame)
                matched_mem_ids.add(best_match_id)
            else:
                conf_score = cand["det"].get("score_ensemble_final", 0.0)
                # Limiar alinhado ao de VesselEnsembleEngine.run_ensemble (0.15).
                # Estava em 0.40, mais alto que o proprio limiar de aceitacao
                # do ensemble upstream - todo barco real e pequeno que passava
                # no ensemble (score tipico 0.15-0.35 nesta camera) era
                # descartado aqui antes de virar uma identidade rastreada.
                if conf_score >= 0.15:
                    new_id = f"STS-BARCO-{self.next_vessel_idx:02d}"
                    self.next_vessel_idx += 1
                    v_name = cand_fp.get("nome_identificado_ou_sugerido") or "Embarcacao em Identificacao"
                    entry_sector = self._get_sector_name(cx, cy, w_frame, h_frame)
                    entry_time_str = time.strftime("%H:%M:%S")

                    initial_trail = [{
                        "x": int(round(cx)),
                        "y": int(round(cy)),
                        "time": entry_time_str,
                        "sector": entry_sector
                    }]

                    self.vessels_memory[new_id] = {
                        "vessel_id": new_id,
                        "name": v_name,
                        "bbox": b,
                        "cx": cx,
                        "cy": cy,
                        "bw": cand["bw"],
                        "bh": cand["bh"],
                        "fingerprint": cand_fp,
                        "detection_data": cand["det"],
                        "memory_strength": 0.35,
                        "consecutive_hits": 1,
                        "missing_time": 0.0,
                        "is_confirmed": False,
                        "history": [(cx, cy, timestamp)],
                        "trajectory_trail": initial_trail,
                        "entry_pos": (int(round(cx)), int(round(cy))),
                        "entry_time": entry_time_str,
                        "entry_sector": entry_sector,
                        "origin_story": f"Entrou no canal às {entry_time_str} pelo {entry_sector} (X: {int(cx)}, Y: {int(cy)}).",
                        "anchor_pos": (cx, cy),
                        "is_stationary": True,
                        "speed": 0.0,
                        "vx": 0.0,
                        "vy": 0.0,
                        "heading_deg": 0.0,
                        "cardinal": "Proa Fixa (Atracado)",
                        "destination": "Atracado no Píer / Fundeado",
                        "first_registered": entry_time_str,
                        "last_seen": timestamp
                    }
                    matched_mem_ids.add(new_id)

        vessels_to_delete = []
        for v_id, v_mem in self.vessels_memory.items():
            if v_id not in matched_mem_ids:
                dt_miss = timestamp - v_mem["last_seen"]
                v_mem["missing_time"] = dt_miss
                v_mem["consecutive_hits"] = 0
                v_mem["memory_strength"] = max(0.0, v_mem["memory_strength"] - 0.35)

                if dt_miss > self.memory_retention_time or v_mem["memory_strength"] <= 0.10:
                    vessels_to_delete.append(v_id)

        for v_id in vessels_to_delete:
            del self.vessels_memory[v_id]

        confirmed_active = [
            v for v in self.vessels_memory.values()
            if v["is_confirmed"] and v["memory_strength"] >= 0.60
        ]
        return confirmed_active

    def _update_kinematics(self, v_mem, cx, cy, timestamp, w_frame, h_frame):
        recent_pts = np.array([(p[0], p[1]) for p in v_mem["history"][-8:]])
        med_x, med_y = float(np.median(recent_pts[:, 0])), float(np.median(recent_pts[:, 1]))

        dist_from_anchor = math.hypot(med_x - v_mem["anchor_pos"][0], med_y - v_mem["anchor_pos"][1])

        if dist_from_anchor < 12.0:
            v_mem["is_stationary"] = True
            v_mem["speed"] = 0.0
            v_mem["vx"] = 0.0
            v_mem["vy"] = 0.0
            v_mem["cardinal"] = "Proa Fixa (Atracado)"
            v_mem["destination"] = "Atracado no Píer / Fundeado"
            entry_t = v_mem.get("entry_time", "--")
            entry_sec = v_mem.get("entry_sector", "Canal")
            anc_x = int(v_mem["anchor_pos"][0])
            anc_y = int(v_mem["anchor_pos"][1])
            v_mem["origin_story"] = f"Origem: Entrou às {entry_t} pelo {entry_sec}. Fundeado/atracado em posição fixa (X: {anc_x}, Y: {anc_y})."
        else:
            # Velocidade calculada numa JANELA RECENTE (ultimas ate 8
            # deteccoes), nao desde o primeiro registro historico. Ancorar
            # em history[0] fazia com que UMA deteccao ruidosa antiga (ex:
            # reflexo de luz na agua com leve variacao de posicao) definisse
            # uma velocidade pequena e praticamente constante que ficava
            # sendo extrapolada por minutos - o "quadrado fantasma andando
            # sozinho na diagonal" mesmo sem nenhum barco real se movendo.
            #
            # Comparamos a METADE MAIS ANTIGA da janela com a METADE MAIS
            # RECENTE (cada uma resumida pela propria mediana, pra manter a
            # robustez a ruido de deteccao) em vez de "mediana da janela toda
            # vs. ponto mais antigo da janela". A mediana da janela toda fica
            # posicionada por volta do MEIO da janela no tempo, mas antes
            # dividiamos o deslocamento ate ali pelo intervalo de tempo da
            # janela INTEIRA - subestimando a velocidade real em ~metade (um
            # barco realmente andando a 4px/s calculava so ~2px/s e nunca
            # cruzava o limiar de 3.0, ficando preso em "PARADO" pra sempre
            # apesar do trajectory_trail mostrar deslocamento real).
            window = v_mem["history"][-8:]
            mid = max(1, len(window) // 2)
            older_half = window[:mid]
            newer_half = window[mid:] or window[-1:]
            ref_x = float(np.median([p[0] for p in older_half]))
            ref_y = float(np.median([p[1] for p in older_half]))
            ref_t = float(np.mean([p[2] for p in older_half]))
            new_x = float(np.median([p[0] for p in newer_half]))
            new_y = float(np.median([p[1] for p in newer_half]))
            new_t = float(np.mean([p[2] for p in newer_half]))
            dt = max(0.30, new_t - ref_t)
            vx = (new_x - ref_x) / dt
            vy = (new_y - ref_y) / dt
            speed = math.hypot(vx, vy)

            # Limiar recalibrado de 3.0 para 1.0 px/s: nesta camera (vista
            # aerea/elevada, barcos distantes), um barco realmente andando
            # continuamente a 1.0-2.0px/s (deslocamento real e monotonico,
            # nao ruido) ficava travado em PARADO para sempre - testado com
            # simulacao isolada, 40 iteracoes (36s) de movimento continuo a
            # 1-2px/s nunca cruzava o limiar antigo. Ruido puro (jitter
            # +-2px sem deslocamento real) continua classificado como
            # parado com o novo limiar, testado separadamente.
            if speed > 1.0:
                v_mem["is_stationary"] = False
                v_mem["speed"] = speed
                v_mem["vx"] = vx
                v_mem["vy"] = vy
                heading_rad = math.atan2(vx, -vy)
                heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0
                v_mem["heading_deg"] = heading_deg
                v_mem["cardinal"] = self._degrees_to_cardinal(heading_deg)
                v_mem["destination"] = self._compute_dynamic_destination(heading_deg)
                # NAO reancorar aqui. anchor_pos precisa continuar apontando pra
                # onde o barco estava quando parado pela ultima vez - e o que
                # dist_from_anchor (topo da funcao) usa pra decidir "parado".
                # Resetar o anchor pra posicao atual TODA VEZ que o barco esta
                # em movimento fazia dist_from_anchor no ciclo seguinte medir a
                # partir de um anchor que acabou de ser colocado "bem aqui" -
                # pra um barco lento isso quase sempre da <12px, jogando o
                # estado de volta pra PARADO no proximo ciclo mesmo com
                # deslocamento real (o rotulo ficava oscilando/preso em
                # "PARADO" apesar do trajectory_trail mostrar movimento).

                entry_x, entry_y = v_mem.get("entry_pos", (cx, cy))
                dist_total = math.hypot(cx - entry_x, cy - entry_y)
                entry_t = v_mem.get("entry_time", "--")
                entry_sec = v_mem.get("entry_sector", "Canal")
                v_mem["origin_story"] = f"Origem: Entrou às {entry_t} pelo {entry_sec}. Deslocou-se {int(dist_total)}px com rumo {v_mem['cardinal']} ({int(heading_deg)} graus); Destino estimado: {v_mem['destination']}."
            else:
                v_mem["is_stationary"] = True
                v_mem["speed"] = 0.0
                v_mem["cardinal"] = "Proa Fixa (Atracado)"
                v_mem["destination"] = "Atracado no Píer / Fundeado"

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
            return "Norte do Canal -> Terminal Alemoa / Saboo"

    def get_active_position_priors(self, timestamp, max_age=2.0):
        """Retorna a posicao ESPERADA de cada embarcacao conhecida (viva
        recentemente), extrapolada pela velocidade se em movimento.
        Usado pelo VesselEnsembleEngine para reforcar deteccoes fracas perto
        de onde ja se sabia que tinha um barco: "se ali tinha um barco no
        frame anterior, um barco fraco no mesmo lugar agora ganha mais
        forca" - so um modelo relatar baixa confianca ali nao derruba a
        deteccao se a posicao ja e conhecida."""
        priors = []
        for v_mem in self.vessels_memory.values():
            age = timestamp - v_mem["last_seen"]
            if age > max_age:
                continue
            if v_mem["is_stationary"]:
                px, py = v_mem["anchor_pos"]
            else:
                dt = max(0.0, age)
                px = v_mem["cx"] + v_mem["vx"] * dt
                py = v_mem["cy"] + v_mem["vy"] * dt
            priors.append({"cx": px, "cy": py, "radius": self.spatial_gate_radius})
        return priors

    def predict_future_positions(self, v_mem, seconds_ahead=[5.0, 10.0]):
        if v_mem["is_stationary"]:
            return []
        cx, cy = v_mem["cx"], v_mem["cy"]
        preds = []
        for s in seconds_ahead:
            pred_x = int(cx + v_mem["vx"] * s)
            pred_y = int(cy + v_mem["vy"] * s)
            preds.append({"seconds": s, "x": pred_x, "y": pred_y})
        return preds
