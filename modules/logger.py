import os
import pandas as pd
from datetime import datetime


class EventLogger:
    """
    In-memory Alert & Event Logger for Border Surveillance operations.
    Maintains clean tabular logs of intrusions, vehicle movements, and ANPR reads.
    Exports to CSV without external database dependencies.
    """
    def __init__(self, csv_path: str = "alerts.csv"):
        self.csv_path = csv_path
        self.events = []
        self.columns = [
            "timestamp",
            "event_type",
            "track_id",
            "category",
            "class_name",
            "confidence",
            "plate_text",
            "ocr_confidence",
            "status",
            "details"
        ]

    def log_event(
        self,
        event_type: str,
        track_id: int,
        category: str = "human",
        class_name: str = "person",
        confidence: float = 0.0,
        plate_text: str = "-",
        ocr_confidence: float = 0.0,
        status: str = "VERIFIED",
        details: str = "",
        timestamp: str = None
    ):
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "track_id": track_id,
            "category": category,
            "class_name": class_name,
            "confidence": round(float(confidence), 3),
            "plate_text": plate_text,
            "ocr_confidence": round(float(ocr_confidence), 3),
            "status": status,
            "details": details
        }
        self.events.append(event)
        self._append_to_csv(event)
        return event

    def _append_to_csv(self, event: dict):
        try:
            df = pd.DataFrame([event], columns=self.columns)
            file_exists = os.path.exists(self.csv_path) and os.path.getsize(self.csv_path) > 0
            df.to_csv(self.csv_path, mode="a", header=not file_exists, index=False)
        except Exception as e:
            print(f"[LOGGER WARNING] Could not write to CSV: {e}")

    def get_dataframe(self) -> pd.DataFrame:
        if not self.events:
            return pd.DataFrame(columns=self.columns)
        return pd.DataFrame(self.events, columns=self.columns)

    def get_stats(self) -> dict:
        total = len(self.events)
        intrusions = sum(1 for e in self.events if e["event_type"] == "INTRUSION_ALERT")
        vehicles = sum(1 for e in self.events if e["category"] == "vehicle")
        plates_read = sum(1 for e in self.events if e["plate_text"] != "-" and e["status"] == "VERIFIED")
        flagged_reviews = sum(1 for e in self.events if e["status"] == "FLAGGED_FOR_MANUAL_REVIEW")

        return {
            "total_alerts": total,
            "intrusions": intrusions,
            "vehicles_detected": vehicles,
            "plates_read": plates_read,
            "flagged_manual_review": flagged_reviews
        }

    def clear(self):
        self.events = []
        if os.path.exists(self.csv_path):
            try:
                os.remove(self.csv_path)
            except Exception:
                pass
