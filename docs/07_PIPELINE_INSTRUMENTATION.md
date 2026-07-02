# Pipeline Instrumentation Documentation

**Date:** 2026-06-30  
**Status:** Complete

---

## Overview

Complete pipeline instrumentation has been implemented to measure each stage of the face recognition pipeline independently. This provides accurate performance data for optimization decisions.

---

## Measured Stages

### **1. Camera Capture Time**
- **What:** Time to capture frame from camera/stream
- **Includes:** Frame read, buffer wait, rotation (if any)
- **Metric:** `camera_times` list
- **Related FPS:** Camera FPS

### **2. Face Detection Time**
- **What:** InsightFace detection + embedding extraction
- **Includes:** Preprocessing, model inference, postprocessing
- **Metric:** `detection_times` list
- **Note:** Runs only every N frames (configurable via `frame_skip`)

### **3. Recognition (Embedding Comparison) Time**
- **What:** Cosine similarity comparison with database
- **Includes:** Normalization, dot product, max selection
- **Metric:** `recognition_times` list
- **Variable:** Depends on number of embeddings in database

### **4. MiniFASNet V2 Inference Time**
- **What:** Anti-spoofing liveness detection
- **Includes:** Face crop, resize, inference, softmax
- **Metric:** `minifasnet_times` list
- **Per-face:** Executed for each detected face

### **5. UI Rendering Time**
- **What:** OpenCV drawing operations
- **Includes:** Rectangles, text, overlays, timestamp
- **Metric:** `ui_times` list
- **Per-frame:** Executed every frame

### **6. Total Pipeline Time**
- **What:** End-to-end frame processing time
- **Includes:** All stages 1-5
- **Metric:** `total_frame_times` list
- **Per-frame:** Measured for every frame

---

## FPS Metrics

### **Camera FPS**
```python
camera_fps = 1.0 / camera_capture_time
```
- Measures raw camera throughput
- Independent of processing
- Useful for diagnosing camera bottlenecks

### **Display FPS**
```python
display_fps = 1.0 / frame_display_interval
```
- Measures actual display update rate
- Includes all processing + rendering
- What user perceives as "smoothness"

### **Recognition FPS**
```python
recognition_fps = 1.0 / recognition_interval
```
- Measures recognition event frequency
- Depends on `frame_skip` setting
- Useful for throughput analysis

### **Overall FPS (Smoothed)**
```python
fps_smoothed = EMA(1.0 / frame_time)
```
- Exponential moving average (alpha=0.9)
- Displayed on screen
- Used for real-time monitoring

---

## Recognition Metrics

### **Counts (Not Percentages)**

| Metric | Description |
|--------|-------------|
| **Total Recognitions** | Total recognition events |
| **Accepted** | Similarity ≥ threshold |
| **Unknown** | Similarity < threshold |
| **Spoof Detections** | Liveness check failures |

**Why counts, not percentages?**
- Accuracy cannot be inferred from threshold alone
- Requires ground truth labels for true accuracy
- Counts provide raw data without assumptions

### **Embedding Comparisons**
- **Total:** Sum of all comparisons across all recognitions
- **Average:** Total / Total Recognitions
- **Indicates:** Database size impact on performance

---

## Anti-Spoofing Enhancement

### **EMA Smoothing**

Raw liveness scores can fluctuate frame-to-frame. Exponential Moving Average (EMA) provides smoother, more stable scores:

```python
ema_alpha = 0.3  # Smoothing factor
ema_liveness = (alpha * raw_score) + ((1 - alpha) * previous_ema)
```

**Characteristics:**
- **Alpha = 0.3:** Moderate smoothing
- **Response time:** ~3-5 frames to stabilize
- **Benefits:** Reduces flickering, more stable UI
- **Trade-off:** Slight lag in score changes

**Displayed:**
- **Raw score:** Shown in UI for debugging
- **EMA score:** Used for display color/stability
- **Both logged:** For analysis

---

## Usage

### **Run Application**
```bash
.\.venv\Scripts\python.exe main.py
```

### **Exit and View Summary**
Press 'q' to exit. Performance summary will be printed automatically:

