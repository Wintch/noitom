# Protocol research (prior art)

## Goal

Get the Perception Neuron v1 kit fully working on Linux, no Windows, reusing or
extending whatever reverse-engineering already exists.

## What already exists

### 1. The protocol, partially reversed

Repo: [pelrun/perceptionneuron](https://github.com/pelrun/perceptionneuron)
(`nz.py`, `pneuron.lua` — a Wireshark dissector). Very early-stage (7 commits, no
releases), but it documents the essentials:

- Generic framing: `0xfd` (SOF) → `type` (1 byte) → payload → CRC-8 → `0xfe` (EOF)
- Transport: **USB bulk** (protocol `0xFFFF`) **or UDP port 7009** — same framing
  either way.
- Known message types: `0x01` Call, `0x02` Ack, `0x09` IMU data (31-byte payload,
  not decoded field by field), `0x07` firmware upload.
- `Set (0x0a)` command with keys: `0x01` Hub Firmware Version, `0x15` Hub Serial
  Number, **`0x18` Wifi Config**, `0x19` Server Config, `0x30` Wifi Scan. → The
  command to configure WiFi exists, but **nobody published the exact payload**
  (how SSID/password get packed). We would need to capture it ourselves for the
  WiFi path.
- Type `0x09` (IMU data) is **raw sensor data**, not already-fused orientation.
  This matters: the official software (Axis Neuron) does the sensor fusion
  (accelerometer+gyro+magnetometer → orientation) and the skeleton mapping. That
  is **not** reverse-engineered anywhere public.

### 2. Official software (Axis Neuron) — Windows only

- Requires Windows 7 SP1 64-bit minimum, DirectX 11.
- The USB transceiver can enumerate as a **virtual serial port** (typical of an
  FTDI/VCP driver) — a classic weak point under Wine.
- **Zero Wine/Proton/CrossOver/VM reports** anywhere (WineHQ AppDB, ProtonDB,
  CrossOver DB, forums, Reddit) — neither for nor against. Undocumented ground.

### 3. The "official" Linux path the community already uses

Noitom has an SDK called **MocapApi** ([pnmocap/MocapApi](https://github.com/pnmocap/MocapApi))
that does support Linux/macOS/Android/iOS — but **only as a client receiving the
already-processed BVH stream** (over UDP/TCP) from Axis Studio running on Windows.
It never talks to the hardware directly. This is the pattern the whole community
uses, including ROS integrations: Windows does the fusion, Linux consumes the
network stream.

### 4. Wired mode (the alternative to WiFi)

The hub works over **direct USB cable** in addition to WiFi (WiFi is an optional
mode that requires pairing via Axis Neuron). If the USB dongle uses a generic
serial chip (FTDI/CH340/CP210x — common in 2014-2015 hardware), Linux could
recognize it natively as `/dev/ttyUSBx` **with no driver needed**, sidestepping
the undocumented WiFi pairing problem entirely.
→ **Confirmed** — see [`02-linux-usb-bringup.md`](02-linux-usb-bringup.md).

### 5. Accessories

- Remote: official name **"The Shutter"** (paired with "The Rumbler", haptic
  feedback) — a Kickstarter stretch goal. Its documented function is remote
  start/stop of recording, not calibration per se — Axis Neuron has a spacebar
  shortcut for the same thing. Probably not essential.
- WiFi-mode power: **5V/2A** over USB (power bank), confirmed by multiple
  community sources (not an official exact mAh figure, just minimum
  voltage/amperage).

## Possible paths, most to least practical

**A. Wired + own protocol + own fusion (recommended for fully native Linux)**
1. Connect the hub over USB, confirm whether it enumerates as generic serial
   (`/dev/ttyUSB0`) or as proprietary USB. → **Done**, see
   [`02-linux-usb-bringup.md`](02-linux-usb-bringup.md).
2. If generic serial: speak the already-reversed protocol (`0xfd`...CRC8...`0xfe`)
   directly with `pyserial`, no Windows or Wine anywhere.
3. Write our own AHRS filter (Madgwick/Mahony) to fuse each raw IMU sensor
   (~30 nodes) into orientation (quaternion).
4. Map the orientations onto a bone hierarchy in BVH format, with T-pose
   calibration.
   → A real multi-week engineering project, but with zero Windows dependency, not
   even for pairing.

**B. WiFi + reverse-engineer the pairing command ourselves**
Same as A but over WiFi: would require capturing real Axis Neuron traffic while it
pairs the hub (Wireshark + `pneuron.lua`) to deduce the `0x18 Wifi Config` command
payload — i.e. running Axis Neuron **once** (on some borrowed Windows box/VM/
whatever) just for that capture. After that, no more Windows needed. More work
than A for no real gain, unless the wired mode turns out not to work.

**C. Try Wine directly**
Cheap to attempt, zero guarantees (no precedent exists). If the USB transceiver
enumerates as standard serial, Wine might not even need the VCP driver (Linux
would already expose it). Worth trying in parallel with A, but not something to
depend on.

We are pursuing **A**, with an attempted shortcut through a one-time Windows
capture (see [`03-windows-capture-procedure.md`](03-windows-capture-procedure.md))
to skip reverse-engineering the CRC-8 by hand — currently blocked, see
[`04-licensing-blocker.md`](04-licensing-blocker.md) and
[`docs/pruebas.jsonl`](pruebas.jsonl) T6-T7.
