<div align="center">

<img src="assets/chiz_logo_header_transparent.png" alt="Chiz Fishing Tool" width="240"/>

# Chiz Fishing Tools

**Fishing tool for NTE on Windows.**

</div>

## Notice

This tool automates game input and screen reading. Use it at your own risk and respect the game's Terms of Service. The maintainers are not responsible for account penalties or misuse.

## Download

Download `Chiz-Fishing-Tools.exe` from the latest release:

[Releases](https://github.com/Taiyakichan/Chiz-Fishing-Tools/releases)

Put the `.exe` in its own folder, run it, and approve the Windows admin prompt. Keep NTE (`HTGame.exe`) open and visible while using the tool.

## Basic Use

1. Open NTE and make sure the fishing UI is visible.
2. Start `Chiz-Fishing-Tools.exe`.
3. In Settings, press **Find game**.
4. Calibrate **Bar area**, **Notice area**, and **Button** if needed.
5. Press **Preview areas** to check the regions.
6. Start the bot from the main controls.
7. Stop the bot before closing the game or changing calibration.

If keys feel stuck, press **Release** in Settings.

## Config

The app creates `config.json` automatically on first launch. Delete `config.json` to reset local settings.

`config.default.json` is kept in the repo as the default reference.

## Run From Source

```bash
pip install -r requirements.txt
python start_gui.py
```

Or on Windows:

```bat
run.bat
```

## Build

```bash
pip install pyinstaller
build_release.bat
```

The executable is created at `dist/Chiz-Fishing-Tools.exe`.

## Test

```bash
python -m unittest discover -v
```
