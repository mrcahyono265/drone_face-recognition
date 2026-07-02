# Quick Start Guide

## Prerequisites

- **Python 3.10+** (will be installed automatically by uv)
- **uv** package manager (already installed)
- **Windows PowerShell** (for running setup scripts)

---

## Step 1: Setup Environment (One-Time Setup)

```powershell
# Navigate to project directory
cd D:\5_Project\lainnya\skripsi\drone_e99_face_recognition

# Run setup script
.\setup_environment.ps1
```

**What this does:**
- Creates isolated virtual environment with Python 3.10
- Installs all dependencies with compatible versions
- Verifies installation

**Expected output:**
```
Environment created successfully!
To activate the environment: .\.venv\Scripts\Activate.ps1
```

---

## Step 2: Activate Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(venv)` prefix in your terminal.

---

## Step 3: Populate Database

### Option A: Legacy Database (Quick Test)

```powershell
# Use existing tool
python build_embedding_database.py
```

### Option B: Multiple Embedding Database (Recommended)

```powershell
# Image enrollment
python tools/enroll_image.py

# Video enrollment
python tools/enroll_video.py
```

---

## Step 4: Configure Database Mode

Edit `config.yaml`:

```yaml
database:
  mode: "legacy"    # Use pickle database
  # OR
  mode: "multiple"  # Use new embedding database (recommended)
```

---

## Step 5: Run Application

```powershell
# Make sure environment is activated
python main.py
```

**Controls:**
- **Q** - Quit
- **S** - Snapshot
- **R** - Toggle recording

---

## Step 6: Performance Comparison (Optional)

```powershell
# Requires both databases populated
python tools/performance_comparison.py
```

---

## Troubleshooting

### OpenCV GUI Error

```
cv2.error: The function is not implemented
```

**Solution:**
```powershell
pip uninstall opencv-python-headless
pip install opencv-python==4.9.0.80
```

### NumPy Compatibility Error

```
AttributeError: _ARRAY_API not found
```

**Solution:**
```powershell
pip install numpy==1.26.4
```

### Module Not Found

```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```powershell
# Make sure you're in project directory and environment is activated
cd D:\5_Project\lainnya\skripsi\drone_e99_face_recognition
.\.venv\Scripts\Activate.ps1
```

---

## Environment Management

### Activate Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### Deactivate Environment
```powershell
deactivate
```

### Check Installed Packages
```powershell
pip list
```

### Add New Package
```powershell
uv pip install package_name
```

---

## Next Steps

1. ✅ Setup environment (Step 1)
2. ✅ Activate environment (Step 2)
3. ✅ Populate database (Step 3)
4. ✅ Configure mode (Step 4)
5. ✅ Run application (Step 5)
6. ⏳ Performance comparison (Step 6)

---

**For detailed documentation, see:**
- `docs/01_PROJECT_CONTEXT.md`
- `docs/02_SYSTEM_DESIGN.md`
- `docs/03_DEVELOPMENT_GUIDE.md`
- `docs/06_PHASE3_INTEGRATION.md`