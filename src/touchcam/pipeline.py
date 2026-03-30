from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Optional

import cv2
import numpy as np

from .calibration import CalibrationModel
from .config import AppConfig
from .controller import MouseController
from .detection import DetectionResult, TouchDetector


@dataclass(slots=True)
class FramePacket:
    frame: np.ndarray
    debug: np.ndarray
    detection: Optional[DetectionResult]


class TouchPipeline:
    def __init__(self, config: AppConfig, calibration: CalibrationModel):
        self.config = config
        self.calibration = calibration
        self.detector = TouchDetector(config.detection)
        self.mouse = MouseController(dry_run=config.dry_run_mouse)
        self._lock = threading.Lock()
        self._latest: Optional[FramePacket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._smoothed: Optional[tuple[float, float]] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def latest(self) -> Optional[FramePacket]:
        with self._lock:
            return self._latest

    def _run(self) -> None:
        cap = cv2.VideoCapture(self.config.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.capture_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.capture_height)
        cap.set(cv2.CAP_PROP_FPS, self.config.fps)
        frame_delay = 1.0 / max(self.config.fps, 1)

        while self._running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.03)
                continue

            debug = frame.copy()
            result = self.detector.detect(frame, debug if self.config.show_debug else None)
            if result is not None:
                sx, sy = self.calibration.map_to_screen(result.x, result.y)
                if self._smoothed is None:
                    self._smoothed = (sx, sy)
                else:
                    alpha = self.config.detection.smoothing
                    self._smoothed = (
                        alpha * sx + (1 - alpha) * self._smoothed[0],
                        alpha * sy + (1 - alpha) * self._smoothed[1],
                    )
                self.mouse.move(*self._smoothed)
                self.mouse.set_touch(result.is_touch)
            else:
                self.mouse.set_touch(False)

            packet = FramePacket(frame=frame, debug=debug, detection=result)
            with self._lock:
                self._latest = packet
            time.sleep(frame_delay / 2)

        cap.release()
