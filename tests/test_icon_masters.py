"""Structural guards for the two SVG icon masters."""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
DETAILED = RESOURCES / "icon.svg"
SIMPLE = RESOURCES / "icon_small.svg"
SVG_NS = "{http://www.w3.org/2000/svg}"


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_master_exists_and_parses(master):
    assert master.exists(), f"{master.name} is missing"
    ET.parse(master)


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_master_is_1024_square(master):
    root = ET.parse(master).getroot()
    assert root.get("viewBox") == "0 0 1024 1024"


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_glyphs_are_paths_not_text(master):
    """Font-independent: rendering must not depend on installed fonts."""
    root = ET.parse(master).getroot()
    texts = list(root.iter(f"{SVG_NS}text"))
    assert texts == [], (
        f"{master.name} uses <text>; glyphs must be vector paths"
    )


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_master_shares_squircle_and_gradient(master):
    """Both masters must read as one icon across the size bands."""
    source = master.read_text(encoding="utf-8")
    assert 'rx="230"' in source, "squircle corner radius missing"
    assert "#4F46E5" in source and "#7C3AED" in source, "brand gradient missing"
    assert "#22D3EE" in source, "cyan accent missing"


def test_simple_master_is_substantially_simpler():
    """The small master must carry far fewer drawing ops, or it will still mush."""
    def ops(path):
        root = ET.parse(path).getroot()
        return sum(1 for el in root.iter()
                   if el.tag in {f"{SVG_NS}rect", f"{SVG_NS}path",
                                 f"{SVG_NS}circle"})

    assert ops(SIMPLE) < ops(DETAILED) / 2, (
        "icon_small.svg must be at least 2x simpler than icon.svg"
    )
