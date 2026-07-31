@echo off
REM Build KeepNote for Windows 11 using PyInstaller
REM 
REM Prerequisites:
REM   1. Install Python 3.10+ from python.org (check "Add to PATH")
REM   2. Install GTK 3 for Windows from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
REM      - Or use MSYS2: pacman -S mingw-w64-x86_64-gtk3
REM   3. pip install pyinstaller PyGObject pycairo
REM   4. Run this script from the keepnote source directory

echo === Building KeepNote for Windows 11 ===

REM Check Python version
python --version
if errorlevel 1 (
    echo ERROR: Python 3 not found. Please install Python 3.10+ and add to PATH.
    exit /b 1
)

REM Install/upgrade dependencies
echo Installing dependencies...
pip install --upgrade pip setuptools wheel
pip install PyGObject pycairo pyinstaller

REM Enable long path support on Windows (for Windows 11 compatibility)
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f 2>nul

REM Build with PyInstaller
echo Building KeepNote...
pyinstaller keepnote.spec --clean

if errorlevel 1 (
    echo ERROR: Build failed.
    exit /b 1
)

echo ===
echo Build successful! Output in dist/KeepNote/
echo ===
