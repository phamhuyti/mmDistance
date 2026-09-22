# Cheatsheet

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
python3 -m mmdistance doctor

python3 -m mmdistance simulate --frames 40
python3 -m mmdistance simulate --static-range 10 --frames 30
python3 -m mmdistance simulate --write-bin examples/approaching_car.bin

python3 -m mmdistance inspect examples/approaching_car.bin --index 0
python3 -m mmdistance replay examples/approaching_car.bin
python3 -m mmdistance serve --port 8080

python3 -m mmdistance --config configs/default.toml live \
  --cfg configs/profile.cfg --capture captures/run.bin --dashboard 8080

python3 -m mmdistance analyze logs/run.jsonl --html logs/report.html
```

Baud: CLI 115200, Data 921600. `guiMonitor -1 2 0 0 0 0 0`.

Trục: +X phải, +Y trước, +Z lên. `vr < 0` ≈ lại gần.

Không nối phanh/ga.
