#!/bin/bash
# pkg/win/build.sh - Modernized PyInstaller build script for Windows 11
# FIX: Replaces deprecated py2exe workflow (KEEP-PLAN-5.2)
# MARKER: [REPLACEMENT] Do not use with original py2exe-based script

set -e

echo "=== KeepNote Windows Build Script (PyInstaller) ==="
echo "Date: $(date)"

# Validate environment
if [ ! -f "keepnote.spec" ]; then
    echo "ERROR: keepnote.spec not found. Run from project root."
    exit 1
fi

# Detect Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "WARNING: PyInstaller not found. Installing..."
    pip install pyinstaller>=6.0
fi

# Set GTK_PATH if not already set (MSYS2 default)
if [ -z "$GTK_PATH" ] && [ -d "/mingw64" ]; then
    export GTK_PATH="/mingw64"
    echo "Set GTK_PATH=$GTK_PATH (MSYS2)"
fi

# Clean previous build
rm -rf dist/KeepNote build/ *.spec.bak 2>/dev/null || true

# Build with PyInstaller
echo "Running PyInstaller..."
pyinstaller --clean keepnote.spec

# Verify build output
if [ -d "dist/KeepNote" ]; then
    echo "SUCCESS: Build completed"
    echo "Output directory: dist/KeepNote"
    ls -la dist/KeepNote/
else
    echo "ERROR: Build failed. Check keepnote.spec and PyInstaller logs."
    exit 1
fi

# Optional: Create installer with Inno Setup
if [ "$1" = "--installer" ] && command -v iscc &> /dev/null; then
    echo "Creating installer with Inno Setup..."
    # iscc pkg/win/keepnote.iss
    echo "Inno Setup integration pending implementation"
fi
