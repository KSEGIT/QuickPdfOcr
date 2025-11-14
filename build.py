#!/usr/bin/env python3
"""
Build script for creating standalone executables
Supports macOS, Linux, and Windows

Note for macOS:
- Builds architecture-specific binaries (arm64 or x86_64) rather than universal2
- This is because some Python packages (like Pillow) may have thin single-arch 
  binaries that cannot be merged into universal2 executables
- In GitHub Actions, we build separate binaries for ARM64 and Intel Macs
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
    ]
    
    # Add target architecture for macOS
    # Note: Building architecture-specific binaries instead of universal2
    # because some dependencies (like Pillow's _webp module) may not be universal2
    if system == "Darwin":  # macOS
        arch = platform.machine()
        # Build for the current architecture only
        cmd.extend([f"--target-arch={arch}"])
    
    cmd.append("main.py")
    
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
        print("\nBuild successful!")
        print(f"Executable location: dist/QuickPdfOcr")
        print("\nNote: Users still need to install system dependencies:")
        print("  - Tesseract OCR")
        print("  - Poppler")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
