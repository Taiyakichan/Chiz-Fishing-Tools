<div align="center">

<img src="assets/chiz_logo_header_transparent.png" alt="Chiz Fishing Tool" width="240"/>

# NTE Auto-Fishing

**A Windows GUI-first visual auto-fishing assistant for HTGame.exe.**

Built with Python, OpenCV, MSS, PyDirectInput, PyWin32, and CustomTkinter.

</div>

## Important Notice

This project automates game input and screen reading. Use it at your own risk, and make sure your use follows the game's Terms of Service and any applicable rules. The maintainers are not responsible for account actions, game penalties, or misuse.

## Highlights

- GUI-first control center for bot state, fish count, session time, settings, logs, and calibration.
- Window-aware capture that targets `HTGame.exe` and maps ROIs to the game client area.
- Manual ROI calibration for the fishing bar and banner regions.
- HSV-based detection for bite triggers, cursor tracking, target tracking, and banner checks.
- PID struggle control with key release safety on stop and shutdown.
- One shipped default config in `config.default.json`; local settings are saved to `config.json`.

## Project Structure

| Path | Description |
| :--- | :--- |
| `start_gui.py` | Supported GUI entrypoint. |
| `nte_auto_fish/core/` | Fishing engine, state machine, and PID controller. |
| `nte_auto_fish/drivers/` | Window discovery, screen capture, and input drivers. |
| `nte_auto_fish/vision/` | HSV tracking and template matching helpers. |
| `nte_auto_fish/config/` | Config manager and ROI scaling utilities. |
| `nte_auto_fish/gui/` | CustomTkinter app, controller, bridge, theme, and ROI picker. |
| `tests/` | Unit tests for config, ROI scaling, PID, engine stop safety, and vision fixtures. |
| `config.default.json` | Public default config. The app saves local changes to `config.json`. |

## Run From Source

Requirements:

- Windows
- Python 3.11+
- A visible `HTGame.exe` window for real bot usage
- Elevated terminal if simulated input does not reach the game

```bash
pip install -r requirements.txt
python start_gui.py
```

The app starts from `config.default.json` when no local config exists. Saving settings or calibration creates `config.json`, which is gitignored by design.

## Calibration

Open the Settings tab and calibrate:

- **Bar area**: the fishing struggle bar.
- **Notice area**: the top banner/notice region where bite text appears.
- **Button**: the hook prompt/button region, if the default area does not match your screen.

Calibration is saved as ratio-based ROI data so it can scale across common window sizes.

The Settings tab also includes small manual tools:

- **Preview areas**: shows the active bar, notice, and button regions.
- **Find game**: rechecks for the `HTGame.exe` window.
- **Test hook** and **Test close**: sends the configured keys to the game window.
- **Release**: releases held movement keys.

## Testing

```bash
python -m unittest discover -v
```

Vision tests use screenshots in `tests/vision/data/`. Add fixtures when detection behavior changes.

## Launcher

On Windows you can also run:

```bat
run.bat
```

The launcher uses `.venv\Scripts\python.exe` when a local virtual environment exists, otherwise it uses `python`.

## Build A Windows EXE

Install PyInstaller, then build from the repo root:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --uac-admin --name NTE-Auto-Fish --collect-data customtkinter --add-data "assets;assets" --add-data "config.default.json;." start_gui.py
```

GitHub Actions can also build the Windows artifact from release tags like `v1.0.0` or from a manual workflow run.
