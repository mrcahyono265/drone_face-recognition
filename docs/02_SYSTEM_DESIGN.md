# SYSTEM DESIGN

## Overview

This document describes the software architecture of the Drone-Based Face Recognition System.

The system uses pretrained MobileFaceNet from InsightFace for face recognition and MiniFASNetV2 for face anti-spoofing.

The drone acts only as a camera. All processing is performed on a laptop.

No model retraining is performed.

---

# High Level Architecture

Camera (Drone / Webcam)

↓

Frame Capture

↓

Face Detection

↓

Face Anti-Spoofing

↓

Face Recognition

↓

Display Result

↓

Snapshot / Recording

The embedding database is built during the enrollment stage and is only used during recognition.

---

# System Modules

The project consists of several independent modules.

1. Camera Module
2. Face Detection Module
3. Face Recognition Module
4. Anti-Spoofing Module
5. Enrollment Module
6. Embedding Database Module
7. User Interface Module
8. Evaluation Module

Each module should have a single responsibility.

---

# Recognition Pipeline

Real-time recognition follows the pipeline below.

Frame

↓

Face Detection

↓

Face Alignment (handled internally by InsightFace)

↓

Face Embedding Extraction

↓

Embedding Normalization

↓

Cosine Similarity

↓

Identity Decision

↓

Display Result

Only one embedding is extracted for each detected face.

Recognition uses pretrained MobileFaceNet only.

---

# Anti-Spoofing Pipeline

For every detected face:

Face Crop

↓

MiniFASNetV2

↓

Real / Spoof

If the face is spoof:

Recognition is rejected.

If the face is real:

Recognition continues.

---

# Enrollment Pipeline

Enrollment is divided into two stages.

Stage 1

Image Enrollment

↓

Face Detection

↓

Embedding Extraction

↓

Embedding Database

Stage 2

Video Enrollment

↓

Frame Sampling

↓

Quality Filtering

↓

Embedding Extraction

↓

Embedding Database

Video enrollment is NOT used to train the model.

Video enrollment only enriches the embedding database.

---

# Frame Sampling

Videos should not generate embeddings from every frame.

Instead:

Video

↓

Sample Frames

↓

Quality Filtering

↓

Embedding Extraction

The sampling interval should be configurable.

Example:

Every 5 frames

or

Every 200 milliseconds

---

# Quality Filtering

Only high-quality frames should be accepted.

Filtering may include:

- Blur detection
- Face size checking
- Face confidence checking
- Duplicate embedding removal
- Occlusion filtering (optional)

Poor-quality frames should be discarded.

---

# Embedding Database

The recognition database stores multiple embeddings for every person.

Example

Database

├── Ridho

│ ├── emb001.npy

│ ├── emb002.npy

│ ├── emb003.npy

│ └── ...

│

├── Wafa

│ ├── emb001.npy

│ ├── emb002.npy

│ └── ...

Each embedding represents one valid face observation.

The number of embeddings is dynamic.

There is NO fixed limit.

---

# Recognition Strategy

Given a query embedding:

Compare against every stored embedding.

Compute cosine similarity.

The highest similarity score becomes the identity score.

Example

Query

↓

Ridho

0.82

0.91

0.88

↓

Maximum = 0.91

↓

Identity = Ridho

Average similarity should NOT be used.

---

# Similarity Threshold

Recognition uses cosine similarity.

Threshold should be configurable.

Example

0.45

0.50

0.55

Threshold optimization belongs to the evaluation stage.

The threshold should never be hardcoded inside algorithms.

---

# Dataset Structure

Dataset

├── ridho

│ ├── enrollment

│ │ ├── images

│ │ └── videos

│ │

│ └── processed

│ ├── sampled_frames

│ ├── filtered_frames

│ └── embeddings

│

├── wafa

│ ├── enrollment

│ └── processed

Each person owns an independent dataset.

---

# Project Structure

The project should be modular.

Suggested structure

project/

├── configs/

├── dataset/

├── database/

├── docs/

├── logs/

├── models/

├── output/

├── src/

│ ├── camera/

│ ├── recognition/

│ ├── spoof/

│ ├── enrollment/

│ ├── database/

│ ├── evaluation/

│ ├── ui/

│ └── utils/

├── main.py

└── requirements.txt

---

# Module Responsibilities

Camera

Responsible only for acquiring frames.

Recognition

Responsible only for recognition.

Spoof

Responsible only for liveness detection.

Enrollment

Responsible only for building embeddings.

Database

Responsible only for loading and saving embeddings.

Evaluation

Responsible only for calculating metrics.

UI

Responsible only for visualization.

Modules should not depend on unrelated modules.

---

# Runtime Configuration

System parameters should be configurable.

Examples

Camera source

Frame sampling interval

Recognition threshold

Spoof threshold

Logging level

Output directory

Avoid hardcoded values whenever possible.

---

# Expected Runtime Output

Each detected face should display:

Bounding Box

Identity

Confidence Score

Real / Spoof

FPS

Timestamp

Unknown faces should be labeled:

Unknown

with their similarity score.

---

# Design Principles

The software should satisfy the following principles.

- Modular
- Easy to maintain
- Easy to test
- Easy to extend
- Research-oriented
- Real-time capable
- Readable source code

The architecture should prioritize stability and simplicity over unnecessary complexity.

This project is intended as a research prototype rather than a production-scale system.
