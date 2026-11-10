@echo off
cd /d "%~dp0"
title EcoWatt

:: 1. Thu chay bang pythonw (khong hien cua so den)
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw main.py
    exit /b 0
)

:: 2. Thu chay bang pythonw duong dan goc
if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" main.py
    exit /b 0
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" main.py
    exit /b 0
)

:: 3. Fallback sang python thuong
where python >nul 2>nul
if %errorlevel% equ 0 (
    start "" python main.py
    exit /b 0
)

echo [LOI] Khong tim thay Python de khoi chay EcoWatt!
echo Vui long thu mo file Debug_EcoWatt.bat de kiem tra.
pause
