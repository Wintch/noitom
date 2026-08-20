# Next step

> ## START HERE (2026-08-20, T007 — end of the kickoff day)

Two independent blockers, both on the Windows side, neither blocking the other:

1. **Redo the capture with `capture.ps1`, not by hand.** It's already sitting at
   `C:\debug_noitom\windows-kit\` on the owner's machine. The first attempt (T007) missed
   the hub entirely because it captured one USBPcap interface at a time by hand instead of
   letting the script capture all of them at once — see `docs/03` for exactly what went
   wrong and why the script avoids it.
2. **Licensing.** Axis Studio (installed, current-generation) needs an activation the
   owner doesn't have, and static analysis suggests it doesn't even support the old
   PNHU01 hub anymore regardless of license — see `docs/04`. Email drafted to
   `contact@neuronmocap.com` (not yet sent as of T007). Also worth just trying to open
   Axis Studio unlicensed and seeing exactly where it stops — some trialware still allows
   connecting hardware, only gating save/export.

**The actual next action**: once Axis Studio can reach the point of pressing "Connect" on
the hub (licensed or not), rerun the capture per `docs/03`, then:

```bash
python3 scripts/parse-pn-capture.py windows-kit/capturas/connect_*-trim.pcapng
```

If that turns up real `0xfd...0xfe` frames, extract the "connect" command bytes and replay
them from `/dev/ttyUSB0` on Linux with `pyserial` — that's the point where the CRC-8
mystery stops mattering, we'd just be repeating known-good bytes.

**Do not re-litigate**: blind CRC-8 brute-force from Linux (36 combinations, T006) is
exhausted — don't retry variations of it before the reference capture exists. There are
too many unexplored axes (framing fields, `id`/`src` values, baud rate, algorithm) for
guessing to be worth the time versus just getting the real bytes once.
