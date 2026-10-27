# =============================================================================
#  deploy.ps1 - salin firmware macropad ke board ESP32-S2 Mini (drive CIRCUITPY)
#
#  Pemakaian:
#     powershell -ExecutionPolicy Bypass -File tools\deploy.ps1
#     powershell -ExecutionPolicy Bypass -File tools\deploy.ps1 -Bringup
#     powershell -ExecutionPolicy Bypass -File tools\deploy.ps1 -Drive E:\
#
#  Tanpa -Bringup : copy kb.py + code.py  (mode normal)
#  -Bringup       : copy bringup.py sebagai code.py (mode tes hardware)
#
#  KMK diunduh otomatis ke CIRCUITPY\kmk kalau belum ada.
# =============================================================================
[CmdletBinding()]
param(
    [string]$Drive,
    [switch]$Bringup,
    [switch]$ForceKmK
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$fwDir = Join-Path $root 'firmware'

function Write-Step($msg) { Write-Host "  $msg" }
function Write-Ok($msg) { Write-Host "  [ok] $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }

function Find-CircuitPy {
    try {
        $vol = Get-Volume -ErrorAction Stop |
            Where-Object { $_.FileSystemLabel -eq 'CIRCUITPY' -and $_.DriveLetter }
        if ($vol) { return ($vol[0].DriveLetter + ':\') }
    } catch {
        # modul Storage tidak tersedia: lanjut ke cara kedua
    }

    foreach ($d in (Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
        if (-not $d.Root) { continue }
        try {
            if (Test-Path -LiteralPath (Join-Path $d.Root 'boot_out.txt') -ErrorAction Stop) {
                return $d.Root
            }
        } catch { }
    }
    return $null
}

Write-Host ""
Write-Host "DEPLOY MACROPAD S2 MINI" -ForegroundColor Cyan
Write-Host "======================="

if (-not $Drive) {
    Write-Step "mencari drive CIRCUITPY..."
    $Drive = Find-CircuitPy
}

if (-not $Drive) {
    Write-Host ""
    Write-Host "Drive CIRCUITPY tidak ditemukan." -ForegroundColor Red
    Write-Host ""
    Write-Host "  - Pastikan board tersambung dengan kabel USB DATA (bukan charge-only)."
    Write-Host "  - Board harus sudah jalan CircuitPython (drive CIRCUITPY muncul di Explorer)."
    Write-Host "  - Kalau tidak muncul: tekan RESET, atau flash ulang CircuitPython (README Langkah 1)."
    Write-Host ""
    exit 1
}

$Drive = $Drive.TrimEnd('\') + '\'
if (-not (Test-Path -LiteralPath (Join-Path $Drive 'boot_out.txt'))) {
    Write-Warn2 "di $Drive tidak ada boot_out.txt - yakin ini drive CIRCUITPY?"
}

Write-Ok "board di $Drive"
try {
    $boot = Get-Content -LiteralPath (Join-Path $Drive 'boot_out.txt') -ErrorAction SilentlyContinue |
        Select-Object -First 3
    if ($boot) { Write-Step ("board: " + ($boot -join ' | ')) }
} catch { }

# ------------------------------------------------------------------ 1. firmware
# semua .py di firmware/ ikut dikopi (kb.py, code.py, ui.py, ssd1306.py, font5x7.py)
$fwFiles = Get-ChildItem -LiteralPath $fwDir -Filter '*.py' |
    Where-Object { $_.Name -ne 'bringup.py' }

if (-not $fwFiles) { throw "tidak ada file .py di $fwDir" }

foreach ($f in $fwFiles) {
    Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $Drive $f.Name) -Force
    Write-Ok "copy $($f.Name)"
}

if ($Bringup) {
    Copy-Item -LiteralPath (Join-Path $fwDir 'bringup.py') -Destination (Join-Path $Drive 'code.py') -Force
    Write-Ok "copy bringup.py -> code.py (mode tes)"
}

# ------------------------------------------------------------------ 2. KMK
$kmkDir = Join-Path $Drive 'kmk'
$needKmK = $ForceKmK -or -not (Test-Path -LiteralPath (Join-Path $kmkDir 'kmk_keyboard.py'))

if ($needKmK) {
    Write-Step "KMK belum ada di board, mengunduh..."

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('kmk_' + [guid]::NewGuid().ToString('N'))
    $zip = Join-Path $tmp 'kmk.zip'
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null

    try {
        $url = 'https://github.com/KMKfw/kmk_firmware/archive/refs/heads/main.zip'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
        Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force

        $extracted = Join-Path $tmp 'kmk_firmware-main\kmk'
        if (-not (Test-Path -LiteralPath $extracted)) {
            throw "struktur zip KMK tidak dikenal (folder kmk tidak ditemukan)"
        }

        if (Test-Path -LiteralPath $kmkDir) { Remove-Item -LiteralPath $kmkDir -Recurse -Force }
        Copy-Item -LiteralPath $extracted -Destination $kmkDir -Recurse -Force
        Write-Ok "KMK terpasang ($((Get-ChildItem $kmkDir -Recurse -File).Count) file)"
    } catch {
        Write-Host ""
        Write-Host "Gagal memasang KMK: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Download manual: https://github.com/KMKfw/kmk_firmware/archive/refs/heads/main.zip"
        Write-Host "lalu copy folder 'kmk' ke $Drive"
        exit 1
    } finally {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Ok "KMK sudah ada di board (pakai -ForceKmK untuk memperbarui)"
}

# ------------------------------------------------------------------ selesai
Write-Host ""
Write-Host "Selesai. Board akan restart sendiri (~2 detik)." -ForegroundColor Green
if ($Bringup) {
    Write-Host "Buka REPL (https://code.circuitpython.org) lalu tekan tombol satu per satu."
} else {
    Write-Host "Kalau tombol belum bereaksi: jalankan  tools\deploy.ps1 -Bringup  untuk tes hardware."
}
Write-Host ""
exit 0
