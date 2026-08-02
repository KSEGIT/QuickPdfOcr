#!/usr/bin/env python3
"""Build the standalone application.

There is nothing to hunt for on disk any more. PDF rendering ships inside the
pypdfium2 wheel and macOS OCR comes from the operating system, so this script
just drives PyInstaller against packaging/quickpdfocr.spec.

On macOS the result is dist/QuickPdfOcr.app in directory mode. By default this
is a thin, architecture-specific build for local development -- launching it
requires the PyInstaller-freezing interpreter to already be universal2, which
a normal local Homebrew/uv venv is not, and PyInstaller freezes the host
interpreter rather than producing one. Set QUICKPDFOCR_UNIVERSAL2=1 (which
packaging/quickpdfocr.spec reads) to build universal2 instead; that requires
running packaging/prepare_universal_deps.py first and a universal2
interpreter to run this script with. See packaging/verify_universal.py for
the architecture-census gate and code-signing step that follows either build.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
SPEC_FILE = PROJECT_ROOT / "packaging" / "quickpdfocr.spec"


def build() -> None:
    """Run PyInstaller and report what was produced."""
    system = platform.system()
    print(f"Building for {system} ({platform.machine()})...")

    if not SPEC_FILE.exists():
        print(f"Spec file not found: {SPEC_FILE}", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", str(SPEC_FILE)]

    print("\n" + "=" * 60)
    print("STARTING PYINSTALLER BUILD")
    print("=" * 60)
    print("This may take several minutes...\n")

    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
    except subprocess.CalledProcessError as exc:
        print(f"\nBuild failed: {exc}", file=sys.stderr)
        sys.exit(1)

    artifact = (
        PROJECT_ROOT / "dist" / "QuickPdfOcr.app"
        if system == "Darwin"
        else PROJECT_ROOT / "dist" / "QuickPdfOcr"
    )

    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL")
    print("=" * 60)
    print(f"\nArtifact: {artifact}")
    print("\nBUNDLED COMPONENTS:")
    print("  [OK] Python interpreter")
    print("  [OK] PySide6")
    print("  [OK] PDFium (via pypdfium2) -- no Poppler needed")
    if system == "Darwin":
        print("  [OK] OCR via the OS's Vision framework -- no Tesseract needed")
        if os.environ.get("QUICKPDFOCR_UNIVERSAL2") == "1":
            print("\nBuilt with QUICKPDFOCR_UNIVERSAL2=1 (universal2 requested).")
            print("NEXT STEP: python packaging/verify_universal.py")
            print("  (required -- verifies universal2 and signs; unsigned")
            print("  arm64 binaries will not launch)")
        else:
            print(f"\nThis is an {platform.machine()}-only build for local development.")
            print("It will not launch on the other Mac architecture, and it is not")
            print("code-signed, so it is NOT distributable. Release artifacts are")
            print("built universal2 and signed in CI -- see")
            print("packaging/prepare_universal_deps.py, the target_arch handling")
            print("in packaging/quickpdfocr.spec, and packaging/verify_universal.py.")
            print("\nNEXT STEP (still required locally): python packaging/verify_universal.py")
            print("  (signs the app; unsigned arm64 binaries will not launch)")
    else:
        print("  [!!] Tesseract must be installed on the target system")


if __name__ == "__main__":
    build()
