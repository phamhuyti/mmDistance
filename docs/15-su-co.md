# 15 — Sự cố thường gặp

| Hiện tượng | Nguyên nhân hay gặp | Việc làm |
|---|---|---|
| Không có magic / `inspect` rỗng | Sai Data port, baud ≠ 921600, firmware không OOB | Đổi cổng, Visualizer trên PC |
| `Error` khi gửi cfg | Dòng `profileCfg` sai chip/SDK | Xuất lại Estimator đúng AWR6843AOP |
| Mọi `vr` đảo dấu lúc chạy | `vmax` chirp quá nhỏ (profile cabin) | Đổi chirp, xem [05](05-chirp-firmware.md) |
| Primary bám đất | Pitch xuống / elevation gate rộng | Ngẩng board, hẹp `elevation_min_deg` |
| Không thấy xe thẳng | `yaw` chưa calib, cửa ±12° cắt boresight | `simulate` thì thử `[mount] yaw_deg` |
| USB mất khi gờ giảm tốc | Cáp micro-USB lỏng | Khóa cáp, cáp ngắn, ferrite |
| Pi reset khi đề máy | Nguồn yếu | DC-DC đúng loại |
| Thẻ SD corrupt | Tắt máy đột ngột + ghi log thẻ | Overlayfs, log USB |
| UART nghẽn, frame rớt | Heatmap TLV | `guiMonitor -1 2 0 0 0 0 0` |
| `doctor` bảo thiếu profileCfg | Đang dùng file `.example` | Copy + dán chirp |
| Dashboard không mở | Bind `127.0.0.1` từ máy khác | `--host 0.0.0.0`, cùng LAN |
| GPIO im | Không phải Pi / sai BCM pin | `GpioAlertSink` chỉ log level |
| Tầm 20 m không có điểm | AOP hết SNR | Đó là kết quả hợp lệ; đổi ISK/1843 |

Log hữu ích: `FilterStats` (`dropped_*`), `health.stale`, `n_raw`. Nếu `n_raw=0` mãi: RF/cfg. Nếu `n_raw` lớn mà `n_filtered=0`: cổng lọc / mount.
