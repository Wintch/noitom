# windows-kit

The one Windows-side artifact this project needs: a script to capture the USB
handshake between Axis Neuron and the PNHU01 hub, so it never has to be repeated.

Full procedure, requirements, and what went wrong the first time:
[`../docs/03-windows-capture-procedure.md`](../docs/03-windows-capture-procedure.md).

- `capture.ps1` — run this, as Administrator, on the Windows machine.
- `capturas/` — output folder (gitignored — raw captures aren't committed, see
  [`../docs/04-licensing-blocker.md`](../docs/04-licensing-blocker.md) for the
  current blocker before rerunning this).
- `axis-studio-extract/` — Noitom's own DLLs, pulled for local static analysis only.
  Gitignored on purpose; never redistribute these.
- `vendor-backup/` — durable local backup of the working, unlicensed legacy Axis
  Neuron install (`docs/04`, `docs/05`): the installer zip, the full installed
  app folder, and its firmware/bodies config. Noitom is unlikely to ever make
  this available again, so it's worth keeping on this disk indefinitely - but
  gitignored on purpose, same reasoning as `axis-studio-extract/`: never
  redistribute Noitom's proprietary software under this repo's MIT license.
