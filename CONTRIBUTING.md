# Contributing to NTE Auto-Fishing

Thanks for helping improve the project. This repository is intentionally focused on the current GUI-first app.

## Prerequisites

- Windows
- Python 3.11+
- Elevated terminal when testing input simulation
- A running `HTGame.exe` window for manual bot testing

## Setup

```bash
pip install -r requirements.txt
python start_gui.py
```

Run tests before opening a PR:

```bash
python -m unittest discover -v
```

## Architecture

The bot loop is a state machine:

```text
IDLE -> CASTING -> WAITING -> HOOKING -> STRUGGLING -> RESULT -> IDLE
```

| Layer | Files | Responsibility |
|---|---|---|
| Core | `nte_auto_fish/core/` | Engine loop, state machine, PID controller |
| Drivers | `nte_auto_fish/drivers/` | Window discovery, screen capture, input |
| Vision | `nte_auto_fish/vision/` | HSV centroid tracking, pixel counting, template matching |
| Config | `nte_auto_fish/config/` | Local config loading, validation, ROI scaling |
| GUI | `nte_auto_fish/gui/` | CustomTkinter app, bridge, controller, ROI picker |

## Config Policy

- `config.default.json` is committed as the starter config.
- `config.json` is local-only and gitignored.
- Do not commit personal ROI calibration, keybinds, or machine-specific settings.

## Style

- Keep the current GUI design intact unless a task explicitly asks for visual redesign.
- Keep runtime behavior changes separate from cleanup when possible.
- Prefer small modules under `nte_auto_fish/` instead of adding code to the launcher.
- Avoid broad exception handling unless a Windows automation boundary genuinely needs it.
- Add or update focused tests when behavior changes.
- Keep `run.bat` simple and dependency-free; it is meant for normal Windows users.

## Release Notes

GitHub Actions runs tests on PRs and pushes to `main`. Windows release artifacts are built manually or from version tags such as `v1.0.0`.
