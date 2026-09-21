from __future__ import annotations

from typing import Iterator

from mmdistance.cluster import cluster_detections
from mmdistance.config import AppConfig
from mmdistance.filters import apply_spatial_filter
from mmdistance.models import FrameResult, RadarFrame
from mmdistance.tracker import FrontTargetTracker


class Pipeline:
    def __init__(self, cfg: AppConfig | None = None, tracker: FrontTargetTracker | None = None):
        self.cfg = cfg or AppConfig()
        self.tracker = tracker or FrontTargetTracker(self.cfg.tracker, self.cfg.ego)

    def process(self, frame: RadarFrame, dt: float | None = None) -> FrameResult:
        filtered, stats = apply_spatial_filter(frame.detections, self.cfg.filter)
        clusters = cluster_detections(filtered, self.cfg.cluster)
        tracks = self.tracker.update(clusters, dt)
        primary = self.tracker.select_primary(tracks)
        return FrameResult(
            frame_number=frame.frame_number,
            raw=frame.detections,
            filtered=filtered,
            clusters=clusters,
            tracks=tracks,
            primary=primary,
            filter_stats=stats,
            dt=dt or self.cfg.tracker.default_dt,
        )


def run_frames(
    frames: Iterator[RadarFrame],
    cfg: AppConfig | None = None,
    dt: float | None = None,
) -> Iterator[FrameResult]:
    pipe = Pipeline(cfg)
    for frame in frames:
        yield pipe.process(frame, dt)
