"""Guards on the rendered icon artefacts and the size->master mapping."""
import sys
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
sys.path.insert(0, str(RESOURCES))

Image = pytest.importorskip("PIL.Image", reason="Pillow is asset tooling")
render_icons = pytest.importorskip(
    "render_icons", reason="asset tooling not installed"
)

ICO = RESOURCES / "icon.ico"
ICNS = RESOURCES / "icon.icns"
PNG_256 = RESOURCES / "icon.png"
PNG_512 = RESOURCES / "icon_512.png"
FAVICON = RESOURCES / "favicon.png"


def test_small_sizes_come_from_the_simple_master():
    for size in (16, 32, 48, 64):
        assert render_icons.SIZE_SOURCES[size].name == "icon_small.svg"


def test_large_sizes_come_from_the_detailed_master():
    for size in (128, 256, 512, 1024):
        assert render_icons.SIZE_SOURCES[size].name == "icon.svg"


@pytest.mark.parametrize(
    "path,expected",
    [(PNG_256, (256, 256)), (PNG_512, (512, 512)), (FAVICON, (32, 32))],
    ids=["icon.png", "icon_512.png", "favicon.png"],
)
def test_png_outputs_exist_at_expected_size(path, expected):
    assert path.exists(), f"{path.name} not rendered"
    with Image.open(path) as im:
        assert im.size == expected


def test_ico_carries_all_six_sizes():
    assert ICO.exists(), "icon.ico not rendered"
    with Image.open(ICO) as im:
        sizes = {s[0] for s in im.info["sizes"]}
    assert sizes == set(render_icons.ICO_SIZES), (
        f"icon.ico sizes {sorted(sizes)} != {render_icons.ICO_SIZES}"
    )


def test_icns_exists_and_is_non_trivial():
    assert ICNS.exists(), "icon.icns not rendered"
    assert ICNS.stat().st_size > 50_000, "icon.icns looks truncated"


def test_16px_is_not_a_downscale_of_the_detailed_art():
    """The whole point of two masters: the 16px slot must be distinct art."""
    small = RESOURCES / "_render" / "icon_16.png"
    large = RESOURCES / "_render" / "icon_256.png"
    if not (small.exists() and large.exists()):
        pytest.skip("intermediate renders not retained; run render_icons.py")
    with Image.open(small) as a, Image.open(large) as b:
        a = a.convert("RGBA")
        downscaled = b.convert("RGBA").resize((16, 16), Image.Resampling.LANCZOS)
        diff = sum(
            abs(p - q)
            for pa, pb in zip(a.getdata(), downscaled.getdata())
            for p, q in zip(pa, pb)
        )
    assert diff > 5000, "16px render is indistinguishable from a downscale"
