# 14 — Thuật ngữ

| Thuật ngữ | Nghĩa trong dự án |
|---|---|
| **AOP** | Antenna-on-package — anten dán trên chip, FoV rộng, gain thấp |
| **EVM** | Evaluation module — board thử, không phải sản phẩm xe |
| **OOB demo** | Firmware mẫu TI, ra point cloud UART |
| **Chirp** | Một nhịp FMCW tăng tần số |
| **Frame** | Một cụm chirp → một packet TLV |
| **TLV** | Type-Length-Value trong UART |
| **CLI / Data port** | 115200 text cfg / 921600 binary |
| **Rmax / vmax** | Tầm / tốc độ unambiguous của **cấu hình**, không phải của anten |
| **ΔR** | Range resolution \(c/(2B)\) |
| **CFAR** | Ngưỡng phát hiện thích nghi nhiễu |
| **SNR** | Tín hiệu / nhiễu; ở TLV 7 đơn vị 0.1 dB |
| **RCS** | Mặt phản xạ; xe lớn >> người |
| **FoV** | Góc nhìn anten |
| **Azimuth / elevation** | Góc ngang / dọc từ boresight |
| **vr** | Vận tốc xuyên tâm; âm ≈ lại gần |
| **Clutter** | Echo không phải mục tiêu (đất, lan can…) |
| **Primary** | Track được chọn là “xe phía trước” |
| **Ego speed** | Tốc độ xe mang radar |
| **Gate** | Bán kính (m) để gán cluster cho track |
| **PoC** | Proof of concept — chứng minh học được, không chứng minh an toàn |
| **ACC / AEB** | Cruise thích nghi / phanh khẩn — **không** phải repo này |
