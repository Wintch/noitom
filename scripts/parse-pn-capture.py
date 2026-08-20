#!/usr/bin/env python3
"""Parses USBPcap (Windows) pcapng captures looking for Perception Neuron v1 frames.

Reuses the dependency-free pcapng/USBPcap reader from
../../reverb-g2/scripts/parse-usbpcap.py (same format, different protocol on top).

Perception Neuron framing (from pelrun/perceptionneuron's pneuron.lua, byte-exact):
  0xfd SOF | type(1) | ... | crc8(1) | 0xfe EOF

type 0x01 "Call" body: id(1) src(1) dst(1) cmd(1) then either
  cmd==0x02: key(1) + data(4)
  else:      data(5)
Known cmd=0x01 ("Function") data payloads from the dissector's comments:
  03 0d 00 01 00   connect?
  02 00 00 00 00   disconnect?  (NB: comment shows "01 02 00 00 00 00" - leading 01 is
                                  the cmd byte per the `commands` table, not the type)
  03 02 00 00 00   -> triggers a 0x71 (Node Firmware Versions) response
  03 07 00 00 00   -> triggers a 0x73 (Node Serial Numbers) response
cmd=0x02 ("Get config"): key(1) + 4 bytes, e.g. key=0x18 "Wifi Config"

Usage: ./parse-pn-capture.py capture.pcapng [another.pcapng ...]
"""
import struct
import sys
import collections

EPB = 0x00000006
SHB = 0x0A0D0D0A

TYPES = {
    0x01: "Call", 0x02: "Ack", 0x03: "Value", 0x04: "Data",
    0x07: "FirmwareUpload", 0x09: "IMUdata", 0x0a: "Set",
}
CMDS = {0x01: "Function", 0x02: "GetConfig"}
KEYS = {
    0x01: "HubFirmwareVersion", 0x15: "HubSerialNumber", 0x18: "WifiConfig",
    0x19: "ServerConfig", 0x30: "WifiScan", 0x71: "NodeFirmwareVersions",
    0x73: "NodeSerialNumbers", 0x7c: "NodeSerialNumbers",
}


def usb_packets(path):
    """Yields (device, endpoint, transfer, data) for each USB packet in the capture."""
    with open(path, "rb") as f:
        head = f.read(12)
        if len(head) < 12:
            return
        btype = struct.unpack("<I", head[0:4])[0]
        if btype != SHB:
            print(f"  !! {path}: does not start with a Section Header Block", file=sys.stderr)
            return
        bom = struct.unpack("<I", head[8:12])[0]
        endi = "<" if bom == 0x1A2B3C4D else ">"
        blen = struct.unpack(endi + "I", head[4:8])[0]
        f.seek(blen)

        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                return
            btype, blen = struct.unpack(endi + "II", hdr)
            if blen < 12:
                return
            body = f.read(blen - 12)
            f.read(4)
            if btype != EPB or len(body) < 20:
                continue
            caplen = struct.unpack(endi + "I", body[12:16])[0]
            pkt = body[20:20 + caplen]
            if len(pkt) < 27:
                continue
            header_len = struct.unpack(endi + "H", pkt[0:2])[0]
            device = struct.unpack(endi + "H", pkt[19:21])[0]
            endpoint = pkt[21]
            transfer = pkt[22]
            data_len = struct.unpack(endi + "I", pkt[23:27])[0]
            if data_len == 0 or header_len > len(pkt):
                continue
            yield device, endpoint, transfer, pkt[header_len:header_len + data_len]


def find_frames(buf):
    """Scan raw bytes for 0xfd...0xfe framed Perception Neuron packets."""
    out = []
    i = 0
    n = len(buf)
    while i < n:
        if buf[i] != 0xfd:
            i += 1
            continue
        # need at least SOF+type+...+crc+EOF; search for the next 0xfe within a sane window
        end = buf.find(0xfe, i + 2, i + 64)
        if end == -1:
            i += 1
            continue
        frame = buf[i:end + 1]
        out.append(frame)
        i = end + 1
    return out


def describe(frame):
    if len(frame) < 4:
        return "TOO SHORT"
    ftype = frame[1]
    tname = TYPES.get(ftype, f"0x{ftype:02x}")
    body = frame[2:-2]  # strip SOF+type ... CRC+EOF
    crc = frame[-2]
    extra = ""
    if ftype == 0x01 and len(body) >= 6:
        pid, src, dst, cmd = body[0], body[1], body[2], body[3]
        cname = CMDS.get(cmd, f"0x{cmd:02x}")
        payload = body[4:9]
        extra = f" id={pid:02x} src={src:02x} dst={dst:02x} cmd={cname} payload={payload.hex()}"
    elif ftype == 0x0a and len(body) >= 2:
        key = body[0]
        kname = KEYS.get(key, f"0x{key:02x}")
        extra = f" key={kname} raw_body={body.hex()}"
    return f"type={tname}{extra} crc=0x{crc:02x} full={frame.hex()}"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        print(f"\n{'='*78}\n  {path}\n{'='*78}")
        n = 0
        devs = collections.Counter()
        seen = set()
        frames = []
        for device, endpoint, transfer, data in usb_packets(path):
            n += 1
            devs[device] += 1
            if not data or 0xfd not in data:
                continue
            for frame in find_frames(data):
                h = frame.hex()
                if h not in seen:
                    seen.add(h)
                    frames.append((device, endpoint, transfer, frame))
        print(f"  USB packets: {n}")
        print(f"  devices seen (addr:packets): "
              f"{', '.join(f'{d}:{c}' for d, c in devs.most_common(8))}")
        print(f"\n  --- Perception Neuron frames found: {len(frames)} distinct ---")
        for device, endpoint, transfer, frame in frames:
            print(f"    [dev {device} ep {endpoint:#04x} xfer {transfer}] {describe(frame)}")


main()
