"""Guards on the rendered icon artefacts and the size->master mapping."""
import sys
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
sys.path.insert(0, str(RESOURCES))

# icon_manifest is stdlib-only (just pathlib) -- no Pillow, no Playwright --
# so it can be imported unconditionally in every CI job, including macOS
# (where requirements.txt never installs Pillow) and every workflow (none of
# which install Playwright). The mapping assertions below used to import
# render_icons directly, which drags in Playwright and skipped them on all
# seven CI invocations; reading the same constants from icon_manifest
# instead means they actually run everywhere.
import icon_manifest

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

ICO_SIZES = [16, 32, 48, 64, 128, 256]


def _pil_image():
    """Pillow only where a test genuinely needs it to open/compare images.

    requirements.txt ships Pillow on sys_platform != 'darwin', so this skips
    only the individual tests that call it, on macOS -- not the whole
    module the way a module-scope importorskip did, which used to take
    test_icns_exists_and_is_non_trivial (needs no Pillow at all) and the
    size->master mapping tests (moved to icon_manifest above) down with it.
    """
    return pytest.importorskip("PIL.Image", reason="Pillow is asset tooling")


def _load_render_icons():
    """Import the pipeline module, or skip. Playwright-dependent, so this is
    called only by the tests that genuinely need the rendering pipeline
    itself (as opposed to the size->master mapping, which lives in the
    dependency-free icon_manifest module) — never at module scope."""
    return pytest.importorskip("render_icons", reason="asset tooling not installed")


def _ico_frame(size):
    """Extract one frame from the committed multi-size icon.ico."""
    Image = _pil_image()
    with Image.open(ICO) as im:
        im.size = (size, size)
        im.load()
        return im.convert("RGBA").copy()


def _abs_diff(a, b):
    """Sum of absolute channel differences. Uses tobytes() rather than
    getdata(), which Pillow deprecates and removes in 14."""
    return sum(abs(x - y) for x, y in zip(a.tobytes(), b.tobytes()))


def test_small_sizes_come_from_the_simple_master():
    for size in (16, 32, 48, 64):
        assert icon_manifest.SIZE_SOURCES[size].name == "icon_small.svg"


def test_large_sizes_come_from_the_detailed_master():
    for size in (128, 256, 512, 1024):
        assert icon_manifest.SIZE_SOURCES[size].name == "icon.svg"


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
    Image = _pil_image()
    assert path.exists(), f"{path.name} not rendered"
    with Image.open(path) as im:
        assert im.size == expected


def test_ico_carries_all_six_sizes():
    Image = _pil_image()
    assert ICO.exists(), "icon.ico not rendered"
    with Image.open(ICO) as im:
        sizes = {s[0] for s in im.info["sizes"]}
    assert sizes == set(ICO_SIZES), f"icon.ico sizes {sorted(sizes)} != {ICO_SIZES}"


def test_ico_size_list_matches_the_pipeline():
    """Keeps the CI-visible constant above honest against the pipeline's own.

    Reads icon_manifest (dependency-free) rather than render_icons
    (Playwright-dependent), so this runs everywhere instead of skipping on
    all seven CI invocations the way it used to.
    """
    assert icon_manifest.ICO_SIZES == ICO_SIZES


def test_render_icons_reads_the_same_manifest_it_was_given():
    """render_icons.py imports SIZE_SOURCES/ICO_SIZES from icon_manifest
    rather than redefining them -- this guards against a future edit
    accidentally shadowing those names with a local reassignment inside
    render_icons.py, which would silently change the real render
    pipeline's size->master mapping with nothing else here to catch it
    (the tests above compare icon_manifest against itself/a local
    constant, never against the render_icons module's own attributes).
    Playwright-dependent (importing render_icons pulls it in), so this
    runs wherever the pipeline module itself would import successfully.
    """
    render_icons = _load_render_icons()
    assert render_icons.SIZE_SOURCES is icon_manifest.SIZE_SOURCES
    assert render_icons.ICO_SIZES is icon_manifest.ICO_SIZES


def test_icns_exists_and_is_non_trivial():
    """Needs no Pillow at all -- this is the sole guard on the artefact
    packaging/quickpdfocr.spec feeds to BUNDLE(icon=…), so it must not be
    gated behind an unrelated Pillow import the way it used to be."""
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
    Image = _pil_image()
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
    Image = _pil_image()
    actual_16 = _ico_frame(16)
    downscaled = _ico_frame(32).resize((16, 16), Image.Resampling.LANCZOS)
    diff = _abs_diff(actual_16, downscaled)
    assert diff < 10_000, (
        f"16px and 32px frames differ by {diff:,}; they share a master and "
        f"should be close — the threshold in the sibling test is not meaningful"
    )


def test_missing_iconutil_leaves_tracked_artefacts_untouched(monkeypatch):
    """render_icons.main() must fail before touching any tracked artefact
    when iconutil is unavailable.

    Without this, a Linux or Windows contributor following
    resources/README.md gets a traceback from create_icns_from_pngs with six
    tracked PNGs/.ico already rewritten and icon.icns left holding stale art
    -- which packaging/quickpdfocr.spec then bakes into the app bundle.
    render_icons.main() now checks shutil.which("iconutil") before rendering
    or writing anything, so this never launches a real browser: it fails at
    the up-front check and returns non-zero immediately.

    This test runs against the real git-tracked resources/ and docs/assets/
    files (main() has no test-injectable output directory), so the whole
    body after the snapshot is wrapped in try/finally: if a future
    regression ever reintroduces a write-before-check ordering bug, this
    test must still fail loudly on the `before == after` assertion, but
    without leaving the developer's working tree holding regenerated
    tracked binaries that a red test then hands them to manually revert.
    """
    render_icons = _load_render_icons()
    tracked = [ICO, ICNS, PNG_256, PNG_512, FAVICON, DOCS_FAVICON, DOCS_LOGO]
    assert all(p.exists() for p in tracked), "fixture assumption: all tracked artefacts pre-exist"
    before = {p: p.read_bytes() for p in tracked}

    try:
        monkeypatch.setattr(render_icons.shutil, "which", lambda name: None)
        result = render_icons.main()

        assert result != 0, "main() must report failure when iconutil is missing"
        after = {p: p.read_bytes() for p in tracked}
        assert before == after, "tracked icon artefacts changed despite missing iconutil"
    finally:
        for path, original in before.items():
            if path.read_bytes() != original:
                path.write_bytes(original)
