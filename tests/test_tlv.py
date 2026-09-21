from pathlib import Path

from mmdistance.models import Detection
from mmdistance.tlv import MAGIC, encode_frame, extract_packets, parse_frame
from mmdistance.uart import replay_frames, send_cfg


def test_encode_parse_roundtrip():
    original = [
        Detection(x=1.25, y=8.5, z=0.4, vr=-3.2, snr_db=12.5, noise_db=9.0),
        Detection(x=-0.5, y=4.0, z=-0.2, vr=0.1, snr_db=20.0, noise_db=8.0),
    ]
    packet = encode_frame(17, original)
    assert packet[:8] == MAGIC
    assert len(packet) % 32 == 0
    frame = parse_frame(packet)
    assert frame.frame_number == 17
    assert len(frame.detections) == 2
    first = frame.detections[0]
    assert abs(first.x - 1.25) < 1e-5
    assert abs(first.y - 8.5) < 1e-5
    assert abs(first.vr + 3.2) < 1e-5
    assert abs((first.snr_db or 0) - 12.5) < 0.15


def test_empty_frame_is_valid():
    packet = encode_frame(3, [], include_side_info=False)
    frame = parse_frame(packet)
    assert frame.detections == []
    assert frame.frame_number == 3


def test_extract_packets_resyncs_and_keeps_partial_tail():
    good = encode_frame(1, [Detection(0, 5, 0, -1, snr_db=10)])
    noise = b"\x00\xff" + MAGIC[:3]
    buffer = bytearray(b"junk" + good + noise)
    packets = extract_packets(buffer)
    assert len(packets) == 1
    assert buffer[:3] == MAGIC[:3]


def test_replay_two_frames(tmp_path: Path):
    blob = encode_frame(1, [Detection(0, 3, 0, 0, snr_db=11)]) + encode_frame(
        2, [Detection(0, 4, 0, -1, snr_db=12)]
    )
    path = tmp_path / "cap.bin"
    path.write_bytes(blob)
    frames = list(replay_frames(path))
    assert [frame.frame_number for frame in frames] == [1, 2]


class _FakeCli:
    def __init__(self):
        self.writes: list[bytes] = []
        self.in_waiting = 4
        self._reads = 0

    def write(self, data: bytes) -> None:
        self.writes.append(data)

    def flush(self) -> None:
        return None

    def read(self, _size: int) -> bytes:
        self._reads += 1
        return b"Done"


def test_send_cfg_skips_comments(tmp_path: Path):
    cfg = tmp_path / "tiny.cfg"
    cfg.write_text("% comment\n# also\n\nsensorStop\nguiMonitor -1 2 0 0 0 0 0\n")
    cli = _FakeCli()
    send_cfg(cli, cfg, timeout_s=0.2)
    assert cli.writes == [b"sensorStop\n", b"guiMonitor -1 2 0 0 0 0 0\n"]
