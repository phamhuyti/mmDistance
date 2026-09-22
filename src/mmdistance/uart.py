from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import BinaryIO, Iterator

from mmdistance.config import RadarPorts
from mmdistance.models import RadarFrame
from mmdistance.tlv import extract_packets, parse_frame

log = logging.getLogger(__name__)


def wait_for_port(path: str, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if Path(path).exists():
            return
        time.sleep(0.2)
    raise FileNotFoundError(f"UART port not found after {timeout_s:.0f}s: {path}")


def send_cfg(cli_port, cfg_path: str | Path, timeout_s: float = 0.4) -> None:
    """Push a Visualizer/Estimator .cfg over the CLI UART (115200)."""
    path = Path(cfg_path)
    if not path.is_file():
        raise FileNotFoundError(f"radar cfg not found: {path}")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("%") or line.startswith("#"):
            continue
        log.info("cfg> %s", line)
        cli_port.write((line + "\n").encode("ascii", errors="ignore"))
        cli_port.flush()
        deadline = time.monotonic() + timeout_s
        buf = b""
        while time.monotonic() < deadline:
            chunk = cli_port.read(cli_port.in_waiting or 1)
            if chunk:
                buf += chunk
                if b"Done" in buf or b"Ignored" in buf or b"Error" in buf:
                    break
            else:
                time.sleep(0.01)
        if b"Error" in buf:
            raise RuntimeError(f"radar rejected cfg line: {line!r} ({buf!r})")


def frames_from_bytes(chunks: Iterator[bytes], capture: BinaryIO | None = None) -> Iterator[RadarFrame]:
    buffer = bytearray()
    for chunk in chunks:
        if not chunk:
            continue
        if capture is not None:
            capture.write(chunk)
            capture.flush()
        buffer.extend(chunk)
        for packet in extract_packets(buffer):
            frame = parse_frame(packet)
            frame.captured_at = time.monotonic()
            yield frame


def live_frames(
    ports: RadarPorts,
    serial_module=None,
    capture_path: str | Path | None = None,
) -> Iterator[RadarFrame]:
    """Open CLI+data ports, send cfg, then yield parsed frames.

    serial_module is injectable so tests do not need a real UART.
    """
    if serial_module is None:
        try:
            import serial as serial_module
        except ImportError as exc:
            raise RuntimeError("pyserial is required for live capture") from exc

    wait_for_port(ports.cli_port, ports.wait_port_s)
    wait_for_port(ports.data_port, ports.wait_port_s)
    cli = serial_module.Serial(ports.cli_port, ports.cli_baud, timeout=0.2)
    data = serial_module.Serial(ports.data_port, ports.data_baud, timeout=0.2)
    capture = Path(capture_path).open("wb") if capture_path else None
    try:
        time.sleep(0.2)
        send_cfg(cli, ports.cfg_path, ports.cfg_line_timeout_s)
        yield from frames_from_bytes(_read_forever(data), capture)
    finally:
        if capture is not None:
            capture.close()
        cli.close()
        data.close()


def _read_forever(data) -> Iterator[bytes]:
    while True:
        chunk = data.read(data.in_waiting or 2048)
        if chunk:
            yield chunk


def replay_frames(path: str | Path) -> Iterator[RadarFrame]:
    blob = Path(path).read_bytes()
    buffer = bytearray(blob)
    for packet in extract_packets(buffer):
        frame = parse_frame(packet)
        yield frame
