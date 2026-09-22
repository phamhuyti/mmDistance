from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Optional


@dataclass(frozen=True)
class Detection:
    """One point after the adapter layer. Axes follow TI OOB: +X right, +Y forward, +Z up."""

    x: float
    y: float
    z: float
    vr: float
    snr_db: Optional[float] = None
    noise_db: Optional[float] = None

    @property
    def range_m(self) -> float:
        return math.hypot(self.x, self.y, self.z)

    @property
    def azimuth_deg(self) -> float:
        return math.degrees(math.atan2(self.x, self.y))

    @property
    def elevation_deg(self) -> float:
        return math.degrees(math.atan2(self.z, math.hypot(self.x, self.y)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z": round(self.z, 3),
            "vr": round(self.vr, 3),
            "range_m": round(self.range_m, 3),
            "azimuth_deg": round(self.azimuth_deg, 2),
            "elevation_deg": round(self.elevation_deg, 2),
            "snr_db": None if self.snr_db is None else round(self.snr_db, 2),
        }


@dataclass
class RadarFrame:
    frame_number: int
    detections: list[Detection]
    platform: int = 0
    version: int = 0
    num_tlvs: int = 0
    subframe: int = 0
    cpu_cycles: int = 0
    captured_at: Optional[float] = None


@dataclass
class Cluster:
    x: float
    y: float
    z: float
    vr: float
    snr_db: float
    n_points: int
    detections: list[Detection] = field(default_factory=list)

    @property
    def range_m(self) -> float:
        return math.hypot(self.x, self.y, self.z)

    @property
    def azimuth_deg(self) -> float:
        return math.degrees(math.atan2(self.x, self.y))

    def as_dict(self) -> dict[str, Any]:
        return {
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z": round(self.z, 3),
            "vr": round(self.vr, 3),
            "range_m": round(self.range_m, 3),
            "azimuth_deg": round(self.azimuth_deg, 2),
            "snr_db": round(self.snr_db, 2),
            "n_points": self.n_points,
        }


@dataclass
class Track:
    track_id: int
    x: float
    y: float
    z: float
    range_m: float
    vr: float
    snr_db: float
    hits: int = 1
    misses: int = 0
    age: int = 1
    confirmed: bool = False
    static: bool = False

    @property
    def azimuth_deg(self) -> float:
        return math.degrees(math.atan2(self.x, self.y))

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "id": self.track_id,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z": round(self.z, 3),
            "range_m": round(self.range_m, 3),
            "vr": round(self.vr, 3),
            "azimuth_deg": round(self.azimuth_deg, 2),
            "snr_db": round(self.snr_db, 2),
            "hits": self.hits,
            "misses": self.misses,
            "age": self.age,
            "confirmed": self.confirmed,
            "static": self.static,
        }


@dataclass
class FilterStats:
    n_in: int = 0
    n_out: int = 0
    dropped_range: int = 0
    dropped_azimuth: int = 0
    dropped_elevation: int = 0
    dropped_snr: int = 0
    dropped_behind: int = 0


@dataclass
class FrameResult:
    frame_number: int
    raw: list[Detection]
    filtered: list[Detection]
    clusters: list[Cluster]
    tracks: list[Track]
    primary: Optional[Track]
    filter_stats: FilterStats
    dt: float
    alert: Optional[Any] = None
    health: Optional[Any] = None
    captured_at: Optional[float] = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "frame": self.frame_number,
            "dt": round(self.dt, 4),
            "n_raw": len(self.raw),
            "n_filtered": len(self.filtered),
            "n_clusters": len(self.clusters),
            "n_tracks": len(self.tracks),
            "primary": None if self.primary is None else self.primary.as_dict(),
            "tracks": [track.as_dict() for track in self.tracks],
            "clusters": [cluster.as_dict() for cluster in self.clusters],
            "filter": self.filter_stats.__dict__,
            "alert": None if self.alert is None else self.alert.as_dict(),
            "health": None if self.health is None else self.health.as_dict(),
        }
        return payload
