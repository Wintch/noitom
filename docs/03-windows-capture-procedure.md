# The one Windows trip: capturing the handshake

## Why

We need the exact bytes of the "connect" command Axis Neuron sends the hub on
pairing — with those, we can replay them verbatim from `/dev/ttyUSB0` on Linux and
never need to understand the CRC-8 algorithm at all (see
[`02-linux-usb-bringup.md`](02-linux-usb-bringup.md), T6, for why blind brute-force
of the CRC is a dead end).

This adapts the same capture kit and philosophy already proven on the sibling
`reverb-g2` project (`../reverb-g2/windows-kit/BRINGUP-CAPTURE-RUNBOOK.md`): one
disciplined Windows session, captured once, never repeated.

**One-line goal**: capture the real USB traffic between Axis Neuron and the
PNHU01 hub with USBPcap, at the exact moment of connecting, to read the real
"connect" command bytes (and get the real CRC-8 for free — we only need to repeat
the exact byte, not understand the algorithm in general).

## Requirements (once, on Windows)

- **Wireshark**, installed **with the USBPcap component checked** (not on by
  default). Reboot Windows after installing — USBPcap does not work otherwise.
  <https://www.wireshark.org/download.html>
- **Axis Neuron** (Noitom's legacy software for PN32/v1) — see
  [`04-licensing-blocker.md`](04-licensing-blocker.md), this is currently the
  actual blocker, not the capture mechanics.
- The PNHU01 hub, connected by USB (the **data** port, not power-only).

## Running it: `windows-kit/capture.ps1`

The script discovers **every** USBPcap interface on the machine automatically
(interface numbers vary between installs, so nothing is hardcoded) and starts one
`dumpcap` process per interface, all at once, each to its own timestamped file.
This matters: on a machine with more than one USB controller, capturing only one
interface can miss the hub entirely if it happens to be on a different
controller — see "What went wrong the first time" below.

1. Copy the `windows-kit` folder to the Windows side.
2. **Hub connected over USB, but Axis Neuron still CLOSED** (or open, without
   pressing "Connect" yet). This is critical — the handshake we need happens once,
   at connect time.
3. Open PowerShell **as Administrator**, `cd` into this folder, run once:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
4. Run:
   ```powershell
   .\capture.ps1 -Label connect
   ```
5. Follow the console: capture starts first, **then** open/press "Connect" in Axis
   Neuron, wait for it to connect (hub beep or light), come back and stop with
   Enter. 15-20 seconds after connecting is enough — the hub only sends
   continuous IMU streaming after that, which we don't need.
6. This leaves a `capturas\` folder with several
   `connect_USBPcapN_<timestamp>-trim.pcapng` files — one per interface. Bring
   **all** of them back (they're small).

Optional, same trip, if there's appetite for it: repeat with `-Label wificonfig`
while configuring the hub's WiFi router in Axis Neuron. That would also capture
the exact `0x18 Wifi Config` payload (documented as existing, no known payload —
see [`01-protocol-research.md`](01-protocol-research.md)) — not needed for the
wired path we're prioritizing, but closes the other branch while already there.

## Back on Linux: parsing

```bash
python3 scripts/parse-pn-capture.py windows-kit/capturas/connect_*-trim.pcapng
```

Scans the raw USB traffic for `0xfd...0xfe` frames and decodes them against
`pneuron.lua`'s tables (types/commands/keys/skeleton nodes). Out comes the real
"connect" command, byte for byte.

## What went wrong the first attempt (T7)

The first real capture attempt did **not** use `capture.ps1` — it was run by hand,
one interface at a time, physically moving the hub cable between two USB ports and
connecting/disconnecting on each. Result: **zero PNHU01 frames in either
capture.** The two files (`debug_noitom/1.pcapng`, `2.pcapng`) only contained a
generic USB hub (VID `0x214b`) and a Logitech Unifying receiver (VID `0x046d` PID
`0xc534`) — the hub's actual CP210x (VID `0x10c4` PID `0xea60`, confirmed in
[`02-linux-usb-bringup.md`](02-linux-usb-bringup.md) T1) never showed up in either
file.

Root cause: picking one USBPcap interface by hand, per run, is exactly the trap
`capture.ps1` exists to avoid — if the hub happens to be on a USB controller other
than the one interface chosen, the capture is empty no matter how carefully the
timing is done. `capture.ps1` (now copied to `C:\debug_noitom\windows-kit\` on the
owner's machine) captures every interface simultaneously specifically so this
can't happen — see [`docs/pruebas.jsonl`](pruebas.jsonl) T7 for the full
diagnostic.

The retry is straightforward once
[the licensing blocker](04-licensing-blocker.md) is resolved: just run
`capture.ps1` as documented above instead of driving Wireshark by hand.
