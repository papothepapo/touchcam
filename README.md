# TouchCam (modernized Project Sistine)

TouchCam is a modern, Python 3, cross-platform evolution of the 2018 Project Sistine prototype.
It keeps the original idea (finger + reflection based touch inference from webcam video), and adds:

- modern dependencies (Python 3.10+, OpenCV 4, Qt GUI)
- installable package with command-line entry points
- calibration-aware GUI app
- cross-platform mouse output pipeline (Windows/macOS/Linux)
- GitHub Actions CI/CD for linting, tests, and executable builds

## Quick start

```bash
python -m pip install --upgrade pip
pip install .
touchcam
```

This launches the desktop app.

## Headless smoke run

```bash
touchcam-cli --seconds 5
```

This runs the detection pipeline for 5 seconds and prints detections.

## GUI features

- Live camera preview
- Start/Stop pipeline controls
- Camera index selector
- Dry-run mouse mode for safety/testing
- Calibration workflow (multi-point perspective mapping)

## Calibration flow

1. Start the pipeline.
2. Position your finger over each target on your screen.
3. Click **Start calibration** and then **Capture next point** until complete.
4. The app computes a homography to map camera coordinates to screen coordinates.

## Development

```bash
pip install -e .[dev]
ruff check src
```

## Packaging executables

Local:

```bash
pip install -e . pyinstaller
pyinstaller --noconfirm --clean --name touchcam --onefile scripts/run_touchcam.py
```

CI builds artifacts for:

- `ubuntu-latest`
- `windows-latest`
- `macos-latest`

See `.github/workflows/build.yml`.
