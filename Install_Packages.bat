@echo off
chcp 65001 >nul

title 7K Guild OCR Manager - Package Installer
color 0B

cls
echo.
echo ============================================================
echo          7K Guild OCR Manager - Package Installer
echo ============================================================
echo.

REM ------------------------------------------------
REM 1. CHECK PYTHON
REM ------------------------------------------------
echo [INFO] Checking Python...
python --version >nul 2>&1
if not %errorlevel%==0 (
    color 0C
    echo.
    echo [ERROR] Python is not installed.
    echo [HINT]  Please run Install_Python.bat first.
    echo.
    pause
    goto :eof
)

echo [OK] Python detected.
echo.

REM ------------------------------------------------
REM 2. CHECK requirements.txt
REM ------------------------------------------------
echo [INFO] Checking requirements.txt...
if not exist "requirements.txt" (
    color 0C
    echo.
    echo [ERROR] requirements.txt not found!
    echo [HINT]  Make sure it is in the same folder as this installer.
    echo.
    pause
    goto :eof
)

echo [OK] requirements.txt found.
echo.

REM ------------------------------------------------
REM 3. UPGRADE PIP
REM ------------------------------------------------
echo [STEP] Updating pip...
python -m pip install --upgrade pip
echo.

REM ------------------------------------------------
REM 4. INSTALL REQUIRED PACKAGES
REM ------------------------------------------------
echo [STEP] Installing required packages...
python -m pip install -r requirements.txt

if %errorlevel%==0 (
    color 0A
    echo.
    echo [SUCCESS] All packages installed successfully.
) else (
    color 0C
    echo.
    echo [WARNING] Some packages failed to install.
    echo [HINT]    Please check the error messages above.
)

echo.
pause
