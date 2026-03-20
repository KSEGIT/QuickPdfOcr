import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def isolated_settings():
    """Clear QSettings before and after each test so tests never see
    values left by other tests or prior runs."""
    qs = QSettings("QuickPdfOcr", "QuickPdfOcr")
    qs.clear()
    qs.sync()
    yield
    qs.clear()
    qs.sync()
