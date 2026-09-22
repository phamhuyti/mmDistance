# 03 — Vật lý mmWave (đủ để chỉnh chirp)

Radar FMCW gửi một **chirp**: tần số tăng tuyến tính theo thời gian. Echo trễ → tần số hiệu (beat) tỷ lệ với **khoảng cách**. Nhiều chirp liên tiếp → pha đổi theo thời gian → **vận tốc xuyên tâm** (Doppler). Nhiều anten TX/RX → **góc**.

## Công thức cần nhớ

Gọi \(B\) là băng thông sweep, \(T_c\) idle+ramp, \(N\) số sample, \(N_c\) số chirp trong frame, \(\lambda = c / f\).

| Đại lượng | Ý nghĩa | Muốn tăng thì |
|---|---|---|
| \(\Delta R \approx c / (2B)\) | Độ mịn khoảng cách | Tăng \(B\) (giảm tầm xa) |
| \(R_\max\) | Tầm unambiguous | Giảm slope, tăng sample |
| \(v_\max\) | Tốc độ unambiguous | Giảm \(T_c\) (chirp dày hơn) |
| \(\Delta v\) | Độ mịn tốc độ | Tăng thời gian frame / số chirp |
| FoV / gain | Năng lượng theo hướng | **Antenna** — software không sửa được |

AOP trải năng lượng 120°, nên \(R_\max\) trên giấy (từ sample rate) **không** phải tầm detect xe thật. Tầm thật bị SNR / RCS / clutter quyết định. Đó là lý do Giai đoạn 2 của plan bắt **tự đo** 1 m, 3 m, 5 m…

## Doppler wrap

Nếu `|vr| > vmax`, vận tốc hiện sai dấu. Tracker sẽ nghĩ xe đang ra xa trong khi đang lại gần.

Demo **in-cabin** TI: \(R_\max \approx 2.7\,\mathrm{m}\), \(v_\max \approx 1.7\,\mathrm{m/s}\). **Cấm** dùng profile đó trên đường.

PoC phía trước (rồi đo lại): \(R_\max\) 20–40 m, \(v_\max\) 20–30 m/s, \(\Delta R\) 20–40 cm, 10–20 Hz. Estimator tính chirp; antenna AOP có thể vẫn không đạt.

## Hệ trục TI Out-of-Box

```
        +Z (lên)
         |
         |
         +------ +X (phải của board)
        /
       /
     +Y (boresight, phía trước)
```

- `range = sqrt(x²+y²+z²)`
- `azimuth = atan2(x, y)` — 0° là phía trước, dương sang phải
- `elevation = atan2(z, hypot(x,y))`
- `vr > 0` thường là **ra xa** radar; xe lại gần: `vr < 0`

Lọc “làn xe ±12°” là lọc azimuth trong hệ này, **sau** khi xoay góc lắp (`mount.yaw/pitch/roll`).

## Clutter

FoV rộng + gắn cản trước → mặt đường, lan can, xe làn bên, biển báo. Điểm **gần nhất** thường không phải xe. Pipeline vì thế: lọc → cluster → track theo thời gian → chọn primary không tĩnh.

Khi xe mình chạy, vật tĩnh có `vr ≈ -v_ego * cos(azimuth)`. `ego.speed_mps` (hoặc `speed_file`) dùng để gán cờ `static`.
