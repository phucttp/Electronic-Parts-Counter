# run_kaggle.ps1 - "1 nut" train tren Kaggle GPU tu desktop.
# =========================================================
# Tu dong: dong data.zip -> push dataset -> push code train -> chay GPU
#          -> tai best.pt ve models/.
#
# YEU CAU (xem README.md):
#   - Da set bien moi truong KAGGLE_API_TOKEN (token moi tu Kaggle).
#   - kaggle.json (legacy) van de trong %USERPROFILE%\.kaggle\ (de lay username).
#
# DUNG:
#   .\cloud_kaggle\run_kaggle.ps1
#   .\cloud_kaggle\run_kaggle.ps1 -Message "them tu gom"
#   .\cloud_kaggle\run_kaggle.ps1 -NoWait
#
param(
    [string]$KaggleUser = "",
    [string]$Message = "update dataset",
    [switch]$NoWait
)
# KHONG Stop: lenh native (kaggle) ghi stderr se lam script chet oan tren PS 5.1
$ErrorActionPreference = "Continue"
# Ep UTF-8 cho IO Python -> tranh loi charmap khi kaggle in log/tien do
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUTF8 = "1"

$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj    = Split-Path -Parent $root
$dataset = Join-Path $proj "dataset"
$models  = Join-Path $proj "models"
$upload  = Join-Path $root "upload"

# Fallback: neu chua co env token, thu doc tu secrets.json (do GUI luu)
if (-not $env:KAGGLE_API_TOKEN) {
    $sec = Join-Path $root "secrets.json"
    if (Test-Path $sec) {
        try {
            $j = Get-Content $sec -Raw | ConvertFrom-Json
            if ($j.kaggle_token) { $env:KAGGLE_API_TOKEN = $j.kaggle_token }
            if (-not $KaggleUser -and $j.kaggle_user) { $KaggleUser = $j.kaggle_user }
        } catch {}
    }
}
if (-not $env:KAGGLE_API_TOKEN) { Write-Host "[X] Chua co KAGGLE_API_TOKEN (set env hoac luu qua GUI Cai dat)." -ForegroundColor Red; exit 1 }
if (-not $KaggleUser) {
    $cfg = Join-Path $env:USERPROFILE ".kaggle\kaggle.json"
    if (Test-Path $cfg) { $KaggleUser = (Get-Content $cfg -Raw | ConvertFrom-Json).username }
}
if (-not $KaggleUser) { Write-Host "[X] Khong xac dinh duoc username. Truyen -KaggleUser." -ForegroundColor Red; exit 1 }

$DATASET_SLUG = "$KaggleUser/linhkien-dataset"
$KERNEL_SLUG  = "$KaggleUser/linhkien-train"
Write-Host "==> User=$KaggleUser | Dataset=$DATASET_SLUG | Kernel=$KERNEL_SLUG" -ForegroundColor Cyan

function Write-NoBom($path, $text) { [System.IO.File]::WriteAllText($path, $text) }

# 1) Dong data.zip (build_zip.py tu loc loai bi an + don id, khong dung nhan goc)
Write-Host "==> [1/4] Dong goi data.zip + push dataset..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $upload | Out-Null
python (Join-Path $root "build_zip.py")
if ($LASTEXITCODE -ne 0) { Write-Host "[X] Dong data.zip THAT BAI." -ForegroundColor Red; exit 1 }

Write-NoBom (Join-Path $upload "dataset-metadata.json") @"
{
  "title": "linhkien-dataset",
  "id": "$DATASET_SLUG",
  "licenses": [{ "name": "CC0-1.0" }]
}
"@

# Push dataset: thu VERSION truoc (dataset da ton tai sau lan dau).
# Khong tin exit code cua kaggle CLI -> kiem tra theo NOI DUNG output.
$dsout = (kaggle datasets version -p $upload -m $Message --dir-mode skip 2>&1 | Out-String)
Write-Host $dsout.Trim()
if ($dsout -notmatch "being created|successfully") {
    Write-Host "    (version khong duoc -> thu tao moi)"
    $dsout = (kaggle datasets create -p $upload --dir-mode skip 2>&1 | Out-String)
    Write-Host $dsout.Trim()
}
if ($dsout -notmatch "being created|successfully") {
    Write-Host "[X] Push dataset THAT BAI." -ForegroundColor Red; exit 1
}
Write-Host "    -> Dataset da cap nhat." -ForegroundColor Green

# 2) Metadata + push kernel (train_kernel.py phai ASCII)
Write-NoBom (Join-Path $root "kernel-metadata.json") @"
{
  "id": "$KERNEL_SLUG",
  "title": "linhkien-train",
  "code_file": "train_kernel.py",
  "language": "python",
  "kernel_type": "script",
  "is_private": true,
  "enable_gpu": true,
  "enable_internet": true,
  "dataset_sources": ["$DATASET_SLUG"],
  "competition_sources": [],
  "kernel_sources": []
}
"@

Write-Host "==> [2/4] Push code train + khoi dong GPU..." -ForegroundColor Yellow
Start-Sleep -Seconds 20   # cho dataset version xu ly
kaggle kernels push -p $root
if ($LASTEXITCODE -ne 0) { Write-Host "[X] Push kernel THAT BAI." -ForegroundColor Red; exit 1 }

if ($NoWait) { Write-Host "==> Da push. Xem: kaggle kernels status $KERNEL_SLUG" -ForegroundColor Green; exit 0 }

# 3) Cho train xong
Write-Host "==> [3/4] Dang train tren GPU, cho..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
while ($true) {
    $status = (kaggle kernels status $KERNEL_SLUG 2>&1 | Out-String).Trim()
    Write-Host "    $status"
    if ($status -match "COMPLETE")          { break }
    if ($status -match "ERROR|CANCEL|FAIL")  { Write-Host "[X] Train LOI. Xem: kaggle kernels output $KERNEL_SLUG -p cloud_kaggle\_log" -ForegroundColor Red; exit 1 }
    Start-Sleep -Seconds 30
}

# 4) Tai best.pt ve models/
# LUU Y: kaggle output KHONG ghi de file da co -> tai ra temp roi Copy -Force.
Write-Host "==> [4/4] Tai best.pt ve $models ..." -ForegroundColor Yellow
$outtmp = Join-Path $root "_out"
New-Item -ItemType Directory -Force -Path $outtmp | Out-Null
Remove-Item -Force (Join-Path $outtmp "best.pt"), (Join-Path $outtmp "metrics.json") -ErrorAction SilentlyContinue
kaggle kernels output $KERNEL_SLUG -p $outtmp 2>&1 | Out-Null
if (Test-Path (Join-Path $outtmp "best.pt")) {
    Copy-Item -Force (Join-Path $outtmp "best.pt") (Join-Path $models "best.pt")
    if (Test-Path (Join-Path $outtmp "metrics.json")) {
        Copy-Item -Force (Join-Path $outtmp "metrics.json") (Join-Path $models "metrics.json")
    }
    Write-Host "==> XONG! models\best.pt san sang. Chay: python m3_detect\detect.py --source 0" -ForegroundColor Green
} else {
    Write-Host "[X] Khong thay best.pt trong output." -ForegroundColor Red; exit 1
}
