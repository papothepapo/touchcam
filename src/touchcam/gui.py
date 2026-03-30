from __future__ import annotations

from dataclasses import replace

import cv2
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .calibration import CalibrationModel, fit_homography
from .config import AppConfig, save_config
from .pipeline import TouchPipeline


class TouchCamWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.setWindowTitle("TouchCam")
        self.config = config
        self.calibration = CalibrationModel()
        self.pipeline = TouchPipeline(config, self.calibration)
        self.calibration_targets = [
            (0.2, 0.2),
            (0.5, 0.2),
            (0.8, 0.2),
            (0.2, 0.8),
            (0.5, 0.8),
            (0.8, 0.8),
        ]
        self.calibration_camera_pts: list[tuple[float, float]] = []
        self.calibration_step = 0

        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        self.preview = QLabel("Camera preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(640, 360)

        controls = QWidget()
        form = QFormLayout(controls)
        self.camera_index = QSpinBox()
        self.camera_index.setRange(0, 8)
        self.camera_index.setValue(self.config.camera_index)
        self.dry_run_mouse = QCheckBox("Dry run mouse")
        self.dry_run_mouse.setChecked(self.config.dry_run_mouse)
        self.toggle_btn = QPushButton("Start")
        self.calib_btn = QPushButton("Start calibration")
        self.status = QLabel("Idle")

        form.addRow("Camera index", self.camera_index)
        form.addRow(self.dry_run_mouse)
        form.addRow(self.toggle_btn)
        form.addRow(self.calib_btn)
        form.addRow("Status", self.status)

        layout.addWidget(self.preview, stretch=3)
        layout.addWidget(controls, stretch=1)

        self.toggle_btn.clicked.connect(self.toggle_pipeline)
        self.calib_btn.clicked.connect(self.calibrate_step)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.render)
        self.timer.start(16)

    def _apply_live_config(self) -> None:
        self.config = replace(
            self.config,
            camera_index=self.camera_index.value(),
            dry_run_mouse=self.dry_run_mouse.isChecked(),
        )
        save_config(self.config)

    def toggle_pipeline(self) -> None:
        if self.toggle_btn.text() == "Start":
            self._apply_live_config()
            self.pipeline = TouchPipeline(self.config, self.calibration)
            self.pipeline.start()
            self.toggle_btn.setText("Stop")
            self.status.setText("Running")
        else:
            self.pipeline.stop()
            self.toggle_btn.setText("Start")
            self.status.setText("Stopped")

    def calibrate_step(self) -> None:
        packet = self.pipeline.latest()
        if packet is None or packet.detection is None:
            self.status.setText("No detection for calibration")
            return

        self.calibration_camera_pts.append((packet.detection.x, packet.detection.y))
        self.calibration_step += 1

        if self.calibration_step >= len(self.calibration_targets):
            screen_w = QApplication.primaryScreen().size().width()
            screen_h = QApplication.primaryScreen().size().height()
            screen_pts = [(x * screen_w, y * screen_h) for x, y in self.calibration_targets]
            self.calibration.homography = fit_homography(self.calibration_camera_pts, screen_pts)
            self.calibration.camera_points = list(self.calibration_camera_pts)
            self.calibration.screen_points = list(screen_pts)
            self.calibration_camera_pts.clear()
            self.calibration_step = 0
            self.status.setText("Calibration complete")
            self.calib_btn.setText("Start calibration")
            return

        tx, ty = self.calibration_targets[self.calibration_step]
        self.status.setText(f"Touch target {self.calibration_step + 1}/{len(self.calibration_targets)} @ ({tx:.1f}, {ty:.1f})")
        self.calib_btn.setText("Capture next point")

    def render(self) -> None:
        packet = self.pipeline.latest()
        if packet is None:
            return
        frame = packet.debug if self.config.show_debug else packet.frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.preview.setPixmap(QPixmap.fromImage(image).scaled(self.preview.size(), Qt.KeepAspectRatio))


def run_gui(config: AppConfig) -> int:
    app = QApplication([])
    win = TouchCamWindow(config)
    win.resize(1100, 600)
    win.show()
    return app.exec()
