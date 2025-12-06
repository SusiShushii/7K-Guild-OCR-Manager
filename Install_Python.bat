@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Set console colors: 0 = black background, A = light green text
color 0A

cls
echo ===============================================
echo   Auto-Installer for Python 3.12.10 (GUI Mode)
echo ===============================================
echo.

REM ------------------------------------------------
REM 1. CHECK IF PYTHON IS ALREADY INSTALLED
REM ------------------------------------------------
echo [INFO] Checking for existing Python installation...
python --version >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=2 delims= " %%V in ('python --version 2^>nul') do (
        set "PY_FOUND_VERSION=%%V"
    )
    echo.
    echo [OK] Python is already installed.
    echo [OK] Detected version: !PY_FOUND_VERSION!
    echo.
    echo [NEXT] You can now install the required packages by running:
    echo     Install_Packages.bat
    echo.
    pause
    exit /b 0
)

echo No existing Python installation detected.
echo [INFO] Proceeding with Python 3.12.10 installation...
echo.

REM ------------------------------------------------
REM 2. DOWNLOAD PYTHON INSTALLER (IF NEEDED)
REM ------------------------------------------------
set "PY_VER=3.12.10"
set "PY_FILE=python-%PY_VER%-amd64.exe"
set "PY_URL=https://www.python.org/ftp/python/%PY_VER%/%PY_FILE%"

echo [STEP] Download / Prepare Installer

if exist "%PY_FILE%" (
    echo [OK] Installer already exists: %PY_FILE%
) else (
    echo [INFO] Downloading Python %PY_VER%...
    echo URL: %PY_URL%
    echo.

    curl -L -o "%PY_FILE%" "%PY_URL%"

    REM IMPORTANT: check download result AFTER curl
    if errorlevel 1 (
        echo.
        color 0C
        echo [ERROR] Failed to download Python installer.
        echo [HINT]  Check your internet connection and try again.
        echo.
        pause
        exit /b 1
    )

    echo.
    color 0A
    echo [OK] Download complete!
    echo.
)

REM ------------------------------------------------
REM 3. RUN GUI INSTALLER + SHOW PROGRESS DOTS
REM ------------------------------------------------
echo [STEP] Starting GUI installation...
echo [INFO] Please wait. This may take a few minutes.
echo.

start "" "%PY_FILE%" /passive InstallAllUsers=1 PrependPath=1 Include_test=0

echo [INFO] Monitoring installer progress...
echo    If dots keep appearing, installation is still running:
echo.

:wait_loop
timeout /t 3 /nobreak >nul

REM Check Python installer process
tasklist /FI "IMAGENAME eq %PY_FILE%" | find /I "%PY_FILE%" >nul
if %ERRORLEVEL%==0 (
    set /p "=." <nul
    goto wait_loop
)

REM Check Windows Installer engine
tasklist /FI "IMAGENAME eq msiexec.exe" | find /I "msiexec.exe" >nul
if %ERRORLEVEL%==0 (
    set /p "=." <nul
    goto wait_loop
)

echo.
echo.
echo ===============================================
echo      Python Installer Finished
echo ===============================================
echo.

REM ------------------------------------------------
REM 4. TRY TO DETECT INSTALL PATH FROM REGISTRY
REM ------------------------------------------------
echo [STEP] Detecting Python installation path from registry...
set "PYDIR="

REM Try HKLM (All Users)
for /f "skip=2 tokens=2*" %%A in ('
  reg query "HKLM\SOFTWARE\Python\PythonCore\3.12\InstallPath" /ve 2^>nul
') do (
  set "PYDIR=%%B"
)

REM If not found, try HKCU (Current User)
if not defined PYDIR (
  for /f "skip=2 tokens=2*" %%A in ('
    reg query "HKCU\SOFTWARE\Python\PythonCore\3.12\InstallPath" /ve 2^>nul
  ') do (
    set "PYDIR=%%B"
  )
)

if defined PYDIR (
    echo [OK] Python install path detected:
    echo   !PYDIR!
    echo.
    echo [INFO] Updating PATH for this session...
    set "PATH=%PATH%;!PYDIR!;!PYDIR!\Scripts\"
) else (
    echo [WARNING] Could not detect Python installation path from registry.
    echo [INFO] We will now verify using "python --version".
)

REM ------------------------------------------------
REM 5. FINAL CHECK: VERIFY PYTHON WORKS
REM ------------------------------------------------
echo.
echo Verifying Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    color 0C
    echo [ERROR] Python does not appear to be available on PATH.
    echo [HINT] Installation may have failed or PATH is not updated in this window.
    echo Please close this window, open a new Command Prompt and run:
    echo     python --version
    echo to check manually.
    echo.
    pause
    exit /b 1
)

for /f "tokens=1,2 delims= " %%A in ('python --version 2^>nul') do (
    set "PY_LABEL=%%A"
    set "PY_VERSION=%%B"
)

color 0A
echo.
echo [OK] Python installation looks OK.
echo    Detected: !PY_LABEL! !PY_VERSION!
echo.
echo [NEXT] You can now install the required packages by running:
echo     Install_Packages.bat
echo.
pause
exit /b 0
