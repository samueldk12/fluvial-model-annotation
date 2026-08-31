import math
import numpy as np

class MetricUnitConverter:
    MPS_TO_KNOTS = 1.943844
    KNOTS_TO_MPS = 0.514444

    @classmethod
    def mps_to_knots(cls, speed_mps):
        return float(speed_mps * cls.MPS_TO_KNOTS)

    @classmethod
    def knots_to_mps(cls, speed_knots):
        return float(speed_knots * cls.KNOTS_TO_MPS)

    @classmethod
    def compute_velocity_and_course(cls, pos1_m, pos2_m, dt_s):
        dt = max(0.01, float(dt_s))
        dx = float(pos2_m[0] - pos1_m[0])
        dy = float(pos2_m[1] - pos1_m[1])
        dist_m = math.hypot(dx, dy)
        speed_mps = dist_m / dt
        speed_knots = cls.mps_to_knots(speed_mps)

        heading_rad = math.atan2(dx, dy)
        heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0
        cardinal = cls.degrees_to_cardinal(heading_deg)

        return {
            'dx_m': dx,
            'dy_m': dy,
            'distance_m': dist_m,
            'speed_mps': float(speed_mps),
            'speed_knots': float(speed_knots),
            'heading_deg': float(heading_deg),
            'cardinal': cardinal
        }

    @staticmethod
    def degrees_to_cardinal(deg):
        directions = [
            'Norte (N)', 'Norte-Nordeste (NNE)', 'Nordeste (NE)', 'Leste-Nordeste (ENE)',
            'Leste (E)', 'Leste-Sudeste (ESE)', 'Sudeste (SE)', 'Sul-Sudeste (SSE)',
            'Sul (S)', 'Sul-Sudoeste (SSW)', 'Sudoeste (SW)', 'Oeste-Sudoeste (WSW)',
            'Oeste (W)', 'Oeste-Noroeste (WNW)', 'Noroeste (NW)', 'Norte-Noroeste (NNW)'
        ]
        idx = int((deg + 11.25) / 22.5) % 16
        return directions[idx]


class NauticalThresholds:
    MIN_VESSEL_LENGTH_METERS = 8.0
    MAX_VESSEL_LENGTH_METERS = 420.0
    MIN_VESSEL_BEAM_METERS = 2.0
    MAX_VESSEL_BEAM_METERS = 70.0
    MIN_VESSEL_AREA_SQM = 16.0
    MAX_VESSEL_AREA_SQM = 28000.0

    STATIONARY_SPEED_KNOTS = 0.50
    NAVIGATING_SPEED_KNOTS = 1.50
    STATIONARY_ANCHOR_RADIUS_METERS = 10.0
    SPATIAL_GATE_RADIUS_METERS = 30.0

    @classmethod
    def is_plausible_vessel_metric(cls, length_m, width_m, area_sqm=None):
        if length_m < cls.MIN_VESSEL_LENGTH_METERS or length_m > cls.MAX_VESSEL_LENGTH_METERS:
            return False
        if width_m < cls.MIN_VESSEL_BEAM_METERS or width_m > cls.MAX_VESSEL_BEAM_METERS:
            return False
        if area_sqm is not None:
            if area_sqm < cls.MIN_VESSEL_AREA_SQM or area_sqm > cls.MAX_VESSEL_AREA_SQM:
                return False
        return True

    @classmethod
    def classify_navigation_state(cls, speed_knots, dist_from_anchor_m):
        if dist_from_anchor_m < cls.STATIONARY_ANCHOR_RADIUS_METERS and speed_knots < cls.NAVIGATING_SPEED_KNOTS:
            return 'STATIONARY'
        elif speed_knots >= cls.NAVIGATING_SPEED_KNOTS:
            return 'NAVIGATING'
        else:
            return 'MANEUVERING'
