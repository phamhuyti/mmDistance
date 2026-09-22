# 13 — Bản đồ source

Repo gốc:

```
configs/          default.toml, profile.cfg.example
deploy/           udev, systemd
docs/             tài liệu học (bạn đang đọc)
examples/         approaching_car.bin
src/mmdistance/   package Python
tests/            pytest
.github/workflows/ci.yml
```

## Từng module

| File | Trách nhiệm | Đọc khi |
|---|---|---|
| `models.py` | `Detection`, `Cluster`, `Track`, `FrameResult` | Đổi field log |
| `config.py` | TOML → dataclass, `read_ego_speed` | Thêm knob |
| `tlv.py` | extract / parse / encode / `describe_packet` | SDK khác, học TLV |
| `uart.py` | 2 COM, `send_cfg`, capture raw, wait port | Live không lên |
| `geometry.py` | yaw/pitch/roll | Lắp lệch |
| `filters.py` | Cổng không gian + `is_static` | Nhiễu làn / đất |
| `cluster.py` | DBSCAN nhẹ, không sklearn | Một xe bị tách 2 |
| `tracker.py` | Kalman 2-state, primary | Track nhảy |
| `alerts.py` | info/warn/danger | Ngưỡng LED |
| `health.py` | fps, stale | USB đứng |
| `pipeline.py` | Ghép 1 frame | — |
| `outputs.py` | JSONL, CSV, SQLite, GPIO | Thêm OLED ở đây |
| `simulate.py` | Xe lại gần + mục tiêu tĩnh | Demo |
| `analyze.py` | Thống kê JSONL + HTML | Sau test đường |
| `doctor.py` | Self-check | Máy mới |
| `dashboard.py` + `static/dashboard.html` | HTTP | HDMI / LAN |
| `cli.py` | Tất cả subcommand | — |

CLI: `simulate` `replay` `live` `serve` `inspect` `analyze` `doctor`.

Test map: `tests/test_tlv.py`, `test_filters.py`, `test_cluster_tracker.py`, `test_geometry.py`, `test_alerts_sinks.py`, `test_tools.py`, `test_cli.py`.
