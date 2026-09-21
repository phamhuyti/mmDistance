from __future__ import annotations

from pathlib import Path
import csv
import json
import sys
from typing import TextIO

from mmdistance.models import FrameResult


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
                    "n_raw",
                    "n_filtered",
                    "n_tracks",
                ]
            )

    def emit(self, result: FrameResult) -> None:
        primary = result.primary
        self._writer.writerow(
            [
                result.frame_number,
                None if primary is None else f"{primary.range_m:.3f}",
                None if primary is None else f"{primary.vr:.3f}",
                None if primary is None else f"{primary.x:.3f}",
                None if primary is None else f"{primary.y:.3f}",
                None if primary is None else f"{primary.snr_db:.2f}",
                None if primary is None else primary.track_id,
                len(result.raw),
                len(result.filtered),
                len(result.tracks),
            ]
        )
        self._fp.flush()

    def close(self) -> None:
        self._fp.close()


def print_primary(result: FrameResult) -> None:
    if result.primary is None:
        print(
            f"frame={result.frame_number} primary=none "
            f"raw={len(result.raw)} filtered={len(result.filtered)}",
            file=sys.stderr,
        )
        return
    track = result.primary
    print(
        f"frame={result.frame_number} range={track.range_m:.2f}m "
        f"vr={track.vr:.2f}m/s az={_az(track):.1f}deg "
        f"snr={track.snr_db:.1f}dB id={track.track_id}",
        file=sys.stderr,
    )


def _az(track) -> float:
    import math

    return math.degrees(math.atan2(track.x, track.y))
