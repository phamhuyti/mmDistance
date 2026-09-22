# 01 — Giới thiệu

## Dự án này là gì

**mmDistance** đọc point cloud từ radar TI **AWR6843AOPEVM** (60 GHz, antenna-on-package, FoV ~120°×120°) trên **Raspberry Pi**, rồi ước lượng khoảng cách tới **một mục tiêu phía trước** (thường là xe).

Kết quả: số `range_m`, vận tốc xuyên tâm `vr`, log JSONL/CSV/SQLite, dashboard HTTP, LED tùy chọn.

Không phải: Adaptive Cruise Control, Automatic Emergency Braking, hay bất kỳ hệ thống an toàn nào.

## Vì sao phần mềm được viết như vậy

Board hiện có được TI thiết kế cho **cảm biến trong cabin** (phát hiện người, trẻ em). Antenna gain thấp (~5 dBi), năng lượng trải 120°. Trên đường, tầm thực tế thường chỉ **vài mét đến khoảng 15–30 m** với xe lớn, nếu chirp được chỉnh. Demo cabin mặc định thậm chí chỉ ~2.7 m và `vmax` ~1.7 m/s (~6 km/h) — không dùng được khi xe chạy.

Vì thế code **tách lớp**:

```
UART / file / simulator     ← biết board TI
        ↓
Detection {x, y, z, vr, snr}
        ↓
mount → filter → cluster → tracker → alert → log/dashboard
```

Khi đổi sang IWR6843ISK hoặc AWR1843, chỉ cần adapter mới ra cùng `Detection`. Thuật toán phía sau giữ nguyên.

## Ba chế độ học

1. **Không có radar** — `simulate`, `inspect`, `serve`, `pytest`. Học pipeline.
2. **Có radar trên bàn** — flash OOB, `live`, đo tấm kim loại/xe đứng yên.
3. **Trên xe** — nguồn DC-DC, systemd, người lái phụ, không nhìn màn hình khi cầm lái.

Bắt đầu: [09 — Chạy thử](09-chay.md). Nền tảng vật lý: [03](03-vat-ly-radar.md).
