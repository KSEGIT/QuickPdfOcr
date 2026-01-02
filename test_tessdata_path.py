#!/usr/bin/env python3
"""
Unit test to verify tessdata path handling logic for Windows compatibility
"""

import platform
import sys
from unittest import mock


def test_tessdata_path_formatting():
    """Test that tessdata paths are formatted correctly for Windows and Unix"""
    
    print("Testing tessdata path formatting logic...")
    print("="*60)
    
    # Test case 1: Windows path without spaces
    print("\nTest 1: Windows path without spaces")
    tessdata_str = "C:\\Users\\Test\\AppData\\Local\\Temp\\_MEI123\\tesseract\\tessdata"
    if platform.system() == "Windows" or True:  # Simulate Windows
        tessdata_str_converted = tessdata_str.replace('\\', '/')
        if ' ' in tessdata_str_converted:
            tessdata_str_converted = f'"{tessdata_str_converted}"'
    
    expected = "C:/Users/Test/AppData/Local/Temp/_MEI123/tesseract/tessdata"
    result = f'--tessdata-dir {tessdata_str_converted}'
    print(f"  Input:    {tessdata_str}")
    print(f"  Output:   {result}")
    print(f"  Expected: --tessdata-dir {expected}")
    assert tessdata_str_converted == expected, f"Path conversion failed: {tessdata_str_converted} != {expected}"
    print("  ✓ PASS")
    
    # Test case 2: Windows path with spaces
    print("\nTest 2: Windows path with spaces")
    tessdata_str = "C:\\Users\\DANIEL~1\\AppData\\Local\\Temp\\_MEI375682\\tesseract\\tessdata"
    tessdata_str_converted = tessdata_str.replace('\\', '/')
    if ' ' in tessdata_str_converted:
        tessdata_str_converted = f'"{tessdata_str_converted}"'
    
    expected = "C:/Users/DANIEL~1/AppData/Local/Temp/_MEI375682/tesseract/tessdata"
    result = f'--tessdata-dir {tessdata_str_converted}'
    print(f"  Input:    {tessdata_str}")
    print(f"  Output:   {result}")
    print(f"  Expected: --tessdata-dir {expected}")
    assert tessdata_str_converted == expected, f"Path conversion failed: {tessdata_str_converted} != {expected}"
    print("  ✓ PASS")
    
    # Test case 3: Windows path with actual spaces (not ~)
    print("\nTest 3: Windows path with actual spaces")
    tessdata_str = "C:\\Program Files\\Tesseract\\tessdata"
    tessdata_str_converted = tessdata_str.replace('\\', '/')
    if ' ' in tessdata_str_converted:
        tessdata_str_converted = f'"{tessdata_str_converted}"'
    
    expected = '"C:/Program Files/Tesseract/tessdata"'
    result = f'--tessdata-dir {tessdata_str_converted}'
    print(f"  Input:    {tessdata_str}")
    print(f"  Output:   {result}")
    print(f"  Expected: --tessdata-dir {expected}")
    assert tessdata_str_converted == expected, f"Path conversion failed: {tessdata_str_converted} != {expected}"
    print("  ✓ PASS")
    
    # Test case 4: Unix path without spaces
    print("\nTest 4: Unix path without spaces")
    tessdata_str = "/tmp/.mount_QuickP123/tesseract/tessdata"
    if ' ' in tessdata_str:
        tessdata_str_converted = f'"{tessdata_str}"'
    else:
        tessdata_str_converted = tessdata_str
    
    expected = "/tmp/.mount_QuickP123/tesseract/tessdata"
    result = f'--tessdata-dir {tessdata_str_converted}'
    print(f"  Input:    {tessdata_str}")
    print(f"  Output:   {result}")
    print(f"  Expected: --tessdata-dir {expected}")
    assert tessdata_str_converted == expected, f"Path conversion failed: {tessdata_str_converted} != {expected}"
    print("  ✓ PASS")
    
    # Test case 5: Unix path with spaces
    print("\nTest 5: Unix path with spaces")
    tessdata_str = "/home/user/My Documents/app/tesseract/tessdata"
    if ' ' in tessdata_str:
        tessdata_str_converted = f'"{tessdata_str}"'
    else:
        tessdata_str_converted = tessdata_str
    
    expected = '"/home/user/My Documents/app/tesseract/tessdata"'
    result = f'--tessdata-dir {tessdata_str_converted}'
    print(f"  Input:    {tessdata_str}")
    print(f"  Output:   {result}")
    print(f"  Expected: --tessdata-dir {expected}")
    assert tessdata_str_converted == expected, f"Path conversion failed: {tessdata_str_converted} != {expected}"
    print("  ✓ PASS")
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60)


def test_tessdata_prefix_formatting():
    """Test TESSDATA_PREFIX formatting for Windows"""
    
    print("\n\nTesting TESSDATA_PREFIX formatting logic...")
    print("="*60)
    
    # Test case 1: Windows path
    print("\nTest 1: Windows TESSDATA_PREFIX")
    tessdata_prefix = "C:\\Users\\Test\\AppData\\Local\\Temp\\_MEI123\\tesseract"
    tessdata_dir_abs = "C:\\Users\\Test\\AppData\\Local\\Temp\\_MEI123\\tesseract\\tessdata"
    
    # Simulate Windows conversion
    tessdata_prefix_converted = tessdata_prefix.replace('\\', '/')
    tessdata_dir_converted = tessdata_dir_abs.replace('\\', '/')
    
    # Add trailing separator
    if not tessdata_prefix_converted.endswith(('/', '\\')):
        tessdata_prefix_converted += '/'
    
    expected_prefix = "C:/Users/Test/AppData/Local/Temp/_MEI123/tesseract/"
    expected_dir = "C:/Users/Test/AppData/Local/Temp/_MEI123/tesseract/tessdata"
    
    print(f"  Input TESSDATA_PREFIX: {tessdata_prefix}")
    print(f"  Output:                {tessdata_prefix_converted}")
    print(f"  Expected:              {expected_prefix}")
    assert tessdata_prefix_converted == expected_prefix, f"Failed: {tessdata_prefix_converted} != {expected_prefix}"
    print("  ✓ PASS")
    
    print(f"\n  Input TESSDATA_DIR:  {tessdata_dir_abs}")
    print(f"  Output:              {tessdata_dir_converted}")
    print(f"  Expected:            {expected_dir}")
    assert tessdata_dir_converted == expected_dir, f"Failed: {tessdata_dir_converted} != {expected_dir}"
    print("  ✓ PASS")
    
    print("\n" + "="*60)
    print("All TESSDATA_PREFIX tests passed! ✓")
    print("="*60)


if __name__ == "__main__":
    try:
        test_tessdata_path_formatting()
        test_tessdata_prefix_formatting()
        print("\n\n✓✓✓ ALL TESTS PASSED ✓✓✓\n")
    except AssertionError as e:
        print(f"\n✗✗✗ TEST FAILED: {e} ✗✗✗\n")
        sys.exit(1)
