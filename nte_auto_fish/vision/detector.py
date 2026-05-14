import cv2
import numpy as np
from typing import Optional, Tuple, List

class UIDetector:
    """Handles identification of static UI elements via template matching."""

    def find_template(
        self, 
        scene: np.ndarray, 
        template: np.ndarray, 
        threshold: float = 0.7,
        multi_scale: bool = True
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Find a template image within a scene.
        Returns: (x1, y1, x2, y2) or None
        """
        if scene is None or template is None:
            return None
            
        if multi_scale:
            return self._find_multi_scale(scene, template, threshold)
        
        # Single scale matching
        res = cv2.matchTemplate(scene, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            h, w = template.shape[:2]
            return (max_loc[0], max_loc[1], max_loc[0] + w, max_loc[1] + h)
        
        return None

    def _find_multi_scale(
        self, 
        scene: np.ndarray, 
        template: np.ndarray, 
        threshold: float,
        scales: List[float] = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.7, 2.0, 2.5]
    ) -> Optional[Tuple[int, int, int, int]]:
        """Match template across multiple scales for resolution independence."""
        best_match = None
        best_val = -1
        
        for scale in scales:
            resized_tmpl = cv2.resize(
                template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
            )
            # Ensure template is not larger than scene
            if resized_tmpl.shape[0] > scene.shape[0] or resized_tmpl.shape[1] > scene.shape[1]:
                continue
                
            res = cv2.matchTemplate(scene, resized_tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            if max_val > best_val:
                best_val = max_val
                h, w = resized_tmpl.shape[:2]
                best_match = (max_loc[0], max_loc[1], max_loc[0] + w, max_loc[1] + h)
                
        if best_val >= threshold:
            return best_match
            
        return None
