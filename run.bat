@echo off
REM ============================================================
REM  Nhay doi de CHAY app (tu cai thu vien lan dau)
REM ============================================================
cd /d "%~dp0"

REM Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Chua co Python. Cai Python 3.9+ tu https://python.org
    pause
    exit /b 1
)

REM Lan dau: thieu thu vien thi tu cai
python -c "import ultralytics, cv2, PIL, numpy" >nul 2>&1
if errorlevel 1 (
    echo Lan dau chay - dang cai thu vien, doi mot chut...
    python -m pip install -r requirements.txt
)

REM Chay giao dien
python m4_gui\app.py
if errorlevel 1 pause
