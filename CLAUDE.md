# Context for whoever (human or agent) picks this up next

> ## START HERE (2026-08-20, T001-T007 — the kickoff day).
> Read `docs/00`-`04` + `docs/pruebas.jsonl` T001-T007 + `NEXT-STEP.md`. Everything below
> is current as of the day the project started; there is no earlier state to supersede yet.

## The one-paragraph state of the world

The kit (hub PNHU01 + straps, 2014 Kickstarter) is fully inventoried (`docs/00`), and the
USB transport question is **closed**: the hub is a plain CP210x USB-serial bridge, the
Linux kernel binds it natively, `/dev/ttyUSB0` just works (`docs/02`, T001-T003). The wire
protocol above that is a proprietary `0xfd`...CRC8...`0xfe` framing, partially documented
by [pelrun/perceptionneuron](https://github.com/pelrun/perceptionneuron) — but the CRC-8
algorithm itself was never published anywhere, and blind brute-force across 36
command/algorithm/dst combinations plus DTR/RTS toggling found nothing (`docs/02`, T006).
That makes a real reference capture the only sane way forward, not more guessing.

**Currently blocked on two independent things, not one** (`docs/03`, `docs/04`, T007):

1. The first Windows capture attempt caught the wrong USB interface (hand-run Wireshark,
   one interface at a time, instead of `capture.ps1`'s "capture every interface at once").
   Mechanically trivial to fix on the next attempt.
2. Axis Studio (already installed, but it's the **current** PN3/Studio-generation
   software) needs a license the owner doesn't have handy — bought indirectly as a
   Kickstarter backer, key long gone. Static analysis of the installed binaries turned up
   no trace of PNHU01-era support at all (only current-gen model codes), so Axis Studio is
   very likely the wrong software entirely, license or not. The real target is legacy
   **Axis Neuron**, which historically used a physical Wibu dongle for activation —
   and Noitom appears to have stopped issuing new activations for that dongle.

Two things in flight to clear blocker 2, neither blocking the other: an email to
`contact@neuronmocap.com` asking about reissuing/confirming legacy activation, and trying
whether Axis Studio lets the hub connect even unactivated (some trialware gates only
saving/exporting, not the connection itself) — not yet confirmed which it does.

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
