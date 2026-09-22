# 05 — Chirp và firmware

Firmware trên EVM (Out-of-Box demo của mmWave SDK) **tính FFT, CFAR, góc** rồi chỉ gửi point cloud qua UART. Pi không làm ADC.

## Việc trên PC (một lần)

1. Cài **mmWave SDK** đúng chip 6843 + UniFlash.
2. Flash **Out-of-Box demo** cho AWR6843AOP.
3. Mở **mmWave Demo Visualizer**, xác nhận điểm hiện ra.
4. Mở **mmWave Sensing Estimator**, nhập mục tiêu PoC (xem [03](03-vat-ly-radar.md)), xuất chirp.
5. Dán block `profileCfg` / `chirpCfg` / `frameCfg` / CFAR vào `configs/profile.cfg`.
6. Giữ đúng:

```
guiMonitor -1 2 0 0 0 0 0
```

Nghĩa: subframe -1 (tất cả), **2 = detected points + side info SNR**, các heatmap/profile = 0. UART 921600 không đủ nếu bật heatmap.

## `profile.cfg` được gửi mỗi boot

OOB **không nhớ** chirp khi mất nguồn. `uart.send_cfg` đọc file, bỏ dòng `%` / `#` / trống, gửi từng dòng, chờ `Done`. Gặp `Error` thì dừng — đừng `sensorStart` khi profile còn comment.

File `configs/profile.cfg.example` **cố ý không có số RF**. Copy:

```bash
cp configs/profile.cfg.example configs/profile.cfg
# dán output Estimator vào chỗ đánh dấu
```

Rồi sửa `cfg_path` trong `configs/default.toml`.

## Các lệnh CLI thường gặp

| Lệnh | Vai trò |
|---|---|
| `sensorStop` / `flushCfg` | Reset trước khi nạp |
| `channelCfg` | Bật TX/RX |
| `profileCfg` | Slope, sample, idle — quyết định R và v |
| `chirpCfg` | Gán profile cho từng TX |
| `frameCfg` | Số chirp lặp, chu kỳ frame (Hz) |
| `cfarCfg` | Ngưỡng phát hiện |
| `aoaFovCfg` | Cửa góc **trên radar** (vẫn Wide FoV vật lý) |
| `cfarFovCfg` | Cửa range/doppler trên radar |
| `guiMonitor` | TLV nào được gửi |
| `sensorStart` | Bắt đầu frame |

`aoaFovCfg` hẹp giúp **bớt điểm** gửi đi, không tăng SNR. Vẫn nên lọc lại trên Pi vì CFAR/FoV firmware khác version.

## Không copy profile cabin

Nếu Visualizer đang ở lab “occupant / child presence”, \(R_\max\) ~2.7 m và \(v_\max\) ~1.7 m/s. Nhìn thấy người trong xe không có nghĩa đo được xe phía trước.
