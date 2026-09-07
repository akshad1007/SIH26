import math
from collections import OrderedDict
import numpy as np


class CentroidTracker:
    """
    Lightweight Centroid Tracker tailored for surveillance feeds.
    Associates object centroids frame-to-frame using Euclidean distance,
    tracks history for trajectory/line-crossing analysis, and manages ID lifecycles.
    """
    def __init__(self, max_disappeared: int = 25, max_distance: float = 90.0):
        self.next_object_id = 1
        self.objects = OrderedDict()       # object_id -> current centroid (cx, cy)
        self.disappeared = OrderedDict()   # object_id -> count of consecutive missed frames
        self.trajectories = OrderedDict()  # object_id -> list of past centroids [(x, y), ...]
        self.metadata = OrderedDict()      # object_id -> dict(category, class_name, bbox, conf)
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid: tuple, meta: dict):
        obj_id = self.next_object_id
        self.objects[obj_id] = centroid
        self.disappeared[obj_id] = 0
        self.trajectories[obj_id] = [centroid]
        self.metadata[obj_id] = meta
        self.next_object_id += 1
        return obj_id

    def deregister(self, object_id: int):
        if object_id in self.objects:
            del self.objects[object_id]
        if object_id in self.disappeared:
            del self.disappeared[object_id]
        if object_id in self.trajectories:
            del self.trajectories[object_id]
        if object_id in self.metadata:
            del self.metadata[object_id]

    def update(self, detections: list):
        """
        Updates tracked objects with new frame detections.
        detections: list of dicts with 'centroid', 'bbox', 'conf', 'class_name', 'category'
        Returns: dict of active tracks: {obj_id: dict(centroid, bbox, category, trajectory, ...)}
        """
        # If no detections in this frame, mark all existing objects as disappeared
        if len(detections) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)
            return self.get_active_tracks()

        input_centroids = [d["centroid"] for d in detections]

        # If we currently have no tracked objects, register all detections
        if len(self.objects) == 0:
            for i, centroid in enumerate(input_centroids):
                self.register(centroid, detections[i])
            return self.get_active_tracks()

        # Compute Euclidean distance matrix between existing centroids and new centroids
        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())

        # Distance matrix of shape (num_existing, num_new)
        D = np.zeros((len(object_centroids), len(input_centroids)), dtype="float32")
        for i, (ox, oy) in enumerate(object_centroids):
            for j, (ix, iy) in enumerate(input_centroids):
                D[i, j] = math.hypot(ox - ix, oy - iy)

        # Match smallest distances first
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for (row, col) in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue

            # If distance exceeds threshold, do not associate
            if D[row, col] > self.max_distance:
                continue

            obj_id = object_ids[row]
            new_centroid = input_centroids[col]

            self.objects[obj_id] = new_centroid
            self.disappeared[obj_id] = 0
            self.trajectories[obj_id].append(new_centroid)
            if len(self.trajectories[obj_id]) > 30:
                self.trajectories[obj_id].pop(0)  # Keep last 30 points

            # Update latest metadata
            self.metadata[obj_id] = detections[col]

            used_rows.add(row)
            used_cols.add(col)

        # Any existing object not matched is marked as disappeared
        unused_rows = set(range(0, D.shape[0])).difference(used_rows)
        for row in unused_rows:
            obj_id = object_ids[row]
            self.disappeared[obj_id] += 1
            if self.disappeared[obj_id] > self.max_disappeared:
                self.deregister(obj_id)

        # Any new detection not matched is registered as a new object
        unused_cols = set(range(0, D.shape[1])).difference(used_cols)
        for col in unused_cols:
            self.register(input_centroids[col], detections[col])

        return self.get_active_tracks()

    def get_active_tracks(self):
        active = {}
        for obj_id, centroid in self.objects.items():
            meta = self.metadata.get(obj_id, {})
            active[obj_id] = {
                "track_id": obj_id,
                "centroid": centroid,
                "bbox": meta.get("bbox", (centroid[0]-10, centroid[1]-10, centroid[0]+10, centroid[1]+10)),
                "conf": meta.get("conf", 0.0),
                "class_name": meta.get("class_name", "unknown"),
                "category": meta.get("category", "unknown"),
                "trajectory": list(self.trajectories.get(obj_id, []))
            }
        return active
