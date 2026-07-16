# Drone E99 — Face Recognition & Anti-Spoofing

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CUDA](https://img.shields.io/badge/CUDA-13-green.svg)](https://developer.nvidia.com/cuda-toolkit)

Real-time face recognition + liveness detection for drone (RTSP) and webcam. Built for undergraduate thesis research.

<!--

---

## 📸 Screenshots

<!-- TODO: Tambah screenshot atau GIF sistem berjalan
 Contoh:
| Recognition | Enrollment | Drone Setup |
|------------|------------|-------------|
| ![recognition](docs/screenshots/recognition.png) | ![enrollment](docs/screenshots/enrollment.png) | ![drone](docs/screenshots/drone.jpg) |
-->

---

## ✨ Features

- **Real-time face detection & recognition** — InsightFace buffalo_sc (MobileFaceNet)
- **Anti-spoofing / liveness detection** — MiniFASNetV2 (ONNX)
- **Multi-person support** — multiple faces in a single frame
- **Dual input** — Drone (RTSP over TCP) + Webcam (DirectShow on Windows)
- **Headless mode** — run without display for onboard drone deployment
- **Automated enrollment** — batch image and video enrollment pipeline
- **Snapshot & recording** — keyboard controls for capturing output
- **CUDA acceleration** — onnxruntime-gpu with CUDA 13
- **Live CMD output** — per-frame identity, similarity, and liveness score

---

## Requirements

### Hardware

| Component | Minimum                          | Recommended |
| --------- | -------------------------------- | ----------- |
| GPU       | NVIDIA RTX 2050+                 | RTX 3060+   |
| Driver    | ≥ 610                            | Latest      |
| RAM       | 8 GB                             | 16 GB       |
| Camera    | Any USB webcam / Drone with RTSP | —           |

> No GPU? System defaults to CPU. Set `processing.provider: cpu` in config.yaml.

### Software

| Dependency                       | Version                    |
| -------------------------------- | -------------------------- |
| Python                           | ≥ 3.11                     |
| [uv](https://docs.astral.sh/uv/) | Latest (recommended)       |
| OpenCV                           | ≥ 4.9.0                    |
| NumPy                            | ≥ 1.26, < 2.0              |
| InsightFace                      | ≥ 0.7.3                    |
| ONNX Runtime                     | ≥ 1.27.0 (GPU) / any (CPU) |

---

## 🚀 Quick Start

```bash
# 1. Setup project
git clone https://github.com/mrcahyono265/drone_face-recognition.git
cd drone_face-recognition

# 2. Setup environment (auto-downloads all dependencies) *Recomended
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# Or manually:
uv venv
uv sync

# 3. Prepare dataset and enroll faces
#    Place images in: dataset/<identity>/enrollment/images/
#    Place videos in: dataset/<identity>/enrollment/videos/
uv run python tools\enroll_image.py    # Batch image enrollment
uv run python tools\enroll_video.py    # Batch video enrollment

# 4. (Optional) Edit config.yaml — set provider to "cuda" for GPU
#    or camera.type to "drone" for RTSP streaming

# 5. Run recognition
uv run python main.py
```

---

## ⚙️ Configuration

Edit `config.yaml`:

| Key                                         | Default                    | Description                                                |
| ------------------------------------------- | -------------------------- | ---------------------------------------------------------- |
| `camera.type`                               | `webcam`                   | `webcam` or `drone` (RTSP)                                 |
| `camera.source`                             | `0`                        | Webcam index (integer)                                     |
| `camera.rtsp_url`                           | —                          | RTSP URL for drone (e.g. `rtsp://192.168.1.1:7070/webcam`) |
| `processing.provider`                       | `cpu`                      | `cuda` or `cpu`                                            |
| `processing.frame_skip`                     | `4`                        | Process every Nth frame (0 = every frame)                  |
| `processing.fps_smoothing`                  | `0.9`                      | EMA smoothing factor for FPS display                       |
| `processing.headless`                       | `false`                    | `true` to skip all GUI calls (drone onboard)               |
| `recognition.similarity_threshold`          | `0.45`                     | Cosine similarity threshold for identity match             |
| `recognition.model_name`                    | `buffalo_sc`               | InsightFace model name                                     |
| `recognition.det_size`                      | `[320, 320]`               | Detection input resolution                                 |
| `spoofing.liveness_threshold`               | `0.85`                     | Liveness score cutoff                                      |
| `spoofing.model_path`                       | `models/MiniFASNetV2.onnx` | Path to ONNX model                                         |
| `database.mode`                             | `multiple`                 | `multiple` (per-identity .npy) or `legacy` (single .pkl)   |
| `database.embeddings_dir`                   | `database/embeddings`      | Storage for multiple mode                                  |
| `enrollment.duplicate_threshold`            | `0.995`                    | Cosine sim threshold for duplicate detection               |
| `enrollment.sampling_interval_ms`           | `300`                      | Video frame sampling interval                              |
| `enrollment.validation.min_face_size`       | `80`                       | Minimum face size (px)                                     |
| `enrollment.validation.min_face_confidence` | `0.7`                      | Minimum detection confidence                               |
| `enrollment.validation.max_blur_score`      | `650`                      | Maximum Laplacian variance (blur)                          |

---

## 🏗️ Project Structure

```
├── main.py                          # Entry point — recognition loop
├── config.yaml                      # All configuration
├── pyproject.toml                   # Dependencies & metadata
│
├── src/
│   ├── camera/
│   │   ├── webcam_camera.py         # WebcamStream — DirectShow (Windows)
│   │   └── rtsp_camera.py           # RTSPStream — FFMPEG with TCP reconnect
│   ├── recognition/
│   │   └── recognizer.py            # Models — InsightFace wrapper
│   ├── spoof/
│   │   └── antispoof.py             # MiniFASNetV2 — ONNX liveness
│   ├── database/
│   │   └── database.py              # EmbeddingDatabase — load/add/get
│   ├── enrollment/
│   │   ├── engine.py                # EnrollmentEngine — pipeline
│   │   ├── frame_validator.py       # FrameValidator — blur/confidence/size
│   │   └── video_sampler.py         # VideoFrameSampler — time-based sampling
│   ├── dataset/
│   │   └── utils.py                 # scan_files, get_all_identities
│   ├── ui/
│   │   └── display.py              # UI — snapshot, recording, indicators
│   └── utils.py                     # CUDA paths, config, CSV helpers
│
├── tools/
│   ├── enroll_image.py              # Batch image enrollment
│   ├── enroll_video.py              # Batch video enrollment
│   ├── analyze_enrollment.py        # Statistical enrollment analysis
│   ├── threshold_sensitivity_analysis.py  # Threshold optimization
│   └── performance_comparison.py    # Database mode benchmark
│
├── scripts/
│   └── setup.ps1                    # One-command Windows setup
│
├── models/                          # ONNX model files (download separately)
├── database/embeddings/             # Generated face embeddings
├── dataset/                         # Enrollment images & videos
├── reports/                         # CSV enrollment reports
└── docs/                            # Development documentation
```

---

## 📖 Usage Guide

### Webcam Mode

```bash
# Edit config.yaml:
#   camera.type: webcam
#   camera.source: 0  # or your webcam index

uv run python main.py
```

Controls:
| Key | Action |
|-----|--------|
| **Q** | Quit |
| **S** | Save snapshot |
| **R** | Toggle recording |

### Drone Mode

```bash
# Edit config.yaml:
#   camera.type: drone
#   camera.rtsp_url: rtsp://192.168.1.1:7070/webcam

uv run python main.py
```

### Headless Mode (No Display)

```bash
# Edit config.yaml:
#   processing.headless: true

uv run python main.py
```

> All GUI calls (`imshow`, `waitKey`, `namedWindow`) are skipped. Recognition runs silently with CMD output only.

### Enrollment Pipeline

```bash
# Dataset structure:
#   dataset/
#     alice/
#       enrollment/
#         images/    (*.jpg, *.jpeg)
#         videos/    (*.mp4)

# Image enrollment (one embedding per image)
uv run python tools\enroll_image.py

# Video enrollment (sampled frames per video)
uv run python tools\enroll_video.py
```

### Analysis Tools

```bash
# Statistical analysis of enrollment data
uv run python tools\analyze_enrollment.py

# Threshold sensitivity optimization
uv run python tools\threshold_sensitivity_analysis.py

# Database mode performance comparison
uv run python tools\performance_comparison.py
```

<!--
---

## 📊 Performance

<!-- TODO: Isi dengan hasil benchmark dari pengujian -->
<!-- Contoh:
| Mode | Provider | FPS | Detection Latency | Match Rate |
|------|----------|-----|-------------------|------------|
| Webcam | CPU | 18 | 22 ms | 85% |
| Webcam | CUDA | 32 | 12 ms | 85% |
| Drone  | CPU | 12 | 35 ms | 80% |
| Drone  | CUDA | 28 | 15 ms | 80% |

Catatan: match rate tergantung threshold dan kualitas dataset enrollment.
-->

<!--
---

## 📚 Thesis

<!-- TODO: Isi dengan informasi skripsi -->
<!-- Contoh:
**Judul:** [Judul Skripsi]

**Abstrak:** [Abstrak singkat]

**Laporan lengkap:** [Link ke repositori atau PDF]

**Pembimbing:** [Nama Pembimbing]

**Universitas:** [Nama Universitas]
-->

---

## 📖 Further Documentation

Detailed development documentation is available in the [`docs/`](docs/) directory:

| Document                                               | Description                                |
| ------------------------------------------------------ | ------------------------------------------ |
| [Project Context](docs/01_PROJECT_CONTEXT.md)          | Project objectives, architecture decisions |
| [System Design](docs/02_SYSTEM_DESIGN.md)              | Component architecture, data flow          |
| [Development Guide](docs/03_DEVELOPMENT_GUIDE.md)      | Setup, conventions, workflow               |
| [Enrollment Quickstart](docs/enrollment_quickstart.md) | Detailed enrollment setup                  |

---

## License

MIT
