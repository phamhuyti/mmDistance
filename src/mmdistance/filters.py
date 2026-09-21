from __future__ import annotations

import math

from mmdistance.config import EgoConfig, FilterConfig
from mmdistance.models import Detection, FilterStats


def is_static(detection: Detection, ego: EgoConfig) -> bool:
    """A point is likely ground/sign clutter if its radial speed matches ego motion."""
    expected_static_vr = -ego.speed_mps * math.cos(math.radians(detection.azimuth_deg))
    return abs(detection.vr - expected_static_vr) <= ego.static_vr_tol_mps


def apply_spatial_filter(
    detections: list[Detection],
    cfg: FilterConfig,
) -> tuple[list[Detection], FilterStats]:
    """Software lane / ground / SNR gate. This does not increase antenna gain."""
    stats = FilterStats(n_in=len(detections))
    kept: list[Detection] = []
    for det in detections:
        if cfg.require_in_front and det.y <= 0:
            stats.dropped_behind += 1
            continue
        if not (cfg.range_min_m <= det.range_m <= cfg.range_max_m):
            stats.dropped_range += 1
            continue
        if abs(det.azimuth_deg) > cfg.azimuth_max_deg:
            stats.dropped_azimuth += 1
            continue
        if not (cfg.elevation_min_deg <= det.elevation_deg <= cfg.elevation_max_deg):
            stats.dropped_elevation += 1
            continue
        if det.snr_db is not None and det.snr_db < cfg.snr_min_db:
            stats.dropped_snr += 1
            continue
        kept.append(det)
    stats.n_out = len(kept)
    return kept, stats
