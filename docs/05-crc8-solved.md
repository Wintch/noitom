# The CRC-8 algorithm, reverse-engineered from a real capture

## Where this picks up

[`04-licensing-blocker.md`](04-licensing-blocker.md) was the last known blocker: no
license, no capture, no CRC-8. All three fell in one session (T008-T010,
[`pruebas.jsonl`](pruebas.jsonl)):

1. A specific older build, **`Axis_Neuron_x64_3_8_42_8591_20180411034619617000_X64`**
   (2018-04-11, legacy Axis Neuron for PN32/v1 — not Axis Studio), runs with **no
   license/activation prompt at all**, and genuinely talks to the hub: it read
   `HubPID PNHDE000018` (matches this kit's own serial suffix `de000018`,
   [`00-hardware-inventory.md`](00-hardware-inventory.md)) and successfully upgraded
   its firmware, App version `1.0.2.20` → `1.0.2.21`.
2. That firmware-upgrade session was captured with Wireshark/USBPcap on the Windows
   side (`C:\debug_noitom\upgrade.pcapng`) and pulled back over a read-only mount of
   the Windows NVMe partition. `scripts/parse-pn-capture.py` decoded **508 distinct
   real `0xfd...0xfe` frames** out of it — genuine hub-computed CRC-8 bytes, not
   guesses.
3. With real `(message, crc)` pairs finally available, brute-forcing the algorithm
   itself (rather than guessing blind, which T006 already exhausted) became
   tractable.

## The algorithm

```
crc = CRC8(frame[1:-2], poly=0x07, init=0x00, no bit reflection) ^ 0xFD
```

Where `frame[1:-2]` is everything between the `0xfd` SOF and the CRC byte itself —
`type, id, src, dst, cmd, payload...` — and `poly=0x07` is the plain/standard CRC-8
polynomial (the most common one there is; T006's blind attempt tried six named
variants but not this exact region/init/xorout combination, which is why it didn't
turn up until real data made brute force possible).

`scripts/crc8-search.py` found this by: collecting every real frame from a capture,
filtering to the well-typed `Call`/`Ack`/`Value`/`Data`/`Set` frames (dropping
firmware-blob byte noise that coincidentally matches `0xfd...0xfe`, and frames
mis-split by an internal `0xfd`/`0xfe` byte collision — both real hazards, see the
script's filtering logic), then testing every `(byte-region × poly × init × refin ×
refout × xorout)` combination for the one that reproduces the most frames' CRC
bytes. It reports this as `region=frame[0:-2] ... xorout=0x00` — an equivalent way
to express the same formula above, just folding the `0xfd` SOF byte into the running
CRC as the first input byte (`init` absorbs it) instead of treating it as a separate
final XOR. Same computation, same 368/375 result - rerunning it (see "Rerunning it"
below) reproduces this finding directly.

**Confidence: high but not 100%.** It matches **368 of 375** filtered real frames
(98%). The 7 exceptions are all short/irregular sub-frames — e.g. an `Ack` with a
5-byte body instead of the usual 9, one 17-byte `Data` frame — not yet explained.
Given how small and structurally different they are, they most likely represent an
uncovered sub-format (or leftover capture noise), not a wrong core algorithm. Worth
revisiting once a second capture exists, but not worth blocking on.

## What this unlocked — confirmed, T012

We can now compute a valid CRC-8 for **any** frame we construct — including the
`Function`/`GetConfig`/candidate `Connect` bytes documented in
[`01-protocol-research.md`](01-protocol-research.md) — without needing to capture
that exact command first. Verified for real: `scripts/pn-send.py` builds a
`GetConfig(HubFirmwareVersion)` frame from scratch and sends it from
`/dev/ttyUSB0` on Linux. **The hub answers.** Two-way communication with the real
hardware, from Linux, using nothing but frames we constructed ourselves — no
Windows, no replayed capture bytes.

The missing piece wasn't just the CRC-8: it was also the **send baud rate**. T006's
blind brute force only ever transmitted at 115200 (the rate T003's passive listen
probe happened to use) and got nothing. The real rate is **921600** — at 115200,
still silence; at 921600, an immediate `Ack` then `Data` response, byte-for-byte
matching the shape seen in the real T009 capture, and the firmware-version byte in
the response correctly reads `0x15` (21) instead of the pre-upgrade capture's
`0x14` (20) — it's live data, reflecting the T008 firmware upgrade in real time.
See T012 in [`pruebas.jsonl`](pruebas.jsonl).

```bash
.venv/bin/python3 scripts/pn-send.py /dev/ttyUSB0 921600
```

## Rerunning it

```bash
python3 scripts/parse-pn-capture.py windows-kit/capturas/upgrade.pcapng
python3 scripts/crc8-search.py windows-kit/capturas/upgrade.pcapng
.venv/bin/python3 scripts/pn-send.py    # talks to the real hub over /dev/ttyUSB0
```
