#!/usr/bin/env python3
"""
Build script for creating standalone executables
Supports macOS, Linux, and Windows
"""

import sys
import platform
import subprocess
from pathlib import Path


def build_executable():
    """Build standalone executable using PyInstaller"""
    
    system = platform.system()
    print(f"Building for {system}...")
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=QuickPdfOcr",
        "--windowed",  # No console window
        "--onefile",   # Single executable
        "--noconfirm", # Overwrite without asking
        "main.py"
    ]
    
    # Add icon based on platform (if you add icons later)
    # if system == "Darwin":  # macOS
    #     cmd.extend(["--icon=resources/icon.icns"])
    # elif system == "Windows":
    #     cmd.extend(["--icon=resources/icon.ico"])
    # elif system == "Linux":
    #     cmd.extend(["--icon=resources/icon.png"])
    
    # Add hidden imports for PySide6
    cmd.extend([
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
    ])
    
    # Collect data files
    cmd.extend([
        "--collect-all=PySide6",
    ])
    
    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Build successful!")
        print(f"Executable location: dist/QuickPdfOcr")
        print("\nNote: Users still need to install system dependencies:")
        print("  - Tesseract OCR")
        print("  - Poppler")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
