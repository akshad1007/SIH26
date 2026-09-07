import cv2
import time
from datetime import datetime
from modules.detector import ObjectDetector
from modules.tracker import CentroidTracker
from modules.fence import VirtualFence
from modules.logger import EventLogger


def run_phase2_verification():
    print("=" * 65)
    print("  IBVAP PHASE 2 VERIFICATION: TRACKING + VIRTUAL FENCE INTRUSION")
    print("=" * 65)

    video_path = "sample_videos/bop_perimeter.mp4"
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        return

    # In bop_perimeter.mp4 (1080p), people move across the frame vertically/diagonally.
    # We place a tripwire fence line at y=600 across the corridor.
    fence_line = ((100, 600), (1820, 600))

    detector = ObjectDetector(model_path="models/yolov8n.pt", device="cpu")
    tracker = CentroidTracker(max_disappeared=20, max_distance=85.0)
    fence = VirtualFence(line_coords=fence_line, zone_name="BOP Sector 4 Tripwire")
    logger = EventLogger(csv_path="sample_videos/alerts_phase2.csv")
    logger.clear()

    frame_idx = 0
    max_frames = 120
    saved_alert_frame = None

    t0 = time.time()
    while cap.isOpened() and frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Detection
        detections = detector.detect(frame, conf_threshold=0.35)

        # 2. Tracking
        active_tracks = tracker.update(detections)

        # 3. Virtual Fence Intrusion Check
        new_intrusions = fence.check_intrusions(active_tracks, timestamp=now_str)

        # 4. Logging
        for alert in new_intrusions:
            logger.log_event(
                event_type=alert["event_type"],
                track_id=alert["track_id"],
                category=alert["category"],
                class_name=alert["class_name"],
                confidence=alert["confidence"],
                status=alert["status"],
                details=f"Crossed {alert['zone']} at {alert['location']}",
                timestamp=alert["timestamp"]
            )
            print(f"[ALARM] {now_str} | INTRUSION DETECTED! Track ID #{alert['track_id']} ({alert['class_name'].upper()}) Conf: {alert['confidence']*100:.1f}%")

        # 5. Save a preview frame when intrusions are detected
        if len(fence.intruded_track_ids) > 0 and saved_alert_frame is None and frame_idx > 40:
            # Annotate detections and fence
            annotated = detector.draw_detections(frame, detections)
            annotated = fence.draw_fence(annotated, active_tracks)
            saved_alert_frame = annotated

    elapsed = time.time() - t0
    cap.release()

    fps = frame_idx / max(elapsed, 0.001)
    stats = logger.get_stats()

    print("\n" + "=" * 65)
    print("  PHASE 2 SUMMARY & KPI METRICS")
    print("=" * 65)
    print(f"Processed Frames:       {frame_idx} in {elapsed:.2f}s ({fps:.1f} FPS)")
    print(f"Total Intrusions Logged:{stats['intrusions']}")
    print(f"Intruder Track IDs:     {sorted(list(fence.intruded_track_ids))}")
    print(f"Alerts Table Path:      sample_videos/alerts_phase2.csv")

    if saved_alert_frame is not None:
        preview_path = "sample_videos/preview_phase2_intrusion.jpg"
        cv2.imwrite(preview_path, saved_alert_frame)
        print(f"Annotated Preview Saved:{preview_path}")

    # Display logged CSV rows
    df = logger.get_dataframe()
    print("\n[LOGGED ALERTS TABLE PREVIEW]")
    print(df[["timestamp", "event_type", "track_id", "category", "confidence", "status", "details"]].to_string(index=False))
    print("=" * 65)


if __name__ == "__main__":
    run_phase2_verification()
