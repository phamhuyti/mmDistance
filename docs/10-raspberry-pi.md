# 10 — Cài trên Raspberry Pi

Giả sử Pi 4, Raspberry Pi OS 64-bit, Python 3.11+.

## Cài code

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git
git clone <repo> ~/mmDistance
cd ~/mmDistance
python3 -m pip install -e .
```

## udev

```bash
sudo cp deploy/99-ti-mmwave.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -l /dev/radar-*
```

User `pi` cần nhóm `dialout`: `sudo usermod -aG dialout pi` rồi logout.

## systemd

Sửa `WorkingDirectory`, user, và `cfg_path` trong unit cho khớp máy.

```bash
sudo cp deploy/mmdistance.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mmdistance
journalctl -u mmdistance -f
```

Service `Restart=always`: USB rớt khi rung thì tự mở lại (kèm `wait_port_s`).

Muốn dashboard: thêm `--dashboard 8080` vào `ExecStart` và mở firewall cẩn thận (chỉ LAN).

## Thẻ SD

Tắt máy xe = mất điện. Bật overlayfs / read-only root (raspi-config hoặc `overlayroot`). Ghi JSONL/SQLite ra **USB disk**, không ra thẻ.

Nguồn: DC-DC có tụ, không share với máy nén/đề trực tiếp qua dây mỏng.

## `speed_file`

Process GPS ghi một số (m/s) vào `/tmp/ego_speed`:

```toml
[ego]
speed_file = "/tmp/ego_speed"
```

Pipeline đọc mỗi frame. Sai số vài m/s vẫn đủ để loại biển báo.
