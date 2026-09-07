# 🛡️ IBVAP — Intelligent Border Video Analytics Platform
### Smart India Hackathon 2026 | Problem Statement: SIH26187
**Organization:** Ministry of Home Affairs — Sashastra Seema Bal (SSB), Police II Division  
**Category:** Software | **Theme:** Smart Automation

---

## 📌 Executive Summary

Conventional CCTV infrastructure deployed at Border Out Posts (BOPs), border check posts, and ingress roads primarily provides passive video recording and live monitoring, demanding continuous human vigilance. Proprietary smart camera hardware and commercial FRS/ANPR equipment are prohibitively expensive and difficult to maintain across remote, rugged border sectors.

**IBVAP (Intelligent Border Video Analytics Platform)** is an AI-driven, software-defined surveillance platform that transforms standard IP-based CCTV infrastructure into an active, intelligent surveillance network. It operates 100% locally on edge hardware (CPU/GPU) without requiring specialized smart cameras or cloud connectivity.

---

## 🚀 Key Capabilities (Delivered MVP)

1. **Human Detection & Multi-Object Tracking:**
   - Stock YOLOv8 nano inference filtered to persons.
   - Real-time Centroid Tracking with persistent track IDs and 30-frame trajectory history.
2. **Virtual Fence & Perimeter Intrusion Detection:**
   - Digital tripwire and restricted perimeter boundary crossing detection.
   - Segment-intersection trajectory analysis triggering instant `INTRUSION_ALERT` alarms with exact geographic coordinates.
3. **Cascaded Automatic Number Plate Recognition (ANPR):**
   - Cascaded pipeline triggered **strictly on detected vehicle classes** (`car`, `truck`, `bus`, `motorcycle`).
   - License plate localization via YOLOv8 plate detector + contrast-normalized EasyOCR.
   - **Temporal Best-per-Track Smoothing:** Aggregates multi-frame plate readings, locking in the highest confidence read as the vehicle approaches.
   - **Operational Integrity Fallback:** Distant, occluded, or unreadable plates are automatically flagged as `FLAGGED_FOR_MANUAL_REVIEW` rather than outputting erroneous readings.
4. **Multi-Channel Defense Command Dashboard (Streamlit):**
   - **Channel 1 — BOP Sector 4 Perimeter:** Real-time pedestrian tracking and boundary breach alerting.
   - **Channel 2 — Checkpost Charlie Ingress:** Real-time vehicular classification, license plate detection, and ANPR.
   - **Channel 3 — Pre-recorded Insurance Demo:** Pre-rendered annotated stream ensuring zero-lag presentations.
   - **Historical Incident Register:** Real-time event log with interactive filtering and one-click CSV audit export.
5. **SSB Operational Scaling Roadmap (Phase 6):**
   - Thermal / Low-Light Night Vision (KAIST/FLIR multispectral sensor integration).
   - Ruggedized Edge Box Deployment (NVIDIA Jetson AGX / Orin Nano @ 15W).
   - Facial Recognition System (RetinaFace + ArcFace MobileFaceNet vector search).
   - Multi-Camera Spatial Re-Identification (Cross-camera OSNet appearance matching).

---

## 🏗️ Project Architecture

```
SIH26187/
├── app.py                       # Streamlit Multi-Channel Surveillance Station
├── run_cli.py                   # Standalone CLI Detection Pipeline Runner
├── test_phase2.py               # Centroid Tracker + Virtual Fence Verifier
├── test_phase3.py               # Cascaded ANPR & Throughput Benchmark
├── render_backup_video.py       # Hackathon Insurance Pre-render Script
├── requirements.txt             # Project Python Dependencies
├── .gitignore                   # Clean Git tracking configuration
├── models/
│   ├── yolov8n.pt               # Pretrained YOLOv8 Nano COCO weights
│   └── licensePlateDetector.pt  # Trained YOLOv8 License Plate Detector
├── modules/
│   ├── __init__.py
│   ├── detector.py              # YOLOv8 Person & Vehicle Detection Module
│   ├── tracker.py               # Centroid Tracker with Trajectory History
│   ├── fence.py                 # Virtual Fence Line-Crossing Intrusion Engine
│   ├── anpr.py                  # Cascaded Plate Detector + EasyOCR + Cache
│   └── logger.py                # In-memory Event Logger & CSV Exporter
└── sample_videos/
    ├── bop_perimeter.mp4        # Channel 1: Pedestrian Border Sector Video
    ├── checkpost_traffic.mp4    # Channel 2: Vehicle Checkpoint Video
    └── backup_annotated_run.mp4 # Channel 3: Pre-rendered Annotated Backup Run
```

---

## ⚡ Quick Start

### 1. Installation
```bash
# Clone repository
git clone https://github.com/akshad1007/SIH26.git
cd SIH26

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Command Center (Streamlit)
```bash
streamlit run app.py
```
*Open http://localhost:8501 in your browser.*

### 3. Headless / CLI Verification
```bash
# Test Core Detection
python run_cli.py

# Test Virtual Fence Intrusion
python test_phase2.py

# Test Cascaded ANPR & Throughput
python test_phase3.py
```

---

## 📊 Evaluation & Verification Summary

| Feature | Benchmark Metric | Result |
| :--- | :--- | :--- |
| **Detection Engine** | YOLOv8n on CPU | 8.5 FPS (720p), 5.0 FPS (1080p) |
| **Intrusion Detection** | Tripwire crossing | 7 verified breach events detected & logged |
| **ANPR Engine** | EasyOCR on vehicle crops | Verified read (`K433ZR` @ 91.8% confidence) |
| **Low-Confidence Handling**| Blurry / distant plates | Flagged for manual review (0% false positives) |

---
*Built for the Smart India Hackathon 2026.*
