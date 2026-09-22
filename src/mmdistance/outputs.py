from __future__ import annotations

from pathlib import Path
import csv
import json
import logging
import sqlite3
import sys
from typing import TextIO

from mmdistance.config import AlertConfig
from mmdistance.models import FrameResult

log = logging.getLogger(__name__)


class JsonlSink:
    def __init__(self, path: str | Path | None = None, stream: TextIO | None = None):
        self._close = False
        if stream is not None:
            self._fp = stream
        elif path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._fp = Path(path).open("a", encoding="utf-8")
            self._close = True
        else:
            self._fp = sys.stdout

    def emit(self, result: FrameResult) -> None:
        self._fp.write(json.dumps(result.as_dict(), ensure_ascii=False) + "\n")
        self._fp.flush()

    def close(self) -> None:
        if self._close:
            self._fp.close()


class CsvSink:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._fp = Path(path).open("a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._fp)
        if self._fp.tell() == 0:
            self._writer.writerow(
                [
                    "frame",
                    "range_m",
                    "vr",
                    "x",
                    "y",
                    "snr_db",
                    "track_id",
                    "alert",
                    "n_raw",
                    "n_filtered",
                    "n_tracks",
                ]
            )

    def emit(self, result: FrameResult) -> None:
        primary = result.primary
        alert = "" if result.alert is None else result.alert.level
        self._writer.writerow(
            [
                result.frame_number,
                None if primary is None else f"{primary.range_m:.3f}",
                None if primary is None else f"{primary.vr:.3f}",
                None if primary is None else f"{primary.x:.3f}",
                None if primary is None else f"{primary.y:.3f}",
                None if primary is None else f"{primary.snr_db:.2f}",
                None if primary is None else primary.track_id,
                alert,
                len(result.raw),
                len(result.filtered),
                len(result.tracks),
            ]
        )
        self._fp.flush()

    def close(self) -> None:
        self._fp.close()


class SqliteSink:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame INTEGER,
                range_m REAL,
                vr REAL,
                x REAL,
                y REAL,
                snr_db REAL,
                track_id INTEGER,
                alert TEXT,
                n_raw INTEGER,
                n_filtered INTEGER,
                n_tracks INTEGER
            )
            """
        )
        self._conn.commit()

    def emit(self, result: FrameResult) -> None:
        primary = result.primary
        self._conn.execute(
            """
            INSERT INTO frames (
                frame, range_m, vr, x, y, snr_db, track_id, alert,
                n_raw, n_filtered, n_tracks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.frame_number,
                None if primary is None else primary.range_m,
                None if primary is None else primary.vr,
                None if primary is None else primary.x,
                None if primary is None else primary.y,
                None if primary is None else primary.snr_db,
                None if primary is None else primary.track_id,
                None if result.alert is None else result.alert.level,
                len(result.raw),
                len(result.filtered),
                len(result.tracks),
            ),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


class GpioAlertSink:
    """Drive warn/danger pins when RPi.GPIO exists; otherwise record the last level."""

    def __init__(self, cfg: AlertConfig):
        self.cfg = cfg
        self.last_level = "none"
        self._gpio = None
        if not cfg.gpio_warn_pin and not cfg.gpio_danger_pin:
            return
        try:
            import RPi.GPIO as GPIO  # type: ignore

            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for pin in (cfg.gpio_warn_pin, cfg.gpio_danger_pin):
                if pin:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
            self._gpio = GPIO
        except Exception as exc:  # pragma: no cover - hardware optional
            log.warning("GPIO không dùng được (%s); chỉ log mức cảnh báo.", exc)

    def emit(self, result: FrameResult) -> None:
        level = "none" if result.alert is None else result.alert.level
        self.last_level = level
        if self._gpio is None:
            return
        warn = level in {"warn", "danger"}
        danger = level == "danger"
        if self.cfg.gpio_warn_pin:
            self._gpio.output(self.cfg.gpio_warn_pin, self._gpio.HIGH if warn else self._gpio.LOW)
        if self.cfg.gpio_danger_pin:
            self._gpio.output(self.cfg.gpio_danger_pin, self._gpio.HIGH if danger else self._gpio.LOW)

    def close(self) -> None:
        if self._gpio is not None:
            self._gpio.cleanup()


def print_primary(result: FrameResult) -> None:
    alert = "" if result.alert is None else f" alert={result.alert.level}"
    if result.primary is None:
        print(
            f"frame={result.frame_number} primary=none "
            f"raw={len(result.raw)} filtered={len(result.filtered)}{alert}",
            file=sys.stderr,
        )
        return
    track = result.primary
    print(
        f"frame={result.frame_number} range={track.range_m:.2f}m "
        f"vr={track.vr:.2f}m/s az={track.azimuth_deg:.1f}deg "
        f"snr={track.snr_db:.1f}dB id={track.track_id}{alert}",
        file=sys.stderr,
    )
