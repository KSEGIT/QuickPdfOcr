#!/usr/bin/env python3
"""Census dist/QuickPdfOcr.app's Mach-O architectures, then ad-hoc sign it.

Replaces make_universal.py, which merged pypdfium2's dylib *after* the .app
was already built. That was too late for a universal2 PyInstaller build (see
packaging/prepare_universal_deps.py, which now does that merge before
`python build.py` runs, and packaging/quickpdfocr.spec's target_arch
handling). This script's job is now purely a verification gate: with
QUICKPDFOCR_UNIVERSAL2=1 set, it fails loudly and lists every offender if any
Mach-O binary inside the built .app is not universal2 -- this is the check
that would have caught the app shipping as arm64-only while being labeled
universal2.

Signing runs either way, regardless of the gate: lipo and PyInstaller output
is unsigned, and unsigned arm64 code will not run on Apple Silicon whether or
not the bundle turned out to be universal2. Ad-hoc signing (--sign -) needs
no Apple Developer account. It does NOT notarize: users downloading from
GitHub will still see a Gatekeeper prompt on first launch.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
APP = PROJECT_ROOT / "dist" / "QuickPdfOcr.app"
REQUIRED_ARCHES = {"arm64", "x86_64"}

# The real bundle has ~118 Mach-O files (PySide6/Qt alone accounts for most
# of them). This is a floor, not the expected count, so it tolerates normal
# variation across dependency versions without needing updates on every
# bump. It exists because "no thin binaries found" is otherwise defined as
# success with no lower bound on the census: if Mach-O detection ever
# regressed to matching nothing (e.g. a `file` output format change, or
# census()'s rglob/symlink filtering breaking), the fatness gate below would
# vacuously pass over zero files and sign a thin (or otherwise broken)
# bundle without ever noticing. This exact "a check that cannot fail"
# pattern has already caused several defects on this branch.
MIN_PLAUSIBLE_MACHO_COUNT = 50


def run(cmd, **kwargs) -> subprocess.CompletedProcess:
    """Run a command, echoing it, and raise on failure."""
    print(f"  $ {' '.join(str(part) for part in cmd)}")
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def is_macho(path: Path) -> bool:
    """True if `file` identifies path as a Mach-O binary.

    Do not gate on the executable bit: PyInstaller-collected .dylib and .so
    files are frequently left world-readable but not executable, yet are
    still genuine Mach-O binaries that need an architecture check.
    """
    output = subprocess.run(
        ["file", "-b", str(path)], capture_output=True, text=True, check=True
    ).stdout
    return "Mach-O" in output


def architectures(binary: Path) -> set:
    """Architectures present in a Mach-O file, via lipo -info."""
    output = run(["lipo", "-info", str(binary)]).stdout
    return set(output.strip().split(":")[-1].split())


def census() -> dict:
    """Map every non-symlink Mach-O file in the bundle to its architectures."""
    result = {}
    for path in APP.rglob("*"):
        # PyInstaller's macOS bundle layout puts real binaries under
        # Contents/Frameworks/ and symlinks them into Contents/Resources/,
        # so every real file is mirrored by a symlink pointing back to it.
        # Skip symlinks or every binary would be counted (and lipo'd) twice.
        if path.is_symlink() or not path.is_file():
            continue
        if is_macho(path):
            result[path] = architectures(path)
    return result


def main() -> int:
    if not APP.exists():
        raise SystemExit(f"{APP} not found; run python build.py first")

    require_universal2 = os.environ.get("QUICKPDFOCR_UNIVERSAL2") == "1"

    print("Scanning bundle for Mach-O binaries...")
    arches = census()
    print(f"Found {len(arches)} Mach-O file(s).")

    if len(arches) < MIN_PLAUSIBLE_MACHO_COUNT:
        raise SystemExit(
            f"Only {len(arches)} Mach-O file(s) found in {APP}, fewer than "
            f"the {MIN_PLAUSIBLE_MACHO_COUNT} floor -- Mach-O detection is "
            "suspected broken (census()'s `file`-based matching, or its "
            "symlink filtering) rather than the bundle genuinely containing "
            "that few binaries. A real build has ~118. Refusing to sign or "
            "report a pass on a census this implausible."
        )

    tally: dict = {}
    for present in arches.values():
        key = " ".join(sorted(present))
        tally[key] = tally.get(key, 0) + 1
    print("\nArchitecture census:")
    for key, count in sorted(tally.items()):
        print(f"  {count:4d}  {key}")

    if require_universal2:
        thin = {p: a for p, a in arches.items() if not REQUIRED_ARCHES <= a}
        if thin:
            print(
                f"\n{len(thin)} Mach-O file(s) are not universal2 "
                f"(missing one of {sorted(REQUIRED_ARCHES)}):",
                file=sys.stderr,
            )
            for path, present in sorted(thin.items()):
                print(f"  {path.relative_to(APP)}: {sorted(present)}", file=sys.stderr)
            raise SystemExit(
                "Bundle is not universal2. QUICKPDFOCR_UNIVERSAL2=1 was set, "
                "so every Mach-O binary must contain both arm64 and x86_64. "
                "See packaging/prepare_universal_deps.py (must run before "
                "the build) and packaging/quickpdfocr.spec's target_arch "
                "handling (needs a universal2 interpreter, not a thin one)."
            )
        print("\nAll Mach-O binaries are universal2 (arm64 + x86_64). Gate passed.")
    else:
        print(
            "\nQUICKPDFOCR_UNIVERSAL2 is not set to '1'; treating this as an "
            "architecture-specific build and skipping the fatness gate."
        )

    # lipo/PyInstaller output is unsigned either way, and unsigned arm64 code
    # will not run on Apple Silicon.
    print("\nAd-hoc signing the bundle...")
    run(["codesign", "--force", "--deep", "--sign", "-", str(APP)])
    run(["codesign", "--verify", "--deep", "--strict", str(APP)])
    print("Signature verified.")

    print("\nDone. Note: ad-hoc signing is not notarization -- users will still")
    print("need Privacy & Security -> 'Open Anyway' on first launch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
