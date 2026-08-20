#!/usr/bin/env python3
"""Send the candidate 'connect' Function frame (pneuron.lua comment: 03 0d 00 01 00)
to the PNHU01 hub, then keep listening for a while to see if type=0x09 IMU frames
start streaming - see docs/pruebas.jsonl T013 (candidate sent, no straps attached,
got a real but unstreamed Value response) and NEXT-STEP.md ("attach straps and
repeat").

Reuses frame()/crc8() from pn-send.py instead of duplicating the CRC-8 call.

If out_file is given, every raw byte received (the immediate response plus all
streamed chunks, in order, nothing else mixed in) is also written there for later
offline decoding - e.g. with find_frames()/describe() from parse-pn-capture.py,
which work on any raw byte buffer, not just pcapng-extracted ones.

Usage: ./pn-connect.py [/dev/ttyUSB0] [baud] [listen_seconds] [out_file]
"""
import importlib.util
import os
import sys
import time

import serial

_spec = importlib.util.spec_from_file_location(
    "pn_send", os.path.join(os.path.dirname(__file__), "pn-send.py")
)
_pn_send = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pn_send)  # safe now: main() is guarded by __name__

frame = _pn_send.frame


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 921600
    listen_s = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    out_path = sys.argv[4] if len(sys.argv) > 4 else None
    out = open(out_path, "wb") if out_path else None

    # Call: id=00 src=a0(PC) dst=c0(Hub) cmd=01(Function) data=03 0d 00 01 00 ("connect?")
    call = frame(0x01, bytes([0x00, 0xa0, 0xc0, 0x01, 0x03, 0x0d, 0x00, 0x01, 0x00]))
    print(f"-> {call.hex()}")

    try:
        with serial.Serial(port, baud, timeout=1) as ser:
            ser.reset_input_buffer()
            ser.write(call)
            ser.flush()

            resp = ser.read(4096)
            if resp:
                print(f"<- {resp.hex()}  ({len(resp)} bytes)  [immediate response]")
                if out:
                    out.write(resp)
            else:
                print("<- (no immediate response)")

            print(f"listening for {listen_s:.0f}s for unsolicited streaming (type=0x09 IMU frames)...")
            deadline = time.monotonic() + listen_s
            total = 0
            imu_frames = 0
            while time.monotonic() < deadline:
                chunk = ser.read(4096)
                if not chunk:
                    continue
                total += len(chunk)
                # naive scan, good enough to flag IMU traffic - parse-pn-capture.py has
                # the real frame splitter if this needs rigorous decoding later
                imu_frames += chunk.count(b"\xfd\x09")
                print(f"<- {chunk.hex()}  ({len(chunk)} bytes)")
                if out:
                    out.write(chunk)

            print(f"done: {total} bytes total, {imu_frames} likely type=0x09 (IMU) frame starts")
            if out:
                print(f"raw bytes written to {out_path}")
    finally:
        if out:
            out.close()


if __name__ == "__main__":
    main()
