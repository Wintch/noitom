# Context for whoever (human or agent) picks this up next

> ## START HERE (2026-08-20, T001-T012 — the kickoff day, two-way Linux comms confirmed).
> Read `docs/00`-`06` + `docs/pruebas.jsonl` T001-T012 + `NEXT-STEP.md`.

## The one-paragraph state of the world

The kit (hub PNHU01 + straps, 2014 Kickstarter) is fully inventoried (`docs/00`), and the
USB transport question is **closed**: the hub is a plain CP210x USB-serial bridge, the
Linux kernel binds it natively, `/dev/ttyUSB0` just works (`docs/02`, T001-T003). The wire
protocol above that is a proprietary `0xfd`...CRC8...`0xfe` framing, partially documented
by [pelrun/perceptionneuron](https://github.com/pelrun/perceptionneuron). Blind CRC-8
brute-force (T006) found nothing, as expected — but a specific older, unlicensed build
(`Axis_Neuron_x64_3_8_42_8591_20180411034619617000_X64`, T008) turned out to run and talk
to the hub with no activation at all, which produced a real reference capture (T009) and,
from that, the CRC-8 algorithm itself (T010, `docs/05`): `poly=0x07, init=0x00` over
`type..payload`, XOR `0xFD`, verified against 98% of real captured frames.

**Both original blockers are resolved** (`docs/04`, `docs/05`, T008-T010) — not by
reactivating Axis Studio/legacy Wibu licensing (that path, and the support email, turned
out to be unnecessary), but by finding a different, older installer that never needed
activation in the first place. A pragmatic parallel path also exists if the goal is
*using* the mocap data rather than a from-scratch Linux stack: legacy Axis Neuron can
broadcast the live skeleton over the network (BVH, ports 7001/7003) straight into Unity,
no reverse-engineering needed at all — see `docs/06`, T011.

Path A is now proven end-to-end, not just theoretically unblocked: `scripts/pn-send.py`
sends a self-constructed `GetConfig` frame from `/dev/ttyUSB0` at **921600 baud** (the
missing piece T006 never varied) and the real hub answers with a real `Ack`+`Data`
response (T012). The real next step is trying an actual `Connect`/streaming command the
same way, per `NEXT-STEP.md`.

## Working conventions on this project

- **Documentation is English, prose files in `docs/`, numbered like `reverb-g2`**
  (`../reverb-g2` — same owner, same house style: measured facts over impressions, honest
  negatives recorded as carefully as positives, README links to a `docs/NN-topic.md`
  index). This project is new and small; don't manufacture false depth to look like
  `reverb-g2` — it earned its density over months, this hasn't yet.
- **`docs/pruebas.jsonl`** is the append-only quick-test log — one line per test, id
  `T00N`, opened/mode/hypothesis/verdict/closed. Add one entry per discrete probe/test/
  capture attempt, whether it succeeds or not. This is the audit trail; prose docs
  synthesize from it, they don't replace it.
- **MIT licensed** (`LICENSE`), matching the owner's usual default for this kind of repo.
- **Never commit `windows-kit/axis-studio-extract/`** — Noitom's own proprietary DLLs,
  pulled for local static analysis only, gitignored on purpose. Same for raw
  `windows-kit/capturas/*.pcapng` — decoded findings belong in `docs/`, not the raw dumps.
- The sibling project `../reverb-g2` solved a structurally identical problem (proprietary
  protocol, one Windows-side capture needed once) — `scripts/parse-pn-capture.py` reuses
  its dependency-free pcapng/USBPcap reader verbatim (`usb_packets()`), and
  `windows-kit/capture.ps1` is adapted from its capture script. Worth checking there again
  if a similar wall comes up (e.g. its `docs/12-g2-protocol.md` for protocol RE method, or
  its licensing/vendor-support triage pattern if that becomes relevant again).

## Next concrete step

See `NEXT-STEP.md` — kept short and current on purpose; this file is the deep context, that
one is the "what do I do right now" pointer.
