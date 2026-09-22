import json

from mmdistance.analyze import load_jsonl, summarize_results
from mmdistance.cli import main
from mmdistance.dashboard import ResultHub, start_dashboard
from mmdistance.tlv import describe_packet, encode_frame
from mmdistance.models import Detection
from mmdistance.uart import frames_from_bytes


def test_inspect_and_analyze_cli(tmp_path, capsys):
    bin_path = tmp_path / "cap.bin"
    jsonl_path = tmp_path / "run.jsonl"
    html_path = tmp_path / "report.html"
    assert main(["simulate", "--frames", "12", "--write-bin", str(bin_path)]) == 0
    capsys.readouterr()
    assert bin_path.is_file() and bin_path.stat().st_size > 0
    assert main(["inspect", str(bin_path), "--index", "0"]) == 0
    inspect_out = capsys.readouterr().out
    assert "magic" in inspect_out
    assert "Detected Points" in inspect_out

    jsonl_path.write_text(
        json.dumps(
            {
                "frame": 1,
                "n_raw": 6,
                "n_filtered": 2,
                "primary": {"range_m": 10.0, "vr": -4.0, "snr_db": 12.0},
                "alert": {"level": "warn"},
            }
        )
        + "\n"
    )
    assert main(["analyze", str(jsonl_path), "--html", str(html_path)]) == 0
    report = capsys.readouterr().out
    assert "detect_rate" not in report or "100" in report
    assert "Số frame" in report
    assert html_path.is_file()
    stats = summarize_results(load_jsonl(jsonl_path))
    assert stats["n_with_primary"] == 1
    assert stats["range_mean_m"] == 10.0


def test_doctor_runs(capsys):
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "simulate          OK" in out


def test_describe_packet_lists_side_info():
    packet = encode_frame(3, [Detection(0.2, 5.0, 0.1, -2.0, snr_db=11.5, noise_db=8.0)])
    text = describe_packet(packet)
    assert "frameNumber        3" in text
    assert "snr=11.5 dB" in text


def test_frames_from_bytes_can_capture(tmp_path):
    packet = encode_frame(1, [Detection(0, 4, 0, 0, snr_db=10)])
    out = tmp_path / "raw.bin"
    with out.open("wb") as capture:
        frames = list(frames_from_bytes(iter([b"xx", packet]), capture))
    assert len(frames) == 1
    assert frames[0].frame_number == 1
    assert frames[0].captured_at is not None
    assert out.read_bytes().endswith(packet) or packet in out.read_bytes()


def test_dashboard_api():
    hub = ResultHub()
    hub.publish({"frame": 1, "primary": {"range_m": 9.5}})
    server = start_dashboard(hub, "127.0.0.1", 0)
    host, port = server.server_address[:2]
    import urllib.request

    try:
        latest = json.loads(urllib.request.urlopen(f"http://{host}:{port}/api/latest", timeout=2).read())
        page = urllib.request.urlopen(f"http://{host}:{port}/", timeout=2).read().decode("utf-8")
    finally:
        server.shutdown()
    assert latest["primary"]["range_m"] == 9.5
    assert "mmDistance" in page
    assert "không nối phanh" in page.lower() or "Không nối phanh" in page
