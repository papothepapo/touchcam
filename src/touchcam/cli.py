from __future__ import annotations

import argparse
import time

from .calibration import CalibrationModel
from .config import load_config
from .pipeline import TouchPipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="TouchCam headless mode")
    parser.add_argument("--seconds", type=int, default=10, help="How long to run")
    args = parser.parse_args()

    cfg = load_config()
    cfg.dry_run_mouse = True
    pipeline = TouchPipeline(cfg, CalibrationModel())
    pipeline.start()

    end = time.time() + args.seconds
    while time.time() < end:
        packet = pipeline.latest()
        if packet and packet.detection:
            d = packet.detection
            print(f"x={d.x:.1f} y={d.y:.1f} touch={d.is_touch} conf={d.confidence:.2f}")
        time.sleep(0.1)

    pipeline.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
