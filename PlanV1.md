# Kế hoạch dự án: Đo khoảng cách xe phía trước bằng AWR6843AOPEVM + Raspberry Pi

## 0. Khung sườn & giả định cần chốt trước

Trước khi bắt tay làm, cần thống nhất rõ để tránh làm sai hướng:

- **Board hiện có (AWR6843AOPEVM)** là radar in-cabin, FoV rất rộng (~120°x120°), gain thấp → tầm đo thực tế ngắn hơn nhiều so với radar ACC ô tô thật (77GHz, FoV hẹp). Dự án này là **bản thử nghiệm/proof-of-concept**, không phải hệ thống cảnh báo an toàn đáng tin cậy để dựa vào khi lái xe.
- Bạn đã xác nhận: sẽ chạy thử thực tế trên đường, và có kế hoạch **đổi sang board tầm xa hơn sau này** → nên thiết kế phần mềm tách lớp (driver riêng, xử lý riêng) để dễ thay board mà không viết lại từ đầu.
- Xử lý dữ liệu bằng **Raspberry Pi gắn trên xe, độc lập, không cần laptop**.
- Không dùng kết quả đo để tự động can thiệp phanh/ga — chỉ log + hiển thị/cảnh báo tham khảo.

---

## Giai đoạn 1 — Chuẩn bị phần cứng (Tuần 1)

| Việc | Chi tiết | Rủi ro cần lưu ý |
|---|---|---|
| Nguồn điện xe | DC-DC 12V→5V chuyên dụng cho dashcam/Pi (có lọc nhiễu, chống đảo cực, chịu được sụt áp khi đề máy) | Sạc điện thoại thường KHÔNG đủ ổn định, dễ làm Pi tự reset |
| Raspberry Pi | Pi 4 (2GB+) hoặc Pi Zero 2W | Zero 2W rẻ/nhỏ hơn nhưng CPU yếu hơn nếu sau này muốn xử lý nặng (ví dụ fusion với camera) |
| Lưu trữ | Thẻ SD tốc độ cao (A2) + cân nhắc ghi log ra USB drive ngoài | Tắt máy đột ngột = mất điện đột ngột → dễ hỏng filesystem thẻ SD, nên bật chế độ ghi log an toàn (xem Giai đoạn 4) |
| Vị trí gắn radar | Lưới tản nhiệt/cản trước, **không** giấu sau kính chắn gió | Kính chắn gió đời mới có phủ kim loại/IR-reflective, chặn sóng 60GHz rất mạnh — cần tự kiểm tra bằng test thực tế nếu buộc phải gắn sau kính |
| Vỏ bảo vệ | Vỏ nhựa không sơn kim loại (radome), chống nước/bụi | Board ghi rõ "for evaluation only", KHÔNG đạt chuẩn IP — tự chế vỏ hoặc mua case in 3D |
| Cố định cơ khí | Giá đỡ chống rung | Rung động khi xe chạy dễ làm lỏng cáp USB micro — nên khóa cáp bằng dây rút/keo nóng |

---

## Giai đoạn 2 — Cấu hình & firmware radar (Tuần 1-2)

1. Cài **mmWave SDK** + **mmWave Automotive Toolbox** trên PC (chỉ dùng để flash/cấu hình ban đầu, không phải để vận hành lâu dài).
2. Dùng **mmWave Sensing Estimator** (công cụ web TI) để tính cấu hình chirp tối ưu tầm xa nhất có thể với board này — chấp nhận đánh đổi resolution/update rate.
3. Flash **Out-of-Box Demo** hoặc build config tùy chỉnh, xuất point cloud (range, velocity, angle, SNR) qua UART dạng TLV.
4. Test bằng **mmWave Demo Visualizer** (chạy trên PC, kết nối tạm thời) để xác nhận board hoạt động đúng trước khi chuyển qua Pi.
5. **Tự đo giới hạn thực tế**: đặt vật phản xạ chuẩn ở 1m, 3m, 5m, 10m, 15m... ghi lại board detect được đến đâu. Đừng tin số liệu chung chung trong datasheet — mỗi cấu hình chirp cho kết quả khác nhau.

---

## Giai đoạn 3 — Driver & xử lý dữ liệu trên Pi (Tuần 2-3)

Kiến trúc phần mềm (tách lớp để dễ đổi board sau này):

