# mmDistance

Đo khoảng cách xe phía trước từ **AWR6843AOPEVM** trên Raspberry Pi. Đây là PoC log/hiển thị, **không** phải ACC/AEB.

Cách code: **tách lớp cứng**. Parser TLV và UART là adapter của board hiện tại. Filter / cluster / tracker chỉ nói chuyện với model `Detection`, nên đổi board sau này không viết lại thuật toán.

```
UART / file / simulator
        ↓
   tlv.parse_frame  →  RadarFrame[Detection]
        ↓
   filters          →  lane / ground / SNR
        ↓
   cluster          →  một xe = một Cluster
        ↓
   tracker          →  Track[range, vr] + primary
        ↓
   JSONL / CSV / journal
```

## Vì sao không code “điểm gần nhất”

Board AOP có FoV ~120°. Lọc góc ±12° **không** tăng SNR, chỉ vứt điểm. Trên đường, điểm gần nhất thường là mặt đường hoặc lan can.

Pipeline vì thế làm theo thứ tự:

1. Lọc không gian (tầm, azimuth, elevation, SNR, `y > 0`).
2. Gộp điểm gần nhau thành object.
3. Kalman 2 trạng thái `[range, vr]`, giữ track khi mất 1–2 frame.
4. Chọn **primary**: track đã confirmed, không phải clutter tĩnh (so với vận tốc ego), ưu tiên đang lại gần.

## Chạy ngay, chưa cần radar

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m mmdistance simulate --frames 40
```

`replay` dùng file UART đã ghi:

```bash
python3 -m mmdistance replay capture.bin
```

Trên Pi, sau khi flash Out-of-Box demo và điền `configs/profile.cfg`:

```bash
sudo cp deploy/99-ti-mmwave.rules /etc/udev/rules.d/
sudo udevadm control --reload
python3 -m mmdistance --config configs/default.toml live \
  --cli-port /dev/radar-cli --data-port /dev/radar-data \
  --cfg configs/profile.cfg
```

CLI = 115200, Data = 921600. Mỗi lần boot phải gửi lại `.cfg` — board OOB không nhớ chirp giữa các lần mất nguồn.

## Sửa file nào khi làm thật

| Việc | File |
|---|---|
| Đổi cổng, cổng lọc, ngưỡng track | `configs/default.toml` |
| Chirp / `guiMonitor` | `configs/profile.cfg` (copy từ `.example`) |
| TLV SDK khác version | `src/mmdistance/tlv.py` |
| UART / gửi cfg | `src/mmdistance/uart.py` |
| Lane / mặt đường / SNR | `src/mmdistance/filters.py` |
| Gộp điểm | `src/mmdistance/cluster.py` |
| Bám theo thời gian | `src/mmdistance/tracker.py` |
| OLED / LED / buzzer | thêm sink trong `outputs.py`, gọi từ `cli.py` |
| Board mới (1843 / ISK) | adapter mới cùng trả về `Detection`; giữ filter/tracker |

Model nội bộ (không đổi khi đổi board):

```text
Detection {x, y, z, vr, snr_db}   # TI OOB: +X phải, +Y trước, +Z lên
Cluster   {x, y, z, vr, snr_db, n_points}
Track     {id, range_m, vr, hits, static}
```

`vr > 0` theo TI thường là ra xa radar. Xe đang lại gần: `vr < 0`.

## Chirp

Không nhúng số chirp cabin (~2.7 m / 1.7 m/s) vào firmware chạy xe. Xuất profile từ Sensing Estimator với `Rmax`, `vmax`, `ΔR`, frame period, rồi dán vào `profile.cfg`.

Bắt buộc: `guiMonitor -1 2 0 0 0 0 0` (điểm + SNR, tắt heatmap để UART 921600 không nghẽn).

## systemd

```bash
sudo cp deploy/mmdistance.service /etc/systemd/system/
sudo systemctl enable --now mmdistance
```

Chỉnh `WorkingDirectory` / user trong unit cho khớp máy. Ghi CSV ra USB nếu rootfs để overlay/read-only.

## Giới hạn

Phần mềm không biến AOP thành radar ACC. Nếu test tĩnh không thấy xe chắc ở 10–15 m thì dừng tối ưu tracker và đổi board (IWR6843ISK hoặc 76–81 GHz FoV hẹp). Không nối ra phanh/ga.
