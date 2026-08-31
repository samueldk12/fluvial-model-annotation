import math
import numpy as np

class StateAnchorManager:
    def __init__(self, initial_metric_pos=(0.0, 0.0), initial_img_pos=(0.0, 0.0), min_nav_dwell_s=3.0, min_stat_dwell_s=4.0):
        self.anchor_metric_pos = list(initial_metric_pos)
        self.anchor_img_pos = list(initial_img_pos)
        self.current_state = 'STATIONARY'
        self.min_nav_dwell_s = float(min_nav_dwell_s)
        self.min_stat_dwell_s = float(min_stat_dwell_s)
        self.state_since_timestamp = None
        self.candidate_state = None
        self.candidate_since_timestamp = None
        self.candidate_start_pos = None

    def update_state(self, current_metric_pos, speed_knots, timestamp, current_img_pos=None):
        if self.state_since_timestamp is None:
            self.state_since_timestamp = timestamp
            self.anchor_metric_pos = list(current_metric_pos)
            if current_img_pos is not None:
                self.anchor_img_pos = list(current_img_pos)

        cur_x, cur_y = current_metric_pos
        dist_from_anchor = math.hypot(cur_x - self.anchor_metric_pos[0], cur_y - self.anchor_metric_pos[1])

        instantaneous_state = self.current_state
        if self.current_state == 'STATIONARY':
            if dist_from_anchor > 15.0 and speed_knots >= 1.50:
                instantaneous_state = 'NAVIGATING'
            else:
                instantaneous_state = 'STATIONARY'
        elif self.current_state == 'NAVIGATING':
            if speed_knots < 0.50:
                instantaneous_state = 'STATIONARY'
            else:
                instantaneous_state = 'NAVIGATING'

        is_changed = False
        if instantaneous_state != self.current_state:
            if self.candidate_state != instantaneous_state:
                self.candidate_state = instantaneous_state
                self.candidate_since_timestamp = timestamp
                self.candidate_start_pos = (cur_x, cur_y)
            else:
                dwell_target = self.min_nav_dwell_s if instantaneous_state == 'NAVIGATING' else self.min_stat_dwell_s
                cand_dist = math.hypot(cur_x - self.candidate_start_pos[0], cur_y - self.candidate_start_pos[1])

                dist_ok = True
                if instantaneous_state == 'STATIONARY' and cand_dist > 8.0:
                    dist_ok = False

                if (timestamp - self.candidate_since_timestamp) >= dwell_target and dist_ok:
                    self.current_state = instantaneous_state
                    self.state_since_timestamp = timestamp
                    self.candidate_state = None
                    self.candidate_since_timestamp = None
                    self.candidate_start_pos = None
                    is_changed = True
                    if self.current_state == 'STATIONARY':
                        self.anchor_metric_pos = list(current_metric_pos)
                        if current_img_pos is not None:
                            self.anchor_img_pos = list(current_img_pos)
        else:
            self.candidate_state = None
            self.candidate_since_timestamp = None
            self.candidate_start_pos = None

        time_in_state = timestamp - self.state_since_timestamp
        return self.current_state, is_changed, self.anchor_metric_pos, time_in_state
