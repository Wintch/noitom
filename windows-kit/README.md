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
