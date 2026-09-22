# 02 — An toàn và giới hạn

Đọc xong mục này trước khi cắm board lên xe.

## Được làm

- Log khoảng cách / vận tốc để học radar.
- Buzzer/LED **tham khảo**, với người khác cầm lái.
- Test tĩnh trong bãi, rồi tốc độ thấp có người quan sát.

## Không được làm

- Nối ra phanh, ga, hộp số, CAN điều khiển xe.
- Tự lái một mình vừa nhìn dashboard vừa lái.
- Tin số liệu khi mưa lớn, sau kính phủ kim loại, hoặc ngoài tầm đã đo.
- Gọi đây là “cảnh báo va chạm” cho người khác dùng.

Cảnh báo trong code (`alert.warn` / `alert.danger`) **chỉ là ngưỡng số**. Phần mềm không biết làn đường thật, không biết người đi bộ, không đạt ISO 26262.

## Giới hạn vật lý của AWR6843AOPEVM

| Mục | Thực tế |
|---|---|
| Tần số | 60–64 GHz (không phải 76–81 GHz của ACC) |
| FoV | ~120° × 120° — không thu hẹp bằng phần cứng |
| Gain | Cố định, thấp; config không tăng gain |
| Vỏ EVM | “evaluation only”, không IP, không chịu mưa/đá |
| Kính chắn gió | Đời mới phủ kim loại/IR thường chặn 60 GHz |
| TLV heatmap | Dễ nghẽn UART 921600 nếu bật |

Nếu test tĩnh không ổn định ở 10–15 m với xe thật: **đừng tối ưu tracker thêm**. Đổi board. Xem [12](12-doi-board.md).

## Trách nhiệm

Bạn tự chịu việc lắp EVM ngoài trời, nguồn 12 V, và việc chạy thử trên đường. Repo này không phải sản phẩm.
