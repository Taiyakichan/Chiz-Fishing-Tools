import cv2
import numpy as np
from typing import Tuple, Optional

class ObjectTracker:
    """Specialized in tracking horizontal positions of UI elements using HSV range."""
    
    def __init__(self, kernel_size: int = 3):
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def find_centroid_x(
        self, 
        bgr_img: np.ndarray, 
        hsv_lower: Tuple[int, int, int], 
        hsv_upper: Tuple[int, int, int],
        min_area: float = 10.0
    ) -> Tuple[Optional[float], float]:
        """
        Find the horizontal center of mass for a color range.
        Returns: (x_relative, total_area)
        """
        if bgr_img is None or bgr_img.size == 0:
            return None, 0.0

        hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))
        
        # Cleanup noise and inflate small objects (crucial for cursors)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.dilate(mask, self.kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, 0.0

        # Filter by area and find the largest/most prominent candidate
        valid_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
        if not valid_contours:
            return None, 0.0

        # Pick the largest contour
        best_contour = max(valid_contours, key=cv2.contourArea)
        M = cv2.moments(best_contour)
        
        if M["m00"] == 0:
            return None, 0.0

        cx = int(M["m10"] / M["m00"])
        return cx, M["m00"]

    def check_pixel_count(
        self, 
        bgr_img: np.ndarray, 
        hsv_lower: Tuple[int, int, int], 
        hsv_upper: Tuple[int, int, int]
    ) -> int:
        """Count how many pixels fall into a color range."""
        if bgr_img is None or bgr_img.size == 0:
            return 0
        hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(hsv_lower), np.array(hsv_upper))
        return cv2.countNonZero(mask)
