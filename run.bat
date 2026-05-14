@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
)

echo Starting NTE Auto-Fishing...
"%PYTHON_EXE%" start_gui.py

if errorlevel 1 (
    echo.
    echo The app exited with an error. Check the message above.
    pause
)
