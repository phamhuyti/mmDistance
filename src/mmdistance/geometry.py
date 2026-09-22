from __future__ import annotations

import math

from mmdistance.config import MountConfig
from mmdistance.models import Detection


def transform_detection(det: Detection, mount: MountConfig) -> Detection:
    """Map a point from the sensor frame into the vehicle frame.

    Intuitive sign convention (documented in docs/08):
    - yaw_deg > 0: board aimed to the vehicle's right (+X)
    - pitch_deg > 0: board aimed up (+Z)
    - roll_deg > 0: clockwise when looking forward
    """
    x, y, z = _apply(_mount_matrix(mount), det.x, det.y, det.z)
    return Detection(
        x=x,
        y=y,
        z=z,
        vr=det.vr,
        snr_db=det.snr_db,
        noise_db=det.noise_db,
    )


def transform_detections(dets: list[Detection], mount: MountConfig) -> list[Detection]:
    if mount.is_identity():
        return dets
    return [transform_detection(det, mount) for det in dets]


def _mount_matrix(mount: MountConfig) -> tuple[tuple[float, float, float], ...]:
    return _mul(
        _rz(-mount.yaw_deg),
        _mul(_rx(mount.pitch_deg), _ry(mount.roll_deg)),
    )


def _rx(deg: float) -> tuple[tuple[float, float, float], ...]:
    c, s = _cs(deg)
    return (
        (1.0, 0.0, 0.0),
        (0.0, c, -s),
        (0.0, s, c),
    )


def _ry(deg: float) -> tuple[tuple[float, float, float], ...]:
    c, s = _cs(deg)
    return (
        (c, 0.0, s),
        (0.0, 1.0, 0.0),
        (-s, 0.0, c),
    )


def _rz(deg: float) -> tuple[tuple[float, float, float], ...]:
    c, s = _cs(deg)
    return (
        (c, -s, 0.0),
        (s, c, 0.0),
        (0.0, 0.0, 1.0),
    )


def _cs(deg: float) -> tuple[float, float]:
    angle = math.radians(deg)
    return math.cos(angle), math.sin(angle)


def _mul(
    a: tuple[tuple[float, float, float], ...],
    b: tuple[tuple[float, float, float], ...],
) -> tuple[tuple[float, float, float], ...]:
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3)
    )


def _apply(
    r: tuple[tuple[float, float, float], ...],
    x: float,
    y: float,
    z: float,
) -> tuple[float, float, float]:
    return (
        r[0][0] * x + r[0][1] * y + r[0][2] * z,
        r[1][0] * x + r[1][1] * y + r[1][2] * z,
        r[2][0] * x + r[2][1] * y + r[2][2] * z,
    )
