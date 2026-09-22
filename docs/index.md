# Tài liệu mmDistance

Bộ tài liệu này dạy **toàn bộ dự án**: vì sao làm, phần cứng, vật lý chirp, từng lớp Python, cách chạy, cách test, và khi nào phải đổi board.

Đọc theo thứ tự nếu bạn mới bắt đầu. Nhảy cóc nếu bạn đã biết radar.

| Bước | File | Bạn sẽ hiểu |
|---|---|---|
| 0 | [01 — Giới thiệu](01-gioi-thieu.md) | Mục tiêu, không phải ACC, kiến trúc 1 trang |
| 1 | [02 — An toàn](02-an-toan.md) | Việc được làm / tuyệt đối không làm |
| 2 | [03 — Vật lý mmWave](03-vat-ly-radar.md) | Range, Doppler, FoV, vì sao AOP tầm ngắn |
| 3 | [04 — Phần cứng](04-phan-cung.md) | Pi, nguồn, gắn radar, cáp USB |
| 4 | [05 — Chirp & firmware](05-chirp-firmware.md) | SDK, Estimator, `profile.cfg`, `guiMonitor` |
| 5 | [06 — Kiến trúc code](06-kien-truc.md) | Pipeline, model `Detection`, đổi board |
| 6 | [07 — TLV từng byte](07-tlv.md) | Magic word, header 40 byte, type 1 & 7 |
| 7 | [08 — Lọc, cluster, track](08-xu-ly.md) | Vì sao không lấy điểm gần nhất |
| 8 | [09 — Chạy thử](09-chay.md) | simulate, inspect, replay, dashboard, analyze |
| 9 | [10 — Raspberry Pi](10-raspberry-pi.md) | udev, systemd, thẻ SD, overlay |
| 10 | [11 — Kiểm thử](11-kiem-thu.md) | Bãi đỗ → đường; tiêu chí pass/fail |
| 11 | [12 — Đổi board](12-doi-board.md) | ISK / 1843; cái gì giữ, cái gì viết lại |
| 12 | [13 — Bản đồ source](13-ban-do-source.md) | Mỗi file Python làm gì |
| 13 | [14 — Thuật ngữ](14-thuat-ngu.md) | SNR, vmax, TLV, CFAR… |
| 14 | [15 — Sự cố](15-su-co.md) | USB rớt, Doppler wrap, không thấy xe |

Lệnh tra nhanh: [cheatsheet.md](cheatsheet.md)

Kế hoạch gốc (không sửa): [`PlanV1.md`](../PlanV1.md)
