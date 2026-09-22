from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from mmdistance.config import AlertConfig
from mmdistance.models import Track


@dataclass(frozen=True)
class Alert:
    level: str
    message: str
    range_m: Optional[float] = None

    def as_dict(self) -> dict:
        return {"level": self.level, "message": self.message, "range_m": self.range_m}


def evaluate_alert(primary: Optional[Track], cfg: AlertConfig) -> Alert:
    """Reference-only distance bands. Never wire this to brakes or throttle."""
    if not cfg.enabled:
        return Alert("off", "Cảnh báo đang tắt trong config.")
    if primary is None:
        return Alert("none", "Không có mục tiêu phía trước (primary).")
    range_m = primary.range_m
    if range_m <= cfg.danger_range_m:
        return Alert(
            "danger",
            f"Rất gần: {range_m:.1f} m — chỉ tham khảo, không can thiệp lái.",
            range_m,
        )
    if range_m <= cfg.warn_range_m:
        return Alert(
            "warn",
            f"Gần: {range_m:.1f} m — kiểm tra bằng mắt, không nhìn màn hình khi lái.",
            range_m,
        )
    return Alert("info", f"Mục tiêu {range_m:.1f} m, vr={primary.vr:.1f} m/s.", range_m)
