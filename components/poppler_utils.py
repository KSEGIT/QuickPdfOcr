#!/usr/bin/env python3
"""
Utility module for detecting bundled Poppler and Tesseract binaries
This module helps pdf2image and pytesseract find binaries when bundled with PyInstaller
"""

import os
import sys
from pathlib import Path


def get_bundled_poppler_path():
    """
    Get the path to bundled Poppler binaries if running from PyInstaller bundle
    
    Returns:
        str or None: Path to bundled Poppler bin directory, or None if not found
    """
    # Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        poppler_bin = bundle_dir / "poppler" / "bin"
        
        if poppler_bin.exists():
            return str(poppler_bin)
    
    # Not running from bundle or Poppler not found
    return None


def get_bundled_tesseract_path():
    """
    Get the path to bundled Tesseract executable if running from PyInstaller bundle
    
    Returns:
        str or None: Path to bundled Tesseract executable, or None if not found
    """
    # Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        
        # Check for Tesseract in different locations based on platform
        import platform
        system = platform.system()
        
        if system == "Windows":
            tesseract_exe = bundle_dir / "tesseract" / "tesseract.exe"
        else:
            tesseract_exe = bundle_dir / "tesseract" / "bin" / "tesseract"
        
        if tesseract_exe.exists():
            return str(tesseract_exe)
    
    # Not running from bundle or Tesseract not found
    return None


def setup_poppler_path():
    """
    Setup Poppler path for pdf2image to use bundled binaries
    This should be called at application startup
    
    Returns:
        str or None: Path that was set up, or None if using system Poppler
    """
    bundled_path = get_bundled_poppler_path()
    
    if bundled_path:
        # Add bundled Poppler to PATH so pdf2image can find it
        os.environ['PATH'] = bundled_path + os.pathsep + os.environ.get('PATH', '')
        print(f"Using bundled Poppler from: {bundled_path}")
        
        # Verify critical executables exist
        import platform
        exe_ext = ".exe" if platform.system() == "Windows" else ""
        critical_tools = ["pdftoppm", "pdfinfo"]
        for tool in critical_tools:
            tool_path = Path(bundled_path) / f"{tool}{exe_ext}"
            if tool_path.exists():
                print(f"  ✓ Found: {tool}{exe_ext}")
            else:
                print(f"  ✗ Missing: {tool}{exe_ext}")
        
        return bundled_path
    else:
        print("Using system Poppler installation")
        return None


def setup_tesseract_path():
    """
    Setup Tesseract path for pytesseract to use bundled binaries
    This should be called at application startup
    
    Returns:
        str or None: Path that was set up, or None if using system Tesseract
    """
    bundled_path = get_bundled_tesseract_path()
    
    if bundled_path:
        # Configure pytesseract to use bundled Tesseract
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = bundled_path
            
            # Verify tesseract executable exists
            if Path(bundled_path).exists():
                print(f"✓ Found Tesseract executable: {bundled_path}")
            else:
                print(f"✗ Tesseract executable not found: {bundled_path}")
            
            # Set TESSDATA_PREFIX for bundled tessdata
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                bundle_dir = Path(sys._MEIPASS)
                tessdata_path = bundle_dir / "tesseract" / "tessdata"
                if tessdata_path.exists():
                    os.environ['TESSDATA_PREFIX'] = str(bundle_dir / "tesseract")
                    
                    # Count language files
                    traineddata_files = list(tessdata_path.glob("*.traineddata"))
                    print(f"  ✓ Found tessdata directory with {len(traineddata_files)} language file(s)")
                    
                    # List language files
                    for lang_file in traineddata_files[:5]:  # Show first 5
                        print(f"    - {lang_file.name}")
                    if len(traineddata_files) > 5:
                        print(f"    ... and {len(traineddata_files) - 5} more")
                else:
                    print(f"  ✗ tessdata directory not found: {tessdata_path}")
            
            print(f"Using bundled Tesseract from: {bundled_path}")
            return bundled_path
        except ImportError:
            print("Warning: pytesseract not found, cannot configure bundled Tesseract")
            return None
    else:
        print("Using system Tesseract installation")
        return None


def setup_bundled_binaries():
    """
    Setup all bundled binaries (Poppler and Tesseract)
    This is a convenience function to call at application startup
    """
    setup_poppler_path()
    setup_tesseract_path()
