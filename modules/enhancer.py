import cv2
import numpy as np


class LowLightEnhancer:
    """
    Image enhancement engine using Contrast Limited Adaptive Histogram Equalization (CLAHE).
    Operates on the Luminance (L) channel in LAB color space to restore visibility in
    low-light, foggy, and nighttime border surveillance feeds without color distortion.
    """
    def __init__(self, clip_limit: float = 3.0, tile_grid_size: tuple = (8, 8)):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)

    def enhance(self, frame: np.ndarray, clip_limit: float = None) -> np.ndarray:
        """
        Enhances contrast and brightness of a BGR frame.
        """
        if frame is None:
            return None

        if clip_limit is not None and clip_limit != self.clip_limit:
            self.clip_limit = clip_limit
            self.clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)

        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Apply CLAHE to L channel only
        enhanced_l = self.clahe.apply(l_channel)

        # Merge back and convert to BGR
        enhanced_lab = cv2.merge((enhanced_l, a_channel, b_channel))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        return enhanced_bgr
