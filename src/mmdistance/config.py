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
    wait_port_s: float = 20.0
    stale_after_s: float = 2.0


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
    speed_file: str = ""


@dataclass
class MountConfig:
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    height_m: float = 0.4

    def is_identity(self) -> bool:
        return self.yaw_deg == 0.0 and self.pitch_deg == 0.0 and self.roll_deg == 0.0


@dataclass
class AlertConfig:
    enabled: bool = True
    warn_range_m: float = 12.0
    danger_range_m: float = 6.0
    gpio_warn_pin: int = 0
    gpio_danger_pin: int = 0


@dataclass
class OutputConfig:
    csv_path: str = ""
    jsonl_path: str = ""
    sqlite_path: str = ""
    print_primary: bool = True


@dataclass
class AppConfig:
    radar: RadarPorts = field(default_factory=RadarPorts)
    filter: FilterConfig = field(default_factory=FilterConfig)
    cluster: ClusterConfig = field(default_factory=ClusterConfig)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    ego: EgoConfig = field(default_factory=EgoConfig)
    mount: MountConfig = field(default_factory=MountConfig)
    alert: AlertConfig = field(default_factory=AlertConfig)
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
            mount=_fill(MountConfig, data.get("mount", {})),
            alert=_fill(AlertConfig, data.get("alert", {})),
            output=_fill(OutputConfig, data.get("output", {})),
        )

    def warnings(self) -> list[str]:
        notes: list[str] = []
        if self.radar.cfg_path.endswith(".example"):
            notes.append(
                f"cfg_path đang trỏ file mẫu ({self.radar.cfg_path}); "
                "copy sang configs/profile.cfg và dán chirp từ Sensing Estimator."
            )
        if self.alert.danger_range_m >= self.alert.warn_range_m:
            notes.append("alert.danger_range_m nên nhỏ hơn warn_range_m.")
        if self.filter.range_min_m >= self.filter.range_max_m:
            notes.append("filter.range_min_m phải nhỏ hơn range_max_m.")
        return notes


def _fill(cls: type, raw: dict[str, Any]):
    allowed = {item.name for item in fields(cls)}
    return cls(**{key: value for key, value in raw.items() if key in allowed})


def read_ego_speed(ego: EgoConfig) -> float:
    if not ego.speed_file:
        return ego.speed_mps
    path = Path(ego.speed_file)
    if not path.is_file():
        return ego.speed_mps
    try:
        return float(path.read_text(encoding="utf-8").strip().split()[0])
    except (ValueError, IndexError, OSError):
        return ego.speed_mps
