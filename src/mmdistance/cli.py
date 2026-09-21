from __future__ import annotations

import argparse
import sys

from mmdistance.config import AppConfig
from mmdistance.outputs import CsvSink, JsonlSink, print_primary
from mmdistance.pipeline import Pipeline
from mmdistance.simulate import approaching_car_frames
from mmdistance.uart import live_frames, replay_frames


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mmdistance",
        description="Layered TI mmWave front-range pipeline (log/display only, not safety-critical).",
    )
    parser.add_argument("--config", help="TOML app config (ports, gates, tracker).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sim = sub.add_parser("simulate", help="Run a synthetic approaching-car scene (no hardware).")
    sim.add_argument("--frames", type=int, default=40)
    sim.add_argument("--dt", type=float, default=0.05)

    replay = sub.add_parser("replay", help="Parse a recorded UART capture (.bin).")
    replay.add_argument("path")

    live = sub.add_parser("live", help="Read AWR6843AOPEVM CLI+data UART on the Pi.")
    live.add_argument("--cli-port")
    live.add_argument("--data-port")
    live.add_argument("--cfg")

    args = parser.parse_args(argv)
    cfg = AppConfig.load(args.config)
    if args.cmd == "live":
        if args.cli_port:
            cfg.radar.cli_port = args.cli_port
        if args.data_port:
            cfg.radar.data_port = args.data_port
        if args.cfg:
            cfg.radar.cfg_path = args.cfg

    sinks = []
    if cfg.output.jsonl_path:
        sinks.append(JsonlSink(cfg.output.jsonl_path))
    if cfg.output.csv_path:
        sinks.append(CsvSink(cfg.output.csv_path))
    if not sinks:
        sinks.append(JsonlSink(stream=sys.stdout))

    pipe = Pipeline(cfg)
    try:
        if args.cmd == "simulate":
            frames = approaching_car_frames(n_frames=args.frames, dt=args.dt)
            dt = args.dt
            for frame in frames:
                _emit(pipe.process(frame, dt), sinks, cfg)
        elif args.cmd == "replay":
            for frame in replay_frames(args.path):
                _emit(pipe.process(frame), sinks, cfg)
        else:
            for frame in live_frames(cfg.radar):
                _emit(pipe.process(frame), sinks, cfg)
    except KeyboardInterrupt:
        return 0
    finally:
        for sink in sinks:
            close = getattr(sink, "close", None)
            if close:
                close()
    return 0


def _emit(result, sinks, cfg: AppConfig) -> None:
    if cfg.output.print_primary:
        print_primary(result)
    for sink in sinks:
        sink.emit(result)


if __name__ == "__main__":
    raise SystemExit(main())
