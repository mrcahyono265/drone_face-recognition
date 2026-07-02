# PROJECT CONTEXT

## Project Title

Drone-Based Face Recognition System Using MobileFaceNet (InsightFace) and MiniFASNetV2 for Anti-Spoofing

---

# Project Objective

This project aims to develop a real-time face recognition system for drones using a pretrained MobileFaceNet model provided by the InsightFace library.

The system performs face recognition through facial embeddings without retraining the recognition model.

The project also integrates MiniFASNetV2 to perform face anti-spoofing so that only real faces are allowed for recognition.

---

# Research Scope

This project focuses on:

- Face Detection
- Face Recognition
- Face Anti-Spoofing
- Real-time Processing
- Face Enrollment
- Embedding Database Construction
- Evaluation

This project DOES NOT focus on:

- Training MobileFaceNet
- Transfer Learning
- Fine-Tuning
- Few-Shot Learning
- Face Classification Model Training

---

# Recognition Method

Recognition is performed using a pretrained MobileFaceNet model from InsightFace.

Pipeline:

Face Image

↓

InsightFace

↓

512-D Face Embedding

↓

Cosine Similarity

↓

Identity

The recognition model is NEVER retrained.

Only the embedding database is built.

---

# Enrollment Method

Enrollment consists of:

1. Face Images
2. Face Videos

Images are processed directly.

Videos are processed using:

Video

↓

Frame Sampling

↓

Quality Filtering

↓

Embedding Extraction

↓

Embedding Database

The number of embeddings for each person is dynamic.

There is NO fixed number of embeddings.

Only high-quality frames are stored.

---

# Embedding Database

Each person owns multiple embeddings.

Example

Ridho

├── emb001.npy

├── emb002.npy

├── emb003.npy

└── ...

Recognition compares the query embedding against every stored embedding.

The highest cosine similarity becomes the final similarity score.

---

# Anti Spoofing

MiniFASNetV2 is executed after face detection.

If Spoof

↓

Recognition Result = Rejected

If Real

↓

Continue Face Recognition

---

# Expected Output

For every detected face:

- Bounding Box
- Identity
- Confidence Score
- Real / Spoof Status
- FPS

Example

Ridho

Confidence : 0.87

Status : Real

---

# Dataset

Dataset is collected manually.

Each subject contains:

Enrollment

├── Images

└── Videos

Images contain multiple head poses.

Videos contain multiple environments.

Examples:

- Plain background
- Noisy background
- Near distance
- Medium distance

---

# Important Rules

The AI MUST NEVER:

- Suggest retraining MobileFaceNet.
- Replace InsightFace.
- Replace MiniFASNetV2.
- Introduce Few-Shot Learning.
- Introduce Transfer Learning.
- Introduce Fine-Tuning.

The AI MUST ALWAYS:

- Preserve pretrained MobileFaceNet.
- Use embedding-based recognition.
- Use cosine similarity.
- Build embedding database only.
- Maintain modular architecture.
- Explain every design decision before coding.

---

# Development Goal

The primary goal is producing a stable and modular research prototype suitable for undergraduate thesis evaluation.

Code readability, modularity, maintainability, and research consistency are prioritized over implementing unnecessary features.
