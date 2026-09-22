from __future__ import annotations

import time
from typing import Iterator

from mmdistance.alerts import evaluate_alert
from mmdistance.cluster import cluster_detections
from mmdistance.config import AppConfig, read_ego_speed
from mmdistance.filters import apply_spatial_filter
from mmdistance.geometry import transform_detections
from mmdistance.health import HealthMonitor
from mmdistance.models import FrameResult, RadarFrame
from mmdistance.tracker import FrontTargetTracker


class Pipeline:
    def __init__(self, cfg: AppConfig | None = None, tracker: FrontTargetTracker | None = None):
        self.cfg = cfg or AppConfig()
        self.tracker = tracker or FrontTargetTracker(self.cfg.tracker, self.cfg.ego)
        self.health = HealthMonitor(stale_after_s=self.cfg.radar.stale_after_s)
        self._last_t: float | None = None

    def process(self, frame: RadarFrame, dt: float | None = None) -> FrameResult:
        now = frame.captured_at if frame.captured_at is not None else time.monotonic()
        if dt is None or dt <= 0:
            if self._last_t is None:
                dt = self.cfg.tracker.default_dt
            else:
                dt = max(now - self._last_t, 1e-3)
        self._last_t = now

        speed = read_ego_speed(self.cfg.ego)
        self.tracker.ego.speed_mps = speed

        world = transform_detections(frame.detections, self.cfg.mount)
        filtered, stats = apply_spatial_filter(world, self.cfg.filter)
        clusters = cluster_detections(filtered, self.cfg.cluster)
        tracks = self.tracker.update(clusters, dt)
        primary = self.tracker.select_primary(tracks)
        return FrameResult(
            frame_number=frame.frame_number,
            raw=world,
            filtered=filtered,
            clusters=clusters,
            tracks=tracks,
            primary=primary,
            filter_stats=stats,
            dt=dt,
            alert=evaluate_alert(primary, self.cfg.alert),
            health=self.health.tick(now),
            captured_at=frame.captured_at,
        )


def run_frames(
    frames: Iterator[RadarFrame],
    cfg: AppConfig | None = None,
    dt: float | None = None,
) -> Iterator[FrameResult]:
    pipe = Pipeline(cfg)
    for frame in frames:
        yield pipe.process(frame, dt)
