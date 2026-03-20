"""Persistent application settings using QSettings."""

from typing import Optional
from PySide6.QtCore import QSettings


class Settings:
    """Cross-platform persistent settings for QuickPdfOcr.

    Uses QSettings which stores to:
      - Windows: Registry (HKEY_CURRENT_USER\\Software\\QuickPdfOcr)
      - macOS: ~/Library/Preferences/com.QuickPdfOcr.plist
      - Linux: ~/.config/QuickPdfOcr/QuickPdfOcr.conf
    """

    _DEFAULTS = {
        "language": "eng",
        "dpi_override": None,
        "output_directory": "",
    }

    def __init__(self):
        self._qs = QSettings("QuickPdfOcr", "QuickPdfOcr")

    # -- language --
    @property
    def language(self) -> str:
        return self._qs.value("language", self._DEFAULTS["language"])

    @language.setter
    def language(self, value: str):
        self._qs.setValue("language", value)

    # -- dpi_override --
    @property
    def dpi_override(self) -> Optional[int]:
        val = self._qs.value("dpi_override", self._DEFAULTS["dpi_override"])
        if val is None or val == "":
            return None
        return int(val)

    @dpi_override.setter
    def dpi_override(self, value: Optional[int]):
        if value is None:
            self._qs.remove("dpi_override")
        else:
            self._qs.setValue("dpi_override", value)

    # -- output_directory --
    @property
    def output_directory(self) -> str:
        return self._qs.value("output_directory", self._DEFAULTS["output_directory"])

    @output_directory.setter
    def output_directory(self, value: str):
        self._qs.setValue("output_directory", value)
