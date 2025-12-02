#!/usr/bin/env python3
"""
Create macOS .icns file from PNG
Uses iconutil-compatible iconset structure
"""

import os
import shutil
from pathlib import Path
from PIL import Image

def create_icns_from_png(png_path, output_icns_path):
    """
    Create a macOS .icns file from a PNG image
    
    Args:
        png_path (str): Path to source PNG file (should be at least 512x512)
        output_icns_path (str): Path for output .icns file
    """
    # Load the source image
    img = Image.open(png_path)
    
    # Create an iconset directory
    iconset_dir = Path(output_icns_path).with_suffix('.iconset')
    iconset_dir.mkdir(exist_ok=True)
    
    # Define the required icon sizes for macOS
    # Format: (size, scale, filename)
    icon_sizes = [
        (16, 1, 'icon_16x16.png'),
        (16, 2, 'icon_16x16@2x.png'),
        (32, 1, 'icon_32x32.png'),
        (32, 2, 'icon_32x32@2x.png'),
        (64, 1, 'icon_64x64.png'),  # For older systems
        (128, 1, 'icon_128x128.png'),
        (128, 2, 'icon_128x128@2x.png'),
        (256, 1, 'icon_256x256.png'),
        (256, 2, 'icon_256x256@2x.png'),
        (512, 1, 'icon_512x512.png'),
        (512, 2, 'icon_512x512@2x.png'),
    ]
    
    print(f"Creating iconset in: {iconset_dir}")
    
    # Generate each required size
    for size, scale, filename in icon_sizes:
        actual_size = size * scale
        print(f"  - {filename} ({actual_size}x{actual_size})")
        
        # Resize image
        resized = img.resize((actual_size, actual_size), Image.Resampling.LANCZOS)
        
        # Save to iconset directory
        output_path = iconset_dir / filename
        resized.save(output_path, 'PNG')
    
    print(f"\nIconset created successfully!")
    print(f"Directory: {iconset_dir}")
    
    # Try to convert to .icns using iconutil (only works on macOS)
    try:
        import subprocess
        result = subprocess.run(
            ['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(output_icns_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✅ Successfully created: {output_icns_path}")
            # Clean up iconset directory
            shutil.rmtree(iconset_dir)
            print(f"Cleaned up temporary iconset directory")
        else:
            print(f"\n⚠️  iconutil not available (this is normal on non-macOS systems)")
            print(f"   Iconset directory created: {iconset_dir}")
            print(f"   On macOS, run: iconutil -c icns {iconset_dir} -o {output_icns_path}")
            
            # As a fallback, create a simple .icns from PNG using PIL
            # This won't be as good as iconutil but will work cross-platform
            print(f"\n   Creating basic .icns file using PIL...")
            try:
                # Load the largest size and save as ICNS
                img_1024 = img.resize((1024, 1024), Image.Resampling.LANCZOS)
                img_1024.save(output_icns_path, 'ICNS')
                print(f"   ✅ Created basic .icns: {output_icns_path}")
            except Exception as e:
                print(f"   ⚠️  Could not create .icns: {e}")
                print(f"   You can manually convert the iconset on macOS")
    except FileNotFoundError:
        print(f"\n⚠️  iconutil not found (this is normal on non-macOS systems)")
        print(f"   Iconset directory created: {iconset_dir}")
        print(f"   On macOS, run: iconutil -c icns {iconset_dir} -o {output_icns_path}")
        
        # Create basic .icns using PIL
        print(f"\n   Creating basic .icns file using PIL...")
        try:
            img_1024 = img.resize((1024, 1024), Image.Resampling.LANCZOS)
            img_1024.save(output_icns_path, 'ICNS')
            print(f"   ✅ Created basic .icns: {output_icns_path}")
        except Exception as e:
            print(f"   ⚠️  Could not create .icns: {e}")
            print(f"   You may need to convert the iconset manually on macOS")


def main():
    script_dir = Path(__file__).parent
    
    # Use the high-res PNG as source
    png_path = script_dir / "icon_512.png"
    icns_path = script_dir / "icon.icns"
    
    print("Creating macOS .icns icon...")
    print(f"Source: {png_path}")
    print(f"Output: {icns_path}\n")
    
    if not png_path.exists():
        print(f"Error: Source PNG not found: {png_path}")
        print("Please run generate_icon.py first")
        return 1
    
    create_icns_from_png(str(png_path), str(icns_path))
    
    return 0


if __name__ == "__main__":
    exit(main())
