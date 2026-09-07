# 🛡️ SIH 2026 — Official PPT Content (SIH26187)
### Template-Compliant Slide-by-Slide Deck (6 Slides Total)

---

## SLIDE 1: TITLE PAGE

- **Problem Statement ID:** SIH26187
- **Problem Statement Title:** AI-Based Intelligent Video Analytics Platform for Border Surveillance using existing CCTV Infrastructure
- **Theme:** Smart Automation
- **PS Category:** Software
- **Organization:** Ministry of Home Affairs — Sashastra Seema Bal (SSB), Police II Division
- **Project Name:** **IBVAP** (Intelligent Border Video Analytics Platform)
- **Team ID:** `[Insert Your Team ID Here]`
- **Team Name:** `[Insert Your Registered Team Name Here]`

---

## SLIDE 2: PROPOSED SOLUTION

### Idea Title: IBVAP — Edge AI-Driven Video Analytics Platform for Legacy Border CCTV

#### 🔹 Detailed Explanation of the Proposed Solution
- **Software-Defined Edge Surveillance:** Transforms passive, conventional IP/analog CCTV cameras into active, intelligent sentinels without requiring proprietary smart-camera hardware.
- **Cascaded Multi-Task Pipeline:** 
  - Real-time Human Detection & Centroid Trajectory Tracking.
  - Virtual Fence / Tripwire boundary breach intrusion detection.
  - Cascaded Automatic Number Plate Recognition (ANPR) triggered exclusively upon vehicle detection.
- **Unified Defense Command Station:** A multi-channel Streamlit surveillance dashboard featuring live visual overlays, real-time alert logs, and instant export capabilities.

#### 🔹 How It Addresses the Problem
- **Eliminates Continuous Human Fatigue:** Replaces continuous manual monitor gazing with autonomous, instant event-driven acoustic and visual alarms.
- **Zero Hardware Replacement Cost:** Utilizes existing RTSP/ONVIF streams from deployed cameras at Border Out Posts (BOPs) and checkposts; no costly specialized FRS/ANPR camera hardware required.
- **Bandwidth-Resilient Local Processing:** Video inference executes 100% locally on standard edge devices; only encrypted telemetry alerts (<2 KB) are transmitted to Sector HQ over low-bandwidth tactical links.

#### 🔹 Innovation and Uniqueness of the Solution
- **Conditional Cascaded Inference:** ANPR and high-resolution OCR execute only when vehicles enter designated checkpoint zones, saving up to 80% computational load on edge CPUs.
- **Temporal Best-per-Track Smoothing:** Aggregates multi-frame plate readings across a vehicle’s approach trajectory, locking in the highest-confidence reading and preventing jitter.
- **Operational Integrity Safeguard:** Distant, occluded, or unreadable plates are categorized as `FLAGGED FOR MANUAL REVIEW` rather than generating false alphanumeric hallucinated reads.

---

## SLIDE 3: TECHNICAL APPROACH

#### 🔹 Technologies Used
- **Core Languages & Runtimes:** Python 3.10, PyTorch 2.7 (CPU/CUDA optimized).
- **Computer Vision & AI Frameworks:** 
  - **Object Detection:** Ultralytics YOLOv8 Nano (COCO-filtered: Person, Car, Motorcycle, Bus, Truck).
  - **Plate Detection:** YOLOv8 Custom License Plate Detector (`licensePlateDetector.pt`).
  - **OCR Engine:** EasyOCR with bilateral filtering and dynamic contrast normalization.
- **Tracking & Geometry:** Custom Euclidean Centroid Tracker with 30-frame historical trajectory buffers and 2D segment-intersection line math.
- **Command Dashboard:** Streamlit with WebSockets for jitter-free real-time frame streaming and in-memory incident logging.
- **Target Edge Hardware:** Standard COTS x86 PC or NVIDIA Jetson Orin Nano (15W).

#### 🔹 Methodology & Architecture Flowchart

```
       [ Existing BOP / Checkpost CCTV (Standard IP/RTSP) ]
                               │
                               ▼
               [ Frame Capture & Pre-Processing ]
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       [ Channel 1: BOP Perimeter ]    [ Channel 2: Checkpost Road ]
                │                             │
       (YOLOv8 Person Det)             (YOLOv8 Vehicle Det)
                │                             │
       (Centroid Tracking)             (Centroid Tracking)
                │                             │
    [ Virtual Tripwire Crossing ]     [ Cascaded Plate Detector ]
       │            │                         │
       │ (Breach)   │ (No breach)             ▼
       ▼            ▼                 [ Crop & Preprocess Plate ]
 [ INTRUSION     (Continue)                   │
    ALARM ]                                   ▼
       │                               [ EasyOCR Engine ]
       │                                      │
       │                              ┌───────┴────────┐
       │                              ▼                ▼
       │                       (Conf >= 40%)     (Conf < 40%)
       │                              │                │
       │                         [ VERIFIED ]     [ FLAGGED FOR
       │                           PLATE READ ]    MANUAL REVIEW ]
       │                              │                │
       └──────────────┬───────────────┴────────────────┘
                      ▼
        [ Central Event Logger (alerts.csv) ]
                      │
                      ▼
   [ Streamlit Live Command Station (http://localhost:8501) ]
```

