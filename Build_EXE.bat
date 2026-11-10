@echo off
cd /d "%~dp0"
title Dong goi EcoWatt thanh file EXE
echo ==================================================
echo   Dang dong goi EcoWatt thanh 1 file EXE duy nhat...
echo ==================================================
echo.
"%LOCALAPPDATA%\Programs\Python\Python312\Scripts\pyinstaller.exe" --noconsole --onefile --icon="app_icon.ico" --name "EcoWatt" --collect-all customtkinter --clean main.py
if %errorlevel% equ 0 (
    copy /y "dist\EcoWatt.exe" "EcoWatt.exe"
    echo.
    echo ==================================================
    echo   THANH CONG! File EcoWatt.exe da san sang o thu muc goc.
    echo ==================================================
) else (
    echo.
    echo [LOI] Dong goi that bai. Vui long kiem tra lai.
)
pause

