@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
)

where "%PYTHON_EXE%" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Python was not found.
    echo Install Python or create a .venv first.
    pause
    exit /b 1
)

echo Starting Chiz Fishing Tools from source...
"%PYTHON_EXE%" "%~dp0start_gui.py"

if errorlevel 1 (
    echo.
    echo The source app exited with an error. Check the message above.
    pause
)
