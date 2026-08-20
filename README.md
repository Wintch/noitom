# noitom

Getting an original [Perception Neuron](https://en.wikipedia.org/wiki/Perception_Neuron)
motion-capture kit (Noitom, backed on Kickstarter in 2014) running on Linux — no
Windows, no Wine, using only what the community has already reverse-engineered plus
whatever we add ourselves.

The kit's software, Axis Neuron, is Windows-only and has not been reported working
under Wine/Proton/CrossOver/any VM anywhere — not a single report either way. Noitom's
current software line (Axis Studio, for the newer PN3/Studio generation) does not
support this hub at all. The hardware itself is a straightforward CP210x USB-serial
bridge underneath a proprietary framed protocol — that's the actual target.

Everything documented here was measured, not assumed. Honest negatives (a probe that
found nothing, a capture that caught the wrong device) are recorded with the same care
as positive results — see [`docs/pruebas.jsonl`](docs/pruebas.jsonl).

## Status (2026-08)

| Area | State |
|---|---|
| Hardware inventory | ✅ hub + straps labeled and logged, see `docs/00` |
| USB transport | ✅ confirmed generic CP210x, `/dev/ttyUSB0`, no driver needed — `docs/02` |
| Serial permissions | ✅ `dialout` group, works without full relogin — `docs/02` |
| Protocol framing | ✅ documented by prior art (`0xfd`...CRC8...`0xfe`) — `docs/01` |
| CRC-8 algorithm | ✅ reverse-engineered from a real capture, 98% verified — `docs/05` |
| Licensing (legacy Axis Neuron, unactivated) | ✅ a specific older build runs and talks to the hub with no license at all — `docs/04` |
| Handshake capture (Windows, one-time) | ✅ obtained (via a firmware-upgrade session) — `docs/03`, `docs/05` |
| Two-way comms from Linux | ✅ confirmed — self-constructed frame sent at 921600 baud, hub replies for real — `docs/05` T012 |
| Live-stream-to-Unity alternative (no RE needed) | ✅ documented, license-free path exists — `docs/06` |
| IMU payload decoding | ⏳ not started — next real step is trying a `Connect`/streaming command the same way |
| Sensor fusion (AHRS) | ⏳ not started |
| Skeleton mapping / BVH export | ⏳ not started |

## Docs

| # | Topic |
|---|---|
| [00](docs/00-hardware-inventory.md) | The kit: hub, straps, serials, market context |
| [01](docs/01-protocol-research.md) | Prior art on the wire protocol, and the paths considered |
| [02](docs/02-linux-usb-bringup.md) | USB bring-up on Linux, probing attempts, honest negatives |
| [03](docs/03-windows-capture-procedure.md) | The one-time Windows capture session, and what went wrong the first try |
| [04](docs/04-licensing-blocker.md) | The Axis Studio/Neuron licensing dead end — and how it turned out not to matter |
| [05](docs/05-crc8-solved.md) | The CRC-8 algorithm, reverse-engineered from a real capture |
| [06](docs/06-bvh-broadcast-alternative.md) | The pragmatic alternative: Axis Neuron's built-in BVH broadcast into Unity |

## Getting started

```bash
# USB bring-up + protocol probing (Linux side)
python3 -m venv .venv && . .venv/bin/activate && pip install pyserial

# Once a real capture exists (see docs/03):
python3 scripts/parse-pn-capture.py windows-kit/capturas/upgrade.pcapng

# Recover/verify the CRC-8 algorithm from a real capture (see docs/05):
python3 scripts/crc8-search.py windows-kit/capturas/upgrade.pcapng

# Talk to the real hub directly from Linux (see docs/05, T012):
python3 scripts/pn-send.py /dev/ttyUSB0 921600
```

## Reference hardware

Perception Neuron v1 (Kickstarter 2014), hub **PNHU01**, CP210x USB-serial bridge.
Linux side is whatever machine is doing the bring-up work — nothing PN-specific is
required from the host beyond a free USB port and the `cp210x` kernel driver (built
in on any recent kernel).

## Contributing

The licensing and CRC-8 blockers that used to gate this project are resolved
(`docs/04`, `docs/05`) — the current actual next step is replaying a constructed
`Connect` frame from `/dev/ttyUSB0` on Linux, see `NEXT-STEP.md`. If you have real
IMU payload structure (type `0x09`) or skeleton-mapping/AHRS-fusion experience for
this exact hardware generation, that's the part still genuinely unstarted.

Everything in this repo is written in English. Measurements beat opinions: if you
assert something, say how you measured it.
