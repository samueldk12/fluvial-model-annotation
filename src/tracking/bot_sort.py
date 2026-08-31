import math
import time
import numpy as np

from src.geometry.camera_calibration import CameraGeometryConfig
from src.geometry.metric_conversions import MetricUnitConverter, NauticalThresholds
from src.tracking.state_anchor_manager import StateAnchorManager

class STrack:
    def __init__(self, bbox, score, label='Embarcacao', embedding=None, camera_geometry=None):
        self.bbox = list(bbox)
        self.score = float(score)
        self.label = label
        self.embedding = np.array(embedding, dtype=np.float32) if embedding is not None else None
        self.camera_geometry = camera_geometry

        self.track_id = None
        self.state = 'New'
        self.is_activated = False
        self.frame_id = 0
        self.tracklet_len = 0
        self.hits = 1
        self.missing_time = 0.0
        self.last_seen = time.time()

        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        bw = max(1.0, bbox[2] - bbox[0])
        bh = max(1.0, bbox[3] - bbox[1])

        self.mean = np.array([cx, cy, bw, bh, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        self.covariance = np.diag([10.0, 10.0, 10.0, 10.0, 100.0, 100.0, 100.0, 100.0])

        metric_pos = [0.0, 0.0]
        if self.camera_geometry is not None:
            try:
                water_pts = self.camera_geometry.homography.image_to_water(np.array([[cx, cy]]))
                metric_pos = water_pts[0].tolist()
            except Exception:
                pass

        self.anchor_manager = StateAnchorManager(initial_metric_pos=metric_pos, initial_img_pos=(cx, cy))
        self.history = [(cx, cy, self.last_seen)]
        self.trajectory_trail = []
        self.entry_pos = (int(round(cx)), int(round(cy)))
        self.entry_time = time.strftime('%H:%M:%S')
        self.entry_sector = 'Canal de Acesso'
        self.origin_story = f'Entrou no canal às {self.entry_time}.'
        self.speed_knots = None
        self.speed_mps = None
        self.speed_px_s = 0.0
        self.heading_deg = 0.0
        self.cardinal = 'N/D'
        self.destination = 'N/D'
        self.metric_dimensions = None
        self.is_metric_calibrated = self.camera_geometry is not None

    def predict(self, dt=1.0):
        dt_val = max(0.033, min(2.0, float(dt)))
        F = np.eye(8, dtype=np.float64)
        F[0, 4] = dt_val
        F[1, 5] = dt_val
        F[2, 6] = dt_val
        F[3, 7] = dt_val

        Q = np.diag([1.0, 1.0, 1.0, 1.0, 4.0, 4.0, 4.0, 4.0]) * dt_val
        self.mean = F @ self.mean
        self.covariance = F @ self.covariance @ F.T + Q

        cx, cy, bw, bh = self.mean[:4]
        self.bbox = [cx - bw / 2.0, cy - bh / 2.0, cx + bw / 2.0, cy + bh / 2.0]

    def update(self, new_track, frame_id, timestamp=None):
        t = timestamp or time.time()
        self.frame_id = frame_id
        self.tracklet_len += 1
        self.hits += 1
        self.missing_time = 0.0
        self.last_seen = t
        self.score = new_track.score
        self.label = new_track.label

        new_box = new_track.bbox
        new_cx = (new_box[0] + new_box[2]) / 2.0
        new_cy = (new_box[1] + new_box[3]) / 2.0
        new_bw = max(1.0, new_box[2] - new_box[0])
        new_bh = max(1.0, new_box[3] - new_box[1])

        z = np.array([new_cx, new_cy, new_bw, new_bh], dtype=np.float64)
        H = np.zeros((4, 8), dtype=np.float64)
        H[0, 0] = 1.0
        H[1, 1] = 1.0
        H[2, 2] = 1.0
        H[3, 3] = 1.0
        R = np.diag([4.0, 4.0, 4.0, 4.0])

        y = z - H @ self.mean
        S = H @ self.covariance @ H.T + R
        K = self.covariance @ H.T @ np.linalg.inv(S)
        self.mean = self.mean + K @ y
        self.covariance = (np.eye(8) - K @ H) @ self.covariance

        cx, cy, bw, bh = self.mean[:4]
        self.bbox = [cx - bw / 2.0, cy - bh / 2.0, cx + bw / 2.0, cy + bh / 2.0]

        if new_track.embedding is not None:
            if self.embedding is None:
                self.embedding = new_track.embedding
            else:
                alpha = 0.85
                self.embedding = alpha * self.embedding + (1.0 - alpha) * new_track.embedding
                norm = np.linalg.norm(self.embedding)
                if norm > 1e-6:
                    self.embedding = self.embedding / norm

        self.history.append((cx, cy, t))
        if len(self.history) > 30:
            self.history.pop(0)

        self._update_trail_and_kinematics(cx, cy, t)
        self.state = 'Tracked'
        self.is_activated = True

    def _update_trail_and_kinematics(self, cx, cy, t):
        if len(self.trajectory_trail) == 0 or math.hypot(cx - self.trajectory_trail[-1]['x'], cy - self.trajectory_trail[-1]['y']) > 5.0:
            self.trajectory_trail.append({
                'x': int(round(cx)),
                'y': int(round(cy)),
                'time': time.strftime('%H:%M:%S', time.localtime(t))
            })
            if len(self.trajectory_trail) > 80:
                self.trajectory_trail.pop(0)

        metric_pos = [0.0, 0.0]
        if self.camera_geometry is not None:
            try:
                water_pts = self.camera_geometry.homography.image_to_water(np.array([[cx, cy]]))
                metric_pos = water_pts[0].tolist()
                self.metric_dimensions = self.camera_geometry.homography.box_to_metric_dimensions(self.bbox)
            except Exception:
                pass

        if len(self.history) >= 2:
            window = self.history[-6:]
            ref_x, ref_y, ref_t = window[0]
            dt = max(0.10, t - ref_t)
            vx = (cx - ref_x) / dt
            vy = (cy - ref_y) / dt
            self.speed_px_s = math.hypot(vx, vy)
            heading_rad = math.atan2(vx, -vy)
            self.heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0
            self.cardinal = MetricUnitConverter.degrees_to_cardinal(self.heading_deg)

            # So reporta velocidade/dimensoes em unidades fisicas reais (nos, metros) se
            # existir uma calibracao de camera de verdade (homografia com pontos de controle
            # medidos na cena real). Sem isso, inventar "0.5 m/px" seria fabricar precisao
            # que nao existe - por isso speed_knots fica None e so o px/s (real, honesto) e exposto.
            if self.camera_geometry is not None:
                try:
                    w_pts = self.camera_geometry.homography.image_to_water(np.array([[ref_x, ref_y], [cx, cy]]))
                    vel = MetricUnitConverter.compute_velocity_and_course(w_pts[0], w_pts[1], dt)
                    self.speed_knots = vel['speed_knots']
                    self.speed_mps = vel['speed_mps']
                except Exception:
                    self.speed_knots = None
                    self.speed_mps = None

        # Limiar em px/s (nao calibrado): mesma logica de "ainda em movimento" usada e
        # validada no VesselSpatialMemoryTracker nesta sessao, so que sem fingir nos reais.
        is_moving = self.speed_px_s > 1.0
        state_str = 'STATIONARY' if not is_moving else 'NAVIGATING'
        if self.is_metric_calibrated:
            metric_speed_for_anchor = self.speed_knots if self.speed_knots is not None else 0.0
            state_str, changed, anc_pos, dwell_s = self.anchor_manager.update_state(metric_pos, metric_speed_for_anchor, t, (cx, cy))
            is_moving = (state_str != 'STATIONARY')

        if not is_moving:
            self.speed_knots = None
            self.speed_mps = None
            self.speed_px_s = 0.0
            self.cardinal = 'Proa Fixa (Atracado)'
            self.destination = 'Atracado no Píer / Fundeado'
            self.origin_story = f'Entrou às {self.entry_time}. Fundeado/atracado em posição fixa.'
        else:
            self.destination = f'Deslocando-se para {self.cardinal}'
            if self.speed_knots is not None:
                self.origin_story = f'Entrou às {self.entry_time}. Velocidade: {self.speed_knots:.1f} nós rumo {self.cardinal} ({int(self.heading_deg)}°).'
            else:
                self.origin_story = f'Entrou às {self.entry_time}. Rumo {self.cardinal} ({int(self.heading_deg)}°). Velocidade real indisponível (câmera não calibrada).'


class BoTSORTTracker:
    """Rastreador Kalman + custo IoU/aparencia. Por padrao roda em modo NAO calibrado
    (camera_geometry=None): velocidade/destino ficam so em px/s e rumo (graus), honestos.
    So passe uma CameraGeometryConfig real (com pontos de controle medidos na cena) se
    quiser velocidade/dimensoes em unidades fisicas (nos/metros) - sem isso seria fabricar
    precisao que a camera atual nao tem calibracao para sustentar."""
    def __init__(self, track_high_thresh=0.40, track_low_thresh=0.15, new_track_thresh=0.50, match_thresh=0.70, camera_geometry=None):
        self.track_high_thresh = float(track_high_thresh)
        self.track_low_thresh = float(track_low_thresh)
        self.new_track_thresh = float(new_track_thresh)
        self.match_thresh = float(match_thresh)
        self.camera_geometry = camera_geometry

        self.tracked_stracks = []
        self.lost_stracks = []
        self.removed_stracks = []
        self.frame_id = 0
        self.next_id = 1
        self.max_time_lost = 30

    @staticmethod
    def _compute_iou_matrix(boxes1, boxes2):
        if len(boxes1) == 0 or len(boxes2) == 0:
            return np.zeros((len(boxes1), len(boxes2)), dtype=np.float64)

        b1 = np.array(boxes1, dtype=np.float64)
        b2 = np.array(boxes2, dtype=np.float64)

        x1 = np.maximum(b1[:, None, 0], b2[None, :, 0])
        y1 = np.maximum(b1[:, None, 1], b2[None, :, 1])
        x2 = np.minimum(b1[:, None, 2], b2[None, :, 2])
        y2 = np.minimum(b1[:, None, 3], b2[None, :, 3])

        inter = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
        area1 = np.maximum(1.0, (b1[:, 2] - b1[:, 0]) * (b1[:, 3] - b1[:, 1]))
        area2 = np.maximum(1.0, (b2[:, 2] - b2[:, 0]) * (b2[:, 3] - b2[:, 1]))
        union = area1[:, None] + area2[None, :] - inter
        return inter / np.maximum(1.0, union)

    @staticmethod
    def _compute_appearance_matrix(stracks, detections):
        if len(stracks) == 0 or len(detections) == 0:
            return np.ones((len(stracks), len(detections)), dtype=np.float64)

        dist_matrix = np.ones((len(stracks), len(detections)), dtype=np.float64)
        for i, st in enumerate(stracks):
            if st.embedding is None:
                continue
            for j, det in enumerate(detections):
                if det.embedding is None:
                    continue
                cos_sim = float(np.dot(st.embedding, det.embedding) / (np.linalg.norm(st.embedding) * np.linalg.norm(det.embedding) + 1e-7))
                dist_matrix[i, j] = 1.0 - max(0.0, cos_sim)
        return dist_matrix

    def update(self, detections_list, timestamp=None):
        self.frame_id += 1
        t = timestamp or time.time()

        det_stracks = []
        for d in detections_list:
            box = d.get('box', d.get('bbox', [0, 0, 0, 0]))
            score = float(d.get('conf', d.get('score', 0.0)))
            lbl = d.get('label', 'Embarcacao')
            emb = d.get('embedding', None)
            st = STrack(box, score, label=lbl, embedding=emb, camera_geometry=self.camera_geometry)
            det_stracks.append(st)

        high_dets = [d for d in det_stracks if d.score >= self.track_high_thresh]
        low_dets = [d for d in det_stracks if self.track_low_thresh <= d.score < self.track_high_thresh]

        unconfirmed = []
        tracked_pool = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_pool.append(track)

        strack_pool = tracked_pool + self.lost_stracks
        for track in strack_pool:
            track.predict()

        iou_matrix = self._compute_iou_matrix([st.bbox for st in strack_pool], [d.bbox for d in high_dets])
        app_matrix = self._compute_appearance_matrix(strack_pool, high_dets)
        cost_matrix = 0.60 * (1.0 - iou_matrix) + 0.40 * app_matrix

        matched_tracks = []
        matched_dets = []
        if len(strack_pool) > 0 and len(high_dets) > 0:
            pairs = []
            for i in range(len(strack_pool)):
                for j in range(len(high_dets)):
                    if iou_matrix[i, j] > 0.20 or app_matrix[i, j] < 0.35:
                        pairs.append((cost_matrix[i, j], i, j))
            pairs.sort(key=lambda x: x[0])

            used_t = set()
            used_d = set()
            for cost, i, j in pairs:
                if i not in used_t and j not in used_d and cost <= self.match_thresh:
                    used_t.add(i)
                    used_d.add(j)
                    matched_tracks.append(strack_pool[i])
                    matched_dets.append(high_dets[j])

        for st, dt in zip(matched_tracks, matched_dets):
            st.update(dt, self.frame_id, t)

        unmatched_stracks = [st for st in strack_pool if st not in matched_tracks]
        unmatched_high_dets = [d for d in high_dets if d not in matched_dets]

        if len(unmatched_stracks) > 0 and len(low_dets) > 0:
            low_iou_matrix = self._compute_iou_matrix([st.bbox for st in unmatched_stracks], [d.bbox for d in low_dets])
            for i in range(len(unmatched_stracks)):
                best_j = -1
                best_iou = 0.30
                for j in range(len(low_dets)):
                    if low_iou_matrix[i, j] > best_iou:
                        best_iou = low_iou_matrix[i, j]
                        best_j = j
                if best_j >= 0:
                    unmatched_stracks[i].update(low_dets[best_j], self.frame_id, t)
                    unmatched_stracks.pop(i)
                    break

        new_tracks = []
        for d in unmatched_high_dets:
            if d.score >= self.new_track_thresh:
                d.track_id = f'STS-BOT-{self.next_id:02d}'
                self.next_id += 1
                d.state = 'Tracked'
                d.is_activated = True
                new_tracks.append(d)

        for st in unmatched_stracks:
            if st.state != 'Lost':
                st.state = 'Lost'
                self.lost_stracks.append(st)

        self.tracked_stracks = [st for st in self.tracked_stracks if st.state == 'Tracked'] + new_tracks
        self.lost_stracks = [st for st in self.lost_stracks if st.state == 'Lost' and (self.frame_id - st.frame_id) < self.max_time_lost]

        active_output = []
        for st in self.tracked_stracks:
            if st.is_activated and st.hits >= 2:
                active_output.append({
                    'track_id': st.track_id,
                    'bbox': st.bbox,
                    'score': st.score,
                    'label': st.label,
                    'speed_knots': round(st.speed_knots, 2) if st.speed_knots is not None else None,
                    'speed_mps': round(st.speed_mps, 2) if st.speed_mps is not None else None,
                    'speed_px_s': round(st.speed_px_s, 1),
                    'heading_deg': round(st.heading_deg, 1),
                    'cardinal': st.cardinal,
                    'destination': st.destination,
                    'origin_story': st.origin_story,
                    'trajectory_trail': st.trajectory_trail,
                    'metric_dimensions': st.metric_dimensions,
                    'is_metric_calibrated': st.is_metric_calibrated,
                    'is_stationary': st.speed_px_s <= 1.0,
                    'hits': st.hits
                })

        return active_output
