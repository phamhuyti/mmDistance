# 07 — Giao thức TLV (từng byte)

Out-of-Box demo gửi **một packet mỗi frame**, little-endian, pad tổng số byte chia hết 32.

Luyện: `python3 -m mmdistance inspect examples/approaching_car.bin`

## Magic word

8 byte đầu **luôn**:

```
02 01 04 03 06 05 08 07
```

Đây là `uint16` 0x0102, 0x0304, 0x0506, 0x0708 viết little-endian. Parser tìm chuỗi này trong buffer UART bẩn (USB rớt, byte rác).

## Header (40 byte)

| Offset | Kiểu | Trường |
|---|---|---|
| 0 | 8 byte | magic |
| 8 | uint32 | version SDK |
| 12 | uint32 | **totalPacketLen** (cả pad) |
| 16 | uint32 | platform (mã chip) |
| 20 | uint32 | frameNumber |
| 24 | uint32 | timeCpuCycles |
| 28 | uint32 | numDetectedObj |
| 32 | uint32 | numTLVs |
| 36 | uint32 | subFrameNumber |

`uart.py` đọc `totalPacketLen` ở offset 12, chờ đủ byte, rồi cắt. Nếu length < 40 hoặc > 64 KiB: bỏ 1 byte, tìm magic lại.

Frame **0 object** vẫn hợp lệ (đường trống). Parser TI mẫu đôi khi coi 0 object là fail — mmDistance **không**.

## TLV

Mỗi TLV: `uint32 type` + `uint32 length` + payload `length` byte.

| type | Tên | Payload |
|---|---|---|
| 1 | Detected Points | mỗi object 16 byte: `float x y z vr` |
| 7 | Side info | mỗi object 4 byte: `int16 snr, int16 noise` đơn vị **0.1 dB** → chia 10 |
| 2–6, 8, 9 | profile / heatmap / stats | **tắt** bằng `guiMonitor` |

SNR 15.0 dB ↔ raw 150.

## Đồng bộ CLI / Data

| Cổng | Baud | Việc |
|---|---|---|
| CLI | 115200 | text `.cfg` |
| Data | 921600 | binary TLV |

Gửi cfg xong mới đọc data. Sai cổng → Visualizer “hardware not detected”, Pi thì buffer không bao giờ thấy magic.

## Version SDK

Offset của type 1/7 ổn định từ SDK 3.x OOB. Demo “people tracking” dùng TLV khác (target list). Nếu flash nhầm lab, `inspect` sẽ hiện type lạ — xem `TLV_NAMES` trong `tlv.py`.
