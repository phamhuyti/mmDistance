# mmDistance

PoC đo khoảng cách xe phía trước bằng **AWR6843AOPEVM** + Raspberry Pi. Chỉ log / hiển thị / LED tham khảo — **không** phải ACC/AEB, **không** nối phanh/ga.

**Tài liệu học đầy đủ (bắt đầu ở đây):** [docs/index.md](docs/index.md)

## 30 giây

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
python3 -m mmdistance doctor
python3 -m mmdistance simulate --frames 40
python3 -m mmdistance inspect examples/approaching_car.bin
python3 -m mmdistance serve --port 8080   # http://127.0.0.1:8080
```

## Pipeline

```
UART / replay / simulate
        → TLV (magic 02 01 04 03 06 05 08 07)
        → xoay góc lắp
        → lọc làn / đất / SNR
        → cluster
        → Kalman [range, vr]
        → primary + alert
        → JSONL / CSV / SQLite / GPIO / dashboard
```

Board AOP FoV ~120°. Lọc ±12° không tăng SNR. Chi tiết: [docs/08-xu-ly.md](docs/08-xu-ly.md).

## Lệnh

| Lệnh | Việc |
|---|---|
| `simulate` | Xe giả lập; `--write-bin`, `--static-range` |
| `replay FILE` | Phát lại UART `.bin` |
| `live` | 2 cổng COM; `--capture`, `--dashboard` |
| `inspect FILE` | Giải thích từng byte TLV |
| `analyze JSONL` | Thống kê + HTML |
| `serve` | Dashboard + simulate/replay |
| `doctor` | Self-check |

Baud: CLI 115200, Data 921600. Chirp: copy `configs/profile.cfg.example` → `profile.cfg`, dán Sensing Estimator. **Không** dùng profile cabin 2.7 m / 1.7 m/s.

## Sửa file nào

Xem bảng trong [docs/13-ban-do-source.md](docs/13-ban-do-source.md). TOML: `configs/default.toml`. Pi: [docs/10-raspberry-pi.md](docs/10-raspberry-pi.md).

## Giới hạn

AOP là radar in-cabin. Nếu test tĩnh không ổn ở 10–15 m: đổi board ([docs/12-doi-board.md](docs/12-doi-board.md)). Kế hoạch gốc: [PlanV1.md](PlanV1.md).
