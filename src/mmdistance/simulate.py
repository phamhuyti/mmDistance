from __future__ import annotations

from typing import Iterator

from mmdistance.models import Detection, RadarFrame
from mmdistance.tlv import encode_frame


def approaching_car_frames(
    n_frames: int = 40,
    dt: float = 0.05,
    start_range_m: float = 22.0,
    vr: float = -6.0,
    include_clutter: bool = True,
) -> Iterator[RadarFrame]:
    """Synthetic scene: one car on boresight plus wide-FoV clutter."""
    range_m = start_range_m
    for frame_number in range(1, n_frames + 1):
        yield RadarFrame(frame_number=frame_number, detections=_scene(range_m, vr, include_clutter))
        range_m = max(2.0, range_m + vr * dt)


def static_target_frames(
    range_m: float,
    n_frames: int = 30,
    snr_db: float = 16.0,
) -> Iterator[RadarFrame]:
    """Parked-car / corner-reflector scene used for range-gate experiments."""
    for frame_number in range(1, n_frames + 1):
        yield RadarFrame(
            frame_number=frame_number,
            detections=[
                Detection(x=0.1, y=range_m, z=0.35, vr=0.0, snr_db=snr_db, noise_db=12.0),
                Detection(x=-0.15, y=range_m + 0.25, z=0.3, vr=0.05, snr_db=snr_db - 3, noise_db=12.0),
                Detection(x=7.5, y=8.0, z=0.2, vr=0.0, snr_db=11.0, noise_db=12.0),
            ],
        )


def encode_simulation(frames: list[RadarFrame]) -> bytes:
    return b"".join(encode_frame(frame.frame_number, frame.detections) for frame in frames)


def _scene(range_m: float, vr: float, include_clutter: bool) -> list[Detection]:
    detections = [
        Detection(x=0.15, y=range_m, z=0.4, vr=vr, snr_db=18.0, noise_db=12.0),
        Detection(x=-0.2, y=range_m + 0.4, z=0.35, vr=vr + 0.2, snr_db=14.0, noise_db=12.0),
    ]
    if include_clutter:
        detections.extend(
            [
                Detection(x=8.0, y=12.0, z=0.2, vr=-0.1, snr_db=11.0, noise_db=12.0),
                Detection(x=-6.5, y=9.0, z=-0.1, vr=0.2, snr_db=10.0, noise_db=12.0),
                Detection(x=0.3, y=4.0, z=-1.2, vr=0.0, snr_db=16.0, noise_db=12.0),
                Detection(x=0.1, y=30.0, z=4.5, vr=-1.0, snr_db=7.0, noise_db=12.0),
            ]
        )
    return detections
