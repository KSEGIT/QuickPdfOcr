#!/usr/bin/env python3
"""
Utility module for detecting bundled Poppler binaries
This module helps pdf2image find Poppler when bundled with PyInstaller
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
        return bundled_path
    else:
        print("Using system Poppler installation")
        return None
