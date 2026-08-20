# Hardware inventory

Original Perception Neuron (Noitom, Kickstarter 2014). Wired hub with sensor straps,
manufacture date printed on the unit: **2015-07-20**. Backed on Kickstarter by the
owner, not bought retail — see [`04-licensing-blocker.md`](04-licensing-blocker.md)
for why that matters.

## Parts (from physical labels on the owner's kit)

| Part | Label code | Notes |
|---|---|---|
| Hub | **PNHU01** (Perception Neuron HUb, rev. 01) | Serial/lot `de000018`, date `2015-07-20`, unit marked **5V/2A** (matches community documentation for WiFi-mode power) |
| Strap/sensor | **PNS00004** | Perception Neuron Sensor #4 |
| Strap/sensor | **PNS0038** | Perception Neuron Sensor #38 (factory serial numbering, not a count of sensors owned) |
| Internal cable | **PNS00161** | Internal cable/connection between sensors |
| Main harness (upper) | **PNS00072** | The main harness has 2 parts |
| Main harness (lower) | **PNS00001** | |
| Strap/sensor — right leg | **PNS00002** | Label reads "right leg" |
| Strap/sensor — right arm | **PNS00092** | |
| Strap/sensor — left foot | **PNS00037** | |

**Kit tier confirmed by the owner: the 11-sensor Kickstarter tier** (matches the
11-neuron minimum on Axis Neuron's own Mode Hint screen, `docs/pruebas.jsonl` T019).
Individual straps/sensors below this line are still not all inventoried by label.

The owner used this kit successfully for some time before this project (good
captures, per the owner directly) and reports always wanting, but never reliably
getting, all 11 sensors registering at once — i.e. the partial-sensor-count problem
investigated in T018-T023 is a **long-standing characteristic of this specific kit**,
not a new failure that appeared during this project's testing.

## FCC ID search: negative, treated as real

No FCC ID was found for the PNHU01 hub. The full grantee listing for `2ABTR`
(Beijing Noitom Technology) on fccid.io/fcc.report was checked end to end — no
2014-2015 entries, nothing containing "hub", "PN", or "transceiver". Every 2ABTR
filing found postdates the v1 hub (Hi5 Gloves ~2016, Perception Neuron
Studio/3 ~2020). Most likely explanation: the v1 hub used a pre-certified OEM WiFi
module rather than its own FCC ID — common for crowdfunded hardware of that era.
Not worth pursuing further; there is no recoverable official manual down this path.

## Market context (for the e-waste angle, not the engineering)

- **Kickstarter (2014):** 1,329 backers, US$571,908 raised (more than double the
  US$250k goal) — at the time, the most-funded Kickstarter project from a Chinese
  company. That is backers, not units (each could order 9/18/32-sensor kits plus
  add-ons); no public total-units figure exists post-campaign.
- By the time Perception Neuron 2.0 shipped (2016), Noitom's press material
  described the v1 as **"sold out worldwide"** — roughly two years of active
  commercial life (2015-2016) before replacement. A real niche-professional
  product (VFX/games/robotics/research), not mass-market — likely a few thousand
  kits total, no official figure confirmable.
- **Support status today (2026)**: Windows-only Axis Neuron (legacy, PN32/v1) is
  still listed on Noitom's downloads page alongside Axis Studio (current, for
  Perception Neuron Studio/3) — see
  [`04-licensing-blocker.md`](04-licensing-blocker.md) for why the download
  existing does not mean it is usable. A Mac version existed and was pulled (a
  now-dead forum thread titled *"Neuron Axis Mac version removed downloads
  section"* is the only trace). **Linux never had official hardware support** —
  the only "official" thing touching Linux is the MocapApi SDK
  ([pnmocap/MocapApi](https://github.com/pnmocap/MocapApi)), and that is a
  network client for an already-fused BVH stream, not a hardware driver.

**Rough e-waste estimate (component-based, high uncertainty, no official weight
data)**: ~0.3-0.6 kg per kit (1 g/sensor is an official spec; hub and
harness/cables are estimated). Extrapolated: ~400-800 kg on the confirmed
Kickstarter-backer floor (1,329 kits), up to ~0.9-3 tonnes on a speculative
3,000-5,000 total-units estimate through the "sold out worldwide" point. A hard
number — weighing the owner's actual kit — is still pending.
