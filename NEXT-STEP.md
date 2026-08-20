# Next step

> ## START HERE (2026-08-20, T016 — Connect confirmed, session captured, focus shifting to Windows)

Both morning blockers (licensing, missing capture/CRC-8) are resolved, and Path A
is now proven end-to-end including the actual **Connect** command: `scripts/pn-connect.py`
sends `03 0d 00 01 00` (the `0x01 Function` candidate from `docs/01-protocol-research.md`)
over `/dev/ttyUSB0` at **921600 baud** with sensor straps attached, and the hub answers
with an `Ack`, some node-enumeration `Data` frames, then **sustained `type=0x09` IMU
streaming**. A 25s session (80375 bytes, 2170 IMU frames) is saved raw to
`linux-kit/capturas/connect-session-1.bin` (gitignored, like `windows-kit/capturas/`)
for later offline decoding — see `docs/05`, `docs/pruebas.jsonl` T008-T016.

**Deliberately paused for now (owner's call, not blocked):** decoding the `type=0x09`
IMU payload fields and the node-firmware `Data` frame (key `0x71`,
`NodeFirmwareVersions`) from the saved capture. `find_frames()`/`describe()` in
`scripts/parse-pn-capture.py` work on any raw byte buffer, not just pcapng-extracted
ones, so they should apply directly to `connect-session-1.bin` when this resumes.

**Immediate next step (owner is doing this now, outside this Linux session):**
Go back to Windows, update one sensor's firmware through the legacy Axis Neuron
build, and capture that with Wireshark/`windows-kit/capture.ps1` (**capture all USB
interfaces at once, not one picked by hand** — T007's exact failure mode: it picked
one USBPcap interface and the hub was on a different controller, zero frames
captured. `capture.ps1` exists specifically to avoid this). Reproducing the
firmware-update flow itself is a possible follow-up, explicitly out of scope for
today.

**Path A (native Linux, the original goal) — next concrete action once resumed:**
1. Decode the `type=0x09` IMU payload fields (31 bytes, raw accel/gyro/mag per
   `docs/01` — nobody has published this) from `connect-session-1.bin`. Look for
   stable-magnitude byte ranges (likely accelerometer, ~1g at rest) as an anchor,
   the way T010 anchored CRC-8 on real data.
2. Decode the node-enumeration `Data` frame with key `0x71` in the same capture
   before assuming a fresh Windows capture is needed to identify the straps'
   firmware version. Likely old (straps haven't been used since ~2014) - worth
   confirming from this data either way.
3. Once raw IMU is decoded: AHRS fusion (Madgwick/Mahony) + skeleton mapping is the
   big remaining undocumented step - budget real time for it, don't expect a quick win.
4. Cross-check the new Windows firmware-update capture (above) byte-for-byte against
   T016's confirmed Connect frame, and use it to explain the 7/375 frames the
   current CRC-8 formula doesn't yet match.

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
as of T015 - `03 0d 00 01 00` is confirmed, don't re-probe other candidates for it.
