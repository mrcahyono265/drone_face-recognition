# 🚁 Drone E99 - Face Recognition & Anti-Spoofing System

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-310/)
[![InsightFace](https://img.shields.io/badge/insightface-latest-green.svg)](https://github.com/deepinsight/insightface)
[![OpenCV](https://img.shields.io/badge/opencv-4.9-red.svg)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Sistem pengenalan wajah dan deteksi anti-spoofing secara real-time untuk drone dan webcam lokal**

---

## 📋 Overview

Sistem ini mengimplementasikan pipeline end-to-end untuk **face recognition** dan **liveness detection** yang berjalan secara real-time. Dirancang khusus untuk keperluan penelitian skripsi dengan fokus pada implementasi yang **repeatable, modular, dan production-ready**.

### Pipeline Architecture

```
Camera (RTSP/Webcam) 
    ↓
Threaded Frame Capture (Async)
    ↓
Face Detection (InsightFace Buffalo_sc)
    ↓
Embedding Extraction (512-D)
    ↓
Database Comparison (Cosine Similarity)
    ↓
Anti-Spoofing (MiniFASNetV2)
    ↓
Real-time Display + Recording
```

### Mode Operasi

- **`main.py`** - Full pipeline: Detection + Recognition + Anti-Spoofing ⭐ (Recommended)
- **`main_detect.py`** - Detection only (testing/debugging)
- **`main_recog.py`** - Detection + Recognition (tanpa liveness)

---

## 🎯 Key Features

### Recognition
- ✅ **Real-time Face Detection** - InsightFace Buffalo_sc (320×320 input)
- ✅ **Multiple Embedding Database** - Support multiple samples per identity
- ✅ **Cosine Similarity Matching** - Threshold-based recognition (0.45)
- ✅ **L2-Normalized Embeddings** - Consistent normalization untuk semua embeddings

### Anti-Spoofing
- ✅ **MiniFASNetV2** - Lightweight anti-spoofing model (ONNX)
- ✅ **Real-time Liveness Detection** - Score > 0.85 = Real
- ✅ **EMA Smoothing** - Temporal smoothing untuk stabilisasi (α=0.3)
- ✅ **Raw + Smoothed Scores** - Both available for debugging

### Performance
- ✅ **Asynchronous Camera Capture** - Threaded buffering untuk minimal latency
- ✅ **Frame Skip Optimization** - Configurable skip rate (default: every 5th frame)
- ✅ **Pipeline Instrumentation** - Accurate timing metrics per stage
- ✅ **Effective FPS Monitoring** - Real-time performance tracking

### Usability
- ✅ **Multi-Camera Support** - RTSP drone stream + USB webcam
- ✅ **Snapshot & Recording** - Built-in capture (S key) dan recording (R key)
- ✅ **Automated Enrollment** - Image & video enrollment tools
- ✅ **CSV Reporting** - Detailed enrollment logs

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.10 |
| **Face Recognition** | InsightFace (Buffalo_sc) | Latest |
| **Anti-Spoofing** | MiniFASNetV2 (ONNX) | V2 |
| **Computer Vision** | OpenCV | 4.9.0 |
| **Deep Learning** | ONNX Runtime | GPU-accelerated |
| **Numerical** | NumPy | 1.26.4 |
| **Video I/O** | FFmpeg | Built-in OpenCV |

### Hardware Requirements

- **CPU:** Quad-core atau lebih baik
- **GPU:** NVIDIA GPU dengan CUDA support (recommended)
- **RAM:** Minimum 4GB
- **Camera:** RTSP stream (drone) atau USB webcam

---

## 📦 Installation

### Prerequisites

1. **Python 3.10** installed
2. **NVIDIA GPU** with CUDA 12.1 (optional but recommended)
3. **Git** for cloning

### Quick Start (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd drone_e99_face_recognition

# 2. Create virtual environment (using uv - fast!)
uv venv --python 3.10
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download MiniFASNetV2.onnx
# Get from: https://github.com/yakhyo/face-anti-spoofing
# Place in: models/MiniFASNetV2.onnx

# 5. Run enrollment (prepare database)
.\.venv\Scripts\python.exe tools\enroll_image.py
.\.venv\Scripts\python.exe tools\enroll_video.py

# 6. Run recognition
.\.venv\Scripts\python.exe main.py
```

### Manual Installation

```bash
# Create venv
python -m venv .venv
.\.venv\Scripts\activate

# Install packages
pip install numpy==1.26.4
pip install opencv-python==4.9.0
pip install insightface
pip install onnxruntime-gpu  # or onnxruntime for CPU
pip install pyyaml
```

---

## 🚀 Usage

### 1. Dataset Preparation

Create dataset structure:

```
dataset/
├── person1/
│   └── enrollment/
│       ├── images/
│       │   ├── photo1.jpg
│       │   └── photo2.jpg
│       └── videos/
│           └── video1.mp4
└── person2/
    └── enrollment/
        └── images/
            └── photo1.jpg
```

### 2. Enrollment (Build Database)

**Image Enrollment:**
```bash
.\.venv\Scripts\python.exe tools\enroll_image.py
```
- Scans all identities in `dataset/`
- Processes all images automatically
- Saves embeddings to `database/embeddings/`
- Generates CSV report

**Video Enrollment:**
```bash
.\.venv\Scripts\python.exe tools\enroll_video.py
```
- Scans all videos in `dataset/`
- Samples frames every 300ms
- Validates frames (blur, confidence, size)
- Saves unique embeddings

### 3. Run Recognition

```bash
# Full pipeline (recommended)
.\.venv\Scripts\python.exe main.py

# Detection only (testing)
.\.venv\Scripts\python.exe main_detect.py

# Recognition without anti-spoofing
.\.venv\Scripts\python.exe main_recog.py
```

### 4. Runtime Controls

| Key | Function |
|-----|----------|
| **Q** | Quit application |
| **S** | Take snapshot |
| **R** | Toggle video recording |

### 5. Configuration

Edit `config.yaml`:

```yaml
camera:
  type: "webcam"          # or "rtsp"
  source: 1               # webcam ID
  rtsp_url: "rtsp://..."  # RTSP URL

recognition:
  similarity_threshold: 0.45
  det_size: [320, 320]

spoofing:
  liveness_threshold: 0.85

processing:
  frame_skip: 4           # Process every 5th frame
  fps_smoothing: 0.9

database:
  mode: "multiple"        # Use multiple embedding database
  embeddings_dir: "database/embeddings"

enrollment:
  duplicate_threshold: 0.995
  sampling_interval_ms: 300
  
  validation:
    min_face_size: 80
    min_face_confidence: 0.7
    max_blur_score: 650

logging:
  level: "INFO"
  verbose: false
```

---

## 📊 Performance Metrics

### Pipeline Timing (Example)

```
PROCESSING STAGE TIMING:
----------------------------------------------------------------------
  1. Face Detection:        54.00 ms (avg per inference)
  2. Recognition (compare):  0.80 ms (avg per face)
  3. MiniFASNet V2:          6.00 ms (avg per face)
  4. UI Rendering:           8.50 ms (avg per frame)
     (includes: drawing + process_ui + imshow + waitKey)

  TOTAL Pipeline:           25.30 ms (avg per frame)
  Effective Processing FPS: 39.53 FPS

  [Validation]
    Status: ✓ CONSISTENT (within 20% tolerance)
```

### Recognition Statistics

```
RECOGNITION METRICS:
----------------------------------------------------------------------
  Total Recognitions:     200
  Accepted (>threshold):  180 (90.0%)
  Unknown (<threshold):   20 (10.0%)
  Avg Comparisons:        135.0
  Recognition Rate:       7.92 recognitions/sec

ANTI-SPOOFING METRICS:
----------------------------------------------------------------------
  Spoof Detections:  5
  EMA Alpha:         0.3
```

---

## 🏗️ Project Structure

```
drone_e99_face_recognition/
├── main.py                          # Main application (full pipeline)
├── main_detect.py                   # Detection only mode
├── main_recog.py                    # Recognition only mode
├── config.yaml                      # Configuration file
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── ENROLLMENT_QUICKSTART.md        # Quick enrollment guide
│
├── tools/
│   ├── enroll_image.py             # Automated image enrollment
│   └── enroll_video.py             # Automated video enrollment
│
├── src/
│   ├── camera/
│   │   ├── webcam_camera.py        # Webcam capture (threaded)
│   │   └── rtsp_camera.py          # RTSP capture (threaded)
│   ├── recognition/
│   │   └── recognizer.py           # InsightFace wrapper
│   ├── spoof/
│   │   └── antispoof.py            # MiniFASNetV2 wrapper
│   ├── database/
│   │   └── database.py             # Multiple embedding database
│   ├── enrollment/
│   │   ├── engine.py               # Enrollment logic
│   │   ├── video_sampler.py        # Frame sampling
│   │   └── frame_validator.py      # Frame quality validation
│   ├── dataset/
│   │   └── utils.py                # Dataset utilities
│   └── ui/
│       └── display.py              # UI rendering
│
├── database/
│   └── embeddings/                  # Embedding database (auto-created)
│       ├── person1/
│       │   ├── emb_0001.npy
│       │   └── ...
│       └── person2/
│
├── dataset/                         # Input dataset (gitignored)
│   └── <identity>/
│       └── enrollment/
│           ├── images/
│           └── videos/
│
├── reports/
│   └── enrollment/                  # CSV reports (auto-created)
│       ├── image_report_*.csv
│       └── video_report_*.csv
│
├── inference_output/                # Snapshots & recordings (gitignored)
│
├── models/
│   └── MiniFASNetV2.onnx           # Anti-spoofing model
│
└── docs/
    ├── 06_PHASE3_INTEGRATION.md    # Integration documentation
    ├── 07_PIPELINE_INSTRUMENTATION.md  # Instrumentation guide
    ├── 08_AUTOMATED_ENROLLMENT_COMPLETE.md  # Enrollment docs
    └── 09_INSTRUMENTATION_FIX.md   # Instrumentation fixes
```

---

## 🔬 Research Methodology

### Database Design

**Multiple Embedding Approach:**
- Multiple samples per identity (not just one)
- Each embedding stored as separate `.npy` file
- Recognition uses **max similarity** across all embeddings
- More robust than single-embedding approach

**Embedding Storage:**
```
database/embeddings/
├── person1/
│   ├── emb_0001.npy  (512-D, L2-normalized)
│   ├── emb_0002.npy
│   └── emb_0003.npy
└── person2/
    └── emb_0001.npy
```

### Duplicate Detection

**During Enrollment:**
- New embedding compared with existing embeddings of same identity
- Cosine similarity > 0.995 → considered duplicate
- Prevents database bloat with nearly-identical embeddings

**During Recognition:**
- Query compared with ALL embeddings in database
- Max similarity used as identity score
- Threshold 0.45 for acceptance

### Frame Validation (Video Enrollment)

**Validation Checks:**
1. **Face Detection** - Exactly one face required
2. **Face Size** - Minimum 80×80 pixels
3. **Detection Confidence** - Minimum 0.7
4. **Blur Detection** - Variance of Laplacian ≤ 650

Only frames passing all checks are enrolled.

### Anti-Spoofing

**MiniFASNetV2:**
- Input: 80×80 BGR face crop (no normalization, range 0-255)
- Output: 3-class softmax [spoof, real, ?]
- Threshold: Class 1 (real) score > 0.85
- EMA smoothing: α=0.3 for temporal stability

---

## 📈 Performance Optimization

### Frame Skip Strategy

**Default:** Process every 5th frame (`frame_skip=4`)

**Rationale:**
- Face detection is expensive (~54ms)
- Recognition can reuse previous frame's results
- Maintains high FPS while reducing computational load

**Trade-off:**
- Higher skip → Higher FPS, lower recognition frequency
- Lower skip → Lower FPS, higher recognition frequency

**Recommended:** `frame_skip=4` for real-time (25-40 FPS)

### Asynchronous Camera Capture

**Architecture:**
```python
# Background thread continuously captures frames
class CameraThread:
    def update():
        while True:
            frame = stream.read()  # Blocking capture
    
    def read():
        return latest_frame  # Non-blocking read
```

**Benefits:**
- Main thread never blocked
- Always processes latest frame
- Minimal latency
- Smooth display even with slow processing

---

## 🧪 Testing & Validation

### Pre-Deployment Checklist

- [ ] Dataset structure created
- [ ] Images/videos placed in correct folders
- [ ] Enrollment completed successfully
- [ ] Database validated (all embeddings 512-D, L2-normalized)
- [ ] CSV reports generated
- [ ] Configuration adjusted (thresholds, frame_skip)
- [ ] Test run with webcam
- [ ] Test run with RTSP (if applicable)
- [ ] Performance metrics verified

### Expected Results

**Image Enrollment:**
- ~2 seconds per image
- 100% success rate for good quality images
- Duplicate detection working (>0.995 similarity skipped)

**Video Enrollment:**
- ~30 seconds per minute of video
- ~20-30% valid frame rate
- High duplicate rate (good coverage indicator)

**Recognition:**
- Effective FPS: 30-50 FPS (with frame_skip=4)
- Detection time: ~50-60ms per inference
- Recognition time: <1ms per face
- MiniFASNet: ~5-10ms per face

---

## 🐛 Troubleshooting

### Common Issues

**1. "Multiple embeddings database is empty"**
- Run enrollment tools first
- Check `dataset/` structure
- Verify images are in `enrollment/images/`

**2. "No face detected" (during enrollment)**
- Ensure face is visible and well-lit
- Check image resolution
- Lower `min_face_confidence` in config

**3. High duplicate rate**
- Normal if database has good coverage
- Indicates embeddings are similar
- Consider lowering `duplicate_threshold` to 0.98

**4. Low FPS (<15)**
- Reduce `det_size` to 240×240
- Increase `frame_skip` to 6 or 8
- Check GPU utilization

**5. CUDA out of memory**
- Close other GPU applications
- Use `onnxruntime` (CPU) instead of `onnxruntime-gpu`
- Reduce batch sizes

### Performance Tuning

| Symptom | Solution |
|---------|----------|
| Low FPS | Increase `frame_skip`, reduce `det_size` |
| Poor recognition | Lower `similarity_threshold`, add more embeddings |
| False spoofs | Lower `liveness_threshold`, improve lighting |
| High latency | Use GPU, reduce model complexity |

---

## 📚 Documentation

- **[ENROLLMENT_QUICKSTART.md](ENROLLMENT_QUICKSTART.md)** - Quick enrollment guide
- **[docs/06_PHASE3_INTEGRATION.md](docs/06_PHASE3_INTEGRATION.md)** - Integration plan
- **[docs/07_PIPELINE_INSTRUMENTATION.md](docs/07_PIPELINE_INSTRUMENTATION.md)** - Instrumentation guide
- **[docs/08_AUTOMATED_ENROLLMENT_COMPLETE.md](docs/08_AUTOMATED_ENROLLMENT_COMPLETE.md)** - Enrollment documentation
- **[docs/09_INSTRUMENTATION_FIX.md](docs/09_INSTRUMENTATION_FIX.md)** - Instrumentation fixes

---

## 🔐 Security & Privacy

**Data Storage:**
- Embeddings stored locally (not uploaded)
- No cloud dependency
- Dataset and database gitignored

**Recommendations:**
- Use strong encryption for sensitive data
- Regular backups of `database/embeddings/`
- Secure RTSP streams with authentication

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

**Citation (if used in research):**
```bibtex
@software{drone_e99_face_recognition,
  title = {Drone E99 Face Recognition and Anti-Spoofing System},
  year = {2026},
  url = {https://github.com/your-username/drone_e99_face_recognition}
}
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## 📧 Contact & Support

For questions, issues, or collaboration:
- **Issues:** Open a GitHub issue
- **Email:** your.email@example.com

---

## 🎓 Acknowledgments

- **InsightFace** - Face recognition library
- **MiniFASNet** - Anti-spoofing model (via [yakhyo/face-anti-spoofing](https://github.com/yakhyo/face-anti-spoofing))
- **OpenCV** - Computer vision library
- **ONNX Runtime** - Model inference

---

**Last Updated:** 2026-07-02  
**Version:** 2.0.0 (Automated Enrollment)