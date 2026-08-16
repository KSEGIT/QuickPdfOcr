#!/usr/bin/env python3
"""
Create macOS .icns file from pre-rendered PNGs
Uses iconutil-compatible iconset structure
"""

import shutil
import subprocess
from pathlib import Path

ICONSET_SLOTS = [
    (16, 1, 'icon_16x16.png'),
    (16, 2, 'icon_16x16@2x.png'),
    (32, 1, 'icon_32x32.png'),
    (32, 2, 'icon_32x32@2x.png'),
    (64, 1, 'icon_64x64.png'),
    (128, 1, 'icon_128x128.png'),
    (128, 2, 'icon_128x128@2x.png'),
    (256, 1, 'icon_256x256.png'),
    (256, 2, 'icon_256x256@2x.png'),
    (512, 1, 'icon_512x512.png'),
    (512, 2, 'icon_512x512@2x.png'),
]


def create_icns_from_pngs(png_by_size, output_icns_path):
    """Build a macOS .icns from PNGs already rendered at each exact size.

    Every slot is copied, never resized: the point of the two-master
    pipeline is that a 16pt slot carries different art from a 512pt slot,
    which downscaling would destroy.

    Args:
        png_by_size: {pixel_size: Path} covering every size in ICONSET_SLOTS.
        output_icns_path: destination .icns path.
    """
    iconset_dir = Path(output_icns_path).with_suffix('.iconset')
    iconset_dir.mkdir(exist_ok=True)

    for size, scale, filename in ICONSET_SLOTS:
        pixels = size * scale
        source = png_by_size.get(pixels)
        if source is None:
            raise KeyError(
                f"no rendered PNG for {pixels}px (slot {filename}); "
                f"have {sorted(png_by_size)}"
            )
        shutil.copyfile(source, iconset_dir / filename)
        print(f"  - {filename} ({pixels}x{pixels}) <- {Path(source).name}")

    result = subprocess.run(
        ['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(output_icns_path)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        shutil.rmtree(iconset_dir)
        print(f"Created: {output_icns_path}")
        return

    raise RuntimeError(
        f"iconutil failed ({result.returncode}): {result.stderr.strip()}\n"
        f"Iconset retained at {iconset_dir} for manual conversion on macOS."
    )
