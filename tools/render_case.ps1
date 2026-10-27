# =============================================================================
#  render_case.ps1 - ekspor STL dari OpenSCAD lalu render ke PNG
#
#  Butuh: OpenSCAD (CLI) + Python 3 dengan Pillow & numpy.
#  Renders yang sudah jadi ada di hardware/render_mx.png dan render_tactile.png.
#
#  Pemakaian:
#    powershell -ExecutionPolicy Bypass -File tools\render_case.ps1
#    powershell -ExecutionPolicy Bypass -File tools\render_case.ps1 -OpenScad "C:\Program Files\OpenSCAD\openscad.exe"
# =============================================================================
[CmdletBinding()]
param(
    [string]$OpenScad = "",
    [string]$Python = "python"
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$stlDir = Join-Path ([System.IO.Path]::GetTempPath()) 'mp_stl'
$scadDir = Join-Path ([System.IO.Path]::GetTempPath()) 'mp_scad'
New-Item -ItemType Directory -Force -Path $stlDir, $scadDir | Out-Null

function Find-OpenScad {
    if ($OpenScad -and (Test-Path -LiteralPath $OpenScad)) { return $OpenScad }
    $cmd = Get-Command openscad -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $guess = Join-Path $env:LOCALAPPDATA 'macropad-tools\openscad\openscad-2021.01\openscad.exe'
    if (Test-Path -LiteralPath $guess) { return $guess }
    return $null
}

$osc = Find-OpenScad
if (-not $osc) {
    Write-Host "OpenSCAD tidak ditemukan." -ForegroundColor Red
    Write-Host "  pasang dari https://openscad.org/downloads.html, atau jalankan dengan -OpenScad <path>"
    exit 1
}
Write-Host "OpenSCAD : $osc"

# PART di file .scad tidak bisa diubah lewat -D (kutip string bikin ribet di
# PowerShell), jadi tiap part dibuat file sementara dengan PART yang diganti.
foreach ($v in @('mx', 'tactile')) {
    foreach ($p in @('plate', 'tray')) {
        $src = Get-Content -LiteralPath (Join-Path $root "hardware\case_$v.scad") -Raw
        $patched = $src -replace 'PART = "both";', ('PART = "' + $p + '";')
        $tmp = Join-Path $scadDir "$($v)_$p.scad"
        Set-Content -LiteralPath $tmp -Value $patched -Encoding ascii

        $stl = Join-Path $stlDir "$($v)_$p.stl"
        Remove-Item -LiteralPath $stl -Force -ErrorAction SilentlyContinue
        # openscad.exe adalah aplikasi GUI: pakai Start-Process + -Wait, karena
        # kalau dipanggil dengan redirection PowerShell (2>$null / 2>&1) proses
        # tidak jalan sama sekali dan $LASTEXITCODE tidak terisi.
        $proc = Start-Process -FilePath $osc -ArgumentList @('-o', $stl, $tmp) `
            -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $stl)) {
            throw "gagal render $v $p (exit $($proc.ExitCode))"
        }
        Write-Host ("  {0,-18} {1:N0} KB" -f "$($v)_$p.stl", ((Get-Item $stl).Length / 1KB))
    }
}

Write-Host "render PNG..."
& $Python (Join-Path $root 'tools\render_case.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "selesai: hardware\render_mx.png, hardware\render_tactile.png"
