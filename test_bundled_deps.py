#!/usr/bin/env python3
"""
Test script to verify bundled dependencies are properly configured
This helps diagnose issues with Poppler and Tesseract in the bundled executable
"""

import sys
import os
from pathlib import Path


def test_bundle_detection():
    """Test if running from PyInstaller bundle"""
    print("="*60)
    print("BUNDLE DETECTION TEST")
    print("="*60)
    
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        print(f"✓ Running from PyInstaller bundle")
        print(f"  Bundle directory: {sys._MEIPASS}")
        bundle_dir = Path(sys._MEIPASS)
        
        # List contents of bundle directory
        print("\nBundle directory contents:")
        for item in sorted(bundle_dir.iterdir())[:20]:  # Show first 20 items
            print(f"  - {item.name}")
        
        return bundle_dir
    else:
        print(f"✗ Running from Python interpreter (not bundled)")
        return None


def test_poppler():
    """Test Poppler binaries"""
    print("\n" + "="*60)
    print("POPPLER TEST")
    print("="*60)
    
    from components.poppler_utils import get_bundled_poppler_path, setup_poppler_path
    
    bundled_path = get_bundled_poppler_path()
    if bundled_path:
        print(f"✓ Bundled Poppler path: {bundled_path}")
        
        # Check if directory exists
        poppler_dir = Path(bundled_path)
        if poppler_dir.exists():
            print(f"  ✓ Directory exists")
            
            # List contents
            print(f"\n  Directory contents:")
            for item in sorted(poppler_dir.iterdir())[:10]:  # Show first 10
                print(f"    - {item.name}")
            
            # Check for critical executables
            import platform
            exe_ext = ".exe" if platform.system() == "Windows" else ""
            critical_tools = ["pdftoppm", "pdfinfo"]
            
            print(f"\n  Critical executables:")
            for tool in critical_tools:
                tool_path = poppler_dir / f"{tool}{exe_ext}"
                if tool_path.exists():
                    print(f"    ✓ {tool}{exe_ext} found")
                else:
                    print(f"    ✗ {tool}{exe_ext} MISSING")
        else:
            print(f"  ✗ Directory does not exist!")
    else:
        print(f"✗ No bundled Poppler found (will use system Poppler)")
    
    # Setup Poppler
    print(f"\nSetting up Poppler path...")
    setup_poppler_path()
    
    # Test pdf2image
    print(f"\nTesting pdf2image import...")
    try:
        from pdf2image import convert_from_path
        print(f"  ✓ pdf2image imported successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import pdf2image: {e}")


def test_tesseract():
    """Test Tesseract binaries"""
    print("\n" + "="*60)
    print("TESSERACT TEST")
    print("="*60)
    
    from components.poppler_utils import get_bundled_tesseract_path, setup_tesseract_path
    
    bundled_path = get_bundled_tesseract_path()
    if bundled_path:
        print(f"✓ Bundled Tesseract path: {bundled_path}")
        
        # Check if executable exists
        tesseract_exe = Path(bundled_path)
        if tesseract_exe.exists():
            print(f"  ✓ Executable exists")
            print(f"  File size: {tesseract_exe.stat().st_size:,} bytes")
        else:
            print(f"  ✗ Executable does not exist!")
        
        # Check tessdata directory
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundle_dir = Path(sys._MEIPASS)
            tessdata_path = bundle_dir / "tesseract" / "tessdata"
            
            if tessdata_path.exists():
                traineddata_files = list(tessdata_path.glob("*.traineddata"))
                print(f"  ✓ tessdata directory found with {len(traineddata_files)} language file(s)")
                
                # List language files
                for lang_file in traineddata_files:
                    print(f"    - {lang_file.name}")
            else:
                print(f"  ✗ tessdata directory not found at: {tessdata_path}")
    else:
        print(f"✗ No bundled Tesseract found (will use system Tesseract)")
    
    # Setup Tesseract
    print(f"\nSetting up Tesseract path...")
    setup_tesseract_path()
    
    # Test pytesseract
    print(f"\nTesting pytesseract import...")
    try:
        import pytesseract
        print(f"  ✓ pytesseract imported successfully")
        print(f"  Tesseract command: {pytesseract.pytesseract.tesseract_cmd}")
        
        # Check TESSDATA_PREFIX
        tessdata_prefix = os.environ.get('TESSDATA_PREFIX', 'Not set')
        print(f"  TESSDATA_PREFIX: {tessdata_prefix}")
    except ImportError as e:
        print(f"  ✗ Failed to import pytesseract: {e}")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "DEPENDENCY TEST SUITE" + " "*22 + "║")
    print("╚" + "="*58 + "╝")
    print()
    
    # Run tests
    bundle_dir = test_bundle_detection()
    test_poppler()
    test_tesseract()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if bundle_dir:
        print("Running from bundle: YES")
    else:
        print("Running from bundle: NO (development mode)")
    
    print("\nIf you see any ✗ marks above, those indicate missing or")
    print("misconfigured dependencies that need to be fixed.")
    print("\n" + "="*60 + "\n")
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
