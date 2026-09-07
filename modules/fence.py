import cv2
import numpy as np


def ccw(A, B, C):
    """Checks if three points are listed in counter-clockwise order."""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def segments_intersect(p1, p2, p3, p4):
    """
    Returns True if segment (p1, p2) intersects segment (p3, p4).
    """
    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))


class VirtualFence:
    """
    Virtual Fence / Tripwire intrusion detector for Border Security Posts.
    Monitors object trajectories and raises alerts when unauthorized
    movement breaches the designated boundary line or restricted zone.
    """
    def __init__(self, line_coords: tuple = None, zone_name: str = "BOP Sector 4 Perimeter"):
        # Default line tuned for 1080p surveillance video (y=620 horizontal tripwire)
        if line_coords is None:
            self.p1 = (50, 620)
            self.p2 = (1870, 620)
        else:
            self.p1, self.p2 = line_coords

        self.zone_name = zone_name
        self.intruded_track_ids = set()   # Tracks that have breached the perimeter
        self.alert_history = []           # List of triggered alert events

    def check_intrusions(self, active_tracks: dict, timestamp: str = ""):
        """
        Evaluates active tracks for boundary crossing.
        Returns list of new alert events triggered in this frame.
        """
        new_alerts = []

        for track_id, data in active_tracks.items():
            # If already alerted for this track, skip re-alerting
            if track_id in self.intruded_track_ids:
                continue

            traj = data.get("trajectory", [])
            if len(traj) < 2:
                continue

            # Check if recent movement segment intersects the fence line
            prev_pt = traj[-2]
            curr_pt = traj[-1]

            if segments_intersect(prev_pt, curr_pt, self.p1, self.p2):
                self.intruded_track_ids.add(track_id)
                alert_event = {
                    "timestamp": timestamp,
                    "event_type": "INTRUSION_ALERT",
                    "track_id": track_id,
                    "category": data.get("category", "human"),
                    "class_name": data.get("class_name", "person"),
                    "confidence": data.get("conf", 0.0),
                    "zone": self.zone_name,
                    "location": f"({curr_pt[0]}, {curr_pt[1]})",
                    "status": "VERIFIED"
                }
                self.alert_history.append(alert_event)
                new_alerts.append(alert_event)

        return new_alerts

    def draw_fence(self, frame: np.ndarray, active_tracks: dict):
        """
        Draws the virtual fence boundary line and overlays intrusion warning markers.
        """
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # Draw Fence Line (Neon Red / Crimson)
        fence_color = (0, 0, 255)  # BGR Red
        cv2.line(annotated, self.p1, self.p2, fence_color, 3)

        # Fence Warning Badge
        badge_text = f"RESTRICTED BORDER VIRTUAL FENCE - {self.zone_name.upper()}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 2
        (tw, th), baseline = cv2.getTextSize(badge_text, font, font_scale, thickness)

        mid_x = int((self.p1[0] + self.p2[0]) / 2) - int(tw / 2)
        mid_y = int((self.p1[1] + self.p2[1]) / 2) - 10

        # Semi-transparent background for fence label
        cv2.rectangle(annotated, (mid_x - 6, mid_y - th - 6), (mid_x + tw + 6, mid_y + baseline), (0, 0, 180), -1)
        cv2.putText(annotated, badge_text, (mid_x, mid_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        # Draw Intrusion highlights on active breached tracks
        for track_id, data in active_tracks.items():
            traj = data.get("trajectory", [])
            # Draw trajectory trail
            if len(traj) >= 2:
                pts = np.array(traj, np.int32).reshape((-1, 1, 2))
                trail_color = (0, 0, 255) if track_id in self.intruded_track_ids else (0, 255, 255)
                cv2.polylines(annotated, [pts], False, trail_color, 2)

            # If track is an active intruder, highlight in bold Red
            if track_id in self.intruded_track_ids:
                x1, y1, x2, y2 = data["bbox"]
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)

                alert_tag = f"! INTRUSION ALERT #{track_id} !"
                cv2.rectangle(annotated, (x1, y1 - 22), (x1 + 220, y1), (0, 0, 255), -1)
                cv2.putText(annotated, alert_tag, (x1 + 4, y1 - 6), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        return annotated
