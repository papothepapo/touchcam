from __future__ import annotations

from .config import load_config
from .gui import run_gui


def main() -> int:
    config = load_config()
    return run_gui(config)


if __name__ == "__main__":
    raise SystemExit(main())
