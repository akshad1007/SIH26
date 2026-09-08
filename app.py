import os
import time
from datetime import datetime
import cv2
import pandas as pd
import streamlit as st

from modules.detector import ObjectDetector
from modules.tracker import CentroidTracker
from modules.fence import VirtualFence
from modules.anpr import CascadedANPR
from modules.logger import EventLogger
from modules.enhancer import LowLightEnhancer
from modules.watchlist import WatchlistDatabase

# Page Configuration
st.set_page_config(
    page_title="IBVAP — Border CCTV Video Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Military / Surveillance CSS Styling
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Top Header Bar */
    .header-box {
        background: linear-gradient(90deg, #161b22 0%, #1f2937 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .header-title {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #58a6ff;
        margin: 0;
    }
    .header-subtitle {
        font-size: 13px;
        color: #8b949e;
        margin: 4px 0 0 0;
    }
    .badge-live {
        background-color: #ef4444;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 1px;
        animation: pulse 2s infinite;
    }
    .badge-status {
        background-color: #238636;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Metric Containers */
    div[data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="metric-container"]:hover {
        border-color: #58a6ff;
    }

    /* Video Player Container */
    .video-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    }

    /* Roadmap Card */
    .roadmap-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .roadmap-title {
        font-size: 16px;
        font-weight: 700;
        color: #58a6ff;
        margin-bottom: 6px;
    }
    .roadmap-desc {
        font-size: 13px;
        color: #8b949e;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_models():
    """Initializes models once to eliminate reload lag."""
    detector = ObjectDetector(model_path="models/yolov8n.pt", device="cpu")
    anpr = CascadedANPR(
        plate_model_path="models/licensePlateDetector.pt",
        device="cpu",
        ocr_conf_threshold=0.40,
        throttle_frames=15,
        min_vehicle_height=50
    )
    enhancer = LowLightEnhancer(clip_limit=3.0)
    watchlist = WatchlistDatabase()
    return detector, anpr, enhancer, watchlist


detector, anpr, enhancer, watchlist = load_models()

# Persistent Session State Setup
if "logger" not in st.session_state:
    st.session_state.logger = EventLogger(csv_path="alerts.csv")

if "tracker" not in st.session_state:
    st.session_state.tracker = CentroidTracker(max_disappeared=20, max_distance=90.0)

if "active_channel" not in st.session_state:
    st.session_state.active_channel = "Channel 1"

logger = st.session_state.logger
tracker = st.session_state.tracker

# Sidebar Controls
st.sidebar.markdown("### 🛡️ IBVAP Command Station")
st.sidebar.caption("Ministry of Home Affairs — Sashastra Seema Bal")
st.sidebar.markdown("---")

channel_selection = st.sidebar.radio(
    "Surveillance Sector Feed",
    [
        "Channel 1: Sector A - BOP Perimeter (1080p Long-Range)",
        "Channel 2: Sector B - Pedestrian Crossing (vedio-sih26.mp4)",
        "Channel 3: Sector C - Checkpost Charlie (Vehicles & ANPR)",
        "Channel 4: Backup Pre-recorded Demo (Insurance Run)"
    ],
    index=1  # Default to Sector B (vedio-sih26.mp4) to showcase newly added human crossing feed!
)

# Detect Channel Switch and Reset Tracker
current_ch_key = channel_selection.split(":")[0].strip()
if st.session_state.active_channel != current_ch_key:
    st.session_state.active_channel = current_ch_key
    st.session_state.tracker = CentroidTracker(max_disappeared=20, max_distance=90.0)
    tracker = st.session_state.tracker

# Virtual Fence / Tripwire interactive calibration
is_perimeter_mode = "Channel 1" in channel_selection or "Channel 2" in channel_selection
tripwire_y = None

if is_perimeter_mode:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 Virtual Fence Calibration")
    is_sector_b = "Channel 2" in channel_selection
    tripwire_y = st.sidebar.slider(
        "Tripwire Boundary Line (Y-position)",
        min_value=50 if is_sector_b else 100,
        max_value=450 if is_sector_b else 1000,
        value=280 if is_sector_b else 600,
        step=10,
        help="Calibrate the intrusion tripwire line height for this sector"
    )

st.sidebar.markdown("---")
st.sidebar.subheader("🌟 Image Enhancement (Step 2)")
enable_clahe = st.sidebar.checkbox(
    "🌙 Low-Light / Fog CLAHE",
    value=False,
    help="Restores visibility in pitch-black or foggy border feeds using OpenCV CLAHE"
)
clahe_limit = 3.0
if enable_clahe:
    clahe_limit = st.sidebar.slider("Contrast Clip Limit", 1.0, 6.0, 3.0, 0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Watchlist Verification (Steps 7 & 8)")
enable_watchlist = st.sidebar.checkbox(
    "🔍 Local Watchlist Search",
    value=True,
    help="Cross-references breach events against the Authorized SSB Patrol & Vehicle Roster"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Stream Telemetry")
conf_thresh = st.sidebar.slider("Detection Sensitivity (Confidence)", 0.25, 0.70, 0.35, 0.05)
frame_stride = st.sidebar.slider("Frame Processing Stride", 1, 3, 1, 1, help="Higher stride yields smoother playback on CPU")

run_stream = st.sidebar.checkbox("▶️ Run Surveillance Feed", value=True)

if st.sidebar.button("🔄 Clear Event Logs & Reset"):
    logger.clear()
    st.session_state.tracker = CentroidTracker(max_disappeared=20, max_distance=90.0)
    st.sidebar.success("Logs and active tracks cleared.")
    st.rerun()

# Top Header Layout
st.markdown("""
<div class="header-box">
    <div>
        <h1 class="header-title">🛡️ INTELLIGENT BORDER VIDEO ANALYTICS PLATFORM (IBVAP)</h1>
        <p class="header-subtitle">SSB Police II Division • Edge CCTV Computer Vision Network • Problem Statement: SIH26187</p>
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
        <span class="badge-status">ONLINE • CPU MODE</span>
        <span class="badge-live">● LIVE FEED</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top KPI Metric Cards (Using dynamic placeholders to eliminate visual jitter)
c1, c2, c3, c4 = st.columns(4)
ph_metric1 = c1.empty()
ph_metric2 = c2.empty()
ph_metric3 = c3.empty()
ph_metric4 = c4.empty()

# Initial KPI values
initial_stats = logger.get_stats()
init_df = logger.get_dataframe()
auth_count = len(init_df[init_df["event_type"].str.contains("AUTHORIZED", na=False)]) if not init_df.empty else 0

ph_metric1.metric("🚨 Intrusion Alerts", initial_stats["intrusions"])
ph_metric2.metric("✅ Authorized Patrols", auth_count)
ph_metric3.metric("🚗 Vehicles Tracked", initial_stats["vehicles_detected"])
ph_metric4.metric("🪪 Verified Plates Read", initial_stats["plates_read"])

# Tab Layout: Live Post vs Historical Analytics vs SSB Roadmap
tab_live, tab_logs, tab_roadmap = st.tabs([
    "📺 Live Surveillance Post",
    "📊 Event Log & Analytics",
    "🚀 SSB Operational Roadmap (Future Work)"
])

# -------------------------------------------------------------
# TAB 1: LIVE SURVEILLANCE POST
# -------------------------------------------------------------
with tab_live:
    col_player, col_feed = st.columns([3, 2])

    with col_player:
        st.markdown(f"**📹 Sector Video Stream:** `{channel_selection.split(':')[1].strip()}`")
        ph_banner = st.empty()
        ph_video = st.empty()

    with col_feed:
        st.markdown("**🚨 Real-Time Security Incident Stream**")
        ph_alerts = st.empty()

    # Route video path and channel parameters
    if "Channel 1" in channel_selection:
        video_path = "sample_videos/bop_perimeter.mp4"
        y_pos = tripwire_y if tripwire_y is not None else 600
        fence = VirtualFence(line_coords=((50, y_pos), (1870, y_pos)), zone_name="Sector A Perimeter")
        is_perimeter_mode = True
    elif "Channel 2" in channel_selection:
        # Preferred: root vedio-sih26.mp4 or sample_videos copy
        if os.path.exists("vedio-sih26.mp4"):
            video_path = "vedio-sih26.mp4"
        elif os.path.exists("sample_videos/pedestrian_crossing.mp4"):
            video_path = "sample_videos/pedestrian_crossing.mp4"
        else:
            video_path = "sample_videos/vedio-sih26.mp4"
        y_pos = tripwire_y if tripwire_y is not None else 280
        fence = VirtualFence(line_coords=((20, y_pos), (828, y_pos)), zone_name="Sector B Tripwire")
        is_perimeter_mode = True
    elif "Channel 3" in channel_selection:
        video_path = "sample_videos/checkpost_traffic.mp4"
        fence = None
        is_perimeter_mode = False
    else:
        video_path = "sample_videos/backup_annotated_run.mp4"
        if not os.path.exists(video_path):
            video_path = "sample_videos/checkpost_traffic.mp4"
        fence = None
        is_perimeter_mode = False

    # Execute Live Stream Loop
    if run_stream and os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        frame_idx = 0

        while cap.isOpened() and run_stream:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame_idx += 1
            if frame_idx % frame_stride != 0:
                continue

            now_str = datetime.now().strftime("%H:%M:%S")

            # Check if playing pre-rendered backup video
            if "Channel 4" in channel_selection and os.path.exists("sample_videos/backup_annotated_run.mp4"):
                annotated_frame = frame
                time.sleep(0.02)
            else:
                # Step 2: Image Enhancement (Zero-DCE / CLAHE)
                if enable_clahe:
                    frame = enhancer.enhance(frame, clip_limit=clahe_limit)

                # Step 3: Object Detection & Tracking (YOLOv8 + CentroidTracker)
                detections = detector.detect(frame, conf_threshold=conf_thresh)
                active_tracks = tracker.update(detections)

                annotated_frame = detector.draw_detections(frame, detections)

                # Step 4, 5, 7 & 8: Channel Specific Boundary Check & Identity Decision
                if is_perimeter_mode and fence is not None:
                    new_intrusions = fence.check_intrusions(
                        active_tracks,
                        timestamp=now_str,
                        watchlist=watchlist if enable_watchlist else None
                    )
                    for alert in new_intrusions:
                        logger.log_event(
                            event_type=alert["event_type"],
                            track_id=alert["track_id"],
                            category=alert["category"],
                            class_name=alert["class_name"],
                            confidence=alert["confidence"],
                            status=alert["status"],
                            details=f"{alert.get('identity', 'UNKNOWN')} | {alert.get('direction', 'CROSSING')} at {alert['location']}",
                            timestamp=alert["timestamp"]
                        )
                    annotated_frame = fence.draw_fence(
                        annotated_frame,
                        active_tracks,
                        watchlist=watchlist if enable_watchlist else None
                    )

                else:
                    # Vehicle Checkpoint & ANPR (Step 6B)
                    for track_id, data in active_tracks.items():
                        if data.get("category") == "vehicle":
                            anpr_res = anpr.process_vehicle(frame, data["bbox"], track_id=track_id, frame_idx=frame_idx)
                            if anpr_res:
                                is_auth_veh, veh_rec = watchlist.verify_vehicle(anpr_res["plate_text"]) if enable_watchlist else (False, None)
                                veh_status = "AUTHORIZED_PATROL_VEHICLE" if is_auth_veh else anpr_res["status"]
                                veh_details = f"{veh_rec['unit']} ({veh_rec['vehicle_type']})" if is_auth_veh else f"Plate Conf: {anpr_res['plate_conf']*100:.0f}%"

                                annotated_frame = anpr.draw_anpr(annotated_frame, anpr_res)
                                logger.log_event(
                                    event_type="AUTHORIZED_VEHICLE" if is_auth_veh else "VEHICLE_ANPR",
                                    track_id=track_id,
                                    category="vehicle",
                                    class_name=data.get("class_name", "car"),
                                    confidence=data.get("conf", 0.0),
                                    plate_text=anpr_res["plate_text"],
                                    ocr_confidence=anpr_res["ocr_conf"],
                                    status=veh_status,
                                    details=veh_details,
                                    timestamp=now_str
                                )

            # Render to Streamlit Display
            rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            ph_video.image(rgb_frame, use_column_width=True)

            # Update Metrics cleanly in placeholders
            stats = logger.get_stats()
            df = logger.get_dataframe()
            auth_count = len(df[df["event_type"].str.contains("AUTHORIZED", na=False)]) if not df.empty else 0

            ph_metric1.metric("🚨 Intrusion Alerts", stats["intrusions"])
            ph_metric2.metric("✅ Authorized Patrols", auth_count)
            ph_metric3.metric("🚗 Vehicles Tracked", stats["vehicles_detected"])
            ph_metric4.metric("🪪 Verified Plates Read", stats["plates_read"])

            # Update Dynamic Alert Banner & Recent Incident Feed
            if not df.empty:
                last_event = df.iloc[-1]
                if last_event["event_type"] == "AUTHORIZED_PATROL" or last_event["event_type"] == "AUTHORIZED_VEHICLE":
                    ph_banner.success(f"✅ MATCH FOUND (Authorized Patrol): {last_event['details']} • False Alarm Suppressed")
                elif last_event["event_type"] == "INTRUSION_ALERT":
                    ph_banner.error(f"🚨 NO MATCH (Unknown Intruder): Track #{last_event['track_id']} Breached Perimeter! • Security Dispatched")

                recent_df = df.tail(7)[["timestamp", "event_type", "track_id", "status", "details"]]
                ph_alerts.dataframe(
                    recent_df,
                    use_container_width=True,
                    hide_index=True
                )

        cap.release()

    elif not os.path.exists(video_path):
        st.error(f"Target video feed not located: {video_path}")
    else:
        st.info("Surveillance feed paused. Check 'Run Surveillance Feed' in the sidebar to resume.")

# -------------------------------------------------------------
# TAB 2: HISTORICAL LOGS & AUDIT TRAIL
# -------------------------------------------------------------
with tab_logs:
    st.subheader("📋 Comprehensive Surveillance Incident Register")
    full_df = logger.get_dataframe()

    if not full_df.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            event_filter = st.multiselect(
                "Filter by Event Type",
                options=full_df["event_type"].unique().tolist(),
                default=full_df["event_type"].unique().tolist()
            )
        with col_f2:
            status_filter = st.multiselect(
                "Filter by Verification Status",
                options=full_df["status"].unique().tolist(),
                default=full_df["status"].unique().tolist()
            )

        filtered_df = full_df[
            (full_df["event_type"].isin(event_filter)) &
            (full_df["status"].isin(status_filter))
        ]

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Exported Incident CSV",
            data=csv_bytes,
            file_name=f"ssb_ibvap_incident_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No incident records currently logged in this session.")

    # Step 7: Watchlist Database Viewer
    st.markdown("---")
    with st.expander("🗂️ Step 7: Local Offline Watchlist Database (FAISS / SQLite Architecture)", expanded=True):
        st.caption("Sub-millisecond local offline matching for authorized border personnel and official patrol vehicles.")
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown("##### 👮 Authorized Border Patrol Roster (ArcFace / Face Vector)")
            st.dataframe(watchlist.get_personnel_dataframe(), use_container_width=True, hide_index=True)
        with col_w2:
            st.markdown("##### 🚙 Authorized Patrol & Logistics Vehicles (ANPR Plates)")
            st.dataframe(watchlist.get_vehicles_dataframe(), use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# TAB 3: SSB OPERATIONAL ROADMAP (PRESENTATION SLIDES)
# -------------------------------------------------------------
with tab_roadmap:
    st.subheader("🚀 Operational Architecture & Future Scaling Roadmap")
    st.caption("Strategic expansion roadmap for border deployment as specified in Problem Statement SIH26187.")

    st.markdown("""
    <div class="roadmap-card">
        <div class="roadmap-title">1. Thermal & Low-Light / Night-Vision Integration (NIR / LWIR)</div>
        <div class="roadmap-desc">
            <b>SSB Requirement:</b> Surveillance across unlit riverine borders and dense foliage at night.<br>
            <b>Architecture:</b> Integration of FLIR / Long-Wave Infrared thermal video feeds. YOLOv8 fine-tuned on multispectral (FLIR/KAIST) datasets allows zero-light human heat-signature detection without requiring active illuminators.
        </div>
    </div>
    
    <div class="roadmap-card">
        <div class="roadmap-title">2. Edge Computing Architecture (NVIDIA Jetson AGX / Orin Nano)</div>
        <div class="roadmap-desc">
            <b>SSB Requirement:</b> High reliability in remote Border Out Posts (BOPs) with limited or intermittent satellite backhaul.<br>
            <b>Architecture:</b> TensorRT-compiled INT8 models running locally on low-power ruggedized edge boxes (15W). Video processing occurs 100% on-premise; only lightweight encrypted telemetry alerts (< 2 KB) are transmitted to Sector HQ.
        </div>
    </div>
    
    <div class="roadmap-card">
        <div class="roadmap-title">3. Facial Recognition System (FRS) & Watchlist Matching</div>
        <div class="roadmap-desc">
            <b>SSB Requirement:</b> Intercepting known suspects, cross-border smugglers, and persons of interest.<br>
            <b>Architecture:</b> Cascaded face detector (RetinaFace/YOLOv8-Face) triggered upon pedestrian boundary approach. Feature embeddings extracted using lightweight ArcFace (MobileFaceNet) matched against local encrypted SQLite/Milvus vector index in < 15ms.
        </div>
    </div>
    
    <div class="roadmap-card">
        <div class="roadmap-title">4. Multi-Camera Spatial Fusion & Cross-Camera Re-Identification (Re-ID)</div>
        <div class="roadmap-desc">
            <b>SSB Requirement:</b> Tracking a suspect traversing between multiple perimeter CCTV towers and road checkpoints.<br>
            <b>Architecture:</b> Deep visual appearance embeddings (OSNet) associated across overlapping and non-overlapping camera fields of view to construct a unified 3D spatial track trajectory on an interactive map.
        </div>
    </div>
    """, unsafe_allow_html=True)
