import argparse
import time
import cv2
from modules.detector import ObjectDetector


def test_video(video_path: str, max_frames: int = 75, preview_save_path: str = None):
    print(f"\n[INFO] Initializing test on: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[VIDEO INFO] Dimensions: {w}x{h} | FPS: {fps:.1f} | Total Frames: {total_video_frames}")

    detector = ObjectDetector(model_path="models/yolov8n.pt", device="cpu")

    frame_idx = 0
    t0 = time.time()
    human_count = 0
    vehicle_count = 0
    sample_annotated_frame = None

    while cap.isOpened() and frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        detections = detector.detect(frame, conf_threshold=0.35)

        for d in detections:
            if d["category"] == "human":
                human_count += 1
            elif d["category"] == "vehicle":
                vehicle_count += 1

        if frame_idx == min(30, max_frames):
            sample_annotated_frame = detector.draw_detections(frame, detections)

    elapsed = time.time() - t0
    cap.release()

    fps_achieved = frame_idx / max(elapsed, 0.001)
    print(f"[RESULTS] Processed {frame_idx} frames in {elapsed:.2f}s | Throughput: {fps_achieved:.1f} FPS")
    print(f"[COUNTS] Human Detections: {human_count} | Vehicle Detections: {vehicle_count}")

    if preview_save_path and sample_annotated_frame is not None:
        cv2.imwrite(preview_save_path, sample_annotated_frame)
        print(f"[PREVIEW] Saved annotated preview frame to: {preview_save_path}")

    return {
        "frames": frame_idx,
        "fps": fps_achieved,
        "humans": human_count,
        "vehicles": vehicle_count
    }


def main():
    parser = argparse.ArgumentParser(description="IBVAP Phase 1 Detection CLI Verification")
    parser.add_argument("--channel1", default="sample_videos/bop_perimeter.mp4", help="Channel 1 video path")
    parser.add_argument("--channel2", default="sample_videos/checkpost_traffic.mp4", help="Channel 2 video path")
    parser.add_argument("--frames", type=int, default=60, help="Frames to test per channel")
    args = parser.parse_args()

    print("=" * 65)
    print("  IBVAP PHASE 1 VERIFICATION: CORE DETECTION PIPELINE")
    print("=" * 65)

    res1 = test_video(args.channel1, max_frames=args.frames, preview_save_path="sample_videos/preview_channel1.jpg")
    res2 = test_video(args.channel2, max_frames=args.frames, preview_save_path="sample_videos/preview_channel2.jpg")

    print("\n" + "=" * 65)
    print("  PHASE 1 SUMMARY REPORT")
    print("=" * 65)
    if res1:
        print(f"Channel 1 (Perimeter): {res1['frames']} frames @ {res1['fps']:.1f} FPS | Humans: {res1['humans']}, Vehicles: {res1['vehicles']}")
    if res2:
        print(f"Channel 2 (Checkpost): {res2['frames']} frames @ {res2['fps']:.1f} FPS | Humans: {res2['humans']}, Vehicles: {res2['vehicles']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
