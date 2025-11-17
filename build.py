#!/usr/bin/env python3
"""
Build script for creating standalone executables
Supports macOS, Linux, and Windows

Note for macOS:
- Builds architecture-specific binaries (arm64 or x86_64) rather than universal2
- This is because some Python packages (like Pillow) may have thin single-arch 
  binaries that cannot be merged into universal2 executables
- In GitHub Actions, we build separate binaries for ARM64 and Intel Macs

Note for Poppler:
- If poppler_binaries directory exists, Poppler will be bundled with the executable
- Users will still need to install Tesseract OCR separately
"""

import sys
import platform
import subprocess
import os
import shutil
from pathlib import Path


def find_poppler_binaries():
    """
    Find Poppler binaries to bundle with the executable
    
    Returns:
        Path or None: Path to Poppler binaries directory, or None if not found
    """
    system = platform.system()
    
    # Check for pre-downloaded binaries in poppler_binaries directory
    poppler_dir = Path("poppler_binaries")
    if poppler_dir.exists():
        print(f"Found Poppler binaries in: {poppler_dir}")
        return poppler_dir
    
    # Try to find system Poppler installation
    if system == "Darwin":  # macOS
        # Check Homebrew installation paths
        homebrew_paths = [
            Path("/opt/homebrew/bin"),  # ARM64 Homebrew
            Path("/usr/local/bin"),     # Intel Homebrew
        ]
        for path in homebrew_paths:
            if (path / "pdftotext").exists():
                print(f"Found system Poppler in: {path}")
                return path
    
    elif system == "Linux":
        # Check common Linux installation paths
        if Path("/usr/bin/pdftotext").exists():
            print("Found system Poppler in: /usr/bin")
            return Path("/usr/bin")
    
    elif system == "Windows":
        # Windows typically doesn't have a system Poppler
        pass
    
    print("Warning: Poppler binaries not found. They will not be bundled.")
    print("Users will need to install Poppler separately.")
    return None


def build_executable():
    """Build standalone executable using PyInstaller"""
    
    system = platform.system()
    print(f"Building for {system}...")
    
    # Find Poppler binaries
    poppler_path = find_poppler_binaries()
    
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
    
    # Add hidden imports for PySide6 and other dependencies
    cmd.extend([
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=pytesseract",
        "--hidden-import=pdf2image",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PyPDF2",
    ])
    
    # Collect all necessary packages to ensure complete bundling
    cmd.extend([
        "--collect-all=PySide6",
        "--collect-all=pdf2image",
        "--collect-all=pytesseract",
    ])
    
    # Bundle Poppler binaries if found
    if poppler_path:
        print(f"\nBundling Poppler binaries from: {poppler_path}")
        
        if system == "Windows":
            # For Windows, bundle all DLLs and executables
            bin_path = poppler_path / "Library" / "bin"
            if bin_path.exists():
                cmd.extend([
                    f"--add-binary={bin_path}{os.pathsep}poppler/bin",
                ])
                print(f"  Added: {bin_path}")
            else:
                # If not in Library/bin, try direct bin folder
                bin_path = poppler_path / "bin"
                if bin_path.exists():
                    cmd.extend([
                        f"--add-binary={bin_path}{os.pathsep}poppler/bin",
                    ])
                    print(f"  Added: {bin_path}")
        
        elif system == "Darwin":  # macOS
            # Bundle specific Poppler executables for macOS
            poppler_tools = [
                "pdftotext", "pdftoppm", "pdfinfo", "pdfimages",
                "pdftocairo", "pdftohtml", "pdftops", "pdfunite", "pdfseparate"
            ]
            for tool in poppler_tools:
                tool_path = poppler_path / tool
                if tool_path.exists():
                    cmd.extend([
                        f"--add-binary={tool_path}{os.pathsep}poppler/bin",
                    ])
                    print(f"  Added: {tool}")
        
        elif system == "Linux":
            # Bundle specific Poppler executables for Linux
            poppler_tools = [
                "pdftotext", "pdftoppm", "pdfinfo", "pdfimages",
                "pdftocairo", "pdftohtml", "pdftops", "pdfunite", "pdfseparate"
            ]
            for tool in poppler_tools:
                tool_path = poppler_path / tool
                if tool_path.exists():
                    cmd.extend([
                        f"--add-binary={tool_path}{os.pathsep}poppler/bin",
                    ])
                    print(f"  Added: {tool}")
    
    # Add license files as data
    license_files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]
    for license_file in license_files:
        if Path(license_file).exists():
            cmd.extend([
                f"--add-data={license_file}{os.pathsep}.",
            ])
            print(f"Including license file: {license_file}")
    
    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*60)
        print("BUILD SUCCESSFUL!")
        print("="*60)
        print(f"\nExecutable location: dist/QuickPdfOcr")
        
        print("\n📦 BUNDLED COMPONENTS:")
        print("  ✓ Python interpreter (users do NOT need Python installed)")
        print("  ✓ All Python packages (PySide6, pytesseract, pdf2image, Pillow, PyPDF2)")
        
        if poppler_path:
            print("  ✓ Poppler binaries (users do NOT need to install Poppler)")
        else:
            print("  ⚠ Poppler NOT bundled (users must install Poppler separately)")
        
        print("\n⚠️  EXTERNAL DEPENDENCIES (must be installed separately):")
        print("  - Tesseract OCR (required for text recognition)")
        print("    - macOS: brew install tesseract")
        print("    - Linux: sudo apt-get install tesseract-ocr")
        print("    - Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        
        print("\n" + "="*60)
        print("The executable is completely standalone and does NOT require")
        print("Python to be installed on the target system!")
        print("="*60)
        
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
