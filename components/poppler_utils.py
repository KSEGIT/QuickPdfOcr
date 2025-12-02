#!/usr/bin/env python3
"""
Utility module for detecting bundled Poppler and Tesseract binaries
This module helps pdf2image and pytesseract find binaries when bundled with PyInstaller
"""

import os
import sys
from pathlib import Path

# Maximum number of items to display when listing directory contents for diagnostics
MAX_DIAGNOSTIC_ITEMS = 20
# Maximum number of language files to display individually
MAX_LANGUAGE_FILES_TO_SHOW = 5


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
                tesseract_dir = bundle_dir / "tesseract"
                tessdata_path = tesseract_dir / "tessdata"
                
                print(f"  Checking for tessdata at: {tessdata_path}")
                
                if tessdata_path.exists() and tessdata_path.is_dir():
                    # TESSDATA_PREFIX must point to the directory that CONTAINS the tessdata folder
                    # For Tesseract to find tessdata/, TESSDATA_PREFIX should end with a path separator
                    # or point to the parent directory. We use os.path.join to ensure proper separator.
                    tessdata_prefix = os.path.join(os.path.abspath(str(tesseract_dir)), '')
                    os.environ['TESSDATA_PREFIX'] = tessdata_prefix
                    
                    # Also try setting alternative environment variables for compatibility
                    # Some Tesseract versions look for different variables
                    os.environ['TESSDATA_DIR'] = os.path.abspath(str(tessdata_path))
                    
                    # Count language files
                    traineddata_files = list(tessdata_path.glob("*.traineddata"))
                    print(f"  ✓ Found tessdata directory with {len(traineddata_files)} language file(s)")
                    print(f"  ✓ TESSDATA_PREFIX set to: {tessdata_prefix}")
                    print(f"  ✓ TESSDATA_DIR set to: {os.environ['TESSDATA_DIR']}")
                    
                    # List language files (limited to avoid excessive output)
                    for lang_file in traineddata_files[:MAX_LANGUAGE_FILES_TO_SHOW]:
                        print(f"    - {lang_file.name}")
                    if len(traineddata_files) > MAX_LANGUAGE_FILES_TO_SHOW:
                        print(f"    ... and {len(traineddata_files) - MAX_LANGUAGE_FILES_TO_SHOW} more")
                else:
                    print(f"  ✗ tessdata directory not found at: {tessdata_path}")
                    print(f"  Listing contents of bundle tesseract directory:")
                    if tesseract_dir.exists():
                        for item in sorted(tesseract_dir.iterdir())[:MAX_DIAGNOSTIC_ITEMS]:
                            item_type = "DIR" if item.is_dir() else "FILE"
                            print(f"    - [{item_type}] {item.name}")
                    else:
                        print(f"  ✗ Bundle tesseract directory not found!")
                        print(f"  Listing contents of bundle root:")
                        for item in sorted(bundle_dir.iterdir())[:MAX_DIAGNOSTIC_ITEMS]:
                            item_type = "DIR" if item.is_dir() else "FILE"
                            print(f"    - [{item_type}] {item.name}")
            
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
