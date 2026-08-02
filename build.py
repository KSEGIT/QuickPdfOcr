#!/usr/bin/env python3
"""Build the standalone application.

There is nothing to hunt for on disk any more. PDF rendering ships inside the
pypdfium2 wheel and macOS OCR comes from the operating system, so this script
just drives PyInstaller against packaging/quickpdfocr.spec.

On macOS the result is dist/QuickPdfOcr.app in directory mode. See
packaging/make_universal.py for the universal2 and code-signing steps.
"""

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
        print("\nNEXT STEP: python packaging/make_universal.py")
        print("  (required -- arm64 binaries will not launch unsigned)")
    else:
        print("  [!!] Tesseract must be installed on the target system")


if __name__ == "__main__":
    build()