```
======================================================================
PIPELINE PERFORMANCE SUMMARY
======================================================================
Database Mode: multiple
Total Frames Processed: 1234
Total Recognition Events: 308

PIPELINE STAGE TIMING (average):
----------------------------------------------------------------------
  1. Camera Capture:        8.52ms
  2. Face Detection:        45.23ms
  3. Recognition (compare): 12.67ms
  4. MiniFASNet V2:         3.45ms
  5. UI Rendering:          2.18ms
  TOTAL Pipeline:           72.05ms

FPS METRICS:
----------------------------------------------------------------------
  Camera FPS:      29.8 (avg)
  Display FPS:     27.5 (avg)
  Recognition FPS: 7.4 (avg)
  Overall FPS:     27.5 (smoothed)

RECOGNITION METRICS:
----------------------------------------------------------------------
  Total Recognitions:     308
  Accepted (>threshold):  285 (92.5%)
  Unknown (<threshold):   23 (7.5%)
  Avg Comparisons:        135.0

ANTI-SPOOFING METRICS:
----------------------------------------------------------------------
  Spoof Detections:  12
  EMA Alpha:         0.3

======================================================================
```

---

## Performance Analysis

### **Identifying Bottlenecks**

| Symptom | Likely Bottleneck | Solution |
|---------|-------------------|----------|
| High camera time | Slow camera/stream | Reduce resolution, change codec |
| High detection time | Model inference | Use smaller det_size, optimize model |
| High recognition time | Large database | Embedding indexing, pruning |
| High MiniFASNet time | Multiple faces | Limit faces processed |
| High UI time | Complex overlays | Simplify drawing operations |
| High total time | Multiple bottlenecks | Address each stage individually |

### **Expected Values**

| Stage | Good | Acceptable | Needs Attention |
|-------|------|------------|-----------------|
| Camera | <10ms | 10-20ms | >20ms |
| Detection | <50ms | 50-100ms | >100ms |
| Recognition | <5ms | 5-20ms | >20ms |
| MiniFASNet | <5ms | 5-10ms | >10ms |
| UI | <2ms | 2-5ms | >5ms |
| **Total** | **<60ms** | **60-100ms** | **>100ms** |

---

## Configuration Impact

### **Frame Skip Rate**
```yaml
processing:
  frame_skip: 4  # Process every 5th frame
```

**Effect:**
- Higher skip = lower recognition FPS, higher overall FPS
- Lower skip = higher recognition FPS, lower overall FPS
- **Recommended:** 4-6 for real-time balance

### **Detection Size**
```yaml
recognition:
  det_size: [320, 320]  # Smaller = faster, less accurate
```

**Effect:**
- Smaller = faster detection, may miss small faces
- Larger = slower detection, better accuracy
- **Recommended:** 320x320 for drone applications

---

## Data Logging

All metrics are stored in lists during runtime:
- `camera_times[]`
- `detection_times[]`
- `recognition_times[]`
- `minifasnet_times[]`
- `ui_times[]`
- `total_frame_times[]`
- `camera_fps_values[]`
- `display_fps_values[]`
- `recognition_fps_values[]`

**Future Enhancement:**
- Export to CSV for offline analysis
- Real-time plotting
- Statistical analysis (std dev, percentiles)

---

## Comparison Methodology

### **Before Optimization:**
1. Run application with current settings
2. Collect metrics for 2-3 minutes
3. Note average values
4. Apply optimization
5. Repeat steps 1-3
6. Compare before/after

### **A/B Testing:**
```bash
# Test A: Legacy database
# Edit config.yaml: database.mode: "legacy"
python main.py
# Exit with 'q', note metrics

# Test B: Multiple database
# Edit config.yaml: database.mode: "multiple"
python main.py
# Exit with 'q', compare metrics
```

---

## Troubleshooting

### **Inconsistent Metrics**
- **Cause:** Too short test duration
- **Solution:** Run for at least 2-3 minutes

### **Negative FPS**
- **Cause:** Timer overflow or system sleep
- **Solution:** Restart application, avoid sleep mode

### **Missing Metrics**
- **Cause:** No faces detected
- **Solution:** Ensure faces visible in frame

### **High Variance**
- **Cause:** System load fluctuations
- **Solution:** Close other applications, use median instead of mean

---

## Next Steps

1. **Baseline Measurement:**
   - Run with legacy database
   - Document all metrics
   - Establish baseline performance

2. **Multiple Database Test:**
   - Switch to multiple embedding mode
   - Run same test conditions
   - Compare metrics

3. **Optimization Targets:**
   - Identify slowest stage
   - Research optimization strategies
   - Implement and measure

4. **Continuous Monitoring:**
   - Log metrics for each session
   - Track performance over time
   - Detect degradation early

---

**Instrumentation Status:** ✅ Complete  
**Ready for Testing:** ✅ YES  
**Next Action:** Run baseline performance test