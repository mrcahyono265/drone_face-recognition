# DEVELOPMENT GUIDE

## Purpose

This document defines the implementation rules for the project.

The AI must follow these guidelines before modifying, creating, or deleting any source code.

The objective is to maintain research consistency, code quality, and modular software architecture throughout the development process.

---

# General Development Philosophy

This project is an undergraduate research prototype.

The priority order is:

1. Research consistency
2. Code correctness
3. Real-time performance
4. Maintainability
5. Readability
6. Additional features

Do not add unnecessary features.

Every implementation must directly support the research objectives.

---

# Development Principles

The AI should always:

- Think before coding.
- Explain the implementation plan.
- Minimize unnecessary changes.
- Preserve existing working features.
- Refactor only when beneficial.
- Keep the project modular.
- Write readable code.
- Write reusable code.

---

# Project Development Stages

Development is divided into several phases.

## Phase 1

Project Refactoring

Objectives

- Organize folder structure.
- Organize Python modules.
- Remove duplicate code.
- Separate responsibilities.

No algorithm changes.

---

## Phase 2

Enrollment System

Objectives

- Image enrollment.
- Video enrollment.
- Frame sampling.
- Quality filtering.
- Embedding extraction.
- Embedding database construction.

No recognition optimization yet.

---

## Phase 3

Recognition System

Objectives

- Real-time recognition.
- Multiple embedding comparison.
- Cosine similarity.
- Unknown recognition.
- Threshold configuration.

---

## Phase 4

Anti Spoofing Integration

Objectives

- MiniFASNetV2 integration.
- Recognition blocking for spoof.
- Status visualization.

---

## Phase 5

Evaluation

Objectives

- Recognition accuracy.
- Recognition latency.
- FPS measurement.
- Threshold evaluation.
- Confusion matrix.
- FAR and FRR calculation (if required).

---

# Coding Standards

The project uses:

Python 3.11

Follow PEP8.

Use descriptive variable names.

Keep functions short.

Avoid duplicated logic.

Use comments only when necessary.

Avoid magic numbers.

Avoid global variables.

Avoid deeply nested conditions.

---

# Module Rules

Every module must have only one responsibility.

Example

Camera Module

Acquire frames only.

Recognition Module

Recognition only.

Enrollment Module

Enrollment only.

Database Module

Load and save embeddings only.

UI Module

Display information only.

Utility Module

Reusable helper functions only.

---

# Configuration Rules

System parameters should not be hardcoded.

Examples

Recognition Threshold

Spoof Threshold

Sampling Interval

Camera Source

Output Directory

Configuration should be stored in a dedicated configuration file.

---

# Database Rules

The embedding database should contain:

Multiple embeddings per person.

Each embedding is stored independently.

The database must support:

Adding new embeddings.

Updating existing identities.

Removing identities.

Loading at startup.

Saving after enrollment.

---

# Video Processing Rules

Videos are NOT training data.

Videos are additional enrollment sources.

Pipeline

Video

↓

Frame Sampling

↓

Quality Filtering

↓

Embedding Extraction

↓

Database Update

Only high-quality embeddings should be stored.

The number of embeddings is dynamic.

Do not force a fixed number of embeddings.

---

# Recognition Rules

Recognition uses:

InsightFace

↓

MobileFaceNet

↓

Embedding

↓

Cosine Similarity

↓

Identity

The recognition model must remain pretrained.

Do not modify model weights.

Do not retrain.

Do not fine-tune.

Do not replace MobileFaceNet.

---

# Anti Spoofing Rules

MiniFASNetV2 is executed before identity confirmation.

If spoof

↓

Reject recognition

If real

↓

Continue recognition

The anti-spoofing module must remain independent from the recognition module.

---

# Error Handling

Every module should handle failures gracefully.

Examples

Camera disconnected.

No face detected.

Multiple faces detected.

Empty database.

Missing model.

Invalid image.

Missing video.

The application should never crash because of expected runtime errors.

---

# Logging

Use logging instead of excessive print statements.

Log important events.

Examples

Camera connected.

Model loaded.

Enrollment completed.

Database saved.

Recognition started.

Spoof detected.

Application closed.

Logging should help debugging without cluttering the console.

---

# Performance Guidelines

The system targets real-time execution.

Avoid unnecessary computations.

Avoid repeated loading of models.

Reuse initialized objects whenever possible.

Cache reusable resources.

Prioritize lightweight processing.

---

# Code Refactoring Policy

Before deleting any existing code:

The AI must explain:

- Why it should be removed.
- Which module replaces it.
- Why the new implementation is better.

Do not remove working features without justification.

---

# Documentation Rules

Every public class should have a short description.

Every public function should describe:

Purpose

Parameters

Returns

Complex implementations should include brief explanations.

---

# Git Commit Style

Suggested commit format

refactor:

Refactor project structure

feat:

Add video enrollment

fix:

Fix cosine similarity calculation

docs:

Update development guide

style:

PEP8 formatting

---

# AI Decision Policy

Before implementing any feature, the AI must answer:

1. What problem is being solved?

2. Which module is affected?

3. Does it change the research methodology?

4. Does it violate PROJECT_CONTEXT?

5. Does it preserve pretrained MobileFaceNet?

Only after these questions are satisfied may implementation begin.

The AI must implement only one approved step at a time.

After completing a step:

1. Explain the changes made.
2. List all modified files.
3. Explain how to test the changes.
4. Wait for user confirmation before continuing.

Do not automatically implement multiple steps in one iteration.

Each step should leave the project in a runnable and testable state.

---

# Success Criteria

The project is considered complete when:

- The system performs real-time face recognition.
- Recognition uses pretrained MobileFaceNet.
- Anti-spoofing is integrated.
- Enrollment supports both images and videos.
- Multiple embeddings per identity are supported.
- Unknown faces are detected correctly.
- The software architecture is modular.
- The code is readable and maintainable.
- The implementation matches the research methodology.

Research consistency is more important than implementing additional features.
