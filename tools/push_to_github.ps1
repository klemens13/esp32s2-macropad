# =============================================================================
#  push_to_github.ps1 - buat repo GitHub dan push proyek ini dalam satu perintah
#
#  Prasyarat (sekali saja):
#    1. install Git        : winget install --id Git.Git -e
#    2. install GitHub CLI : winget install --id GitHub.cli -e
#    3. login              : gh auth login
#
#  Pemakaian:
#    powershell -ExecutionPolicy Bypass -File tools\push_to_github.ps1
#    powershell -ExecutionPolicy Bypass -File tools\push_to_github.ps1 -Repo macropad-s2 -Private
#
#  Script ini TIDAK menyimpan token apa pun. Autentikasi sepenuhnya milik gh.
# =============================================================================
[CmdletBinding()]
param(
    [string]$Repo = 'esp32s2-macropad',
    [switch]$Private,
    [string]$Description = 'Macropad ESP32-S2 Mini: 12 tombol + OLED status/companion (versi MX & tactile)'
)

$ErrorActionPreference = 'Stop'

function Write-Step($m) { Write-Host "  $m" }
function Write-Ok($m) { Write-Host "  [ok] $m" -ForegroundColor Green }
function Write-Warn2($m) { Write-Host "  [!]  $m" -ForegroundColor Yellow }

$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

Write-Host ""
Write-Host "PUSH KE GITHUB" -ForegroundColor Cyan
Write-Host "=============="
Write-Step "folder : $root"
Write-Step "repo   : $Repo ($(if ($Private) { 'private' } else { 'public' }))"

# ---------------------------------------------------------------- 1. prasyarat
$git = Get-Command git -ErrorAction SilentlyContinue
$gh = Get-Command gh -ErrorAction SilentlyContinue

if (-not $git -or -not $gh) {
    Write-Host ""
    Write-Host "Git / GitHub CLI belum terpasang." -ForegroundColor Red
    Write-Host "Jalankan dulu (PowerShell baru setelah install):"
    if (-not $git) { Write-Host "  winget install --id Git.Git -e" }
    if (-not $gh) { Write-Host "  winget install --id GitHub.cli -e" }
    Write-Host "  gh auth login"
    exit 1
}

# ---------------------------------------------------------------- 2. auth
$authOk = $false
try { gh auth status 2>&1 | Out-Null; $authOk = ($LASTEXITCODE -eq 0) } catch { $authOk = $false }

if (-not $authOk) {
    Write-Host ""
    Write-Host "Belum login ke GitHub." -ForegroundColor Red
    Write-Host "  gh auth login     (pilih GitHub.com -> HTTPS -> login lewat browser)"
    exit 1
}
Write-Ok "sudah login ke GitHub"

$login = (gh api user --jq .login).Trim()
Write-Step "akun   : $login"

# ---------------------------------------------------------------- 3. git lokal
if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) {
    git init -b main | Out-Null
    Write-Ok "git init (branch main)"
} else {
    Write-Ok "repo git sudah ada"
}

# identitas commit (pakai identitas GitHub kalau belum diatur)
$name = (git config user.name) 2>$null
$email = (git config user.email) 2>$null
if (-not $name) {
    git config user.name $login
    Write-Step "set user.name = $login"
}
if (-not $email) {
    git config user.email "$login@users.noreply.github.com"
    Write-Step "set user.email = $login@users.noreply.github.com"
}

# ---------------------------------------------------------------- 4. commit
git add -A
$pending = (git status --porcelain) 2>$null
if ($pending) {
    git commit -m "Macropad ESP32-S2 Mini: 12 tombol + OLED (MX & tactile)" | Out-Null
    Write-Ok "commit dibuat"
} else {
    Write-Step "tidak ada perubahan untuk di-commit"
}

# ---------------------------------------------------------------- 5. repo github
$remoteUrl = "https://github.com/$login/$Repo.git"
$hasRemote = $false
try {
    $remotes = git remote
    if ($remotes -contains 'origin') { $hasRemote = $true }
} catch { }

if (-not $hasRemote) {
    $vis = if ($Private) { '--private' } else { '--public' }
    Write-Step "membuat repo github.com/$login/$Repo ..."
    try {
        gh repo create $Repo --source . --remote origin --push $vis --description $Description | Out-Null
        Write-Ok "repo dibuat dan di-push"
        Write-Host ""
        Write-Host "Selesai: $remoteUrl" -ForegroundColor Green
        exit 0
    } catch {
        Write-Warn2 "gh repo create gagal: $($_.Exception.Message)"
        Write-Step "mencoba menambah remote dan push manual..."
        git remote add origin $remoteUrl
        $hasRemote = $true
    }
}

Write-Step "push ke origin/main ..."
git push -u origin main

Write-Host ""
Write-Host "Selesai: $remoteUrl" -ForegroundColor Green
Write-Host ""
exit 0
