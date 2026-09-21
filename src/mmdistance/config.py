from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
import tomllib
from typing import Any


@dataclass
class RadarPorts:
    cli_port: str = "/dev/radar-cli"
    data_port: str = "/dev/radar-data"
    cli_baud: int = 115200
    data_baud: int = 921600
    cfg_path: str = "configs/profile.cfg.example"
    cfg_line_timeout_s: float = 0.4


@dataclass
class FilterConfig:
    range_min_m: float = 1.0
    range_max_m: float = 40.0
    azimuth_max_deg: float = 12.0
    elevation_min_deg: float = -6.0
    elevation_max_deg: float = 8.0
    snr_min_db: float = 8.0
    require_in_front: bool = True


@dataclass
class ClusterConfig:
    eps_m: float = 1.5
    min_points: int = 1


@dataclass
class TrackerConfig:
    gate_m: float = 2.5
    max_misses: int = 5
    min_hits: int = 3
    process_var_range: float = 1.0
    process_var_vr: float = 2.0
    meas_var_range: float = 0.25
    meas_var_vr: float = 0.5
    default_dt: float = 0.05


@dataclass
class EgoConfig:
    speed_mps: float = 0.0
    static_vr_tol_mps: float = 0.8


@dataclass
class OutputConfig:
    csv_path: str = ""
    jsonl_path: str = ""
    print_primary: bool = True


@dataclass
class AppConfig:
    radar: RadarPorts = field(default_factory=RadarPorts)
    filter: FilterConfig = field(default_factory=FilterConfig)
    cluster: ClusterConfig = field(default_factory=ClusterConfig)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    ego: EgoConfig = field(default_factory=EgoConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def load(cls, path: str | Path | None) -> AppConfig:
        cfg = cls()
        if path is None:
            return cfg
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            radar=_fill(RadarPorts, data.get("radar", {})),
            filter=_fill(FilterConfig, data.get("filter", {})),
            cluster=_fill(ClusterConfig, data.get("cluster", {})),
            tracker=_fill(TrackerConfig, data.get("tracker", {})),
            ego=_fill(EgoConfig, data.get("ego", {})),
            output=_fill(OutputConfig, data.get("output", {})),
        )


def _fill(cls: type, raw: dict[str, Any]):
    allowed = {item.name for item in fields(cls)}
    return cls(**{key: value for key, value in raw.items() if key in allowed})
