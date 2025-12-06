@echo off
REM ชื่อไฟล์ติดตั้ง Python ของคุณ (ตัวอย่าง: python-3.12.0-amd64.exe)
SET INSTALLER_FILE=python-3.12.0-amd64.exe

REM พารามิเตอร์สำหรับการติดตั้งแบบเงียบ (Silent Installation)
REM /quiet = ไม่แสดงหน้าต่างติดตั้งใดๆ
REM InstallAllUsers=1 = ติดตั้งให้ผู้ใช้ทุกคน
REM PrependPath=1 = เพิ่ม Python เข้าไปใน PATH environment variable โดยอัตโนมัติ
REM Include_test=0 = ไม่ติดตั้ง Test suite (ประหยัดพื้นที่)
SET INSTALL_ARGS=/quiet InstallAllUsers=1 PrependPath=1 Include_test=0

REM เริ่มต้นกระบวนการติดตั้งและรอจนกว่าจะเสร็จสิ้น
echo Starting Python silent installation...
start /wait "" %INSTALLER_FILE% %INSTALL_ARGS%

REM ตรวจสอบว่าติดตั้งสำเร็จหรือไม่ โดยดูจาก Errorlevel ที่ส่งกลับมา
IF %ERRORLEVEL% EQU 0 (
    echo Python installation completed successfully!
) ELSE (
    echo Python installation failed with error code %ERRORLEVEL%.
)

REM ตรวจสอบเวอร์ชัน Python หลังจากติดตั้ง
echo Verifying installation...
python --version

pause