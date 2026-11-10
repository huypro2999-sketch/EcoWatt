@echo off
cd /d "%~dp0"
title EcoWatt Debug Mode
echo ==================================================
echo   EcoWatt - Kiem tra khoi dong ung dung
echo ==================================================
echo.
echo Dang kiem tra Python...
python --version
echo.
echo Dang khoi dong EcoWatt...
python main.py
echo.
echo Ung dung da dong (Exit code: %errorlevel%).
pause

