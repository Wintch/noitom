#!/usr/bin/env python3
"""Send a constructed Perception Neuron 0xfd...0xfe frame to the PNHU01 hub over
/dev/ttyUSB0 and print whatever comes back. Uses the CRC-8 formula recovered in
docs/05-crc8-solved.md: poly=0x07, init=0x00, over type..payload, XOR 0xFD.

Default command: GetConfig(key=HubFirmwareVersion) - chosen because we have a real
captured example of the hub answering exactly this (Ack then Data), so a response
here validates the CRC-8/framing end-to-end without guessing at "Connect" blind.

921600 baud is the confirmed working rate (docs/pruebas.jsonl T012) - 115200 gets
silence. Defaults to it; override only to re-probe other rates.

Usage: ./pn-send.py [/dev/ttyUSB0] [baud]
"""
import importlib.util
import os
import sys

import serial

# reuse crc8-search.py's build_table(poly) instead of duplicating the CRC-8 math -
# see its brute-force derivation of poly=0x07 in docs/05-crc8-solved.md.
_spec = importlib.util.spec_from_file_location(
    "crc8_search", os.path.join(os.path.dirname(__file__), "crc8-search.py")
)
_crc8_search = importlib.util.module_from_spec(_spec)
_real_argv = sys.argv
sys.argv = [sys.argv[0]]  # argv<2 -> its main() sys.exit()s harmlessly, we only want build_table
try:
    _spec.loader.exec_module(_crc8_search)
except SystemExit:
    pass
finally:
    sys.argv = _real_argv

TABLE = _crc8_search.build_table(0x07)


def crc8(data):
    crc = 0x00
    for b in data:
        crc = TABLE[crc ^ b]
    return crc ^ 0xFD


def frame(ftype, body):
    payload = bytes([ftype]) + body
    return b"\xfd" + payload + bytes([crc8(payload)]) + b"\xfe"


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 921600

    # Call: id=00 src=a0(PC) dst=c0(Hub) cmd=02(GetConfig) payload=key(01=HubFirmwareVersion)+4 zero bytes
    call = frame(0x01, bytes([0x00, 0xa0, 0xc0, 0x02, 0x01, 0x02, 0x00, 0x00, 0x00]))
    print(f"-> {call.hex()}")

    with serial.Serial(port, baud, timeout=1) as ser:
        ser.reset_input_buffer()
        ser.write(call)
        ser.flush()
        resp = ser.read(4096)  # waits up to `timeout` (real responses are ~13-28 bytes,
        # well under 4096, so this always waits the full second - kept short on purpose)
        if resp:
            print(f"<- {resp.hex()}  ({len(resp)} bytes)")
        else:
            print("<- (no response)")


if __name__ == "__main__":
    main()
