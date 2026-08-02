#!/usr/bin/env python3
"""Fatten pypdfium2's libpdfium.dylib in site-packages, before PyInstaller runs.

pypdfium2 ships arch-specific wheels (arm64 and x86_64); everything else this
project depends on (PySide6, pyobjc Vision/Quartz) ships genuine universal2
wheels already, so this is the one dependency that needs help.

This has to happen *before* the build, not after it. PyInstaller's
target_arch="universal2" (see packaging/quickpdfocr.spec) refuses to proceed
if any binary it collects -- including this dylib -- is thin, so a fat copy
must already exist in site-packages by the time `python build.py` runs.
Merging it into the built .app afterwards, as the removed make_universal.py
did, is too late for a universal2 PyInstaller build; that script's signing
job now lives in packaging/verify_universal.py, which runs after the build.

Run this against the same interpreter that will run PyInstaller.
"""

import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PDFIUM_NAME = "libpdfium.dylib"
REQUIRED_ARCHES = {"arm64", "x86_64"}


def run(cmd, **kwargs) -> subprocess.CompletedProcess:
    """Run a command, echoing it, and raise on failure."""
    print(f"  $ {' '.join(str(part) for part in cmd)}")
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def find_pdfium() -> Path:
    """Locate libpdfium.dylib inside the running interpreter's site-packages.

    Uses importlib to ask the interpreter where it actually put the package,
    rather than assuming a `.venv` layout -- this script must work whichever
    venv (or python.org framework build, in CI) it is run against.
    """
    spec = importlib.util.find_spec("pypdfium2_raw")
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit(
            "pypdfium2_raw is not importable in this interpreter; "
            "pip install -r requirements.txt first"
        )
    package_dir = Path(list(spec.submodule_search_locations)[0])
    dylib = package_dir / PDFIUM_NAME
    if not dylib.exists():
        raise SystemExit(f"{PDFIUM_NAME} not found at {dylib}")
    return dylib


def architectures(binary: Path) -> set:
    """Architectures present in a Mach-O file."""
    output = run(["lipo", "-info", str(binary)]).stdout
    return set(output.strip().split(":")[-1].split())


def download_other_arch(target: str, version: str, python_version: str, into: Path) -> Path:
    """Download the opposite-architecture pypdfium2 wheel and extract its dylib."""
    run([
        sys.executable, "-m", "pip", "download",
        f"pypdfium2=={version}",
        "--only-binary=:all:",
        f"--platform=macosx_13_0_{target}",
        f"--python-version={python_version}",
        "--no-deps",
        "-d", str(into),
    ])
    wheels = list(into.glob("*.whl"))
    if not wheels:
        raise SystemExit(f"No pypdfium2=={version} wheel downloaded for {target}")

    extracted = into / "extracted"
    with zipfile.ZipFile(wheels[0]) as archive:
        archive.extractall(extracted)

    dylibs = list(extracted.rglob(PDFIUM_NAME))
    if not dylibs:
        raise SystemExit(f"No {PDFIUM_NAME} inside {wheels[0].name}")
    return dylibs[0]


def main() -> int:
    pdfium = find_pdfium()
    version = importlib.metadata.version("pypdfium2")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"pypdfium2 version: {version} (interpreter: {python_version})")
    print(f"Located {PDFIUM_NAME} at {pdfium}")

    present = architectures(pdfium)
    print(f"Current architectures: {sorted(present)}")

    if REQUIRED_ARCHES <= present:
        print("Already universal2; nothing to do.")
        return 0

    missing = "x86_64" if "arm64" in present else "arm64"
    print(f"Merging in {missing}...")
    with tempfile.TemporaryDirectory() as tmp:
        other = download_other_arch(missing, version, python_version, Path(tmp))
        merged = Path(tmp) / "merged.dylib"
        run(["lipo", "-create", str(pdfium), str(other), "-output", str(merged)])
        shutil.copy2(merged, pdfium)

    merged_arches = architectures(pdfium)
    if not REQUIRED_ARCHES <= merged_arches:
        raise SystemExit(
            f"Merge failed; got {sorted(merged_arches)}, "
            f"expected at least {sorted(REQUIRED_ARCHES)}"
        )
    print(f"Merged: {sorted(merged_arches)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
