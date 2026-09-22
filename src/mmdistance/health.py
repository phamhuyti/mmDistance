from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Health:
    frames: int = 0
    fps: float = 0.0
    last_age_s: float = 0.0
    stale: bool = False

    def as_dict(self) -> dict:
        return {
            "frames": self.frames,
            "fps": round(self.fps, 2),
            "last_age_s": round(self.last_age_s, 3),
            "stale": self.stale,
        }


class HealthMonitor:
    def __init__(self, stale_after_s: float = 2.0):
        self.stale_after_s = stale_after_s
        self.frames = 0
        self._last_t: float | None = None
        self._fps = 0.0

    def tick(self, now: float | None = None) -> Health:
        now = time.monotonic() if now is None else now
        self.frames += 1
        if self._last_t is not None:
            dt = max(now - self._last_t, 1e-6)
            instant = 1.0 / dt
            self._fps = instant if self._fps == 0 else (0.8 * self._fps + 0.2 * instant)
        self._last_t = now
        return Health(
            frames=self.frames,
            fps=self._fps,
            last_age_s=0.0,
            stale=False,
        )

    def snapshot(self, now: float | None = None) -> Health:
        now = time.monotonic() if now is None else now
        age = 0.0 if self._last_t is None else now - self._last_t
        return Health(
            frames=self.frames,
            fps=self._fps,
            last_age_s=age,
            stale=self.frames > 0 and age > self.stale_after_s,
        )