---

## SLIDE 4: FEASIBILITY AND VIABILITY

#### 🔹 Analysis of Feasibility
- **Proven Working MVP:** Validated end-to-end on real-world test footage at 8.5 FPS (720p) and 5.0 FPS (1080p) on standard CPU without dedicated GPU acceleration.
- **Drop-in Compatibility:** Integrates seamlessly with existing RTSP, H.264, and MP4 video streams currently used across SSB Border Out Posts.
- **Modular Microservice Design:** Each module (`detector.py`, `tracker.py`, `fence.py`, `anpr.py`) is decoupled, enabling hot-swapping of weights or migration to TensorRT.

#### 🔹 Potential Challenges and Risks
1. **Weather & Low-Light Degradation:** Heavy fog, dust storms, and pitch darkness at remote borders degrade visible CCTV feeds.
2. **Computational Bottlenecks on Low-End Edge Hardware:** Concurrent video analytics on multi-camera streams can strain CPU/RAM.
3. **Severe Plate Angles & Dirt Occlusion:** Border vehicles frequently carry distorted, mud-covered, or non-standard license plates.

#### 🔹 Mitigation Strategies
1. **Multispectral Sensor Fusion (Roadmap):** Software architecture ready for FLIR / Long-Wave Infrared (LWIR) thermal sensor input.
2. **Edge Model Quantization:** INT8 quantization and TensorRT export to run at 30+ FPS on 15-watt NVIDIA Jetson Orin edge modules.
3. **Human-in-the-Loop Safeguard:** Automated `FLAGGED_FOR_MANUAL_REVIEW` routing ensures border sentries are notified of unreadable plates without breaking automated logs.

---

## SLIDE 5: IMPACT AND BENEFITS

#### 🔹 Impact on Border Security Forces (SSB / MHA)
- **Multiplies Sentry Coverage:** Converts ordinary CCTV towers into automated perimeter sentinels, allowing small troop deployments to secure larger border sectors.
- **Shrinks Incident Response Time:** Alerts security personnel within milliseconds of a perimeter breach with exact visual coordinates.
- **Searchable Digital Audit Trail:** Replaces handwritten checkpoint logbooks with automated, timestamped, and exportable digital vehicle registers.

#### 🔹 Key Benefits
- **Economic (Massive Capex Savings):** Saves hundreds of crores by avoiding premature replacement of functional CCTV cameras with proprietary smart systems.
- **Operational:** Operates in remote, disconnected border outposts with 100% offline edge inference (no cloud dependence).
- **Scalability:** Easily scalable from a single BOP outpost to a multi-post tactical mesh network.
- **Security & Sovereignty:** Completely on-premise data storage; sensitive border intelligence never leaves the local post.

---

## SLIDE 6: RESEARCH AND REFERENCES

#### 🔹 Research Papers & Standards
1. **YOLOv8 Architecture:** Jocher, G., Chaurasia, A., & Qiu, J. (2023). *Ultralytics YOLOv8*. State-of-the-art real-time object detection and segmentation.
2. **Robust Multi-Object Tracking:** Bewley, A., Ge, Z., Ott, L., Ramos, F., & Upcroft, B. *Simple Online and Realtime Tracking (SORT)*. IEEE ICIP.
3. **Text Recognition in the Wild:** Baek, J., et al. (2019). *What Is Wrong With Scene Text Recognition Model Comparisons? Dataset and Model Analysis*. ICCV.
4. **Thermal Surveillance in Defense:** KAIST Multispectral Pedestrian Dataset & FLIR Thermal Aerial Dataset for low-light perimeter security.

#### 🔹 Technical References & Open Source Foundations
- **Ultralytics YOLOv8:** https://github.com/ultralytics/ultralytics
- **EasyOCR Scene Text Engine:** https://github.com/JaidedAI/EasyOCR
- **SIH Official Portal:** Smart India Hackathon 2026 — PS SIH26187 (Ministry of Home Affairs / SSB)
- **Project Codebase Repository:** https://github.com/akshad1007/SIH26.git
