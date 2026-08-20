#!/usr/bin/env python3
"""Live IMU 'meter': send Connect (03 0d 00 01 00, T015) then keep listening and
print a running per-node-id frame-rate + last-raw-payload readout, once a second,
until stopped or listen_seconds elapses. Meant for eyeballing "is this sensor still
streaming, steadily, right now" while physically holding/placing it - not a decode
tool. Reuses find_frames()/frame() instead of re-deriving framing or CRC-8.

Also writes every raw byte received to out_file (default linux-kit/capturas/
meter-live.bin) for later offline decoding, same convention as pn-connect.py.

Usage: ./pn-meter.py [/dev/ttyUSB0] [baud] [listen_seconds] [out_file]
"""
import collections
import importlib.util
import os
import sys
import time

import serial

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


_pn_send = _load("pn_send", os.path.join(_here, "pn-send.py"))
_parse = _load("parse_pn_capture", os.path.join(_here, "parse-pn-capture.py"))

frame = _pn_send.frame
find_frames = _parse.find_frames


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 921600
    listen_s = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0
    out_path = sys.argv[4] if len(sys.argv) > 4 else "linux-kit/capturas/meter-live.bin"
    out = open(out_path, "wb")

    call = frame(0x01, bytes([0x00, 0xa0, 0xc0, 0x01, 0x03, 0x0d, 0x00, 0x01, 0x00]))
    print(f"-> connect {call.hex()}", flush=True)

    counts = collections.Counter()
    last_payload = {}
    buf = b""

    try:
        with serial.Serial(port, baud, timeout=0.2) as ser:
            ser.reset_input_buffer()
            ser.write(call)
            ser.flush()

            deadline = time.monotonic() + listen_s
            next_report = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                chunk = ser.read(4096)
                if chunk:
                    out.write(chunk)
                    buf += chunk
                    # keep buf from growing unbounded; find_frames scans in place
                    if len(buf) > 1 << 20:
                        buf = buf[-4096:]
                    for f in find_frames(chunk):
                        if len(f) > 4 and f[1] == 0x09:
                            node = f[3]
                            counts[node] += 1
                            last_payload[node] = f[4:-2].hex()

                now = time.monotonic()
                if now >= next_report:
                    next_report = now + 1.0
                    if counts:
                        parts = ", ".join(
                            f"node 0x{n:02x}: {c}/s last={last_payload[n]}"
                            for n, c in sorted(counts.items())
                        )
                        print(parts, flush=True)
                    else:
                        print("(no IMU frames yet)", flush=True)
                    counts.clear()
    finally:
        out.close()
        print(f"raw bytes written to {out_path}")


if __name__ == "__main__":
    main()
