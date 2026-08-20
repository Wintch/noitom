#!/usr/bin/env python3
"""Brute-force search for the CRC-8 algorithm used by the PNHU01 hub's 0xfd..0xfe
framing, using real (frame, crc) pairs pulled from an actual Windows USB capture
(see docs/pruebas.jsonl T004/T006 for why this couldn't be done blind before).

For each candidate byte-region of the frame, and each (poly, init, refin, refout)
combination, derive xorout from one frame of the modal (most common) length and
verify against a handful more of that same length before scoring against the full
frame set. Prints the best-scoring combination found, exact or not (a real capture
has a few short/irregular sub-frames that may never hit 100%, see
docs/05-crc8-solved.md).

Usage: ./crc8-search.py capture.pcapng [another.pcapng ...]
"""
import sys
import os
import collections

sys.path.insert(0, os.path.dirname(__file__))

# parse-pn-capture.py has a hyphen (can't import normally) and calls main() itself
# at module scope on top of that - swap out argv/stdout while loading it so it
# doesn't reprocess our capture files as a side effect.
import importlib.util
import io

spec = importlib.util.spec_from_file_location(
    "parse_pn_capture", os.path.join(os.path.dirname(__file__), "parse-pn-capture.py")
)
parse_pn_capture = importlib.util.module_from_spec(spec)
_real_argv, _real_stdout = sys.argv, sys.stdout
sys.argv, sys.stdout = [sys.argv[0]], io.StringIO()  # argv<2 -> main() sys.exit()s harmlessly
try:
    spec.loader.exec_module(parse_pn_capture)
except SystemExit:
    pass
finally:
    sys.argv, sys.stdout = _real_argv, _real_stdout


def reflect8(b):
    r = 0
    for i in range(8):
        if b & (1 << i):
            r |= 1 << (7 - i)
    return r


REFLECT = [reflect8(b) for b in range(256)]


def build_table(poly):
    table = []
    for byte in range(256):
        crc = byte
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
        table.append(crc)
    return table


def crc_of(data, table, init, refin, refout):
    crc = init
    for b in data:
        if refin:
            b = REFLECT[b]
        crc = table[crc ^ b]
    if refout:
        crc = REFLECT[crc]
    return crc


def collect_frames(paths):
    frames = []
    seen = set()
    for path in paths:
        for device, endpoint, transfer, data in parse_pn_capture.usb_packets(path):
            if not data or 0xfd not in data:
                continue
            for frame in parse_pn_capture.find_frames(data):
                h = frame.hex()
                if h not in seen and len(frame) >= 5:
                    seen.add(h)
                    frames.append(frame)
    return frames


KNOWN_TYPES = {0x01, 0x02, 0x03, 0x04, 0x0a}  # Call/Ack/Value/Data/Set - excludes
# firmware-blob byte noise that coincidentally matches 0xfd..0xfe (see T009)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    all_frames = collect_frames(sys.argv[1:])
    frames = [f for f in all_frames if f[1] in KNOWN_TYPES and len(f) <= 20
              and 0xfd not in f[1:-1] and 0xfe not in f[1:-1]]
    print(f"{len(all_frames)} distinct frames loaded, {len(frames)} after filtering to "
          f"known short Call/Ack/Value/Data/Set types with no internal fd/fe collision "
          f"(excludes firmware-blob noise and mis-split frames)")

    regions = {}
    for start in range(0, 4):
        for end in range(1, 4):
            regions[f"frame[{start}:-{end}]"] = (lambda s, e: (lambda f: f[s:-e]))(start, end)

    # quick pre-filter subset, cheap to test before the expensive full-frame verify.
    # Deliberately drawn from the MODAL frame length, not just "shortest N" - a real
    # capture has a handful of short/irregular sub-frames (see docs/05-crc8-solved.md)
    # that would otherwise dominate a length-sorted sample and poison the derivation
    # before the dominant, well-formed population ever gets tested.
    length_counts = collections.Counter(len(f) for f in frames)
    modal_length = length_counts.most_common(1)[0][0]
    quick = [f for f in frames if len(f) == modal_length][:8]
    print(f"quick pre-filter: {len(quick)} frames of the modal length ({modal_length} bytes, "
          f"{length_counts[modal_length]}/{len(frames)} of the filtered set)")

    best = None  # (matches, region_name, poly, init, refin, refout, xorout)
    for region_name, region_fn in regions.items():
        quick_data = [(region_fn(f), f[-2]) for f in quick]
        for poly in range(256):
            table = build_table(poly)
            for refin in (False, True):
                for refout in (False, True):
                    d0, crc0 = quick_data[0]
                    for init in range(256):
                        pre = crc_of(d0, table, init, refin, refout)
                        xorout = pre ^ crc0
                        ok = True
                        for d, target in quick_data[1:]:
                            if crc_of(d, table, init, refin, refout) ^ xorout != target:
                                ok = False
                                break
                        if not ok:
                            continue
                        # survived the quick subset - score against everything
                        matches = sum(
                            1 for f in frames
                            if crc_of(region_fn(f), table, init, refin, refout) ^ xorout == f[-2]
                        )
                        if best is None or matches > best[0]:
                            best = (matches, region_name, poly, init, refin, refout, xorout)

    found = []
    if best:
        matches, region_name, poly, init, refin, refout, xorout = best
        pct = 100 * matches / len(frames)
        tag = "EXACT MATCH" if matches == len(frames) else f"BEST MATCH ({pct:.0f}%, not exact)"
        print(f"{tag} region={region_name} poly=0x{poly:02x} init=0x{init:02x} "
              f"refin={refin} refout={refout} xorout=0x{xorout:02x} "
              f"-- {matches}/{len(frames)} frames")
        if matches == len(frames):
            found.append(best)

    if best is None:
        print("No CRC-8 candidate even matched the quick subset. Trying simple "
              "(non-CRC) checksums over the same regions...")
        checksum_fns = {
            "xor-sum": lambda data: (lambda v: v)(_xor_all(data)),
            "add-sum": lambda data: sum(data) & 0xFF,
            "twos-complement-sum": lambda data: (-sum(data)) & 0xFF,
        }
        for region_name, region_fn in regions.items():
            for cs_name, cs_fn in checksum_fns.items():
                d0 = region_fn(quick[0])
                base = cs_fn(d0)
                offset = (quick[0][-2] - base) & 0xFF
                ok = all((cs_fn(region_fn(f)) + offset) & 0xFF == f[-2] for f in quick)
                if not ok:
                    continue
                if all((cs_fn(region_fn(f)) + offset) & 0xFF == f[-2] for f in frames):
                    found.append((region_name, cs_name, offset))
                    print(f"MATCH region={region_name} checksum={cs_name} offset=0x{offset:02x} "
                          f"-- verified against all {len(frames)} frames")
        if not found:
            print("No match found in the tested (poly,init,refin,refout,xorout) x region "
                  "space, nor the simple-checksum fallback.")


def _xor_all(data):
    v = 0
    for b in data:
        v ^= b
    return v


main()
