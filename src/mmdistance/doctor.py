from __future__ import annotations

from pathlib import Path
import sys

from mmdistance.config import AppConfig
from mmdistance.pipeline import Pipeline
from mmdistance.simulate import approaching_car_frames


def run_doctor(cfg: AppConfig) -> int:
    lines = ["mmDistance doctor", ""]
    ok = True

    lines.append(f"Python            {sys.version.split()[0]}")
    try:
        import serial  # noqa: F401

        lines.append("pyserial          OK")
    except ImportError:
        lines.append("pyserial          THIẾU — pip install pyserial (cần cho live)")
        ok = False

    cfg_path = Path(cfg.radar.cfg_path)
    if cfg_path.is_file():
        text = cfg_path.read_text(encoding="utf-8")
        lines.append(f"radar cfg         {cfg_path}  ({len(text.splitlines())} dòng)")
        if "guiMonitor" not in text:
            lines.append("                  CẢNH BÁO: không thấy guiMonitor")
        if "guiMonitor -1 2" not in " ".join(text.split()):
            lines.append(
                "                  Nên dùng guiMonitor -1 2 0 0 0 0 0 (điểm + SNR, tắt heatmap)"
            )
        has_profile = any(line.strip().startswith("profileCfg") for line in text.splitlines())
        if not has_profile:
            lines.append("                  CẢNH BÁO: chưa dán profileCfg từ Estimator (live sẽ fail)")
    else:
        lines.append(f"radar cfg         THIẾU {cfg_path}")
        ok = False

    for label, port in (("CLI", cfg.radar.cli_port), ("Data", cfg.radar.data_port)):
        exists = Path(port).exists()
        lines.append(f"cổng {label:4}        {port}  {'có' if exists else 'chưa thấy (bình thường nếu không cắm board)'}")

    for note in cfg.warnings():
        lines.append(f"config            CẢNH BÁO: {note}")

    pipe = Pipeline(cfg)
    last = None
    for frame in approaching_car_frames(n_frames=8, dt=0.05):
        last = pipe.process(frame, dt=0.05)
    if last is None or last.primary is None:
        lines.append("simulate          FAIL — không khóa được xe giả lập")
        ok = False
    else:
        lines.append(
            f"simulate          OK  range={last.primary.range_m:.2f}m  "
            f"vr={last.primary.vr:.2f}  filtered={last.filter_stats.n_out}/{last.filter_stats.n_in}"
        )

    lines.append("")
    lines.append("Kết luận: " + ("sẵn sàng học/sim; live cần board + profile.cfg thật" if ok else "còn mục đỏ ở trên"))
    print("\n".join(lines))
    return 0 if ok else 1
