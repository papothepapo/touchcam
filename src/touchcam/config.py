from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass(slots=True)
class DetectionConfig:
    finger_lab_b_low: int = 95
    finger_lab_b_high: int = 125
    min_area: int = 2800
    reflection_ratio: float = 0.08
    blur_kernel: int = 5
    morph_kernel: int = 3
    smoothing: float = 0.35


@dataclass(slots=True)
class AppConfig:
    camera_index: int = 0
    capture_width: int = 1280
    capture_height: int = 720
    fps: int = 60
    show_debug: bool = True
    dry_run_mouse: bool = False
    detection: DetectionConfig = field(default_factory=DetectionConfig)


def config_path() -> Path:
    root = Path.home() / ".touchcam"
    root.mkdir(exist_ok=True)
    return root / "config.json"


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()
    raw = json.loads(path.read_text())
    detection = DetectionConfig(**raw.get("detection", {}))
    return AppConfig(
        camera_index=raw.get("camera_index", 0),
        capture_width=raw.get("capture_width", 1280),
        capture_height=raw.get("capture_height", 720),
        fps=raw.get("fps", 60),
        show_debug=raw.get("show_debug", True),
        dry_run_mouse=raw.get("dry_run_mouse", False),
        detection=detection,
    )


def save_config(config: AppConfig) -> None:
    path = config_path()
    payload = asdict(config)
    path.write_text(json.dumps(payload, indent=2))
