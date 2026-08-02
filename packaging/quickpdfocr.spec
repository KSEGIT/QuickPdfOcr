# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for QuickPdfOcr.

Builds a directory-mode bundle, not --onefile. --onefile unpacks the whole app
to /var/folders/.../T/_MEIxxxx on every launch; that temp directory is where
issue #26's @rpath lookup failed, and re-extracting the bundle each run is slow.

There are no external binaries to bundle any more.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent
IS_MACOS = sys.platform == "darwin"

# universal2 is opt-in via this env var, set by CI after
# packaging/prepare_universal_deps.py has fattened pypdfium2's dylib in
# site-packages and after CI has installed a universal2 interpreter from
# python.org (Homebrew and uv publish arm64-only interpreters for Apple
# Silicon, so a normal local dev venv cannot supply one). PyInstaller errors
# out if target_arch="universal2" is requested while any collected binary --
# including the interpreter itself -- is thin, which is exactly the check we
# want in CI and exactly what we must not impose on an arm64 dev machine.
UNIVERSAL2 = os.environ.get("QUICKPDFOCR_UNIVERSAL2") == "1"
TARGET_ARCH = "universal2" if (IS_MACOS and UNIVERSAL2) else None

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / "resources"), "resources"),
        (str(PROJECT_ROOT / "LICENSE"), "."),
        (str(PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"), "."),
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "pypdfium2",
    ] + ([
        "Vision",
        "Quartz",
        "Foundation",
    ] if IS_MACOS else [
        "pytesseract",
        "PIL",
        "PIL.Image",
    ]),
    hookspath=[],
    runtime_hooks=[],
    # Keep the non-macOS OCR stack out of the macOS bundle entirely. Pillow has
    # no universal2 wheel, so its presence would break the universal2 build.
    excludes=["PIL", "pytesseract", "pdf2image", "PyPDF2"] if IS_MACOS else [],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="QuickPdfOcr",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(PROJECT_ROOT / "resources" / ("icon.icns" if IS_MACOS else "icon.ico")),
    target_arch=TARGET_ARCH,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="QuickPdfOcr",
)

if IS_MACOS:
    app = BUNDLE(
        coll,
        name="QuickPdfOcr.app",
        icon=str(PROJECT_ROOT / "resources" / "icon.icns"),
        bundle_identifier="com.quickpdfocr.app",
        info_plist={
            "CFBundleName": "QuickPdfOcr",
            "CFBundleDisplayName": "QuickPdfOcr",
            "CFBundleShortVersionString": "2.0.0",
            "CFBundleVersion": "2.0.0",
            "LSMinimumSystemVersion": "13.0",
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "See THIRD_PARTY_LICENSES.md",
        },
    )
