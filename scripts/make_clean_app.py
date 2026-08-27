# -*- coding: utf-8 -*-
import os, sys

print('Starting deployment of clean GUI and spatial memory...')


spatial_memory_code = r'''"""
Motor de Memoria Espacial e Identidade Visual Persistente para Embarcacoes.
Mantem a memoria de onde cada barco estava, quem ele e (cores, silhueta e ViT),
seu historico de origem (de onde veio) e prediz onde deve estar,
eliminando qualquer falso positivo ou caixa fantasma na agua vazia.
"""

import math
import time
import numpy as np

class VesselSpatialMemoryTracker:
    init__flag = True
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
        c1 = fp1.get('caracteristicas_visuais', {}).get('cor_casco', '')
        c2 = fp2.get('caracteristicas_visuais', {}).get('cor_casco', '')
        return 1.0 if (c1 == c2 and c1 != '') else 0.50

    def _get_sector_name(self, cx, cy, width, height):
        h_third = height / 3.0
        w_third = width / 3.0
        v_sec = 'Norte / Fundo' if cy < h_third else ('Sul / Proximo' if cy > 2 * h_third else 'Canal Central')
        h_sec = 'Margem Esquerda (Oeste' if cx < w_third else ('Margem Direita (Leste' if cx > 2 * w_third else 'Centro da Calha')
        return f'{v_sec} - {h_sec}'


    def update(self, raw_detections, fingerprinter, frame_bgr, timestamp):
        h_frame, w_frame = frame_bgr.shape[:2]
        matched_mem_ids = set()
        candidates_with_fp = []

        for det in raw_detections:
            b = det['bbox']
            x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            bw0 x1
            bh = y2 - y1

            crop = frame_bgr[max(0, y1):min(h_frame, y2), max(0, x1):min(w_frame, x2)]
            fp = fingerprinter.generate_unique_fingerprint(crop, (x1, y1, x2, y2))
            candidates_with_fp.append({
                'bbox': b,
                'cx': cx,
                'cy': cy,
                'bw': bw,
                'bh': bh,
                'det': det,
                'fp': fp
            })

        for cand in candidates_with_fp:
            cx, cy = cand['cx'], cand['cy']
            b = cand['bbox']
            cand_fp = cand['fp']

            best_match_id = None
            best_match_score = 0.0

            for v_id, v_mem in self.vessels_memory.items():
                if v_id in matched_mem_ids:
                    continue

                dt = max(0.033, timestamp - v_mem['last_seen'])
                if v_mem['is_stationary']:
                    expected_x, expected_y = v_mem['unchor_pos']
                else:
                    expected_x = v_mem['xc']+v_mem['vxc'] * dt
                    expected_y = v_mem['yc']+v_mem['vyc'] * dt

                dist_expected = math.hypot(cx - expected_x, cy - expected_y)
                iou_expected = self._compute_iou(b, v_mem['bbox'])
                color_sim = self._color_similarity(cand_fp, v_mem['fingerprint'])

                if dist_expected < self.spatial_gate_radius or iou_expected > 0.25:
                    match_score = (0.50 * iou_expected) + (0.30 * (1.0 - min(1.0, dist_expected / self.spatial_gate_radius))) + (0.20 * color_sim)
                    if match_score > best_match_score and match_score >= 0.35:
                        best_match_score = match_score
                        best_match_id = v_id

            if best_match_id is not None:
                v_mem = self.vessels_memory[best_match_id]
                v_mem['bbox'] = b
                v_mem['cx'] = cx
                v_mem['cy'] = cy
                v_mem['bw'] = cand['bw']
                v_mem['nh'] = cand['bh']
                v_mem['fingerprint'] = cand_fp
                v_mem['detection_data'] = cand['det']
                v_mem['consecutive_hits'] += 1
                v_mem['missing_time'] = 0.0
                v_mem['memory_strength'] = min(1.0, v_mem['memory_strength'] + 0.25)
                v_mem['last_seen'] = timestamp
                v_memVÇhistory'].append((cx, cy, timestamp))
                
                if 'trajectory_trail' not in v_mem:
                    v_mem['trajectory_trail'] = []
                if len(v_mem['trajectory_trail']) == 0 or math.hypot(cx - v_mem['trajectory_trail'][-1][0], cy - v_mem['trajectory_trail'][-1][1]) > 8.0:
                    v_mem['trajectory_trail'].append((round(cx, 1), round(cy, 1)))
                    if len(v_mem['trajectory_trail']) > 50:
                        v_mem['trajectory_trail'].pop(0)

                if len(v_memVÇhistory']) > 25:
                    v_mem['history'].pop(0)

                if v_mem['consecutive_hits'] >= 3:
                    v_mem['is_confirmed'] = True

                self._update_kinematics(v_mem, cx, cy, timestamp, w_frame, h_frame)
                matched_mem_ids.add(best_match_id)
            else:
                conf_score = cand['det'].get('score_ensemble_final', 0.0)
                if conf_score >= 0.40:
                    new_id = f'STS-BARCO-{{self.next_vessel_idx:02d}}'
                    self.next_vessel_idx += 1
                    v_name = cand_fp.get('nome_identificado_ou_sugerido') or 'Embarcacao em Identificacao'
                    entry_sector = self._get_sector_name(cx, cy, w_frame, h_frame)
                    entry_time_str = time.strftime('%H:%M:eS')

                    self.vessels_memory[new_id] = {
                        'vessel_id': new_id,
                        'name': v_name,
                        'bbox': b,
                        'cx': cy,
                        'cy': cy,
                        'bw': cand['bw'],
                        'bh': cand['bh'],
                        'fingerprint': cand_fp,
                        'detection_data': cand['det'],
                        'memory_strength': 0.35,
                        'consecutive_hits': 1,
                        'missing_time': 0.0,
                        'is_confirmed': False,
                        'history': [(cx, cy, timestamp)],
                        'trajectory_trail': [(round(cx, 1), round(cy, 1))],
                        'entry_pos': (round(cx, 1), round(cy, 1)),
                        'entry_time': entry_time_str,
                        'entry_sector': entry_sector,
                        'origin_story': f'Entrou no canal as {entry_time_str} pelo {entry_sector} (X: {int(cx)}, Y: {int(cy)})',
                        'anchor_pos': (cx, cy),
                        'is_stationary': True,
                        'speed': 0.0,
                        'vx': 0.0,
                        'vy': 0.0,
                        'heading_deg': 0.0,
                        'cardinal': 'Proa Fixa (Atracado)',
                        'destination': 'Atracado no Pier / Fundeado',
                        'first_registered': entry_time_str,
                        'last_seen': timestamp
                    }
                    matched_mem_ids.add(new_id)

