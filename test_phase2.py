import argparse
import os
import time
import cv2
from datetime import datetime
from modules.detector import ObjectDetector
from modules.tracker import CentroidTracker
from modules.fence import VirtualFence
from modules.logger import EventLogger


def verify_video(video_path: str, zone_name: str = "Tripwire Sector", tripwire_y: int = None,
                 csv_path: str = "sample_videos/alerts_phase2.csv",
                 preview_path: str = "sample_videos/preview_phase2_intrusion.jpg",
                 max_frames: int = 150, detector: ObjectDetector = None):
    print("=" * 65)
    print(f"  VERIFICATION: {zone_name.upper()}")
    print(f"  Source Video: {video_path}")
    print("=" * 65)

    if not os.path.exists(video_path):
        print(f"[ERROR] Video file not found: {video_path}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        return None

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_val = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[METADATA] Resolution: {w}x{h} | FPS: {fps_val:.1f} | Total Frames: {total_frames}")

    # Determine optimal tripwire line based on resolution
    if tripwire_y is None:
        tripwire_y = int(h * 0.58)  # ~280 for 478p, ~620 for 1080p

    fence_line = ((int(w * 0.03), tripwire_y), (int(w * 0.97), tripwire_y))
    print(f"[FENCE CONFIG] Tripwire Line Y: {tripwire_y} | Line: {fence_line[0]} -> {fence_line[1]}")

    if detector is None:
        detector = ObjectDetector(model_path="models/yolov8n.pt", device="cpu")
    tracker = CentroidTracker(max_disappeared=20, max_distance=90.0)
    fence = VirtualFence(line_coords=fence_line, zone_name=zone_name)
    logger = EventLogger(csv_path=csv_path)
    logger.clear()

    frame_idx = 0
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
            direction = alert.get("direction", "CROSSING")
            logger.log_event(
                event_type=alert["event_type"],
                track_id=alert["track_id"],
                category=alert["category"],
                class_name=alert["class_name"],
                confidence=alert["confidence"],
                status=alert["status"],
                details=f"Crossed {alert['zone']} ({direction}) at {alert['location']}",
                timestamp=alert["timestamp"]
            )
            print(f"[ALARM] {now_str} | INTRUSION #{alert['track_id']} ({alert['class_name'].upper()}) "
                  f"Dir: {direction} | Conf: {alert['confidence']*100:.1f}%")

        # 5. Save a preview frame when intrusions are detected
        if len(fence.intruded_track_ids) >= 1 and saved_alert_frame is None and frame_idx > 30:
            annotated = detector.draw_detections(frame, detections)
            annotated = fence.draw_fence(annotated, active_tracks)
            saved_alert_frame = annotated

    elapsed = time.time() - t0
    cap.release()

    fps_achieved = frame_idx / max(elapsed, 0.001)
    stats = logger.get_stats()

    print("\n" + "-" * 65)
    print(f"Processed:              {frame_idx} frames in {elapsed:.2f}s ({fps_achieved:.1f} FPS)")
    print(f"Total Intrusions:       {stats['intrusions']}")
    print(f"Intruder Track IDs:     {sorted(list(fence.intruded_track_ids))}")
    print(f"Alerts Table Path:      {csv_path}")

    if saved_alert_frame is not None:
        cv2.imwrite(preview_path, saved_alert_frame)
        print(f"Annotated Preview Saved:{preview_path}")

    # Display logged CSV rows
    df = logger.get_dataframe()
    if not df.empty:
        print("\n[LOGGED ALERTS PREVIEW]")
        print(df[["timestamp", "event_type", "track_id", "category", "confidence", "status", "details"]].to_string(index=False))
    print("=" * 65 + "\n")

    return {
        "video": video_path,
        "frames": frame_idx,
        "fps": fps_achieved,
        "intrusions": stats["intrusions"],
        "intruders": sorted(list(fence.intruded_track_ids))
    }


def main():
    parser = argparse.ArgumentParser(description="IBVAP Phase 2: Human Tracking & Virtual Fence Line-Crossing Verification")
    parser.add_argument("--video", default="vedio-sih26.mp4", help="Path to video file")
    parser.add_argument("--frames", type=int, default=160, help="Frames to test")
    parser.add_argument("--y", type=int, default=None, help="Tripwire Y-coordinate")
    parser.add_argument("--all", action="store_true", help="Run verification on both Sector A (bop_perimeter) and Sector B (vedio-sih26)")
    args = parser.parse_args()

    shared_detector = ObjectDetector(model_path="models/yolov8n.pt", device="cpu")

    if args.all:
        print("\n" + "#" * 65)
        print("  RUNNING COMPLETE MULTI-SECTOR INTRUSION VERIFICATION")
        print("#" * 65 + "\n")

        # Sector B: vedio-sih26.mp4
        sih_video = "vedio-sih26.mp4" if os.path.exists("vedio-sih26.mp4") else "sample_videos/vedio-sih26.mp4"
        res_b = verify_video(
            video_path=sih_video,
            zone_name="Sector B Pedestrian Tripwire",
            tripwire_y=280,
            csv_path="sample_videos/alerts_sih26.csv",
            preview_path="sample_videos/preview_sih26_intrusion.jpg",
            max_frames=args.frames,
            detector=shared_detector
        )

        # Sector A: bop_perimeter.mp4
        res_a = verify_video(
            video_path="sample_videos/bop_perimeter.mp4",
            zone_name="Sector A BOP Perimeter",
            tripwire_y=600,
            csv_path="sample_videos/alerts_phase2.csv",
            preview_path="sample_videos/preview_phase2_intrusion.jpg",
            max_frames=args.frames,
            detector=shared_detector
        )

        print("\n" + "=" * 65)
        print("  COMPARATIVE MULTI-SECTOR VERIFICATION SUMMARY")
        print("=" * 65)
        if res_b:
            print(f"Sector B (vedio-sih26):  {res_b['intrusions']} intrusions | Tracks: {res_b['intruders']} | {res_b['fps']:.1f} FPS")
        if res_a:
            print(f"Sector A (bop_perimeter): {res_a['intrusions']} intrusions | Tracks: {res_a['intruders']} | {res_a['fps']:.1f} FPS")
        print("=" * 65)
    else:
        zone = "Sector B Pedestrian Tripwire" if "sih26" in args.video else "Sector A BOP Perimeter"
        csv_out = "sample_videos/alerts_sih26.csv" if "sih26" in args.video else "sample_videos/alerts_phase2.csv"
        prev_out = "sample_videos/preview_sih26_intrusion.jpg" if "sih26" in args.video else "sample_videos/preview_phase2_intrusion.jpg"

        verify_video(
            video_path=args.video,
            zone_name=zone,
            tripwire_y=args.y,
            csv_path=csv_out,
            preview_path=prev_out,
            max_frames=args.frames,
            detector=shared_detector
        )


if __name__ == "__main__":
    main()

