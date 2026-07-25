@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo [1/2] Installiere Module...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Installation fehlgeschlagen.
    pause
    exit /b 1
)
echo [2/2] Starte Cit...
python -m cit.main
pause
