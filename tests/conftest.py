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
def isolated_settings(tmp_path):
    """Redirect QSettings to a temporary INI file so tests never touch
    the real registry / plist / .conf."""
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path),
    )
    yield
