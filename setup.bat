@echo off
REM ============================================================
REM  Cai dat 1 lenh cho Electronic Parts Counter
REM  Chay: nhay doi setup.bat (hoac: setup.bat trong terminal)
REM ============================================================
echo ============================================
echo   Cai dat moi truong - Linh Kien Counter
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Chua co Python. Cai Python 3.9+ tu https://python.org roi chay lai.
    pause
    exit /b 1
)

echo [1/2] Nang cap pip...
python -m pip install --upgrade pip

echo.
echo [2/2] Cai thu vien tu requirements.txt...
python -m pip install -r requirements.txt

echo.
echo ============================================
echo   XONG! Chay giao dien bang:
echo       python m4_gui\app.py
echo ============================================
pause
