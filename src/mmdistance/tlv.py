from __future__ import annotations

import struct
from typing import Iterable

from mmdistance.models import Detection, RadarFrame

MAGIC = b"\x02\x01\x04\x03\x06\x05\x08\x07"
HEADER_LEN = 40
MAX_PACKET_LEN = 65_536
TLV_DETECTED_POINTS = 1
TLV_SIDE_INFO = 7


class ParseError(ValueError):
    pass


def extract_packets(buffer: bytearray) -> list[bytes]:
    """Pull complete mmWave SDK frames out of a rolling UART/file buffer."""
    packets: list[bytes] = []
    while True:
        start = buffer.find(MAGIC)
        if start < 0:
            if len(buffer) > 7:
                del buffer[:-7]
            break
        if start > 0:
            del buffer[:start]
        if len(buffer) < HEADER_LEN:
            break
        total = struct.unpack_from("<I", buffer, 12)[0]
        if total < HEADER_LEN or total > MAX_PACKET_LEN:
            del buffer[0]
            continue
        if len(buffer) < total:
            break
        packets.append(bytes(buffer[:total]))
        del buffer[:total]
    return packets


def iter_packets(blob: bytes) -> list[bytes]:
    buffer = bytearray(blob)
    packets = extract_packets(buffer)
    return packets


def parse_frame(packet: bytes) -> RadarFrame:
    if len(packet) < HEADER_LEN or packet[:8] != MAGIC:
        raise ParseError("missing mmWave magic word or short header")

    version, total, platform, frame_number, cpu_cycles, n_obj, n_tlv, subframe = struct.unpack_from(
        "<8I", packet, 8
    )
    if total < HEADER_LEN or total > len(packet):
        raise ParseError(f"invalid packet length {total}")

    points: list[tuple[float, float, float, float]] = []
    snrs: list[float] = []
    noises: list[float] = []
    offset = HEADER_LEN
    for _ in range(n_tlv):
        if offset + 8 > len(packet):
            break
        tlv_type, tlv_len = struct.unpack_from("<II", packet, offset)
        offset += 8
        payload = packet[offset : offset + tlv_len]
        offset += tlv_len
        if tlv_type == TLV_DETECTED_POINTS:
            for index in range(len(payload) // 16):
                points.append(struct.unpack_from("<4f", payload, index * 16))
        elif tlv_type == TLV_SIDE_INFO:
            for index in range(len(payload) // 4):
                snr_raw, noise_raw = struct.unpack_from("<hh", payload, index * 4)
                snrs.append(snr_raw / 10.0)
                noises.append(noise_raw / 10.0)

    detections = []
    count = n_obj if n_obj > 0 else len(points)
    for index in range(min(count, len(points))):
        x, y, z, vr = points[index]
        detections.append(
            Detection(
                x=x,
                y=y,
                z=z,
                vr=vr,
                snr_db=snrs[index] if index < len(snrs) else None,
                noise_db=noises[index] if index < len(noises) else None,
            )
        )

    return RadarFrame(
        frame_number=frame_number,
        detections=detections,
        platform=platform,
        version=version,
        num_tlvs=n_tlv,
        subframe=subframe,
        cpu_cycles=cpu_cycles,
    )


def encode_frame(
    frame_number: int,
    detections: Iterable[Detection],
    *,
    platform: int = 0xA6843,
    version: int = 0x03040000,
    include_side_info: bool = True,
) -> bytes:
    """Build a padded OOB-style packet. Used by tests and the simulator."""
    dets = list(detections)
    points = b"".join(struct.pack("<4f", det.x, det.y, det.z, det.vr) for det in dets)
    tlvs = struct.pack("<II", TLV_DETECTED_POINTS, len(points)) + points
    n_tlv = 1
    if include_side_info:
        side = b"".join(
            struct.pack(
                "<hh",
                int(round((det.snr_db or 0.0) * 10)),
                int(round((det.noise_db or 0.0) * 10)),
            )
            for det in dets
        )
        tlvs += struct.pack("<II", TLV_SIDE_INFO, len(side)) + side
        n_tlv += 1

    body_len = HEADER_LEN + len(tlvs)
    pad = (32 - (body_len % 32)) % 32
    total = body_len + pad
    header = MAGIC + struct.pack(
        "<8I",
        version,
        total,
        platform,
        frame_number,
        0,
        len(dets),
        n_tlv,
        0,
    )
    return header + tlvs + (b"\x00" * pad)
