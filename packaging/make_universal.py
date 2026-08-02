#!/usr/bin/env python3
"""Make dist/QuickPdfOcr.app universal2, then ad-hoc sign it.

Wheel arch survey as of pypdfium2 5.12 / PySide6 6.11:

    PySide6                 universal2 wheel     -- nothing to do
    pyobjc Vision/Quartz    universal2 wheels    -- nothing to do
    pypdfium2               arm64 and x86_64     -- must be lipo-merged

Pillow is the other non-universal2 dependency, which is why the macOS build
excludes it entirely; if it reappears in the bundle this script will say so.

Signing is not optional. lipo invalidates any existing signature, and arm64
binaries do not execute unsigned on Apple Silicon. Ad-hoc signing (--sign -)
needs no Apple Developer account. It does NOT notarize: users downloading from
GitHub will still see a Gatekeeper prompt on first launch.
"""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
APP = PROJECT_ROOT / "dist" / "QuickPdfOcr.app"
PDFIUM_NAME = "libpdfium.dylib"
PYPDFIUM2_VERSION = "5.12.1"


def run(cmd, **kwargs) -> subprocess.CompletedProcess:
    """Run a command, echoing it, and raise on failure."""
    print(f"  $ {' '.join(str(part) for part in cmd)}")
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def find_pdfium() -> Path:
    """Locate the bundled libpdfium.dylib inside the .app.

    PyInstaller's macOS app-bundle layout puts real binaries under
    Contents/Frameworks/ and symlinks them into Contents/Resources/ (that is
    the standard bundle convention: Frameworks holds shared libraries,
    Resources mirrors them for lookup). A plain rglob() for libpdfium.dylib
    therefore always finds two hits for one real file -- the Frameworks
    original and the Resources symlink -- so symlinks must be filtered out
    before the "how many did we find" checks below, or a correctly built
    bundle would always trip the "multiple found" error.
    """
    matches = [p for p in APP.rglob(PDFIUM_NAME) if not p.is_symlink()]
    if not matches:
        raise SystemExit(f"{PDFIUM_NAME} not found in {APP}")
    if len(matches) > 1:
        raise SystemExit(f"Multiple {PDFIUM_NAME} found: {matches}")
    return matches[0]


def architectures(binary: Path) -> set:
    """Architectures present in a Mach-O file."""
    output = run(["lipo", "-info", str(binary)]).stdout
    return set(output.strip().split(":")[-1].split())


def download_other_arch(target: str, into: Path) -> Path:
    """Download the opposite-architecture pypdfium2 wheel and extract its dylib."""
    run([
        sys.executable, "-m", "pip", "download",
        f"pypdfium2=={PYPDFIUM2_VERSION}",
        "--only-binary=:all:",
        f"--platform=macosx_13_0_{target}",
        "--python-version=3.12",
        "--no-deps",
        "-d", str(into),
    ])
    wheels = list(into.glob("*.whl"))
    if not wheels:
        raise SystemExit(f"No pypdfium2 wheel downloaded for {target}")

    extracted = into / "extracted"
    with zipfile.ZipFile(wheels[0]) as archive:
        archive.extractall(extracted)

    dylibs = list(extracted.rglob(PDFIUM_NAME))
    if not dylibs:
        raise SystemExit(f"No {PDFIUM_NAME} inside {wheels[0].name}")
    return dylibs[0]


def check_no_thin_dependencies() -> None:
    """Fail loudly if a non-universal2 package slipped into the bundle."""
    # Same Frameworks/Resources symlink layout as find_pdfium() above: a real
    # PIL directory would also appear as a Resources symlink, so filter those
    # out to avoid reporting the same stray twice.
    strays = [
        p for p in APP.rglob("*")
        if p.is_dir() and p.name == "PIL" and not p.is_symlink()
    ]
    if strays:
        raise SystemExit(
            f"Pillow is present in the bundle ({strays[0]}); it has no "
            "universal2 wheel. Check that nothing imports PIL on macOS."
        )


def main() -> int:
    if not APP.exists():
        raise SystemExit(f"{APP} not found; run python build.py first")

    print("Checking for non-universal2 dependencies...")
    check_no_thin_dependencies()

    pdfium = find_pdfium()
    present = architectures(pdfium)
    print(f"Bundled {PDFIUM_NAME} architectures: {sorted(present)}")

    if {"arm64", "x86_64"} <= present:
        print("Already universal2; skipping merge.")
    else:
        missing = "x86_64" if "arm64" in present else "arm64"
        print(f"Merging in {missing}...")
        with tempfile.TemporaryDirectory() as tmp:
            other = download_other_arch(missing, Path(tmp))
            merged = Path(tmp) / "merged.dylib"
            run(["lipo", "-create", str(pdfium), str(other), "-output", str(merged)])
            shutil.copy2(merged, pdfium)

        merged_arches = architectures(pdfium)
        if not {"arm64", "x86_64"} <= merged_arches:
            raise SystemExit(f"Merge failed; got {sorted(merged_arches)}")
        print(f"Merged: {sorted(merged_arches)}")

    # lipo strips the signature, and unsigned arm64 code will not run.
    print("Ad-hoc signing the bundle...")
    run(["codesign", "--force", "--deep", "--sign", "-", str(APP)])
    run(["codesign", "--verify", "--deep", "--strict", str(APP)])
    print("Signature verified.")

    print("\nDone. Note: ad-hoc signing is not notarization -- users will still")
    print("need Privacy & Security -> 'Open Anyway' on first launch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
