# Setup Script for Drone Face Recognition Project
# Menggunakan uv untuk isolated environment

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Drone Face Recognition - Environment Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if uv is installed
Write-Host "[1/6] Checking uv installation..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version
    Write-Host "  uv found: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: uv not found. Please install uv first:" -ForegroundColor Red
    Write-Host "  Windows: powershell -c "irm https://astral.sh/uv/install.ps1" | iex" -ForegroundColor Yellow
    exit 1
}

# Navigate to project directory
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir
Write-Host "  Project directory: $projectDir" -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
Write-Host "  Using Python 3.10 (recommended for compatibility)" -ForegroundColor Gray
uv venv --python 3.10

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}
Write-Host "  Virtual environment created successfully" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

if (-not $?) {
    Write-Host "  ERROR: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}
Write-Host "  Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "[4/6] Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

# Use requirements_compatible.txt if exists, otherwise requirements.txt
if (Test-Path "requirements_compatible.txt") {
    Write-Host "  Using requirements_compatible.txt (guaranteed compatible versions)" -ForegroundColor Gray
    uv pip install -r requirements_compatible.txt
} else {
    Write-Host "  Using requirements.txt" -ForegroundColor Gray
    uv pip install -r requirements.txt
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "  Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

# Verify installation
Write-Host "[5/6] Verifying installation..." -ForegroundColor Yellow

# Test NumPy
try {
    $numpyVersion = python -c "import numpy; print(numpy.__version__)"
    Write-Host "  NumPy: $numpyVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: NumPy not installed correctly" -ForegroundColor Red
}

# Test OpenCV
try {
    $opencvTest = python -c "import cv2; cv2.namedWindow('Test'); print('GUI Support: OK')"
    Write-Host "  OpenCV: Installed with GUI support" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: OpenCV GUI may have issues" -ForegroundColor Yellow
    Write-Host "  Try: pip install opencv-python==4.9.0.80" -ForegroundColor Gray
}

# Test InsightFace
try {
    python -c "from insightface.app import FaceAnalysis; print('InsightFace: OK')"
    Write-Host "  InsightFace: OK" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: InsightFace may have issues" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "[6/6] Setup Summary" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment in the future:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Cyan
Write-Host "  1. Activate environment: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Run application: python main.py" -ForegroundColor White
Write-Host ""
Write-Host "To switch database mode:" -ForegroundColor Cyan
Write-Host "  Edit config.yaml:" -ForegroundColor White
Write-Host "    database:" -ForegroundColor Gray
Write-Host "      mode: 'legacy'    # Use pickle database" -ForegroundColor Gray
Write-Host "      # OR" -ForegroundColor Gray
Write-Host "      mode: 'multiple'  # Use new embedding database" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""