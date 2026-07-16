# Setup Script for Drone Face Recognition Project
# Requires: uv (https://docs.astral.sh/uv/)

param(
    [switch]$CPU
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Drone Face Recognition - Environment Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check uv
Write-Host "[1/4] Checking uv..." -ForegroundColor Yellow
try {
    $v = uv --version
    Write-Host "  uv: $v" -ForegroundColor Green
} catch {
    Write-Host "  Install uv first: powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Red
    exit 1
}

# Navigate to project root
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent)

# Create venv & install deps
Write-Host "[2/4] Creating virtual environment & installing dependencies..." -ForegroundColor Yellow
uv venv
if ($LASTEXITCODE -ne 0) { exit 1 }
uv sync
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "  Dependencies installed" -ForegroundColor Green

# Verify
Write-Host "[3/4] Verifying..." -ForegroundColor Yellow
try {
    $nv = python -c "import numpy; print('NumPy', numpy.__version__)"
    Write-Host "  $nv" -ForegroundColor Green
    $ov = python -c "import cv2; print('OpenCV', cv2.__version__)"
    Write-Host "  $ov" -ForegroundColor Green
    $iv = python -c "from insightface.app import FaceAnalysis; print('InsightFace OK')"
    Write-Host "  $iv" -ForegroundColor Green
    if (-not $CPU) {
        $gpu = python -c "import onnxruntime as ort; print('ONNX:', ort.get_device())" 2>$null
        if ($?) { Write-Host "  $gpu" -ForegroundColor Green }
        else { Write-Host "  ONNX: CPU only (no CUDA)" -ForegroundColor Yellow }
    }
} catch {
    Write-Host "  Verification failed: $_" -ForegroundColor Red
    exit 1
}

# Config
Write-Host "[4/4] Config" -ForegroundColor Yellow
if (-not (Test-Path "dataset")) { New-Item -ItemType Directory -Path "dataset" -Force | Out-Null }
if (-not (Test-Path "database/embeddings")) { New-Item -ItemType Directory -Path "database/embeddings" -Force | Out-Null }
if (-not (Test-Path "models/MiniFASNetV2.onnx")) {
    Write-Host "  WARNING: models/MiniFASNetV2.onnx not found! Download it first." -ForegroundColor Yellow
}
$provider = if ($CPU) { "cpu" } else { python -c "import onnxruntime as ort; print('cuda' if ort.get_device() == 'GPU' else 'cpu')" 2>$null }
if (-not $?) { $provider = "cpu" }
Write-Host "  Default provider: $provider (edit config.yaml to change)" -ForegroundColor Gray

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Run: python main.py" -ForegroundColor White
Write-Host "Or : .\.venv\Scripts\Activate.ps1 ; python main.py" -ForegroundColor Gray
