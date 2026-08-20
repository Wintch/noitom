<#
.SYNOPSIS
    Captures USB traffic between Axis Neuron and the PNHU01 hub (Perception Neuron v1).
    Adapted from ../../reverb-g2/windows-kit2/capture.ps1 (same mechanism, different
    protocol on top). Goal: capture the "connect" handshake ONCE so we never need
    Windows again.

.DESCRIPTION
    Discovers ALL USBPcap interfaces on its own (interface numbers vary between
    installs, never hardcoded). Starts one dumpcap process PER interface, all at once,
    each to its own file sharing a per-run timestamp.

    The hub speaks USB bulk (CP210x chip, VID 10c4 PID ea60) with its own framing
    (0xfd ... 0xfe). Unlike the Reverb G2 (HID), the data we care about is in
    usb.capdata directly -- no usbhid.data needed.

    WHAT MATTERS: start capturing BEFORE Axis Neuron sends the "connect" command to
    the hub, not after. If you start capturing with everything already connected, you
    miss exactly the handshake we need.

.PARAMETER Label
    Name for this run, e.g. "connect" or "wificonfig".

.EXAMPLE
    .\capture.ps1 -Label connect

    Run in PowerShell AS ADMINISTRATOR from this folder (USBPcap needs the driver at
    admin level).
#>
param(
    [Parameter(Mandatory = $true)][string]$Label
)

$ErrorActionPreference = "Stop"

# --- Find tshark/dumpcap on their own: PATH first, then the default 64/32-bit
#     locations, without assuming the system drive is C: --------------------------
function Find-WiresharkTool($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if (-not $base) { continue }
        $p = Join-Path $base "Wireshark\$name"
        if (Test-Path $p) { return $p }
    }
    return $null
}

$Tshark  = Find-WiresharkTool "tshark.exe"
$Dumpcap = Find-WiresharkTool "dumpcap.exe"

if (-not $Tshark -or -not $Dumpcap) {
    Write-Host "ERROR: cannot find tshark/dumpcap on PATH or in the default" -ForegroundColor Red
    Write-Host "Program Files\Wireshark location (on any drive)." -ForegroundColor Red
    Write-Host "Install Wireshark and CHECK the USBPcap component during install, then reboot."
    exit 1
}
Write-Host "Using tshark:  $Tshark"
Write-Host "Using dumpcap: $Dumpcap"

# --- Discover ALL USBPcap interfaces, without guessing numbers -------------------
$ifaceLines = & $Tshark -D | Select-String "USBPcap"
if (-not $ifaceLines) {
    Write-Host "ERROR: no USBPcap interface shows up in 'tshark -D'." -ForegroundColor Red
    Write-Host "Check that USBPcap is installed and that you rebooted after installing it."
    exit 1
}

$ifaces = foreach ($line in $ifaceLines) {
    if ($line -match '^(\d+)\.\s+(\S+)') {
        [PSCustomObject]@{ Num = $Matches[1]; Name = $Matches[2] }
    }
}

Write-Host ""
Write-Host "=== USBPcap interfaces found (ALL of them get captured, nothing to pick) ==="
$ifaces | ForEach-Object { Write-Host ("  {0}. {1}" -f $_.Num, $_.Name) }
Write-Host ""

$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = "capturas"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host "=========================================================="
Write-Host " SHORT CAPTURE ON PURPOSE."
Write-Host ""
Write-Host " Order (this exact order matters):"
Write-Host "  1. PNHU01 hub connected over USB, but Axis Neuron still CLOSED"
Write-Host "     (or open, but WITHOUT pressing 'Connect' yet)."
Write-Host "  2. Start this capture now (with this same Enter)."
Write-Host "  3. ONLY THEN open Axis Neuron (if not open yet) and press 'Connect'."
Write-Host "  4. Wait for it to connect / calibrate briefly (hub beep or light)."
Write-Host "  5. Come back here and press Enter, at most 15-20s after connecting."
Write-Host "     More time doesn't add handshake data, it just makes the file bigger"
Write-Host "     (the hub sends continuous IMU data once connected -- we don't need that)."
Write-Host "=========================================================="
Read-Host "Enter to start"

# --- One dumpcap process PER interface, all starting together --------------------
$procs = foreach ($ifc in $ifaces) {
    $file = Join-Path $outDir ("{0}_USBPcap{1}_{2}.pcapng" -f $Label, $ifc.Num, $stamp)
    Write-Host "  capturing interface $($ifc.Num) -> $file"
    Start-Process -FilePath $Dumpcap -ArgumentList @("-i", $ifc.Num, "-w", $file) -PassThru -WindowStyle Hidden
}

Write-Host ""
Write-Host ">>> Capturing on $($ifaces.Count) interface(s) at once. Press Connect in Axis Neuron and come back." -ForegroundColor Yellow
Read-Host "Enter to STOP the capture"

foreach ($p in $procs) {
    if (-not $p.HasExited) {
        Stop-Process -Id $p.Id -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=== trimming (dropping the high-volume IMU streaming) and exporting ==="
foreach ($ifc in $ifaces) {
    $raw = Join-Path $outDir ("{0}_USBPcap{1}_{2}.pcapng" -f $Label, $ifc.Num, $stamp)
    if (-not (Test-Path $raw) -or (Get-Item $raw).Length -eq 0) {
        Write-Host "  USBPcap$($ifc.Num): no data, skipping."
        continue
    }
    $trimmed = Join-Path $outDir ("{0}_USBPcap{1}_{2}-trim.pcapng" -f $Label, $ifc.Num, $stamp)
    $tsv     = Join-Path $outDir ("{0}_USBPcap{1}_{2}.tsv" -f $Label, $ifc.Num, $stamp)

    & $Tshark -r $raw -Y "usb.idVendor == 0x10c4 || usb.capdata" -w $trimmed 2>$null
    & $Tshark -r $trimmed -T fields `
        -e frame.time_relative -e usb.device_address -e usb.endpoint_address `
        -e usb.transfer_type -e usb.capdata > $tsv

    $hit      = Select-String -Path $tsv -Pattern "fd" -Quiet
    $sizeRaw  = (Get-Item $raw).Length
    $sizeTrim = (Get-Item $trimmed).Length
    $marca    = if ($hit) { "<-- has 'fd' bytes (possible SOF), candidate for the hub" } else { "" }
    Write-Host ("  USBPcap{0}: {1} bytes raw -> {2} bytes trimmed  {3}" -f $ifc.Num, $sizeRaw, $sizeTrim, $marca)
}

Write-Host ""
Write-Host "Done. Folder '.\$outDir\', prefix '${Label}_*_${stamp}'." -ForegroundColor Green
Write-Host "Take ALL the *-trim.pcapng files (they're small, no harm taking extra)."
Write-Host "The real parsing (looking for 0xfd...0xfe) happens on the Linux side, no need"
Write-Host "to understand the marker above -- it's just a hint, not the final answer."
