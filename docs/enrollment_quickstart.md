# Quick Start Guide - Automated Enrollment

## 🚀 Quick Commands

### **Image Enrollment**
```bash
uv run python tools\enroll_image.py
```

### **Video Enrollment**
```bash
uv run python tools\enroll_video.py
```

---

## 📁 Dataset Structure

```
dataset/
├── ridho/
│   └── enrollment/
│       ├── images/     ← Place .jpg, .jpeg here
│       └── videos/     ← Place .mp4 here
├── wafa/
│   └── enrollment/
│       ├── images/
│       └── videos/
└── ...
```

**Important:**
- Identity name = folder name (e.g., "ridho", "wafa")
- No manual input needed
- Flat structure only (no subfolders)

---

## ⚙️ Configuration (config.yaml)

```yaml
dataset:
  root: "dataset"
  enrollment_images: "enrollment/images"
  enrollment_videos: "enrollment/videos"

enrollment:
  duplicate_threshold: 0.995
  sampling_interval_ms: 300

logging:
  verbose: false   # Set true for detailed output
```

---

## 📊 What Happens

### **Image Enrollment:**
1. Scans all folders in `dataset/`
2. For each identity:
   - Reads all .jpg, .jpeg files
   - Detects faces
   - Extracts embeddings
   - Checks duplicates
   - Saves unique embeddings
3. Generates CSV report

### **Video Enrollment:**
1. Scans all folders in `dataset/`
2. For each identity:
   - Reads all .mp4 files
   - Samples frames every 300ms
   - Validates each frame
   - Extracts embeddings from valid frames
   - Checks duplicates
   - Saves unique embeddings
3. Generates CSV report

---

## 📈 Output

### **Console:**
```
=== Automated Image Enrollment Pipeline ===
Dataset Root: dataset
Identities Found: ridho, wafa

Processing Identity: ridho
  Found 10 image(s)
  Identity Summary: ridho
    Total: 10
    Success: 10
    Embeddings Stored: 10

=== Overall Summary ===
Total Identities: 2
Total Images: 20
Total Embeddings: 20

Validating embeddings...
  All embeddings valid [OK]

CSV Report: reports/enrollment/image_report_20260702_123456.csv
```

### **Database:**
```
database/embeddings/
├── ridho/
│   ├── emb_0001.npy
│   ├── emb_0002.npy
│   └── ...
└── wafa/
    ├── emb_0001.npy
    └── ...
```

### **Reports:**
```
reports/enrollment/
├── image_report_20260702_123456.csv
└── video_report_20260702_123789.csv
```

---

## ✅ Validation

All embeddings are automatically validated:
- ✅ Dimension = 512
- ✅ L2-normalized (norm ≈ 1.0)
- ✅ No corrupt files

If validation fails, warnings are displayed.

---

## 🎯 Tips

### **For Best Results:**
1. **Images:**
   - Various angles (front, left45, left90, right45, right90)
   - Good lighting
   - Clear face visibility
   - 5-10 images per identity minimum

2. **Videos:**
   - Slow head rotation (capture all angles)
   - Good lighting
   - Stable camera
   - 2-3 minutes per video

3. **Performance:**
   - Image enrollment: Fast (~2 sec/image)
   - Video enrollment: Slower (~30 sec/video minute)
   - Run image first, then video for coverage

### **Verbose Mode:**
For detailed per-file output:
```yaml
logging:
  verbose: true
```

### **Check Results:**
- Console summary shows counts
- CSV report has detailed per-file results
- Embeddings stored in `database/embeddings/`

---

## ⚠️ Troubleshooting

**"No identities found"**
→ Check `dataset/` folder structure

**"No images/videos found"**
→ Check folder paths match config

**High duplicate rate**
→ Normal if database already has good coverage

**All frames = "no_face"**
→ Check video quality, ensure faces visible

---

## 📚 More Info

See [README.md](../README.md) for full project documentation.