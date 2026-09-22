from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from statistics import mean
from typing import Any


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primaries = [row["primary"] for row in rows if row.get("primary")]
    ranges = [item["range_m"] for item in primaries]
    snrs = [item["snr_db"] for item in primaries if item.get("snr_db") is not None]
    vrs = [item["vr"] for item in primaries]
    alerts = Counter((row.get("alert") or {}).get("level", "none") for row in rows)
    return {
        "n_frames": len(rows),
        "n_with_primary": len(primaries),
        "detect_rate": (len(primaries) / len(rows)) if rows else 0.0,
        "range_min_m": min(ranges) if ranges else None,
        "range_max_m": max(ranges) if ranges else None,
        "range_mean_m": mean(ranges) if ranges else None,
        "snr_mean_db": mean(snrs) if snrs else None,
        "vr_mean": mean(vrs) if vrs else None,
        "alerts": dict(alerts),
        "mean_n_raw": mean(row["n_raw"] for row in rows) if rows else 0,
        "mean_n_filtered": mean(row["n_filtered"] for row in rows) if rows else 0,
    }


def text_report(stats: dict[str, Any]) -> str:
    def fmt(value: Any, digits: int = 2) -> str:
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.{digits}f}"
        return str(value)

    lines = [
        "=== mmDistance analyze ===",
        f"Số frame              {stats['n_frames']}",
        f"Frame có primary      {stats['n_with_primary']}  ({100 * stats['detect_rate']:.1f}%)",
        f"Range min / mean / max  {fmt(stats['range_min_m'])} / {fmt(stats['range_mean_m'])} / {fmt(stats['range_max_m'])} m",
        f"SNR trung bình        {fmt(stats['snr_mean_db'])} dB",
        f"vr trung bình         {fmt(stats['vr_mean'])} m/s",
        f"Điểm raw / filtered   {fmt(stats['mean_n_raw'])} / {fmt(stats['mean_n_filtered'])}",
        f"Cảnh báo              {stats['alerts']}",
    ]
    return "\n".join(lines)


def html_report(stats: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    points = []
    for row in rows:
        primary = row.get("primary") or {}
        range_m = primary.get("range_m")
        points.append((row.get("frame"), range_m))
    svg = _sparkline(points)
    return f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><title>mmDistance report</title>
<style>
body {{ font-family: sans-serif; max-width: 900px; margin: 2rem auto; color: #102; }}
pre {{ background: #f4f6f8; padding: 1rem; }}
.note {{ color: #a40; }}
</style></head><body>
<h1>mmDistance — báo cáo log</h1>
<p class="note">PoC tham khảo, không phải hệ thống an toàn.</p>
<pre>{text_report(stats)}</pre>
<h2>Range theo frame</h2>
{svg}
</body></html>
"""


def _sparkline(points: list[tuple[Any, Any]]) -> str:
    values = [(i, float(r)) for i, (_, r) in enumerate(points) if r is not None]
    if len(values) < 2:
        return "<p>Không đủ primary để vẽ.</p>"
    width, height = 800, 220
    ys = [item[1] for item in values]
    ymin, ymax = min(ys), max(ys)
    span = max(ymax - ymin, 0.1)
    coords = []
    for index, range_m in values:
        x = 20 + index * (width - 40) / (len(points) - 1 or 1)
        y = height - 20 - (range_m - ymin) / span * (height - 40)
        coords.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'style="background:#f4f6f8;border:1px solid #ddd">'
        f'<polyline fill="none" stroke="#0a6" stroke-width="2" points="{" ".join(coords)}"/>'
        f'<text x="20" y="16" font-size="12">max {ymax:.1f} m</text>'
        f'<text x="20" y="{height - 6}" font-size="12">min {ymin:.1f} m</text>'
        f"</svg>"
    )
