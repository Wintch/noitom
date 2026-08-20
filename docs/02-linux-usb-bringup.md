# Linux USB bring-up

## Result: the hub is a generic CP210x serial bridge

Confirmed by plugging the PNHU01 hub into a Linux box over USB (`journalctl -k`,
no root needed):

```
usb 1-1: New USB device found, idVendor=10c4, idProduct=ea60, bcdDevice= 1.00
usb 1-1: Product: CP2102 USB to UART Bridge Controller
usb 1-1: Manufacturer: Silicon Labs
usb 1-1: cp210x converter now attached to ttyUSB0
```

The Linux kernel binds the built-in `cp210x` driver automatically — nothing to
install. Node created: `/dev/ttyUSB0`, group `dialout`.

**This validates Path A in practice, not just in theory**: no Windows, no Wine, no
proprietary driver needed for the transport layer. See
[`docs/pruebas.jsonl`](pruebas.jsonl) T1.

## Group permission

The user needs to be in the `dialout` group to open `/dev/ttyUSB0`. After adding
the user to the group, the *current* shell session does not pick it up
automatically (expected, no new sudo needed) — `sg dialout -c "..."` (with stdin
redirected to `/dev/null` so it never hangs waiting for a password) opens the port
fine without a full relogin. T2.

## Passive probe: silent hub, as expected

Probed 8 baud rates (115200/921600/1000000/230400/57600/9600/460800/500000): the
hub sends nothing on its own after connecting. This is an honest negative, not a
failure — the hub almost certainly needs an explicit "connect" command before it
streams anything. T3.

## Active probe without a reference capture: honest negative

Before resigning ourselves to needing a Windows capture, we tried actively poking
the hub (not just listening):

- 36 combinations: 3 commands (a reconstructed `connect`, `GetConfig key=0x01`
  firmware version, `GetConfig key=0x15` serial number) × 6 candidate CRC-8
  algorithms (Maxim/Dallas, CCITT, SAE J1850, ROHC, plain XOR, plain sum) × 2 `dst`
  values (`0xc0` Hub, `0x00` broadcast), all at 115200 baud → **0 responses across
  all 36.**
- Toggled DTR/RTS lines (false→true) in case the hub was waiting on that signal to
  "wake up" → **0 bytes after the toggle.**

Conclusion: we exhausted what's reasonable to try blind. The remaining unknowns
(`id`/`src` values other than `0x00`/`0xa0`, undocumented framing fields, a send
baud rate other than 115200, or a CRC algorithm not considered) are too many
combinations to brute-force without a real reference. T6.

**Next step**: get a real reference capture — see
[`03-windows-capture-procedure.md`](03-windows-capture-procedure.md). Once we have
the exact bytes Axis Neuron sends, we can replay them verbatim without needing to
understand the CRC-8 algorithm at all.
