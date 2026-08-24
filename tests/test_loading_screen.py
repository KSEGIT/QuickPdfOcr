"""Coverage for ui/loading_screen.py's dark-palette recolour and the
WA_StyledBackground fix it needed.

Before this task, LoadingScreen had zero test coverage at all -- and the
WA_StyledBackground fix is exactly the kind of bug regression coverage
exists to catch: a bare QWidget does not paint its own stylesheet
background/border by default (only style-aware widgets like QLabel do that
automatically), so without that attribute the outer card silently renders
fully transparent while each child QLabel -- which *does* auto-paint --
independently matches the same untargeted selector and draws its own
separate little bordered box around itself. These tests pin it so a future
refactor dropping that attribute (or the object-name-scoped selector it
pairs with) shows up as a red test, not a silently blank splash screen.

test_card_background_actually_paints() below does not render LoadingScreen
itself for that check: verified experimentally while building this test
file, QT_QPA_PLATFORM=offscreen's grab() cannot capture a translucent
top-level window's own background paint *at all* -- confirmed by a direct
A/B comparison with and without WA_StyledBackground on an otherwise-identical
frameless+translucent widget, both came back fully transparent. That is a
platform/offscreen-QPA limitation for this widget *class* of window (frameless,
WA_TranslucentBackground, WindowStaysOnTopHint), unrelated to whether the
styling mechanism under test here works -- a plain QWidget carrying the exact
same stylesheet and attribute (no window flags, no translucency) renders
correctly under the same platform, which is what that test actually renders.
"""
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from ui.loading_screen import LoadingScreen
from ui.theme import ACCENT, BG, DIM, FRAME


@pytest.fixture
def loading_screen(qapp):
    screen = LoadingScreen()
    yield screen
    screen.deleteLater()


def test_styled_background_attribute_is_set(loading_screen):
    """Without this attribute, QSS background-color/border/border-radius
    silently never renders on a bare QWidget -- see the module docstring."""
    assert loading_screen.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)


def test_stylesheet_selector_is_scoped_to_the_object_name(loading_screen):
    """A bare "QWidget { ... }" selector matches every QLabel/QWidget
    descendant too, not just the widget setStyleSheet() was called on --
    which is how the four-separate-boxes bug happened (see module
    docstring). Scoping to "#loadingCard" is what prevents that regressing."""
    assert loading_screen.objectName() == "loadingCard"
    assert "#loadingCard" in loading_screen.styleSheet()


def test_card_background_actually_paints(loading_screen):
    """The direct, strongest form of the regression test: render the exact
    stylesheet/attribute combination LoadingScreen's card uses and sample
    an actual painted pixel, rather than only checking the attribute/
    selector are present (which could both be true while the widget was
    still visually broken for some other reason -- e.g. a typo in the
    selector string).

    Renders a plain QWidget clone carrying loading_screen's real
    objectName/styleSheet/WA_StyledBackground, not loading_screen itself --
    see the module docstring for why: offscreen grab() cannot capture a
    translucent top-level window's own background at all, in either the
    broken or fixed state, so rendering the real instance here would not
    actually be testing anything.
    """
    clone = QWidget()
    clone.setObjectName(loading_screen.objectName())
    clone.setAttribute(
        Qt.WidgetAttribute.WA_StyledBackground,
        loading_screen.testAttribute(Qt.WidgetAttribute.WA_StyledBackground),
    )
    clone.setStyleSheet(loading_screen.styleSheet())
    clone.setFixedSize(loading_screen.size())
    QApplication.instance().processEvents()

    image = clone.grab().toImage()
    # A point well inside the rounded rect, away from the 15px corners.
    sample = image.pixelColor(10, 150)
    assert sample.alpha() == 255, "card background must be opaque, not transparent"
    assert sample.name().lower() == BG.lower(), (
        f"expected BG ({BG}) at (10, 150), got {sample.name()}"
    )
    clone.deleteLater()


def test_title_uses_accent(loading_screen):
    labels = loading_screen.findChildren(QLabel)
    title = next(lbl for lbl in labels if lbl.text() == "QuickPdfOcr")
    assert f"color: {ACCENT};" in title.styleSheet()


def test_subtitle_and_progress_labels_use_dim(loading_screen):
    labels = loading_screen.findChildren(QLabel)
    subtitle = next(lbl for lbl in labels if lbl.text() == "Starting application...")
    progress = next(lbl for lbl in labels if lbl.text() == "Initializing...")
    assert f"color: {DIM};" in subtitle.styleSheet()
    assert f"color: {DIM};" in progress.styleSheet()


def test_set_progress_updates_the_progress_label(loading_screen):
    loading_screen.set_progress("Using Apple Vision...")

    assert loading_screen.progress_label.text() == "Using Apple Vision..."


def test_card_border_uses_frame(loading_screen):
    assert f"border: 1px solid {FRAME};" in loading_screen.styleSheet()
