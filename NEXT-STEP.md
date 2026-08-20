# Next step

> ## START HERE (2026-08-20, T019 — 4 sensors enumerate/stream, owner re-checking on
> ## Windows whether more should show up)

Both morning blockers (licensing, missing capture/CRC-8) are resolved, and Path A
is proven end-to-end including the actual **Connect** command: `scripts/pn-connect.py`
sends `03 0d 00 01 00` (the `0x01 Function` candidate from `docs/01-protocol-research.md`)
over `/dev/ttyUSB0` at **921600 baud**, and the hub answers with an `Ack`, node-enumeration
`Data` frames, then **sustained `type=0x09` IMU streaming** — see `docs/05`,
`docs/pruebas.jsonl` T008-T016.

The Windows trip asked for in the previous version of this file is done: `upgrade.pcapng`
and `test_use.pcapng` were pulled off the Windows NVMe partition (mounted at `/mnt/win`,
read-only) into `windows-kit/capturas/` and parsed with `scripts/parse-pn-capture.py`
(T017). `upgrade.pcapng` confirms `type=0x07 FirmwareUpload` as a real, working command
(sequential chunk ids). `test_use.pcapng` is the largest real IMU sample gathered so far
(8521 raw `IMUdata` frames).

**New progress today (T018-T019), from Linux with all 4 currently-available sensors
physically connected:**
- The `type=0x09` IMU frame layout is now partially known: byte 3 is a rolling counter,
  **byte 4 is the sensor's node id** — confirmed because it exactly matches the node ids
  listed in the hub's own enumeration frames. The actual accel/gyro/mag payload starts at
  byte 5 and is still **not decoded field-by-field**.
- The `key=0x71 NodeFirmwareVersions` Data frame is now decoded structurally: 1 header
  byte, then repeating `[node_id(1) + 6-byte version blob]`. All 4 currently-connected
  sensors report the identical version blob `00100a011c05` — last-byte match (`0a`=10,
  `05`=5) against the on-screen Boot 1.0.0.10 / App 1.0.1.5 (`shara/photo_2026-08-20_08-
  46-11.jpg`) is consistent, but the full byte→field mapping isn't solved.
- **Open discrepancy, unresolved:** only 4 node ids (`0x01`, `0x5b`, `0x5d`, `0x5e`) ever
  enumerate or stream, confirmed both in the IMU stream over a 20s window and in the
  hub's own `NodeSerialNumbers` (`0x7c`) frame — not a sampling artifact. Owner reports
  seeing more sensor LEDs lit than that. Leading hypothesis: our bare `03 0d 00 01 00`
  Connect may skip a "select mode" step — the Windows `Mode Hint` screenshot
  (`shara/photo_2026-08-20_08-45-59.jpg`, same session) shows Axis Neuron checking
  connected-neuron count against 11/25/32-neuron mode minimums before it lets Connect
  proceed, a step our simplified frame never sends. Not confirmed - also possible the
  LED just indicates power, not hub pairing, or that some sensors are daisy-chained
  (`PNS00161` internal cable per `docs/00`) under one shared logical node id.

**Immediate next step (owner is doing this now, back on Windows):** visually recount how
many sensors are actually lit vs. how many Axis Neuron itself reports as connected in the
Mode Hint screen, to settle whether 4 is really all that's paired or whether a mode-select
frame is missing from our Connect sequence. If it's the latter, the fix is to capture Axis
Neuron doing a real Connect with all sensors attached (reuse `windows-kit/capture.ps1`,
same procedure as `03-windows-capture-procedure.md`) and diff it against our
`03 0d 00 01 00` sequence to find the missing mode-select frame.

**Path A (native Linux, the original goal) — next concrete actions, in order:**
1. Resolve the node-count discrepancy above (owner is on it now).
2. Decode the `type=0x09` IMU payload fields themselves (accel/gyro/mag, byte 5 onward -
   docs/01 says 31 bytes raw, nobody has published this). `test_use.pcapng`'s 8521 frames
   are now the best available sample. Look for stable-magnitude byte ranges (likely
   accelerometer, ~1g at rest) as an anchor, the way T010 anchored CRC-8 on real data.
3. Once raw IMU is decoded: AHRS fusion (Madgwick/Mahony) + skeleton mapping is the big
   remaining undocumented step - budget real time for it, don't expect a quick win.
4. Cross-check `upgrade.pcapng`/`test_use.pcapng` byte-for-byte against T016's confirmed
   Connect frame, and use it to explain the small fraction of frames the current CRC-8
   formula doesn't yet match.

**Path D (pragmatic, if the goal is using the mocap data rather than a from-scratch
Linux stack) — see `docs/06-bvh-broadcast-alternative.md`:**
Run the confirmed-working unlicensed Axis Neuron build
(`Axis_Neuron_x64_3_8_42_8591_20180411034619617000_X64`), enable BVH Broadcasting
(Settings, "Axis Legacy" skeleton, TCP/UDP 7001/7003), consume it in Unity with
`keijiro/NeuronAnimator`. No further reverse-engineering needed for this path at
all - only needs a Windows box (real or VM) running Axis Neuron as the one thing
that touches the hub. Wine is untested for this (`docs/01`, T011) - worth a cheap
try before assuming a VM/dual-boot is required long-term, but don't plan around it
until actually tried.

**Do not re-litigate**: blind CRC-8 brute-force without real data (T006) and
hand-driven Wireshark capture instead of `capture.ps1` (T007) are both closed —
don't retry either approach; the tooling that replaced them (`crc8-search.py`,
`capture.ps1`) already exists and works. The Connect command itself is also closed
as of T015 - `03 0d 00 01 00` is confirmed as *a* working connect, don't re-probe
other candidates for it - the open question (T019) is whether a mode-select frame
should precede it, not whether it's the right command.
