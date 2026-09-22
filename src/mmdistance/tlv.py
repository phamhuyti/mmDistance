from __future__ import annotations

import struct
from typing import Iterable

from mmdistance.models import Detection, RadarFrame

MAGIC = b"\x02\x01\x04\x03\x06\x05\x08\x07"
HEADER_LEN = 40
MAX_PACKET_LEN = 65_536
TLV_DETECTED_POINTS = 1
TLV_SIDE_INFO = 7

TLV_NAMES = {
    1: "Detected Points (x,y,z,vr float32)",
    2: "Range profile",
    3: "Noise profile",
    4: "Azimuth heatmap",
    5: "Range-Doppler heatmap",
    6: "Statistics",
    7: "Side info (SNR, noise) 0.1 dB",
    8: "Azimuth/elevation heatmap (AOP/ODS)",
    9: "Temperature stats",
}


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
    return extract_packets(buffer)


def parse_frame(packet: bytes) -> RadarFrame:
    header = parse_header(packet)
    points: list[tuple[float, float, float, float]] = []
    snrs: list[float] = []
    noises: list[float] = []
    offset = HEADER_LEN
    for _ in range(header["num_tlvs"]):
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
    count = header["num_obj"] if header["num_obj"] > 0 else len(points)
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
        frame_number=header["frame_number"],
        detections=detections,
        platform=header["platform"],
        version=header["version"],
        num_tlvs=header["num_tlvs"],
        subframe=header["subframe"],
        cpu_cycles=header["cpu_cycles"],
    )


def parse_header(packet: bytes) -> dict[str, int]:
    if len(packet) < HEADER_LEN or packet[:8] != MAGIC:
        raise ParseError("missing mmWave magic word or short header")
    version, total, platform, frame_number, cpu_cycles, n_obj, n_tlv, subframe = struct.unpack_from(
        "<8I", packet, 8
    )
    if total < HEADER_LEN or total > len(packet):
        raise ParseError(f"invalid packet length {total}")
    return {
        "version": version,
        "total": total,
        "platform": platform,
        "frame_number": frame_number,
        "cpu_cycles": cpu_cycles,
        "num_obj": n_obj,
        "num_tlvs": n_tlv,
        "subframe": subframe,
    }


def describe_packet(packet: bytes) -> str:
    """Human-readable walkthrough of one OOB UART frame (for learning)."""
    header = parse_header(packet)
    lines = [
        f"magic              {packet[:8].hex(' ')}  (luôn là 02 01 04 03 06 05 08 07)",
        f"version            0x{header['version']:08x}",
        f"totalPacketLen     {header['total']} bytes (kể cả pad 32-byte)",
        f"platform           0x{header['platform']:x}",
        f"frameNumber        {header['frame_number']}",
        f"timeCpuCycles      {header['cpu_cycles']}",
        f"numDetectedObj     {header['num_obj']}",
        f"numTLVs            {header['num_tlvs']}",
        f"subFrameNumber     {header['subframe']}",
        "",
    ]
    offset = HEADER_LEN
    for tlv_index in range(header["num_tlvs"]):
        if offset + 8 > len(packet):
            lines.append(f"TLV #{tlv_index}: header bị cắt")
            break
        tlv_type, tlv_len = struct.unpack_from("<II", packet, offset)
        name = TLV_NAMES.get(tlv_type, "unknown")
        lines.append(f"TLV #{tlv_index}  type={tlv_type} ({name})  length={tlv_len}")
        payload = packet[offset + 8 : offset + 8 + tlv_len]
        if tlv_type == TLV_DETECTED_POINTS:
            for obj in range(len(payload) // 16):
                x, y, z, vr = struct.unpack_from("<4f", payload, obj * 16)
                rng = (x * x + y * y + z * z) ** 0.5
                lines.append(
                    f"  obj{obj:02d}  x={x:7.3f}  y={y:7.3f}  z={z:7.3f}  "
                    f"vr={vr:7.3f}  range={rng:7.3f}"
                )
        elif tlv_type == TLV_SIDE_INFO:
            for obj in range(len(payload) // 4):
                snr, noise = struct.unpack_from("<hh", payload, obj * 4)
                lines.append(
                    f"  obj{obj:02d}  snr={snr / 10:.1f} dB  noise={noise / 10:.1f} dB "
                    f"(raw int16 / 10)"
                )
        else:
            preview = payload[:16].hex(" ")
            lines.append(f"  payload[{tlv_len} bytes] head={preview}")
        offset += 8 + tlv_len
    pad = len(packet) - offset
    if pad:
        lines.append(f"padding            {pad} bytes (sao cho tổng chia hết 32)")
    return "\n".join(lines)


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