```
[UART Reader Layer]      → đọc raw bytes từ 2 cổng COM ảo (CLI port + Data port)
        ↓
[TLV Parser Layer]       → parse theo mmWave SDK TLV format → list điểm (x,y,z,velocity,SNR)
        ↓
[Filter Layer]           → lọc theo góc (giả lập "làn xe" phía trước, vd ±10-15°),
                            lọc ground clutter theo elevation/velocity, lọc SNR thấp
        ↓
[Tracking Layer]         → chọn điểm gần nhất ổn định qua nhiều frame (moving average
                            hoặc Kalman filter 1D), tránh nhiễu 1-frame
        ↓
[Output Layer]           → log CSV/SQLite, hiển thị OLED/HDMI, cảnh báo LED/buzzer
```

Việc cụ thể:
- Viết `uart_reader.py` dùng `pyserial`, đọc 2 cổng COM.
- Viết `tlv_parser.py` theo đúng cấu trúc TLV của mmWave SDK version đang dùng (khác version SDK có thể khác cấu trúc byte).
- Viết `filter.py` — đây là phần quan trọng nhất vì FoV vật lý của board rất rộng và **không thể thu hẹp bằng phần cứng**, chỉ lọc được ở bước phần mềm sau khi đã nhận điểm.
- Viết `tracker.py` — bộ lọc khoảng cách theo thời gian.
- Viết `main.py` chạy như service (systemd) tự khởi động khi Pi boot, không cần cắm màn hình/bàn phím.

---

## Giai đoạn 4 — Độ tin cậy & vận hành trên xe (Tuần 3-4)

- Cấu hình Pi **read-only root filesystem** hoặc dùng overlay filesystem để tránh hỏng thẻ SD khi mất điện đột ngột (tắt máy xe).
- Ghi log ra buffer RAM trước, flush định kỳ hoặc khi phát hiện điện áp sắp mất (nếu có mạch cảnh báo mất nguồn).
- Cơ chế tự khởi động lại khi có điện (systemd service), không cần thao tác thủ công mỗi lần lên xe.
- Test rung động: chạy thử đường xấu, kiểm tra cáp USB/kết nối có ổn định không.

---

## Giai đoạn 5 — Kiểm thử thực tế (Tuần 4-5)

1. Test tĩnh trong bãi đỗ (đã làm ở Giai đoạn 2).
2. Test tốc độ thấp trong bãi đỗ với xe khác di chuyển.
3. Test thực tế trên đường, tốc độ thấp trước, tăng dần — **luôn có người khác quan sát/lái phụ**, không tự vừa lái vừa theo dõi màn hình.
4. So sánh số liệu radar với ước lượng bằng mắt/khoảng cách vạch kẻ đường để đánh giá sai số.
5. Ghi nhận rõ **giới hạn thực tế** (tầm đo tối đa, tốc độ tối đa còn tin cậy, điều kiện thời tiết ảnh hưởng) — đây là dữ liệu quan trọng để quyết định khi nào cần đổi board.

---

## Giai đoạn 6 — Chuẩn bị migration sang board tầm xa

Vì đã biết trước sẽ đổi board:
- Giữ nguyên `TLV Parser`, `Filter`, `Tracker`, `Output` layer — các board mmWave SDK của TI (AWR1843, AWR2243...) dùng format TLV tương tự, chỉ khác một số field/offset.
- Chỉ cần viết lại `uart_reader.py` (nếu đổi giao tiếp) và cấu hình chirp mới.
- Nên chọn board tiếp theo có **FoV hẹp hơn** (kiểu long-range ACC) để giảm việc phải lọc clutter bằng phần mềm.

---

## Rủi ro tổng thể cần theo dõi xuyên suốt dự án

- **Tầm đo thực tế có thể rất thấp** (vài mét đến vài chục mét) — không nên đặt kỳ vọng cao cho bản dùng board hiện tại.
- **Không dùng cho quyết định an toàn** — đây là công cụ log/tham khảo, không phải AEB/ACC.
- **Không xuyên qua kính chắn gió tốt** — cần vị trí gắn hở.
- **Board không đạt chuẩn môi trường ô tô** (không IP-rated, "for evaluation only") — tự chịu trách nhiệm về độ bền khi lắp ngoài trời lâu dài.
