# 08 — Lọc, cluster, tracker

## Vì sao không `min(range)`

AOP thấy cả thế giới. Một frame có thể gồm: mặt đường (gần, SNR cao), lan can, xe làn bên, xe thật. `min(range)` bám mặt đường.

## Filter (`filters.py`)

Cổng **phần mềm**, không tăng gain:

- `y > 0` — trước mặt
- `range_min/max`
- `|azimuth| ≤ azimuth_max_deg` (mặc định 12°) — “giả lập làn”
- `elevation` trong `[min, max]` — bớt đất / trời
- `snr_db ≥ snr_min_db`

`FilterStats` đếm từng lý do drop. Nếu `dropped_azimuth` gần bằng `n_in`, board đang lệch yaw hoặc FoV quá bẩn.

## Cluster (`cluster.py`)

Hai điểm bumper cùng xe cách nhau < `eps_m` (1.5 m) → một `Cluster`. Tâm trọng số theo SNR. `min_points=1` vì AOP thường chỉ 1–3 điểm/xe.

## Tracker (`tracker.py`)

Mỗi track: Kalman 2 trạng thái `[range, vr]`, đồng thời làm mượt `x,y,z`.

- Predict: đi theo hướng radial với `vr`.
- Associate: khoảng cách XY < `gate_m`.
- Miss ≤ `max_misses` thì vẫn giữ (chớp CFAR).
- `confirmed` khi `hits ≥ min_hits` (mặc định 3) — chống nhiễu 1 frame.

`static`: `|vr + v_ego * cos(az)| ≤ tol`. Biển báo khi xe mình chạy bị loại khỏi primary.

Primary: confirmed, không static, `y>0`, ưu tiên đang lại gần (`vr < -0.3`), rồi gần nhất.

## Alert

`danger ≤ 6 m`, `warn ≤ 12 m` (đổi trong TOML). GPIO tùy chọn. **Không** nối actuator.

## Mount

`geometry.py` xoay điểm trước khi lọc. Lắp lệch 10° mà không khai báo → xe trên boresight nằm ngoài cửa ±12°. Hiệu chỉnh bằng một buổi đo tấm kim loại thẳng ahead, xoay `yaw_deg` đến khi azimuth ~0.
