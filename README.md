# Drone E99 — Face Recognition & Anti-Spoofing

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Real-time face recognition + liveness detection for drone (RTSP) and webcam. Built for undergraduate thesis research.

## CUDA Requirements

GPU acceleration uses `onnxruntime-gpu>=1.27.0` with **CUDA 13** native packages (`nvidia-cudnn-cu13`, etc.). Supported GPUs: NVIDIA RTX 2000 series+, driver ≥ 610.

> **CUDA 11/12?** Edit `pyproject.toml` and change `cu13` packages to `cu11`/`cu12`, or switch to CPU: install `onnxruntime` instead of `onnxruntime-gpu` and set `config.yaml` → `processing.provider: cpu`.

## Quick Start

**Prerequisites:** [uv](https://docs.astral.sh/uv/) (recommended) or Python 3.11+

```bash
# 1. Setup environment (auto-downloads all deps)
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# Or manually:
uv venv
uv sync

# 2. Enroll faces from example images
uv run python tools\enroll_image.py

# 3. Run recognition (default: webcam, change config.yaml for drone)
uv run python main.py
```

> **No GPU?** The system defaults to CPU. To enable CUDA acceleration, edit `config.yaml` → `processing.provider: cuda`.

## Pipeline

```
Camera (RTSP/Webcam)
  → Face Detection (InsightFace buffalo_sc)
  → Embedding Extraction (512-D)
  → Database Matching (Cosine Similarity)
  → Anti-Spoofing (MiniFASNetV2)
  → Real-time Display + Recording
```

## Controls

| Key | Action |
|-----|--------|
| **Q** | Quit |
| **S** | Save snapshot |
| **R** | Toggle recording |

## Project Structure

```
├── main.py                      # Entry point
├── config.yaml                  # Configuration
├── pyproject.toml               # Dependencies & metadata
│
├── src/
│   ├── camera/                  # Webcam + RTSP capture
│   ├── recognition/             # InsightFace wrapper
│   ├── spoof/                   # MiniFASNetV2 anti-spoofing
│   ├── database/                # Embedding database
│   ├── enrollment/              # Enrollment engine
│   ├── dataset/                 # Dataset utilities
│   ├── ui/                      # Display, snapshot, recording
│   └── utils.py                 # Shared helpers (CUDA paths, config, CSV)
│
├── tools/                       # Enrollment & analysis scripts
├── scripts/setup.ps1            # One-command setup
├── models/                      # ONNX model files
├── database/embeddings/         # Generated face embeddings
└── dataset/                     # Enrollment images & videos
```

## Configuration

Edit `config.yaml`:

| Key | Default | Description |
|-----|---------|-------------|
| `camera.type` | `webcam` | `webcam` or `drone` (RTSP) |
| `camera.source` | `0` | Webcam index |
| `camera.rtsp_url` | — | RTSP URL for drone |
| `processing.provider` | `cpu` | `cuda` or `cpu` |
| `processing.frame_skip` | `4` | Process every Nth frame |
| `processing.headless` | `false` | `true` to run without display (e.g. drone) |
| `recognition.similarity_threshold` | `0.45` | Match threshold |
| `spoofing.liveness_threshold` | `0.85` | Liveness score cutoff |
| `database.mode` | `multiple` | `multiple` or `legacy` |

## License

MIT
