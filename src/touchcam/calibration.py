from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np


@dataclass(slots=True)
class CalibrationModel:
    homography: Optional[np.ndarray] = None
    camera_points: list[tuple[float, float]] = field(default_factory=list)
    screen_points: list[tuple[float, float]] = field(default_factory=list)

    def ready(self) -> bool:
        return self.homography is not None

    def map_to_screen(self, x: float, y: float) -> tuple[float, float]:
        if self.homography is None:
            return x, y
        src = np.array([[[x, y]]], dtype=np.float32)
        dst = cv2.perspectiveTransform(src, self.homography)
        return float(dst[0, 0, 0]), float(dst[0, 0, 1])


def fit_homography(camera_pts: list[tuple[float, float]], screen_pts: list[tuple[float, float]]) -> np.ndarray:
    src = np.array(camera_pts, dtype=np.float32)
    dst = np.array(screen_pts, dtype=np.float32)
    hom, _ = cv2.findHomography(src, dst, method=0)
    if hom is None:
        raise ValueError("Unable to compute homography from calibration points")
    return hom
