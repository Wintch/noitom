# Next step

> ## START HERE (2026-08-20, T013 — end of the kickoff day, two-way Linux comms confirmed)

Both morning blockers (licensing, missing capture/CRC-8) are resolved, and Path A
is now proven end-to-end: `scripts/pn-send.py` sends a self-constructed frame from
`/dev/ttyUSB0` at **921600 baud** and the real hub answers with a real `Ack`+`Data`
response — see `docs/05`, `docs/pruebas.jsonl` T008-T013. Two real paths remain
open, independent of each other:

**Path A (native Linux, the original goal) — next concrete action:**
T013 already tried the two `0x01 Function` candidates from
`docs/01-protocol-research.md` (`03 0d 00 01 00` "connect?", `02 00 00 00 00`
"disconnect?") — both got real, distinct responses (not echoes/garbage), but no
sensor straps were attached, so nothing streamed either way, and neither is
confirmed as the *real* connect command yet. Next concretely:
1. **Attach sensor straps to the hub** and repeat T013 - if `type=0x09` IMU frames
   start arriving after the "connect?" candidate, that confirms it and gives real
   payload data to decode (undocumented anywhere public - the real remaining
   work, alongside AHRS fusion + skeleton mapping afterward).
2. In parallel/instead: grab one real capture of Axis Neuron's actual **main-window
   Connect** flow (not the Upgrade-dialog session `upgrade.pcapng` used so far,
   `docs/03`) to compare byte-for-byte against the T013 candidates, and to explain
   the 7/375 frames the current CRC-8 formula doesn't yet match.

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
`capture.ps1`) already exists and works.
