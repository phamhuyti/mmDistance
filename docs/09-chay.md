# 09 — Chạy thử (không cần radar)

Từ thư mục gốc repo, Python ≥ 3.11:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
python3 -m mmdistance doctor
```

`doctor` phải thấy `simulate OK`. Cảnh báo `profile.cfg.example` là đúng khi chưa có chirp thật.

## Simulate

```bash
python3 -m mmdistance simulate --frames 40
python3 -m mmdistance simulate --static-range 8 --frames 20
python3 -m mmdistance simulate --frames 40 --write-bin examples/approaching_car.bin
```

Cảnh mặc định: xe từ ~22 m, `vr = -6 m/s`, cộng clutter bên / đất / trời. JSON mỗi dòng ra stdout; stderr in `range=…`.

Quan sát: `n_raw=6`, `n_filtered=2` (hai điểm bumper), `n_clusters=1`, `primary.vr` khoảng −6.

## Inspect TLV

```bash
python3 -m mmdistance inspect examples/approaching_car.bin --index 0
```

Đọc song song [07](07-tlv.md). Đổi `--index` để thấy range giảm dần.

## Replay

```bash
python3 -m mmdistance replay examples/approaching_car.bin
```

Giống live nhưng đọc file. Dùng capture thật (`live --capture captures/run.bin`) để debug khi không còn đứng cạnh xe.

## Dashboard

```bash
python3 -m mmdistance serve --source simulate --port 8080
# mở http://127.0.0.1:8080
```

Số range lớn, bảng track, sparkline, dòng cảnh báo. Vẫn ghi chú “không phải ACC”.

`live --dashboard 8080` trên Pi (bind `0.0.0.0`). Không nhìn màn hình khi đang lái.

## Analyze log

Trong `configs/default.toml`:

```toml
[output]
jsonl_path = "logs/run.jsonl"
csv_path = "logs/run.csv"
sqlite_path = "logs/run.db"
```

```bash
python3 -m mmdistance --config configs/default.toml simulate --frames 50
python3 -m mmdistance analyze logs/run.jsonl --html logs/report.html
```

Báo cáo: tỷ lệ frame có primary, range min/mean/max, SNR, histogram alert.

## Live (khi có board)

```bash
python3 -m mmdistance --config configs/default.toml live \
  --cli-port /dev/radar-cli --data-port /dev/radar-data \
  --cfg configs/profile.cfg \
  --capture captures/$(date +%Y%m%d_%H%M).bin
```

Xem [10](10-raspberry-pi.md) và [05](05-chirp-firmware.md).
