@echo off
title 7K Guild OCR Manager - Auto Runner
chcp 65001 >nul
color 0A

cls
echo ======================================================
echo        7K Guild OCR Manager - Auto Runner
echo        Developed By: SusiShushii
echo        Fan-made tool for Seven Knights community
echo ======================================================
echo.

REM try python first
python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
) else (
    REM try py
    py --version >nul 2>&1
    if %errorlevel%==0 (
        set PYTHON_CMD=py
    ) else (
        color 0C
        echo [ERROR] Python was not found on this system.
        echo [HINT]  Please install Python 3.12 first (from python.org)
        echo.
        pause
        exit /b
    )
)

echo [OK] Python detected.  (%PYTHON_CMD%)
echo.

echo [INFO] Starting main.py ...
echo.
%PYTHON_CMD% main.py
echo.

echo ======================================================
echo [DONE] Process completed.
echo Please open the output folder to check the results.
echo ======================================================
pause
color 07
exit /b
