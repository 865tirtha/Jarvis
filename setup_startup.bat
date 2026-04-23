@echo off
:: setup_startup.bat — JARVIS AUTO-RUN INSTALLER
:: Proyek: Dangerous Human

set "VBS_FILE=c:\Projek iseng\run_hidden.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo [JARVIS] Mengonfigurasi Auto-Run ...
if not exist "%VBS_FILE%" (
    echo [ERROR] File %VBS_FILE% tidak ditemukan!
    pause
    exit /b
)

copy /y "%VBS_FILE%" "%STARTUP_FOLDER%\"

echo ========================================================
echo ✅ JARVIS BERHASIL DIINSTAL KE STARTUP!
echo ========================================================
echo Sekarang JARVIS akan otomatis berjalan di background
echo setiap kali laptop Anda dinyalakan.
echo ========================================================
pause
