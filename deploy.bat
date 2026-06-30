@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Launching Foundry Live Demo Console deployment...
echo Log: ui\deploy3.log
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0deploy.ps1"
echo.
echo ===== Finished. You can close this window. =====
pause
