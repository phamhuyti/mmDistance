# 12 — Đổi board

AOP là bước học, không phải radar ACC.

## Giữ nguyên

`Detection`, `filters`, `cluster`, `tracker`, `alerts`, `outputs`, dashboard, TOML (trừ baud/cổng).

## Viết lại

| Board | Ghi chú |
|---|---|
| **IWR6843ISK** | Cùng 60 GHz, antenna **gain cao hơn**, FoV hẹp hơn. TLV OOB gần như giữ. Đáng thử trước khi lên 77 GHz. |
| **AWR1843BOOST** | 76–81 GHz, gần use-case xe hơn. Adapter UART/TLV tương tự OOB; kiểm tra SDK version. |
| **AWR2944 / mới hơn** | Đọc output format; đừng giả định type 1 = 16-byte float. |
| **AWR2243** | RF frontend, raw ADC — **không** phải “đổi `uart_reader`”. Cần host radar khác hẳn. |

## Checklist adapter mới

1. Magic / header có giống 40 byte không?
2. Point struct: float hay Q-format?
3. SNR có TLV 7 không, đơn vị 0.1 dB?
4. Dấu `vr`, trục X/Y có đổi không? Map về +X phải +Y trước trong adapter.
5. Baud / số cổng / USB vs SPI.
6. Ghim **version SDK + file cfg** vào git.

Interface nội bộ muốn giữ:

```text
Detection {x, y, z, vr, snr_db}
Track     {id, range_m, vr, age, confidence/static}
```
