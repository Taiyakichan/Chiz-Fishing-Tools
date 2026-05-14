<div align="center">

<img src="assets/chiz_logo_header_transparent.png" alt="Chiz Fishing Tool" width="240"/>

# Chiz Fishing Tools

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

## Download And Run

1. Download `Chiz-Fishing-Tools.exe` from the latest GitHub Release.
2. Put the `.exe` in its own folder.
3. Run the `.exe`.
4. Approve the Windows admin prompt when it appears.
5. Keep `HTGame.exe` open and visible while using the tool.

On first launch, the app creates `config.json` next to the executable. That file stores your local settings, keybinds, and calibrated areas.

## Usage Guide

1. Open the game and make sure the fishing UI is visible.
2. Start `Chiz-Fishing-Tools.exe`.
3. Go to the Settings tab and press **Find game**.
4. Calibrate **Bar area**, **Notice area**, and **Button** if the defaults do not match your screen.
5. Use **Preview areas** to confirm the saved regions are placed correctly.
6. Set your hook key, close key, session time, fish limit, and detection settings.
7. Return to the main controls and start the bot.
8. Stop the bot before changing game windows, closing the app, or editing calibration.

If movement keys ever feel stuck, press **Release** in the Settings tab. The app also releases held keys when stopping and closing.

## Config Files

- `config.default.json` is the public default/reset reference.
- `config.json` is created automatically for each user and is not committed to git.
- Delete `config.json` to reset local settings back to defaults on the next launch.

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

The app creates `config.json` automatically on first launch when no local config exists. `config.default.json` is kept as the public default/reset reference.

## Calibration Details

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
build_release.bat
```

The built executable is written to `dist/Chiz-Fishing-Tools.exe`.
