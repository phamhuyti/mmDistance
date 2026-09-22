from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import time

from mmdistance.analyze import html_report, load_jsonl, summarize_results, text_report
from mmdistance.config import AppConfig
from mmdistance.dashboard import ResultHub, start_dashboard
from mmdistance.doctor import run_doctor
from mmdistance.outputs import CsvSink, GpioAlertSink, JsonlSink, SqliteSink, print_primary
from mmdistance.pipeline import Pipeline
from mmdistance.simulate import approaching_car_frames, encode_simulation, static_target_frames
from mmdistance.tlv import describe_packet, extract_packets
from mmdistance.uart import live_frames, replay_frames


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mmdistance",
        description="PoC đo khoảng cách xe phía trước (log/hiển thị, không an toàn chức năng).",
    )
    parser.add_argument("--config", help="TOML: cổng UART, lọc, tracker, cảnh báo.")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sim = sub.add_parser("simulate", help="Cảnh xe lại gần (không cần radar).")
    sim.add_argument("--frames", type=int, default=40)
    sim.add_argument("--dt", type=float, default=0.05)
    sim.add_argument("--start-range", type=float, default=22.0)
    sim.add_argument("--vr", type=float, default=-6.0)
    sim.add_argument("--static-range", type=float, help="Thay bằng mục tiêu đứng yên ở khoảng cách này.")
    sim.add_argument("--write-bin", help="Ghi UART giả lập ra file .bin để luyện replay.")

    replay = sub.add_parser("replay", help="Phát lại capture UART (.bin).")
    replay.add_argument("path")

    live = sub.add_parser("live", help="Đọc AWR6843AOPEVM trên Pi.")
    live.add_argument("--cli-port")
    live.add_argument("--data-port")
    live.add_argument("--cfg")
    live.add_argument("--capture", help="Ghi raw UART ra file .bin")
    live.add_argument("--dashboard", type=int, metavar="PORT", help="Mở dashboard HTTP tại cổng này.")

    sub.add_parser("doctor", help="Kiểm tra Python, cfg, simulate.")

    inspect = sub.add_parser("inspect", help="Giải thích từng byte TLV trong file .bin.")
    inspect.add_argument("path")
    inspect.add_argument("--index", type=int, default=0, help="Frame thứ mấy (0-based).")

    analyze = sub.add_parser("analyze", help="Tóm tắt file JSONL đã ghi.")
    analyze.add_argument("path")
    analyze.add_argument("--html")

    serve = sub.add_parser("serve", help="Dashboard HTTP + simulate/replay.")
    serve.add_argument("--source", choices=("simulate", "replay"), default="simulate")
    serve.add_argument("--path", help="File .bin khi source=replay")
    serve.add_argument("--frames", type=int, default=80)
    serve.add_argument("--dt", type=float, default=0.05)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    cfg = AppConfig.load(args.config)
    _apply_live_overrides(args, cfg)

    if args.cmd == "doctor":
        return run_doctor(cfg)
    if args.cmd == "inspect":
        return _inspect(args.path, args.index)
    if args.cmd == "analyze":
        return _analyze(args.path, args.html)
    if args.cmd == "serve":
        return _serve(args, cfg)

    if args.cmd == "simulate" and args.write_bin:
        frames = list(_sim_frames(args))
        Path(args.write_bin).parent.mkdir(parents=True, exist_ok=True)
        Path(args.write_bin).write_bytes(encode_simulation(frames))

    sinks = _build_sinks(cfg)
    pipe = Pipeline(cfg)
    hub = None
    server = None
    if args.cmd == "live" and getattr(args, "dashboard", None):
        hub = ResultHub()
        server = start_dashboard(hub, "0.0.0.0", args.dashboard)
        print(f"Dashboard http://0.0.0.0:{args.dashboard}", file=sys.stderr)

    try:
        dt = args.dt if args.cmd == "simulate" else None
        for frame in _source_frames(args, cfg):
            result = pipe.process(frame, dt)
            _emit(result, sinks, cfg)
            if hub is not None:
                hub.publish(result.as_dict())
    except KeyboardInterrupt:
        return 0
    finally:
        for sink in sinks:
            close = getattr(sink, "close", None)
            if close:
                close()
        if server is not None:
            server.shutdown()
    return 0


