# Next step

> ## START HERE (2026-08-20, T024 — first IMU payload bytes decoded: bytes [25:31]
> ## of the 31-byte payload are a stable-magnitude vector, likely accelerometer;
> ## the rest is still unknown. This is the small experiment T023 called for.)

**Scope change (T023), read this before picking Path A back up:** this kit's straps
physically come apart at several connector/joint points on their own during normal
handling - a real, recurring mechanical fault, not "unreliable connections" in the
abstract (T019-T022 chased this as a possible protocol gap; it isn't one, T020-T021
already closed that). It's also the "basic" Perception Neuron configuration to begin
with, below the 11/25/32-neuron minimums Axis Neuron's own Mode Hint screen expects
(`docs/00`). Net effect: the reliably-working sensor count tops out at a partial pose
(e.g. one full arm+fingers), never a full-body skeleton, no matter how much protocol
work happens. **Per the owner: stop treating "production-usable native-Linux mocap
stack" as the goal.** The goal now is to gather whatever clean data this specific
hardware still gives and scope one small, bounded experiment around it - not to
budget multi-week AHRS/skeleton-mapping effort as if full-body capture were still on
the table. The technical notes below (Path A steps, captured data, tooling) are all
still accurate and still useful *as data to work with*, just not as a march toward a
full production stack.

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
- **Discrepancy from T019, now resolved (T020):** the "does our Connect skip a mode-select
  step" hypothesis is refuted. `windows-kit/capturas/again1.pcapng` captured Axis Neuron's
  own real, repeated Connect/poll cycle (`03 02 00 00 00` -> `NodeFirmwareVersions`,
  `03 07 00 00 00` -> `NodeSerialNumbers`, `03 0d 00 01 00` -> Connect, cycled several
  times) — and the real vendor app, doing its own real handshake, caps at the exact same
  small node set (`01`/`5b`/`5d`/`5e` in firmware list, `5b`/`5d`/`5e`/`78` in serial-number
  list) every single time, never the ~11 sensors the Upgrade dialog shows as firmware-updated
  (`shara/photo_2026-08-20_09-37-30.jpg`). **Current leading explanation, per the owner
  directly**: strap hardware quality is poor on this kit, connections are intermittent, and
  getting the full kit paired simultaneously is inherently unreliable — this is a known,
  recalled problem, not a missing protocol step. Not fully closed (no byte-level proof the
  LEDs = pairing vs. power-only, and the daisy-chain-under-one-node-id possibility from
  `docs/00`'s `PNS00161` internal cable is still untested), but no further protocol
  reverse-engineering is warranted here — don't re-chase a mode-select frame, `03 0d 00 01 00`
  is confirmed sufficient (T020 backs T015). The remaining open question here (LEDs =
  pairing vs. power-only) is now moot - see T023 below, the straps have a confirmed
  physical fault independent of that.
- **T021, further confirming T020:** with only the right-arm+hand straps physically
  active (not the earlier 4-sensor set), `NodeFirmwareVersions`/`NodeSerialNumbers`
  enumerated 9-10 *different* node ids (`5b,5c,5d,61,62,66,67,6c,71,78`), not the same 4
  as before. Node count tracks whatever is actually plugged in/working right now, not a
  fixed protocol ceiling - strengthens the hardware-reliability explanation, doesn't
  contradict it.
- **T022, new: a real single-sensor Calibrate/demagnetize session** (owner ran Axis
  Neuron's single-sensor wizard, `windows-kit/capturas/diagnostico_1sensor.pcapng`,
  screenshots `shara/photo_2026-08-20_10-07-*.jpg`) exposed protocol surface none of
  the full-connect captures had: two `GetConfig` keys (`0x01` HubFirmwareVersion,
  `0x15` HubSerialNumber) confirmed live for the first time; a `Call` addressed
  `dst=00`; two `Call`s addressed directly `dst=a1` (the sensor's own node id, not the
  hub `0xc0` - first time seen); `Function` payloads `03 0b 00 00 00` and
  `02 01 00 00 00` (both new, not in `docs/01`'s known-command list); and, most
  notably, **the first `type=Set (0x0a)` frame ever captured** - `key=0x0f`, 51 bytes of
  dense packed binary, timed right where the wizard shows the rotate+data-collection
  step - a strong candidate for "write calibration coefficients to the sensor," not
  decoded field-by-field yet. None of this is digested into `docs/01` yet. Separately,
  live-checked with the new `scripts/pn-meter.py` right after: the sensor (node `0xa1`)
  kept streaming cleanly at ~60fps, unmoved, right after the Windows session - the
  calibration/demagnetize step didn't break it.
- **T023, scope change:** owner confirms directly, from physically handling the
  straps across all of today's sessions, that several connector/joint points come
  apart on their own during normal handling - a real recurring mechanical fault, the
  actual root cause behind T019-T021's node-count instability. Combined with this
  being the "basic" kit (below Axis Neuron's own 11/25/32-neuron mode minimums,
  `docs/00`), full-body capture is off the table with this hardware regardless of
  protocol work. See the scope-change note at the top of this file.
- **T024, the first small experiment (IMU payload decode, partial):** wrote
  `scripts/imu-payload-scan.py` - CRC-8-validates frames first (fixes T020/T021's
  noise problem), then scans the 31-byte `type=0x09` payload for a byte-aligned int16
  triplet whose magnitude stays constant under rotation (T010-style anchor on real
  data). Found one: **payload bytes `[25:31]`, little-endian int16 x3, magnitude
  ~69k-72k and stable (CoV 0.038) while T022's capture actively rotates the sensor**,
  consistent across two unrelated sessions/transports. Leaning accelerometer (matches
  what Axis Neuron's wizard says that rotate step calibrates), not proven vs
  magnetometer. The other ~25 payload bytes are still undecoded - no gyro candidate
  found yet. This is a real result, and also a reasonable stopping point per T023's
  new scope - see below, don't feel obliged to keep pushing on the rest immediately.

**Path A, rescoped from "build a production stack" to "candidate small experiments" -
pick one, don't try to do all of them:**
- Fold T022's new frames into `docs/01-protocol-research.md`'s known-command table
  (currently only documents Connect/Disconnect/the two node-enum triggers) and try
  replaying the `dst=a1`-direct-addressing pattern and the `03 0b`/`02 01` Function
  payloads from Linux against a currently-connected sensor to see what they actually
  do outside of the Windows wizard - cheap, bounded, doesn't need more sensors than
  we have.
- Continue decoding the `type=0x09` IMU payload: `[25:31]` (accel candidate) is found
  (T024), the other ~25 bytes aren't. `scripts/imu-payload-scan.py` is reusable -
  rerun/extend it (e.g. exclude the now-known `[25:31]` window and re-rank, or try
  wider/narrower field widths) against `test_use.pcapng` (T017, 8521 frames) or a
  fresh capture. `windows-kit/capturas/full_right.pcapng` (94904 distinct frames,
  T020) is bigger but unvalidated at that volume even by CRC-8 alone - check the
  CRC-valid fraction before trusting it as a bigger sample. Confirming accel-vs-
  magnetometer for `[25:31]` (second still capture at a different fixed tilt, check
  if the vector direction follows physical tilt or compass heading) is a cheap
  next step if this gets picked back up. Full AHRS fusion + skeleton mapping past
  this point is explicitly **not** the goal anymore (T023) - plotting/sanity-checking
  raw axes over time is a fine stopping point, not a fusion pipeline.
- Cross-check `upgrade.pcapng`/`test_use.pcapng` byte-for-byte against T016's confirmed
  Connect frame, and use it to explain the small fraction of frames the current CRC-8
  formula doesn't yet match. Minor, low-priority.
- `windows-kit/capturas/scene-export/` (T020: `SceneChar00.bvh`, `Scene.raw`,
  `Scene.xml`) is real ground-truth output from Axis Neuron's own fusion - useful as a
  reference if anyone ever wants to sanity-check a partial decode against it, not a
  reason to build a competing fusion stack.

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
other candidates for it. The T019 mode-select-frame question is also closed as of
T020 - the real Axis Neuron app's own Connect hits the identical 4-node cap, so
don't re-chase a missing mode-select step; the node-count ceiling is a hardware/
pairing-reliability question (owner's straps), not a protocol one.
