# 06 — Kiến trúc phần mềm

Nguyên tắc: **board-specific ở mép, thuật toán ở giữa**.

```
┌─────────────┐   ┌──────────┐   ┌───────────┐
│ simulate    │   │ replay   │   │ live UART │
│ static/car  │   │ .bin     │   │ + capture │
└──────┬──────┘   └────┬─────┘   └─────┬─────┘
       │               │               │
       └───────────────┴──────┬────────┘
                              ▼
                     tlv.parse_frame
                     RadarFrame[Detection]  (khung cảm biến)
                              ▼
                     geometry (yaw/pitch/roll)
                              ▼
                     filters  → FilterStats
                     cluster  → Cluster[]
                     tracker  → Track[] + primary
                     alerts   → info/warn/danger
                     health   → fps / stale
                              ▼
              JSONL  CSV  SQLite  GPIO  dashboard  stderr
```

## Model không đổi khi đổi board

`Detection(x, y, z, vr, snr_db)` trong hệ +X phải, +Y trước, +Z lên.

Adapter TI hôm nay: `tlv.py` + `uart.py`. Adapter ngày mai có thể là SDK khác, SPI, hay Ethernet — miễn trả về `Detection`.

## Luồng một frame (`Pipeline.process`)

1. Đo `dt` từ timestamp hoặc config.
2. Đọc `ego.speed_mps` / `speed_file`.
3. Xoay điểm sang hệ xe.
4. Lọc range, azimuth, elevation, SNR, `y > 0`.
5. DBSCAN-style cluster (mặc định `min_points=1` vì AOP thưa).
6. Kalman `[range, vr]`, nearest-neighbor gate.
7. Primary = track confirmed, không `static`, ưu tiên `vr < 0`, gần nhất.
8. Gán alert + fps.

## Config

`configs/default.toml` chia section `[radar] [filter] [cluster] [tracker] [ego] [mount] [alert] [output]`. Không nhét số chirp vào TOML — chirp thuộc `profile.cfg`.

## Chỗ cố ý chưa làm

- Fusion camera/lidar
- Tracker JPDA / 4-state đầy đủ
- OLED driver cụ thể (thêm sink trong `outputs.py`)
- Đọc GPS NMEA (ghi m/s vào `speed_file` là đủ để thử cờ static)
