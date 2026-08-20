# The pragmatic alternative: Axis Neuron's built-in BVH broadcast

## Why this doc exists

[`05-crc8-solved.md`](05-crc8-solved.md) unblocks the fully-native-Linux path (A in
[`01-protocol-research.md`](01-protocol-research.md)), but that path is still a
real multi-week engineering project (raw IMU decoding, sensor fusion, skeleton
mapping — none of it reverse-engineered anywhere public). If the actual goal is
*using* the mocap data (e.g. in Unity), not just running it Linux-native, there is a
much shorter path that T011 ([`pruebas.jsonl`](pruebas.jsonl)) turned up, and it
needs none of the protocol work above.

## The feature

Legacy Axis Neuron has a built-in **Broadcasting** tab (Settings menu) that streams
the live skeleton over the network:

- **Port 7001** — raw BVH (displacement + rotation), TCP or UDP.
- **Port 7003** — calculated data (position/velocity/acceleration).
- A skeleton-type selector includes **"Axis Legacy"**, specifically for the
  PN32/PNHU01-era hardware (as opposed to the newer Axis Studio model codes) —
  this is the exact hardware generation this kit is.

No license needed — this is a feature of the same unlicensed build already
confirmed working in [`04-licensing-blocker.md`](04-licensing-blocker.md)/T008.
Still documented today in Noitom's current support articles (for Houdini, Cinema
4D, Unreal 5 real-time streaming), and mirrored by third-party tools like
`axis_neuron_broadcaster`, which hard-code these same 7001/7003 ports.

## Consuming it in Unity

[keijiro/NeuronAnimator](https://github.com/keijiro/NeuronAnimator) is an
open-source Unity plugin — "a minimal subset of the Perception Neuron SDK" — that
wraps Noitom's own NeuronDataReader (NDR) library, whose job is exactly this: connect
to the 7001/7003 broadcast and drive a humanoid rig. Noitom also ships an official
Unity package that does the same thing (their support article "Live Stream data
into Unity"). Either works without Axis Studio and without a license.

## What NOT to do

A community VRPN fork,
[pfiguero/vrpn-PerceptionNeuron](https://github.com/pfiguero/vrpn-PerceptionNeuron)
(the likely explanation for the `vrpnNoitom.dll` noticed during the static analysis
in `04-licensing-blocker.md`), talks to the hub **directly** via `hidapi`, bypassing
Axis Neuron entirely. That's the same reverse-engineering problem this project is
already solving on Linux, not a shortcut — skip it. Its companion Unity client is a
4-commit, 2-star, undocumented proof of concept, not production-viable either.

iClone's Motion LIVE plugin is capture-then-export (record, then export FBX to
Unity), not live streaming — not useful if real-time is the actual requirement.

## The practical recommendation

Run legacy Axis Neuron 3.8.x unlicensed (already confirmed working, T008) → enable
BVH Broadcasting with the "Axis Legacy" skeleton → consume it in Unity with
NeuronAnimator or Noitom's official SDK package. This needs a Windows box running
Axis Neuron as the one thing that talks to the hub (a real machine or a VM — see
"Wine" below for why that's not yet a confirmed alternative), same as any of the
capture work already done, but **no further protocol reverse-engineering at all**.

## Whether Wine changes the "needs a Windows box" part

Researched in parallel (T011): no WineHQ AppDB entry and no community report for
Axis Neuron running under Wine/Proton/Bottles/a VM exists anywhere, positive or
negative — it's simply untested. The serial passthrough itself (`/dev/ttyUSB0` via
`~/.wine/dosdevices/comN`) is a normal, well-documented Wine mechanism, not a known
problem. One real risk did surface: a documented Wine bug capping reported serial
baud rate at 115200, which broke continuous high-rate streaming for an unrelated
Windows app over USB-serial — untested here, but worth checking early if Wine is
tried, since it would fail silently rather than loudly. Bottom line: worth a cheap
empirical try, not something to plan around before actually testing it.
