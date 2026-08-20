# The licensing blocker

## What's installed vs. what's needed

The owner's Windows install already has **Axis Studio** (`Program Files\NOITOM\Axis
Studio\`) — the **current** software, for the Perception Neuron 3 / PN Studio
generation. It requires a paid license (bought indirectly, as a 2014 Kickstarter
backer) and the owner does not have the activation key at hand.

## Static analysis of what's already installed: inconclusive, and probably for a
## real reason

Before assuming a capture needs the license at all, we pulled a set of Axis
Studio binaries (`nc_sdk.dll`, `nclib.dll`, `mbx_sdk.dll`, `dev_hwup.plg`,
`wmod_hwup.plg`, and others — see `windows-kit/axis-studio-extract/`, gitignored,
Noitom's proprietary code, never redistribute it) and searched them for anything
reusable: a CRC-8 table, the `0xfd...0xfe` framing, PID/VID constants for the old
hub.

**No v1-era markers anywhere** — no `PNHU`, `CP210`, or `Silicon Labs` string in
any binary. There is generic "hub" infrastructure (`mcps.comm_type.inertial_hub`,
`SensorHubRef`, `NCGetHubFrequency`), but the model codes actually present —
`N3T`, `U1H`, `U2H`, `U2P` — belong to the **current PN3/Studio family**, not v1.
This lines up with the firmware files shipped alongside it (`pn3_*.fw`,
`pnsplus_*.fw`, `hwup_*.fw` — nothing PNHU01-specific).

**Conclusion: Axis Studio most likely dropped support for the PNHU01 hub
entirely.** Not worth analyzing these binaries further for this goal — they're
the wrong SDK generation.

## The activation system, as far as it could be researched

`noitom.com/serviceinfo.html?id=1` and `support.neuronmocap.com` both return
HTTP 403 to direct fetches, so this is pieced together from search-result
snippets, not a primary source — treat it as a starting point to verify, not a
confirmed fact:

- **Current activation** (`account.noitom.com`) uses a "Product ID" printed on the
  hardware, typically starting with the same model prefix found in the
  binaries above (e.g. `U1H...`). **This does not apply to the PNHU01** — it
  predates this system.
- **Legacy activation** (the era our hub is actually from) used a **physical Wibu
  dongle** (WibuKey/CodeMeter), not a text CD key. According to what could be
  found, **Noitom no longer issues new activations for the legacy version** —
  it only keeps working if the dongle was already activated previously; beyond
  that there's mention of a manual "activation by return" process through
  support.

This is consistent with what [`01-protocol-research.md`](01-protocol-research.md)
already noted: zero Wine/Proton/VM reports for this software, anywhere. It's not
just old — Noitom appears to have actually closed the activation path for this
hardware generation.

## What this changes

The "get the license and run Axis Neuron once" path went from a simple errand to
**open-ended** — it depends on either finding an old, already-activated Wibu
dongle, or Noitom support agreeing to something exceptional for a decade-old
Kickstarter unit. It does **not** change Path A
([`01-protocol-research.md`](01-protocol-research.md)) as the priority — if
anything it reinforces it: the project's unlock shouldn't hinge on reviving a
2014 license Noitom has since discontinued.

Two things worth trying in parallel, neither blocking the other:

1. **Email `contact@neuronmocap.com`** asking whether a legacy activation can be
   reissued/reactivated for a Kickstarter backer, whether a legacy installer +
   activation path still exists at all, or a plain confirmation that neither is
   possible.
2. **Try opening Axis Studio anyway, unlicensed.** Some trial/unactivated modes
   still allow connecting hardware and only gate saving/exporting — if it gets far
   enough to show the hub and accept "Connect", that's enough to run the capture
   in [`03-windows-capture-procedure.md`](03-windows-capture-procedure.md), license
   or not. Not yet confirmed what error, if any, Axis Studio actually shows when
   trying to connect unlicensed.
