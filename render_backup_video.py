import cv2
import time
from modules.detector import ObjectDetector
from modules.tracker import CentroidTracker
from modules.anpr import CascadedANPR


def render_backup():
    print("[INFO] Rendering backup annotated run video (Hackathon Insurance)...")
    input_path = "sample_videos/checkpost_traffic.mp4"
    output_path = "sample_videos/backup_annotated_run.mp4"

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open {input_path}")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    detector = ObjectDetector("models/yolov8n.pt", "cpu")
    tracker = CentroidTracker(max_disappeared=20, max_distance=100.0)
    anpr = CascadedANPR("models/licensePlateDetector.pt", "cpu", throttle_frames=12)

    frame_idx = 0
    max_frames = 120

    t0 = time.time()
    while cap.isOpened() and frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        dets = detector.detect(frame, conf_threshold=0.35)
        tracks = tracker.update(dets)

        annotated = detector.draw_detections(frame, dets)

        for tid, data in tracks.items():
            if data["category"] == "vehicle":
                res = anpr.process_vehicle(frame, data["bbox"], track_id=tid, frame_idx=frame_idx)
                if res:
                    annotated = anpr.draw_anpr(annotated, res)

        # Draw Telemetry watermark badge
        cv2.putText(
            annotated,
            f"IBVAP LIVE SURVEILLANCE FEED - FRAME #{frame_idx}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )

        out.write(annotated)
        if frame_idx % 20 == 0:
            print(f"Rendered {frame_idx}/{max_frames} frames...")

    cap.release()
    out.release()
    elapsed = time.time() - t0
    print(f"[SUCCESS] Saved pre-recorded backup video to {output_path} in {elapsed:.2f}s")


if __name__ == "__main__":
    render_backup()
