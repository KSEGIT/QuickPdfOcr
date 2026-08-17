"""Guards on the rendered icon artefacts and the size->master mapping."""
import sys
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
sys.path.insert(0, str(RESOURCES))

# Pillow only at module scope. requirements.txt ships Pillow on
# sys_platform != 'darwin', so everything guarded by this alone RUNS on the
# build-linux and build-windows CI workflows. Importing render_icons here
# instead would drag in Playwright and skip the entire module on all four
# workflows — which is exactly how the two-master split ended up unprotected.
Image = pytest.importorskip("PIL.Image", reason="Pillow is asset tooling")


def _load_render_icons():
    """Import the pipeline module, or skip. Playwright-dependent, so this is
    called inside the two tests that genuinely need the source mapping —
    never at module scope."""
    return pytest.importorskip("render_icons", reason="asset tooling not installed")


def _ico_frame(size):
    """Extract one frame from the committed multi-size icon.ico."""
    with Image.open(ICO) as im:
        im.size = (size, size)
        im.load()
        return im.convert("RGBA").copy()


def _abs_diff(a, b):
    """Sum of absolute channel differences. Uses tobytes() rather than
    getdata(), which Pillow deprecates and removes in 14."""
    return sum(abs(x - y) for x, y in zip(a.tobytes(), b.tobytes()))

ICO = RESOURCES / "icon.ico"
ICNS = RESOURCES / "icon.icns"
PNG_256 = RESOURCES / "icon.png"
PNG_512 = RESOURCES / "icon_512.png"
FAVICON = RESOURCES / "favicon.png"

# The copies docs/index.html actually loads (relative paths, so GitHub Pages
# — which publishes from main:/docs, outside resources/ — can reach them).
# render_icons.py writes these from the same pipeline run as the
# resources/*.png above, but nothing before this enforced that the commit
# in the tree actually reflects that: this is the same
# exists-at-expected-size pattern as test_png_outputs_exist_at_expected_size,
# extended to catch a docs/assets/*.png left stale after a master SVG edit.
DOCS_ASSETS = RESOURCES.parent / "docs" / "assets"
DOCS_FAVICON = DOCS_ASSETS / "favicon.png"
DOCS_LOGO = DOCS_ASSETS / "logo.png"


def test_small_sizes_come_from_the_simple_master():
    render_icons = _load_render_icons()
    for size in (16, 32, 48, 64):
        assert render_icons.SIZE_SOURCES[size].name == "icon_small.svg"


def test_large_sizes_come_from_the_detailed_master():
    render_icons = _load_render_icons()
    for size in (128, 256, 512, 1024):
        assert render_icons.SIZE_SOURCES[size].name == "icon.svg"


@pytest.mark.parametrize(
    "path,expected",
    [
        (PNG_256, (256, 256)),
        (PNG_512, (512, 512)),
        (FAVICON, (32, 32)),
        (DOCS_FAVICON, (32, 32)),
        (DOCS_LOGO, (64, 64)),
    ],
    ids=["icon.png", "icon_512.png", "favicon.png", "docs/assets/favicon.png",
         "docs/assets/logo.png"],
)
def test_png_outputs_exist_at_expected_size(path, expected):
    assert path.exists(), f"{path.name} not rendered"
    with Image.open(path) as im:
        assert im.size == expected


ICO_SIZES = [16, 32, 48, 64, 128, 256]


def test_ico_carries_all_six_sizes():
    assert ICO.exists(), "icon.ico not rendered"
    with Image.open(ICO) as im:
        sizes = {s[0] for s in im.info["sizes"]}
    assert sizes == set(ICO_SIZES), f"icon.ico sizes {sorted(sizes)} != {ICO_SIZES}"


def test_ico_size_list_matches_the_pipeline():
    """Keeps the CI-visible constant above honest against the pipeline's own."""
    render_icons = _load_render_icons()
    assert render_icons.ICO_SIZES == ICO_SIZES


def test_icns_exists_and_is_non_trivial():
    assert ICNS.exists(), "icon.icns not rendered"
    assert ICNS.stat().st_size > 50_000, "icon.icns looks truncated"


def test_16px_is_not_a_downscale_of_the_detailed_art():
    """The whole point of two masters: the 16px slot must be distinct art.

    Reads the committed icon.ico rather than resources/_render/, which is
    gitignored and therefore absent on every machine but the one that last ran
    the pipeline. This is the only guard against a silent regression to
    single-master rendering, so it must run where regressions actually land.

    Measured at cba1dd1: 33,560 across masters vs 3,025 for the same-master
    control below. The 10,000 threshold sits cleanly between them.
    """
    assert ICO.exists(), "icon.ico not rendered"
    actual_16 = _ico_frame(16)
    downscaled = _ico_frame(256).resize((16, 16), Image.Resampling.LANCZOS)
    diff = _abs_diff(actual_16, downscaled)
    assert diff > 10_000, (
        f"16px frame is indistinguishable from a downscale of the 256px frame "
        f"(diff={diff:,}) — the two-master split has regressed"
    )


def test_same_master_sizes_are_similar_control():
    """Control for the test above: 16 and 32 both come from icon_small.svg, so
    downscaling 32 to 16 should land close. Without this, the threshold could
    be passing for some unrelated reason and nobody would notice."""
    actual_16 = _ico_frame(16)
    downscaled = _ico_frame(32).resize((16, 16), Image.Resampling.LANCZOS)
    diff = _abs_diff(actual_16, downscaled)
    assert diff < 10_000, (
        f"16px and 32px frames differ by {diff:,}; they share a master and "
        f"should be close — the threshold in the sibling test is not meaningful"
    )
