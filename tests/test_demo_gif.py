"""Guards on the committed demo GIF (docs/assets/quickpdfocr-demo.gif).

Same exists-at-expected-size pattern as test_icon_outputs.py: the GIF is a
rendered artefact referenced by both README.md and docs/index.html, so a
missing, truncated, or wrongly-encoded copy must fail CI rather than ship a
broken image to the README and the live site.
"""
from pathlib import Path

import pytest

GIF = Path(__file__).resolve().parent.parent / "docs" / "assets" / "quickpdfocr-demo.gif"


def _pil_image():
    return pytest.importorskip("PIL.Image", reason="Pillow is asset tooling")


def test_demo_gif_exists_and_is_non_trivial():
    """Needs no Pillow -- a missing or truncated asset fails here."""
    assert GIF.exists(), "quickpdfocr-demo.gif not rendered"
    assert GIF.stat().st_size > 50_000, "quickpdfocr-demo.gif looks truncated"


def test_demo_gif_dimensions_frames_and_loop():
    Image = _pil_image()
    with Image.open(GIF) as gif:
        assert gif.size == (1200, 675)
        assert gif.n_frames > 1
        assert gif.info.get("loop") == 0, "demo GIF must loop forever"


def test_demo_gif_stays_under_size_budget():
    """5 MB is the hard cap render_demo_gif.py enforces; 2 MB is the target."""
    assert GIF.stat().st_size <= 5_000_000
