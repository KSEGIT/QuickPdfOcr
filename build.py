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


def find_tesseract_binaries():
    """
    Find Tesseract binaries to bundle with the executable
    
    Returns:
        Path or None: Path to Tesseract installation directory, or None if not found
    """
    system = platform.system()
    
    # Check for pre-downloaded binaries in tesseract_binaries directory
    tesseract_dir = Path("tesseract_binaries")
    if tesseract_dir.exists():
        print(f"Found Tesseract binaries in: {tesseract_dir}")
        return tesseract_dir
    
    # Try to find system Tesseract installation
    if system == "Darwin":  # macOS
        # Check Homebrew installation paths
        homebrew_paths = [
            Path("/opt/homebrew"),  # ARM64 Homebrew
            Path("/usr/local"),     # Intel Homebrew
        ]
        for path in homebrew_paths:
            tesseract_bin = path / "bin" / "tesseract"
            if tesseract_bin.exists():
                print(f"Found system Tesseract in: {path}")
                return path
    
    elif system == "Linux":
        # Check common Linux installation paths
        if Path("/usr/bin/tesseract").exists():
            print("Found system Tesseract in: /usr")
            return Path("/usr")
    
    elif system == "Windows":
        # Check common Windows Tesseract installation paths
        common_paths = [
            Path("C:/Program Files/Tesseract-OCR"),
            Path("C:/Program Files (x86)/Tesseract-OCR"),
        ]
        for path in common_paths:
            if (path / "tesseract.exe").exists():
                print(f"Found system Tesseract in: {path}")
                return path
    
    print("Warning: Tesseract binaries not found. They will not be bundled.")
    print("Users will need to install Tesseract separately.")
    return None



