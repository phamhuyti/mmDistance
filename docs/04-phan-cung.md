# 04 — Phần cứng

## BOM tối thiểu

| Món | Ghi chú |
|---|---|
| AWR6843AOPEVM | USB vừa nguồn vừa 2 COM ảo (CLI + Data) |
| Raspberry Pi 4 (2 GB+) | Đừng bắt đầu bằng Zero 2W |
| Nguồn DC-DC 12 V → 5 V | Dashcam/Pi, lọc nhiễu, chống đảo cực, chịu sụt khi đề |
| Thẻ SD A2 | + USB disk ghi log nếu có |
| Cáp USB ngắn, khóa cáp | Rung làm rớt CP210x |
| Vỏ nhựa không kim loại | Radome; EVM không có IP |
| Giá đỡ chống rung | Pitch/yaw ổn định thì lọc làn mới có nghĩa |

Không dùng củ sạc điện thoại từ cổng 12 V rẻ — Pi dễ reset.

## Gắn radar

- **Lưới tản nhiệt / cản trước**, antenna nhìn ra đường.
- Không giấu sau kính phủ kim loại.
- Cao ~0.3–0.6 m so với mặt đường; pitch hơi xuống sẽ dính ground clutter, ngẩng lên thì dính trời/biển báo.
- Đo góc lắp, điền `[mount]` trong `configs/default.toml`:
  - `yaw_deg > 0`: board aimed sang phải xe
  - `pitch_deg > 0`: ngẩng lên
- `height_m` chỉ để ghi chú; pipeline không dùng để đổi tọa độ (z vẫn theo sensor, sau xoay).

## Hai cổng COM

Standalone EVM (không ICBOOST): thường `/dev/ttyUSB0` = CLI **115200**, `/dev/ttyUSB1` = Data **921600**. Số có thể đảo sau mỗi lần cắm.

`deploy/99-ti-mmwave.rules` tạo `/dev/radar-cli` và `/dev/radar-data` theo `ID_USB_INTERFACE_NUM`. Kiểm tra:

```bash
python3 -m serial.tools.list_ports -v
udevadm info -a -n /dev/ttyUSB0 | head
```

Vendor Silicon Labs thường `10c4:ea70`. Nếu khác, sửa rules.

## Nhiệt và môi trường

Chip AWR chịu automotive, **board EVM thì không**. Nắng gắt, mưa, đá văng: tự làm vỏ, để khe thoát nhiệt, không bịt antenna bằng sơn kim loại.
