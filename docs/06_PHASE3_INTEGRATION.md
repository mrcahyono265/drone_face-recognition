# Phase 3 Integration Plan

**Status:** In Progress  
**Date:** 2026-06-30

---

## Overview

Phase 3 integrates the new multiple embedding database into the real-time recognition application with backward compatibility support for the legacy database.

### Key Features

1. **Configurable Database Mode** - Switch between legacy and multiple embedding databases via `config.yaml`
2. **Performance Measurement** - Automatic collection of FPS, latency, and comparison metrics
3. **Backward Compatibility** - Legacy database remains functional during transition period
4. **Comparison Tools** - Scripts to measure and compare performance between modes

---

## Implementation Status

### ✅ Completed (Step 1-4)

1. **Configuration Update**
   - Added `database.mode` parameter to `config.yaml`
   - Updated blur threshold to 650 (based on sensitivity analysis)
   - Maintains backward compatibility with existing configurations

2. **Dual Database Support in main.py**
   - Import `EmbeddingDatabase` module
   - Conditional database loading based on mode
   - Support for both legacy (pickle) and multiple (file-based) databases

3. **Recognition Logic Update**
   - Dual-path recognition: legacy vs multiple
   - Multiple embeddings use MAX similarity strategy
   - Legacy uses single embedding comparison

4. **Performance Measurement**
   - Recognition latency tracking
   - Embedding comparison counting
   - FPS monitoring
   - Accuracy estimation

5. **Performance Summary**
   - Automatic printing of metrics on exit
   - Includes: latency, comparisons, accuracy, FPS

### 🔄 In Progress (Step 5-6)

6. **Performance Comparison Script**
   - `tools/performance_comparison.py` created
   - Automated A/B testing between modes
   - Statistical comparison of metrics

7. **Integration Testing**
   - Manual testing required with real camera feed
   - Validation of both database modes
   - Performance benchmark collection

### ⏳ Pending (Step 7)

8. **Legacy Removal Decision**
   - Based on performance comparison results
   - Criteria: < 5% FPS degradation, < 2ms latency increase
   - Community feedback period

---

## Configuration

### Switching Database Modes

Edit `config.yaml`:

```yaml
database:
  mode: "legacy"    # Use legacy pickle database
  # OR
  mode: "multiple"  # Use new multiple embedding database
```

### Current Settings

```yaml
database:
  mode: "legacy"  # Default to legacy for safety
  path: "face_db.pkl"
  embeddings_dir: "database/embeddings"

enrollment:
  duplicate_threshold: 0.995
  validation:
    max_blur_score: 650  # Updated from sensitivity analysis
```

---

## Usage

### Running with Legacy Database

```bash
# Ensure config.yaml has mode: "legacy"
python main.py
```

### Running with Multiple Embedding Database

```bash
# Ensure config.yaml has mode: "multiple"
python main.py
```

### Performance Comparison

```bash
# Run automated comparison test
python tools/performance_comparison.py
```

**Note:** Both databases must be populated for comparison test.

---

## Performance Metrics

### Collected Automatically

| Metric | Description | Target |
|--------|-------------|--------|
| **Avg FPS** | Average frames per second | > 25 FPS |
| **Recognition Latency** | Time per recognition (ms) | < 10ms |
| **Embedding Comparisons** | Avg comparisons per recognition | Varies |
| **Recognition Accuracy** | % of recognitions above threshold | > 90% |
| **FPS Stability** | Standard deviation of FPS | < 5 FPS |

### Comparison Criteria

Multiple embedding mode is considered **acceptable** if:

- FPS degradation < 5%
- Latency increase < 2ms
- Accuracy improvement > 5% (expected due to more embeddings)

Multiple embedding mode is considered **superior** if:

- FPS comparable (± 2 FPS)
- Latency comparable (± 1ms)
- Accuracy improvement > 10%

---

## Testing Procedure

### Step 1: Populate Databases

```bash
# Legacy database (if not already done)
python build_embedding_database.py

# Multiple embedding database
python tools/enroll_image.py
python tools/enroll_video.py
```

### Step 2: Test Legacy Mode

```bash
# Set mode to legacy in config.yaml
# Run application for 2-3 minutes
python main.py

# Note the performance summary on exit
```

### Step 3: Test Multiple Mode

```bash
# Set mode to multiple in config.yaml
# Run application for 2-3 minutes
python main.py

# Note the performance summary on exit
```

### Step 4: Run Comparison Test

```bash
# Automated comparison (requires both databases populated)
python tools/performance_comparison.py

# Review comparison summary
```

### Step 5: Analyze Results

Compare metrics against criteria:
- Is FPS acceptable?
- Is latency within target?
- Is accuracy improved?

Make decision on legacy removal based on results.

---

## Expected Results

### Legacy Database

- **Embeddings:** ~2-6 per identity (averaged)
- **Comparisons:** 2-6 per recognition
- **Latency:** ~1-3ms
- **FPS:** 28-32 FPS

### Multiple Embedding Database

- **Embeddings:** ~100-150 per identity
- **Comparisons:** 100-150 per recognition
- **Latency:** ~5-15ms (expected increase)
- **FPS:** 25-30 FPS (slight decrease expected)

### Trade-off

Multiple embedding mode trades **slight performance decrease** for:
- ✅ Better recognition accuracy
- ✅ More robust to pose/illumination changes
- ✅ Dynamic embedding count (no averaging)
- ✅ Research methodology compliance

---

## Rollback Plan

If multiple embedding mode shows unacceptable performance:

1. **Immediate Rollback:**
   - Set `database.mode: "legacy"` in config.yaml
   - Restart application
   - No code changes required

2. **Investigation:**
   - Analyze performance logs
   - Identify bottlenecks
   - Consider optimization strategies

3. **Optimization Options:**
   - Embedding indexing (FAISS, Annoy)
   - Embedding pruning (keep top N per identity)
   - Parallel comparison (multi-threading)
   - GPU acceleration (if available)

---

## Decision Timeline

| Date | Milestone |
|------|-----------|
| 2026-06-30 | Integration complete, testing begins |
| 2026-07-01 | Performance comparison test run |
| 2026-07-02 | Results analysis |
| 2026-07-03 | Decision on legacy removal |
| 2026-07-04+ | Legacy code removal (if approved) |

---

## Files Modified

### Core Application
- `main.py` - Dual database support, performance measurement
- `config.yaml` - Database mode configuration

### Tools
- `tools/performance_comparison.py` - Automated comparison testing

### Documentation
- `docs/06_PHASE3_INTEGRATION.md` - This document

---

## Next Steps

1. ✅ Complete integration (DONE)
2. ⏳ Run performance comparison test
3. ⏳ Analyze results
4. ⏳ Make decision on legacy removal
5. ⏳ (If approved) Remove legacy code

---

**Integration Status: READY FOR TESTING**

Pending performance comparison results before proceeding to legacy removal.