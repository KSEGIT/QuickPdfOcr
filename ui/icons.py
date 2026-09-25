"""Lucide icon loading, tinted to the brand palette.

resources/icons/*.svg (vendored from the Lucide project -- see
THIRD_PARTY_LICENSES.md) ship with stroke="currentColor", a CSS custom
keyword that only resolves inside an actual CSS cascade. QSvgRenderer has no
such cascade -- it renders the SVG's literal attribute values -- so Qt does
not resolve it on its own, and painting one of these files as-is renders
nothing (currentColor is not a valid SVG paint value outside CSS).

load_icon() substitutes the literal hex for that placeholder before handing
the bytes to QSvgRenderer, then rasterizes into a QPixmap wrapped in a
QIcon. This is the one small helper every icon call site in ui/main_window.py
goes through, rather than repeating the substitute-and-render mechanics at
each of them.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

def _bundle_root() -> Path:
    """The directory resources/ sits under, frozen or not.

    Frozen, PyInstaller extracts datas relative to sys._MEIPASS, so that is
    the root -- the same branch main.py already uses to find icon.ico. From
    source it is the repo root, two levels up from this file.

    Deriving it from __file__ unconditionally would *usually* work for a
    onedir build (PyInstaller reports a __file__ under the bundle root for
    frozen modules), but not reliably through a macOS .app: its
    Contents/MacOS and Contents/Frameworks are symlinked into each other,
    and Path.resolve() follows those, so parent.parent can land outside the
    tree the datas were extracted to. sys._MEIPASS is the value PyInstaller
    itself guarantees.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


ICONS_DIR = _bundle_root() / "resources" / "icons"

# Icons are rasterized at 2x the requested logical size and tagged via
# QPixmap.setDevicePixelRatio(), so they stay crisp on Retina/HiDPI displays
# instead of the soft edges a 1x-only raster shows once Qt upscales it to
# match the panel's actual pixel density.
_DEVICE_PIXEL_RATIO = 2.0


@lru_cache(maxsize=None)
def _tinted_svg_bytes(name: str, color: str) -> bytes:
    """resources/icons/<name>'s markup with stroke="currentColor" replaced
    by the literal `color`.

    Raises FileNotFoundError (or another OSError subclass, e.g.
    PermissionError) for a file that cannot be read. load_icon(), the only
    caller, is the layer that decides how to handle that (see its
    docstring); this function itself makes no attempt to hide it.
    """
    svg_text = (ICONS_DIR / name).read_text(encoding="utf-8")
    return svg_text.replace("currentColor", color).encode("utf-8")


@lru_cache(maxsize=None)
def _tinted_pixmap(name: str, color: str, size: int) -> QPixmap:
    """Raises ValueError if `name` does not parse as a valid SVG document.

    Verified experimentally: an unparsed QSvgRenderer does not raise on its
    own -- render() onto a freshly-filled-transparent QPixmap silently
    paints nothing, which without this check would produce the exact same
    "ships a blank icon" outcome load_icon()'s FileNotFoundError handling
    exists to prevent, just via a different failure mode (a corrupted file
    on disk rather than a missing one) with no warning at all.
    """
    physical = round(size * _DEVICE_PIXEL_RATIO)
    renderer = QSvgRenderer(_tinted_svg_bytes(name, color))
    if not renderer.isValid():
        raise ValueError(f"{name!r} did not parse as a valid SVG document")
    pixmap = QPixmap(physical, physical)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, physical, physical))
    painter.end()
    pixmap.setDevicePixelRatio(_DEVICE_PIXEL_RATIO)
    return pixmap


def _load_pixmap_or_warn(name: str, color: str, size: int) -> QPixmap | None:
    """_tinted_pixmap(), or None with a stderr warning if it could not be
    produced (missing/unreadable file, or a malformed SVG document) --
    the shared fallback both load_icon()'s Normal- and Disabled-mode
    pixmaps go through."""
    try:
        return _tinted_pixmap(name, color, size)
    except (OSError, ValueError) as exc:
        print(f"Warning: could not load icon {name!r}: {exc}", file=sys.stderr)
        return None


def load_icon(name: str, color: str, size: int = 20, *, disabled_color: str | None = None) -> QIcon:
    """A resources/icons/<name> Lucide icon, tinted to `color`, as a QIcon
    sized `size` logical pixels (e.g. for QPushButton.setIcon()).

    A missing or malformed icon file degrades to a null QIcon
    (setIcon(QIcon()) simply shows no icon; the button's text is
    unaffected) with a stderr warning, the same convention main.py's own
    app-icon loading already uses, rather than raising and crashing the
    whole window's construction. tests/test_ui_icons.py is the real guard
    against a typo'd `name` ever reaching here -- this is the last-resort
    fallback for an icon asset missing or corrupted at runtime for some
    other reason. (packaging/quickpdfocr.spec does bundle resources/icons/,
    and tests/test_ui_icons.py asserts it keeps doing so, so a frozen build
    reaching this path means something else went wrong.)

    `disabled_color`, if given, registers a second pixmap for QIcon::Disabled
    mode. Without it, Qt auto-generates a disabled-state pixmap via its
    style's default grey-out algorithm -- measured at #6C6C6C, which is only
    2.79:1 on SURFACE (below even the 3:1 non-text floor) regardless of what
    `color` was. Callers whose button can actually become disabled (e.g.
    open_btn/start_ocr_btn during an OCR run) should pass the same DIM used
    for that button's disabled text, so the icon and the label dim together
    at a colour that is actually legible.
    """
    icon = QIcon()
    normal = _load_pixmap_or_warn(name, color, size)
    if normal is not None:
        icon.addPixmap(normal, QIcon.Mode.Normal)
    if disabled_color is not None:
        disabled = _load_pixmap_or_warn(name, disabled_color, size)
        if disabled is not None:
            icon.addPixmap(disabled, QIcon.Mode.Disabled)
    return icon
