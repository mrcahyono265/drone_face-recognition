# Getting Started with Drone E99 Face Recognition

Quick start guide untuk pengguna baru.

## 🚀 Quick Installation (5 minutes)

### 1. Clone & Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd drone_e99_face_recognition

# Create virtual environment (fast with uv)
uv venv --python 3.10
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Model

Download MiniFASNetV2.onnx dari:
- https://github.com/yakhyo/face-anti-spoofing/releases

Letakkan di folder:
```
models/MiniFASNetV2.onnx
```

### 3. Prepare Dataset

Buat struktur folder:
```bash
mkdir -p dataset/your_name/enrollment/images
mkdir -p dataset/your_name/enrollment/videos
```

Copy foto Anda ke:
```
dataset/your_name/enrollment/images/
```

### 4. Run Enrollment

```bash
# Automated enrollment (scans all identities)
.\.venv\Scripts\python.exe tools\enroll_image.py
.\.venv\Scripts\python.exe tools\enroll_video.py
```

### 5. Run Recognition

```bash
.\.venv\Scripts\python.exe main.py
```

**Done!** 🎉

---

## 📋 Detailed Setup

### System Requirements

**Minimum:**
- CPU: Quad-core
- RAM: 4GB
- Python: 3.10
- Camera: Webcam atau RTSP stream

**Recommended:**
- GPU: NVIDIA with CUDA
- RAM: 8GB
- SSD for faster loading

### Environment Setup

**Option A: Using uv (Fastest)**
```bash
uv venv --python 3.10
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Option B: Using venv**
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Option C: Using conda**
```bash
conda create -n drone-face python=3.10
conda activate drone-face
pip install -r requirements.txt
```

### Configuration

Edit `config.yaml` sesuai kebutuhan:

```yaml
camera:
  type: "webcam"      # atau "rtsp"
  source: 1           # webcam ID

recognition:
  similarity_threshold: 0.45  # Lower = lebih mudah accept

processing:
  frame_skip: 4       # Higher = lebih cepat FPS
```

---

## 🎯 First Steps

### 1. Test Installation

```bash
# Test detection only
.\.venv\Scripts\python.exe main_detect.py

# Should show: Face detection working
```

### 2. Enroll Your Face

**Image Mode:**
```bash
.\.venv\Scripts\python.exe tools\enroll_image.py
```

**Video Mode (Recommended):**
```bash
.\.venv\Scripts\python.exe tools\enroll_video.py
```

### 3. Run Full System

```bash
.\.venv\Scripts\python.exe main.py
```

Press:
- **S** - Snapshot
- **R** - Record video
- **Q** - Quit

---

## ❓ Troubleshooting

### "Database is empty"
- Run enrollment tools first
- Check dataset structure

### "No face detected"
- Improve lighting
- Face directly to camera
- Check camera connection

### Low FPS
- Increase `frame_skip` in config
- Reduce `det_size` to [240, 240]
- Use GPU if available

### CUDA errors
- Use CPU version: `pip install onnxruntime`
- Or update CUDA drivers

---

## 📚 Next Steps

1. **Read Documentation:**
   - [README.md](README.md) - Full documentation
   - [ENROLLMENT_QUICKSTART.md](ENROLLMENT_QUICKSTART.md) - Enrollment guide

2. **Experiment:**
   - Adjust thresholds
   - Add more dataset
   - Test with different lighting

3. **Advanced Usage:**
   - RTSP drone setup
   - Custom model integration
   - Performance tuning

---

## 🆘 Need Help?

- Check [docs/](docs/) folder
- Open GitHub issue
- Contact maintainer

**Happy Face Recognizing!** 🎉