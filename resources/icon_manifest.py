"""Size -> source-master mapping for the icon render pipeline.

Split out of render_icons.py so it can be imported with zero optional
dependencies (no Playwright, no Pillow). render_icons.py imports these
constants rather than redefining them, and tests/test_icon_outputs.py
imports this module directly so the size->master mapping assertions run in
every CI job -- including macOS, where Pillow is never installed
(requirements.txt gates it behind sys_platform != 'darwin') -- rather than
only on a machine with the full asset-authoring toolchain installed.
"""

from pathlib import Path

RESOURCES = Path(__file__).resolve().parent
DETAILED = RESOURCES / "icon.svg"
SIMPLE = RESOURCES / "icon_small.svg"

# The detailed master (icon.svg) feeds 128px and above; the simplified
# master (icon_small.svg) feeds 64px and below, so Dock, taskbar and
# favicon sizes stay legible instead of becoming a smear of the large art.
SIZE_SOURCES = {
    16: SIMPLE,
    32: SIMPLE,
    48: SIMPLE,
    64: SIMPLE,
    128: DETAILED,
    256: DETAILED,
    512: DETAILED,
    1024: DETAILED,
}

ICO_SIZES = [16, 32, 48, 64, 128, 256]