def _apply_live_overrides(args, cfg: AppConfig) -> None:
    if args.cmd != "live":
        return
    if args.cli_port:
        cfg.radar.cli_port = args.cli_port
    if args.data_port:
        cfg.radar.data_port = args.data_port
    if args.cfg:
        cfg.radar.cfg_path = args.cfg


def _sim_frames(args):
    if getattr(args, "static_range", None) is not None:
        return static_target_frames(args.static_range, n_frames=args.frames)
    return approaching_car_frames(
        n_frames=args.frames,
        dt=args.dt,
        start_range_m=getattr(args, "start_range", 22.0),
        vr=getattr(args, "vr", -6.0),
    )


def _source_frames(args, cfg: AppConfig):
    if args.cmd == "simulate":
        return _sim_frames(args)
    if args.cmd == "replay":
        return replay_frames(args.path)
    return live_frames(cfg.radar, capture_path=getattr(args, "capture", None))


def _build_sinks(cfg: AppConfig, stdout_fallback: bool = True) -> list:
    sinks = []
    if cfg.output.jsonl_path:
        sinks.append(JsonlSink(cfg.output.jsonl_path))
    if cfg.output.csv_path:
        sinks.append(CsvSink(cfg.output.csv_path))
    if cfg.output.sqlite_path:
        sinks.append(SqliteSink(cfg.output.sqlite_path))
    if cfg.alert.gpio_warn_pin or cfg.alert.gpio_danger_pin:
        sinks.append(GpioAlertSink(cfg.alert))
    if not sinks and stdout_fallback:
        sinks.append(JsonlSink(stream=sys.stdout))
    return sinks


def _emit(result, sinks, cfg: AppConfig) -> None:
    if cfg.output.print_primary:
        print_primary(result)
    for sink in sinks:
        sink.emit(result)


def _inspect(path: str, index: int) -> int:
    packets = extract_packets(bytearray(Path(path).read_bytes()))
    if not packets:
        print("Không tìm thấy frame TLV trong file.", file=sys.stderr)
        return 1
    if index < 0 or index >= len(packets):
        print(f"index={index} ngoài phạm vi 0..{len(packets) - 1}", file=sys.stderr)
        return 1
    print(f"File có {len(packets)} frame; đang xem frame #{index}\n")
    print(describe_packet(packets[index]))
    return 0


def _analyze(path: str, html_path: str | None) -> int:
    rows = load_jsonl(path)
    stats = summarize_results(rows)
    print(text_report(stats))
    if html_path:
        Path(html_path).write_text(html_report(stats, rows), encoding="utf-8")
        print(f"Đã ghi {html_path}", file=sys.stderr)
    return 0


def _serve(args, cfg: AppConfig) -> int:
    hub = ResultHub()
    server = start_dashboard(hub, args.host, args.port)
    print(f"Dashboard http://{args.host}:{args.port}", file=sys.stderr)
    print("PoC tham khảo — Ctrl+C để thoát.", file=sys.stderr)
    pipe = Pipeline(cfg)
    sinks = _build_sinks(cfg, stdout_fallback=False)
    if args.source == "replay":
        if not args.path:
            print("--path bắt buộc khi source=replay", file=sys.stderr)
            return 2
        frames = list(replay_frames(args.path))
        dt = cfg.tracker.default_dt
    else:
        frames = list(approaching_car_frames(n_frames=args.frames, dt=args.dt))
        dt = args.dt
    try:
        while True:
            for frame in frames:
                result = pipe.process(frame, dt)
                _emit(result, sinks, cfg)
                hub.publish(result.as_dict())
                time.sleep(dt)
            if args.source == "simulate":
                pipe = Pipeline(cfg)
            else:
                break
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        server.shutdown()
        for sink in sinks:
            close = getattr(sink, "close", None)
            if close:
                close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