def build_executable():
    """Build standalone executable using PyInstaller"""
    
    system = platform.system()
    print(f"Building for {system}...")
    
    # Find Poppler and Tesseract binaries
    poppler_path = find_poppler_binaries()
    tesseract_path = find_tesseract_binaries()
    
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
    
    # Add icon based on platform
    if system == "Darwin":  # macOS
        cmd.extend(["--icon=resources/icon.icns"])
    elif system == "Windows":
        cmd.extend(["--icon=resources/icon.ico"])
    elif system == "Linux":
        cmd.extend(["--icon=resources/icon.png"])
    
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
                # Bundle all files from Library/bin directory
                for item in bin_path.glob("*"):
                    if item.is_file():
                        cmd.extend([
                            f"--add-binary={item}{os.pathsep}poppler/bin",
                        ])
                print(f"  Added: {bin_path} (all files)")
            else:
                # If not in Library/bin, try direct bin folder
                bin_path = poppler_path / "bin"
                if bin_path.exists():
                    for item in bin_path.glob("*"):
                        if item.is_file():
                            cmd.extend([
                                f"--add-binary={item}{os.pathsep}poppler/bin",
                            ])
                    print(f"  Added: {bin_path} (all files)")
        
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
    
    # Bundle Tesseract binaries if found
    if tesseract_path:
        print(f"\nBundling Tesseract binaries from: {tesseract_path}")
        
        if system == "Windows":
            # For Windows, bundle tesseract.exe and all DLLs
            if (tesseract_path / "tesseract.exe").exists():
                cmd.extend([
                    f"--add-binary={tesseract_path / 'tesseract.exe'}{os.pathsep}tesseract",
                ])
                print(f"  Added: tesseract.exe")
                
                # Add all DLLs
                dll_count = 0
                for dll in tesseract_path.glob("*.dll"):
                    cmd.extend([
                        f"--add-binary={dll}{os.pathsep}tesseract",
                    ])
                    dll_count += 1
                if dll_count > 0:
                    print(f"  Added: {dll_count} DLL files")
                
                # Add tessdata directory if it exists
                tessdata_path = tesseract_path / "tessdata"
                if tessdata_path.exists() and tessdata_path.is_dir():
                    # Count language files
                    traineddata_files = list(tessdata_path.glob("*.traineddata"))
                    if not traineddata_files:
                        print(f"  Warning: tessdata directory found but contains no .traineddata files!")
                        print(f"  Please ensure language files are installed in: {tessdata_path}")
                    else:
                        # Convert Path to string and normalize separators for the platform
                        tessdata_str = str(tessdata_path)
                        cmd.extend([
                            f"--add-data={tessdata_str}{os.pathsep}tesseract/tessdata",
                        ])
                        print(f"  Added: tessdata directory ({len(traineddata_files)} language files)")
                        print(f"  Source: {tessdata_str}")
                        print(f"  Destination in bundle: tesseract/tessdata")
                else:
                    print(f"  Warning: tessdata directory not found at: {tesseract_path / 'tessdata'}")
                    print(f"  OCR will not work in the bundled executable!")
                    print(f"  Please install Tesseract language data files.")
        
        elif system == "Darwin":  # macOS
            # Bundle Tesseract executable and data
            tesseract_bin = tesseract_path / "bin" / "tesseract"
            if tesseract_bin.exists():
                cmd.extend([
                    f"--add-binary={tesseract_bin}{os.pathsep}tesseract/bin",
                ])
                print(f"  Added: tesseract binary")
            
            # Add tessdata directory - try multiple possible locations
            tessdata_locations = [
                tesseract_path / "share" / "tessdata",  # Homebrew standard location
                tesseract_path / "share" / "tesseract-ocr" / "tessdata",  # Alternative location
            ]
            
            tessdata_path = None
            for loc in tessdata_locations:
                if loc.exists():
                    tessdata_path = loc
                    break
            
            if tessdata_path:
                # Count language files
                traineddata_files = list(tessdata_path.glob("*.traineddata"))
                # Convert Path to string for PyInstaller
                tessdata_str = str(tessdata_path)
                cmd.extend([
                    f"--add-data={tessdata_str}{os.pathsep}tesseract/tessdata",
                ])
                print(f"  Added: tessdata directory ({len(traineddata_files)} language files)")
                print(f"  Source: {tessdata_str}")
                print(f"  Destination in bundle: tesseract/tessdata")
            else:
                print(f"  Warning: tessdata directory not found in any expected location")
        
        elif system == "Linux":
            # Bundle Tesseract executable and data
            tesseract_bin = tesseract_path / "bin" / "tesseract"
            if tesseract_bin.exists():
                cmd.extend([
                    f"--add-binary={tesseract_bin}{os.pathsep}tesseract/bin",
                ])
                print(f"  Added: tesseract binary")
            
            # Add tessdata directory - try multiple possible locations
            tessdata_locations = [
                tesseract_path / "share" / "tessdata",  # Old location
                tesseract_path / "share" / "tesseract-ocr" / "5" / "tessdata",  # Ubuntu 24.04+
                tesseract_path / "share" / "tesseract-ocr" / "4" / "tessdata",  # Ubuntu 20.04
                tesseract_path / "share" / "tesseract-ocr" / "tessdata",  # Generic
            ]
            
            tessdata_path = None
            for loc in tessdata_locations:
                if loc.exists():
                    tessdata_path = loc
                    break
            
            if tessdata_path:
                # Count language files
                traineddata_files = list(tessdata_path.glob("*.traineddata"))
                # Convert Path to string for PyInstaller
                tessdata_str = str(tessdata_path)
                cmd.extend([
                    f"--add-data={tessdata_str}{os.pathsep}tesseract/tessdata",
                ])
                print(f"  Added: tessdata directory ({len(traineddata_files)} language files)")
                print(f"  Source: {tessdata_str}")
                print(f"  Destination in bundle: tesseract/tessdata")
            else:
                print(f"  Warning: tessdata directory not found in any expected location")
    
    # Add license files as data
    license_files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]
    for license_file in license_files:
        if Path(license_file).exists():
            cmd.extend([
                f"--add-data={license_file}{os.pathsep}.",
            ])
            print(f"Including license file: {license_file}")
    
    # Add resources directory (icons)
    resources_dir = Path("resources")
    if resources_dir.exists():
        cmd.extend([
            f"--add-data={resources_dir}{os.pathsep}resources",
        ])
        print(f"Including resources directory: {resources_dir}")
    
    # Run PyInstaller
    try:
        print("\n" + "="*60)
        print("STARTING PYINSTALLER BUILD")
        print("="*60)
        print("This may take several minutes...\n")
        
        subprocess.run(cmd, check=True)
        
        print("\n" + "="*60)
        print("BUILD SUCCESSFUL!")
        print("="*60)
        print(f"\nExecutable location: dist/QuickPdfOcr")
        
        print("\nBUNDLED COMPONENTS:")
        print("  [OK] Python interpreter (users do NOT need Python installed)")
        print("  [OK] All Python packages (PySide6, pytesseract, pdf2image, Pillow, PyPDF2)")
        
        if poppler_path:
            print("  [OK] Poppler binaries (users do NOT need to install Poppler)")
        else:
            print("  [WARN] Poppler NOT bundled (users must install Poppler separately)")
        
        if tesseract_path:
            print("  [OK] Tesseract OCR (users do NOT need to install Tesseract)")
        else:
            print("  [WARN] Tesseract NOT bundled (users must install Tesseract separately)")
        
        if not poppler_path or not tesseract_path:
            print("\n[WARNING] EXTERNAL DEPENDENCIES (must be installed separately):")
            if not poppler_path:
                print("  - Poppler (for PDF processing)")
            if not tesseract_path:
                print("  - Tesseract OCR (required for text recognition)")
            print("\nInstallation instructions:")
            print("    - macOS: brew install tesseract" if not tesseract_path else "")
            if not poppler_path:
                print("    - macOS: brew install poppler")
            print("    - Linux: sudo apt-get install tesseract-ocr" if not tesseract_path else "")
            if not poppler_path:
                print("    - Linux: sudo apt-get install poppler-utils")
            print("    - Windows: https://github.com/UB-Mannheim/tesseract/wiki" if not tesseract_path else "")
            if not poppler_path:
                print("    - Windows: https://github.com/oschwartz10612/poppler-windows/releases/")
        else:
            print("\nALL DEPENDENCIES BUNDLED!")
            print("   Users can run the executable without any additional installations!")
        
        print("\n" + "="*60)
        print("The executable is completely standalone and does NOT require")
        print("Python to be installed on the target system!")
        print("="*60)
        
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
