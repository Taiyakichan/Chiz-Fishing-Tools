@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=Chiz-Fishing-Tools"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo Building %APP_NAME% from %CD%

"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo PyInstaller is not installed.
    echo Install it with:
    echo   "%PYTHON%" -m pip install pyinstaller
    exit /b 1
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --name "%APP_NAME%" ^
    --collect-data customtkinter ^
    --add-data "assets;assets" ^
    --add-data "config.default.json;." ^
    start_gui.py

if errorlevel 1 exit /b %errorlevel%

if not exist "dist\%APP_NAME%.exe" (
    echo Build finished, but dist\%APP_NAME%.exe was not found.
    exit /b 1
)

echo.
echo Built dist\%APP_NAME%.exe
echo Upload that file to a GitHub Release when you are ready.
