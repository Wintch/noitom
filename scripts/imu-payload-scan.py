#!/usr/bin/env python3
"""Scan the 31-byte type=0x09 IMU payload (docs/01) for a byte-aligned int16 triplet
whose magnitude sqrt(x^2+y^2+z^2) stays roughly constant while the sensor is rotated -
the same anchor T010 used for CRC-8 ("find the constant in real data"), applied here
per NEXT-STEP.md's Path A. A near-constant magnitude under rotation is the signature
of accelerometer (~1g, gravity) or magnetometer (local field) - gyro would instead
swing in magnitude with rotation *rate*, not stay flat, and pure counters/status bytes
wouldn't reconstruct a stable 3D vector at all.

Only trusts CRC-8-valid frames (docs/05's poly=0x07/init=0x00/XOR 0xFD) - the naive
0xfd/0xfe framing in find_frames() alone produces real noise at volume (T020/T021's
caveat); this is the fix, not a bigger sample of unfiltered frames.

Usage: ./imu-payload-scan.py capture.pcapng [capture2.bin ...]
  Accepts both .pcapng (parsed via parse-pn-capture.py's usb_packets) and raw .bin
  dumps (from pn-connect.py/pn-meter.py's out_file). Reports the lowest-CoV triplet
  offset/endianness/signedness per input file, for every distinct node id seen.
"""
import importlib.util
import os
import struct
import statistics as st
import sys
from collections import Counter, defaultdict

_here = os.path.dirname(__file__)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    real_argv = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    finally:
        sys.argv = real_argv
    return mod


_parse = _load("parse_pn_capture", os.path.join(_here, "parse-pn-capture.py"))
_pn_send = _load("pn_send", os.path.join(_here, "pn-send.py"))

find_frames = _parse.find_frames
usb_packets = _parse.usb_packets
crc8 = _pn_send.crc8

PAYLOAD_LEN = 31
FRAME_LEN = 6 + PAYLOAD_LEN  # fd + type + counter + node + payload + crc + fe


def _valid_imu(frame):
    return (
        len(frame) == FRAME_LEN
        and frame[1] == 0x09
        and crc8(frame[1:-2]) == frame[-2]
    )


def load_imu_frames(path):
    if path.endswith((".pcapng", ".pcap")):
        seen = set()
        out = []
        for _dev, _ep, _xfer, data in usb_packets(path):
            if not data or 0xFD not in data:
                continue
            for frame in find_frames(data):
                h = frame.hex()
                if h in seen:
                    continue
                seen.add(h)
                if _valid_imu(frame):
                    out.append(frame)
        return out
    with open(path, "rb") as f:
        buf = f.read()
    return [f for f in find_frames(buf) if _valid_imu(f)]


def payload(frame):
    return frame[4:35]


def scan_node(frames):
    best = []
    for offset in range(0, PAYLOAD_LEN - 6 + 1):
        for endian, fmt_s, fmt_u in (("LE", "<hhh", "<HHH"), ("BE", ">hhh", ">HHH")):
            for fmt, signed in ((fmt_s, True), (fmt_u, False)):
                mags = []
                for f in frames:
                    x, y, z = struct.unpack_from(fmt, payload(f), offset)
                    mags.append((x * x + y * y + z * z) ** 0.5)
                mean = st.mean(mags)
                if mean == 0:
                    continue
                cov = st.pstdev(mags) / mean
                best.append((cov, offset, endian, signed, mean))
    best.sort(key=lambda t: t[0])
    return best


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        print(f"\n{'='*78}\n  {path}\n{'='*78}")
        frames = load_imu_frames(path)
        by_node = defaultdict(list)
        for f in frames:
            by_node[f[3]].append(f)
        print(f"  CRC-valid IMU frames: {len(frames)}  nodes: "
              f"{dict(Counter(f[3] for f in frames))}")
        for node, nframes in sorted(by_node.items()):
            print(f"\n  -- node 0x{node:02x} ({len(nframes)} frames) --")
            ranked = scan_node(nframes)
            for cov, offset, endian, signed, mean in ranked[:5]:
                print(f"    offset={offset:2d} {endian} {'signed' if signed else 'unsigned':8s} "
                      f"mean_mag={mean:9.1f}  CoV={cov:.4f}")


main()
