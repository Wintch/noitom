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
| CRC-8 algorithm | ❌ unknown, not published anywhere, blind brute-force exhausted — `docs/02` T6 |
| Handshake capture (Windows, one-time) | ❌ blocked — first attempt caught the wrong USB interface, and Axis Studio needs a license the owner doesn't currently have — `docs/03`, `docs/04` |
| IMU payload decoding | ⏳ not started — needs the handshake first |
| Sensor fusion (AHRS) | ⏳ not started |
| Skeleton mapping / BVH export | ⏳ not started |

## Docs

| # | Topic |
|---|---|
| [00](docs/00-hardware-inventory.md) | The kit: hub, straps, serials, market context |
| [01](docs/01-protocol-research.md) | Prior art on the wire protocol, and the paths considered |
| [02](docs/02-linux-usb-bringup.md) | USB bring-up on Linux, probing attempts, honest negatives |
| [03](docs/03-windows-capture-procedure.md) | The one-time Windows capture session, and what went wrong the first try |
| [04](docs/04-licensing-blocker.md) | The Axis Studio/Neuron licensing dead end, and what's being tried about it |

## Getting started

```bash
# USB bring-up + protocol probing (Linux side)
python3 -m venv .venv && . .venv/bin/activate && pip install pyserial

# Once a real capture exists (see docs/03):
python3 scripts/parse-pn-capture.py windows-kit/capturas/connect_*-trim.pcapng
```

## Reference hardware

Perception Neuron v1 (Kickstarter 2014), hub **PNHU01**, CP210x USB-serial bridge.
Linux side is whatever machine is doing the bring-up work — nothing PN-specific is
required from the host beyond a free USB port and the `cp210x` kernel driver (built
in on any recent kernel).

## Contributing

The actual blocker right now is **not engineering** — it's getting one clean USB
capture of Axis Neuron/Studio pairing with the hub (`docs/03`, `docs/04`). If you
have:

- A working, licensed copy of legacy **Axis Neuron** (PN32/v1) and 20 minutes on
  Windows, or
- Any public documentation of the CRC-8 algorithm used by Noitom's `0xfd...0xfe`
  framing (from firmware, another SDK, or a different reverse-engineering effort)

either one skips the current blocker entirely.

Everything in this repo is written in English. Measurements beat opinions: if you
assert something, say how you measured it.
