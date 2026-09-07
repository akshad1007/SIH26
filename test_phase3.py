import cv2
import time
from datetime import datetime
from modules.detector import ObjectDetector
from modules.tracker import CentroidTracker
from modules.anpr import CascadedANPR
from modules.logger import EventLogger


def run_phase3_verification():
    print("=" * 65)
    print("  IBVAP PHASE 3 & 3.5 VERIFICATION: CASCADED ANPR & THROUGHPUT")
    print("=" * 65)

    video_path = "sample_videos/checkpost_traffic.mp4"
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        return

    detector = ObjectDetector(model_path="models/yolov8n.pt", device="cpu")
    tracker = CentroidTracker(max_disappeared=20, max_distance=100.0)
    anpr = CascadedANPR(
        plate_model_path="models/licensePlateDetector.pt",
        device="cpu",
        ocr_conf_threshold=0.45,
        throttle_frames=6
    )
    logger = EventLogger(csv_path="sample_videos/alerts_phase3.csv")
    logger.clear()

    frame_idx = 0
    max_frames = 90
    saved_preview_frame = None

    t0 = time.time()
    vehicle_ids_seen = set()
    plates_found = 0

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

        # 3. Cascaded ANPR (Only for vehicle category)
        frame_anpr_results = []
        for track_id, data in active_tracks.items():
            if data.get("category") == "vehicle":
                vehicle_ids_seen.add(track_id)
                veh_bbox = data["bbox"]

                # Process plate
                anpr_res = anpr.process_vehicle(frame, veh_bbox, track_id=track_id, frame_idx=frame_idx)
                if anpr_res:
                    frame_anpr_results.append(anpr_res)
                    plates_found += 1

                    # Log vehicle ANPR event if not already logged or if updated
                    logger.log_event(
                        event_type="VEHICLE_ANPR",
                        track_id=track_id,
                        category="vehicle",
                        class_name=data.get("class_name", "car"),
                        confidence=data.get("conf", 0.0),
                        plate_text=anpr_res["plate_text"],
                        ocr_confidence=anpr_res["ocr_conf"],
                        status=anpr_res["status"],
                        details=f"Plate Conf: {anpr_res['plate_conf']*100:.1f}%, Status: {anpr_res['status']}",
                        timestamp=now_str
                    )

        # Save an annotated preview frame when plate detection occurs
        if frame_anpr_results and saved_preview_frame is None and frame_idx > 20:
            annotated = detector.draw_detections(frame, detections)
            for res in frame_anpr_results:
                annotated = anpr.draw_anpr(annotated, res)
            saved_preview_frame = annotated

    elapsed = time.time() - t0
    cap.release()

    combined_fps = frame_idx / max(elapsed, 0.001)
    stats = logger.get_stats()

    print("\n" + "=" * 65)
    print("  PHASE 3 & 3.5 SUMMARY & KPI METRICS")
    print("=" * 65)
    print(f"Total Processed Frames:     {frame_idx} in {elapsed:.2f}s")
    print(f"Combined Pipeline FPS (CPU):{combined_fps:.1f} FPS")
    print(f"Unique Vehicles Tracked:    {len(vehicle_ids_seen)}")
    print(f"Total ANPR Events Logged:   {stats['total_alerts']}")
    print(f"Verified High-Conf Plates:  {stats['plates_read']}")
    print(f"Flagged for Manual Review:  {stats['flagged_manual_review']}")
    print(f"Alerts Table Output:        sample_videos/alerts_phase3.csv")

    if saved_preview_frame is not None:
        preview_path = "sample_videos/preview_phase3_anpr.jpg"
        cv2.imwrite(preview_path, saved_preview_frame)
        print(f"Annotated Preview Saved:    {preview_path}")

    df = logger.get_dataframe()
    if not df.empty:
        print("\n[LOGGED ANPR EVENTS PREVIEW]")
        print(df[["timestamp", "track_id", "class_name", "plate_text", "ocr_confidence", "status"]].tail(10).to_string(index=False))
    print("=" * 65)


if __name__ == "__main__":
    run_phase3_verification()
