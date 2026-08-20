# Next step

> ## START HERE (2026-08-20, T022 — node count tracks what's actually plugged in
> ## (T021), and a single-sensor calibration capture exposed new protocol surface
> ## incl. the first Set/0x0a frame, likely the calibration-write itself)

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
  is confirmed sufficient (T020 backs T015).
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

**Path A (native Linux, the original goal) — next concrete actions, in order:**
0. Fold T022's new frames into `docs/01-protocol-research.md`'s known-command table
   (currently only documents Connect/Disconnect/the two node-enum triggers) and try
   replaying the `dst=a1`-direct-addressing pattern and the `03 0b`/`02 01` Function
   payloads from Linux against a currently-connected sensor to see what they actually
   do outside of the Windows wizard - this is a small, well-scoped follow-up, do it
   before diving back into full IMU-payload decoding.
1. Decode the `type=0x09` IMU payload fields themselves (accel/gyro/mag, byte 5 onward -
   docs/01 says 31 bytes raw, nobody has published this). `test_use.pcapng`'s 8521 frames
   are still the best *clean* sample (T017); `windows-kit/capturas/full_right.pcapng`
   (94904 distinct frames, T020) is far bigger but its frames haven't been sanity-checked
   at that volume yet - `find_frames()`'s naive `0xfd`/`0xfe` scan may be mis-splitting
   frames when run over this much data (T020 saw near-uniform garbage on a byte-4 node-id
   extraction there, unlike the clean 4-node result on smaller captures), so treat it as
   unvalidated until that's checked, not as a bigger version of the same trusted sample.
   Look for stable-magnitude byte ranges (likely accelerometer, ~1g at rest) as an anchor,
   the way T010 anchored CRC-8 on real data.
2. Once raw IMU is decoded: AHRS fusion (Madgwick/Mahony) + skeleton mapping is the big
   remaining undocumented step - budget real time for it, don't expect a quick win.
   `windows-kit/capturas/scene-export/` (T020: `SceneChar00.bvh`, `Scene.raw`, `Scene.xml`)
   is real ground-truth output from Axis Neuron's own fusion, pulled specifically to check
   any independent decode/fusion attempt against later - not yet used for anything.
3. Cross-check `upgrade.pcapng`/`test_use.pcapng` byte-for-byte against T016's confirmed
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
other candidates for it. The T019 mode-select-frame question is also closed as of
T020 - the real Axis Neuron app's own Connect hits the identical 4-node cap, so
don't re-chase a missing mode-select step; the node-count ceiling is a hardware/
pairing-reliability question (owner's straps), not a protocol one.
