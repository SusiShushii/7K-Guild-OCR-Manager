@echo off
cd /d "%~dp0"

echo ============================================
echo    7K Guild OCR Manager EXE (PyInstaller)
echo ============================================
echo.

REM สร้างโฟลเดอร์ dist, build ใหม่แบบสะอาด
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
if exist GuildManagerOCR.spec del GuildManagerOCR.spec

REM สร้าง exe ไฟล์เดียวจาก main.py
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --name "GuildManagerOCR" ^
  main.py

echo.
echo ============================================
echo   Build finished
echo   EXE อยู่ที่: dist\SenaOCR.exe
echo ============================================
echo.
pause
