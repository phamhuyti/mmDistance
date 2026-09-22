# 11 — Quy trình kiểm thử

Không nhảy cóc ra đường.

## A. Unit (mỗi lần sửa code)

```bash
python3 -m pytest -q
```

Phủ: TLV roundtrip, resync buffer, cổng lọc, cluster, Kalman miss, mount yaw, alert, SQLite, inspect, doctor, HTTP dashboard.

## B. Simulate gate

`mmdistance doctor` + `simulate --frames 40`. Primary phải khóa, `n_filtered < n_raw`.

## C. Test tĩnh (cổng quyết định phần cứng)

Đặt **xe hoặc tấm kim loại lớn** trên boresight: 3, 5, 10, 15, 20, 25 m.

| Cự ly (m) | Kỳ vọng AOP | Ghi |
|---|---|---|
| 3–5 | Chắc, SNR cao | range vs thước |
| 10 | Thường còn | SNR, % frame có primary |
| 15 | Có thể chập chờn | |
| 20+ | Nhiều board AOP chết | đừng giả vờ |

Ghi: khoảng cách thước, `range_m`, `snr_db`, `n_raw`, thời tiết, góc lắp.

**Fail gate:** không ổn định ≤ 10 m với xe thật → đổi board, đừng chỉnh Kalman.

So sánh bằng thước/laser khi đứng yên. Mắt thường không phải ground truth.

## D. Bãi, tốc độ thấp

Xe khác lăn 5–20 km/h. Một người lái, một người xem log. USB có rớt không, primary có nhảy lan can không, `dropped_elevation` có tăng khi pitch sai không.

## E. Đường công cộng

Chỉ sau C+D pass. Người lái **không** phải người nhìn dashboard. Tốc độ tăng dần. Ghi capture `.bin` để `replay` tại nhà.

## Tiêu chí PoC “đủ dùng để học”

- Parser không mất magic khi rung nhẹ
- systemd tự chạy lúc lên nguồn
- Có đường cong SNR–range
- Biết rõ tầm chết của **board này**
