from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from .config import DetectionConfig


@dataclass(slots=True)
class DetectionResult:
    x: float
    y: float
    is_touch: bool
    confidence: float


class TouchDetector:
    def __init__(self, cfg: DetectionConfig):
        self.cfg = cfg

    def _segment(self, frame: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        b = lab[:, :, 2]
        mask = cv2.inRange(b, self.cfg.finger_lab_b_low, self.cfg.finger_lab_b_high)
        if self.cfg.blur_kernel > 1:
            k = self.cfg.blur_kernel | 1
            mask = cv2.GaussianBlur(mask, (k, k), 0)
        k = max(self.cfg.morph_kernel, 1)
        kernel = np.ones((k, k), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def detect(self, frame: np.ndarray, debug: Optional[np.ndarray] = None) -> Optional[DetectionResult]:
        mask = self._segment(frame)
        n_labels, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
        if n_labels <= 1:
            return None

        components = []
        for i in range(1, n_labels):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area >= self.cfg.min_area:
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]
                cx, cy = centroids[i]
                components.append((area, (x, y, w, h), (cx, cy)))

        if not components:
            return None

        components.sort(key=lambda item: item[0], reverse=True)
        finger_area, finger_rect, finger_center = components[0]
        x, y, w, h = finger_rect
        cx, cy = finger_center

        touch = True
        confidence = 0.6
        if len(components) > 1:
            refl_area, refl_rect, refl_center = components[1]
            rx, ry, rw, rh = refl_rect
            same_x_band = not (x + w < rx or rx + rw < x)
            reflection_above = ry + rh < y
            ratio = refl_area / max(float(finger_area), 1.0)
            if same_x_band and reflection_above and ratio >= self.cfg.reflection_ratio:
                touch = False
                cx = (cx + refl_center[0]) / 2
                cy = (cy + refl_center[1]) / 2
                confidence = min(1.0, 0.7 + ratio)

        if debug is not None:
            cv2.rectangle(debug, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(debug, (int(cx), int(cy)), 8, (255, 0, 255), -1)
            state = "touch" if touch else "hover"
            cv2.putText(debug, f"{state} {confidence:.2f}", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        return DetectionResult(x=float(cx), y=float(cy), is_touch=touch, confidence=confidence)
