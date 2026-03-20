"""Manage Tesseract OCR language packs — discovery, download, installation."""

import os
import sys
import platform
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

AVAILABLE_LANGUAGES = {
    "afr": "Afrikaans", "ara": "Arabic", "bul": "Bulgarian",
    "cat": "Catalan", "ces": "Czech", "chi_sim": "Chinese (Simplified)",
    "chi_tra": "Chinese (Traditional)", "dan": "Danish", "deu": "German",
    "ell": "Greek", "eng": "English", "fin": "Finnish",
    "fra": "French", "heb": "Hebrew", "hin": "Hindi",
    "hrv": "Croatian", "hun": "Hungarian", "ind": "Indonesian",
    "ita": "Italian", "jpn": "Japanese", "kor": "Korean",
    "lit": "Lithuanian", "msa": "Malay", "nld": "Dutch",
    "nor": "Norwegian", "pol": "Polish", "por": "Portuguese",
    "ron": "Romanian", "rus": "Russian", "slk": "Slovak",
    "slv": "Slovenian", "spa": "Spanish", "sqi": "Albanian",
    "srp": "Serbian", "swe": "Swedish", "tha": "Thai",
    "tur": "Turkish", "ukr": "Ukrainian", "vie": "Vietnamese",
}

_TESSDATA_REPO = "https://github.com/tesseract-ocr/tessdata/raw/main"


class LanguageManager(QObject):
    """Discover installed languages and download new Tesseract language packs."""

    download_progress = Signal(str, int)
    download_finished = Signal(str)
    download_error = Signal(str, str)

    def get_tessdata_dir(self) -> Optional[Path]:
        """Return the tessdata directory where .traineddata files live."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidate = Path(sys._MEIPASS) / "tesseract" / "tessdata"
            if candidate.is_dir():
                return candidate

        prefix = os.environ.get("TESSDATA_PREFIX")
        if prefix:
            candidate = Path(prefix.rstrip("/\\")) / "tessdata"
            if candidate.is_dir():
                return candidate
            candidate = Path(prefix.rstrip("/\\"))
            if candidate.is_dir() and list(candidate.glob("*.traineddata")):
                return candidate

        system = platform.system()
        candidates = []
        if system == "Windows":
            candidates = [
                Path("C:/Program Files/Tesseract-OCR/tessdata"),
                Path("C:/Program Files (x86)/Tesseract-OCR/tessdata"),
            ]
        elif system == "Darwin":
            candidates = [
                Path("/opt/homebrew/share/tessdata"),
                Path("/usr/local/share/tessdata"),
            ]
        else:
            candidates = [
                Path("/usr/share/tesseract-ocr/5/tessdata"),
                Path("/usr/share/tesseract-ocr/4/tessdata"),
                Path("/usr/share/tessdata"),
            ]

        for c in candidates:
            if c.is_dir():
                return c

        return None

    def get_installed_languages(self) -> list[str]:
        tessdata = self.get_tessdata_dir()
        if tessdata is None:
            return []
        return sorted(
            p.stem for p in tessdata.glob("*.traineddata") if p.stem != "osd"
        )

    def get_download_url(self, lang_code: str) -> str:
        return f"{_TESSDATA_REPO}/{lang_code}.traineddata"

    def download_language(self, lang_code: str):
        tessdata = self.get_tessdata_dir()
        if tessdata is None:
            self.download_error.emit(lang_code, "Cannot find tessdata directory")
            return

        dest = tessdata / f"{lang_code}.traineddata"
        if dest.exists():
            self.download_finished.emit(lang_code)
            return

        url = self.get_download_url(lang_code)
        try:
            import urllib.request
            self.download_progress.emit(lang_code, 0)

            def _report(block_num, block_size, total_size):
                if total_size > 0:
                    pct = min(int(block_num * block_size * 100 / total_size), 100)
                    self.download_progress.emit(lang_code, pct)

            urllib.request.urlretrieve(url, str(dest), reporthook=_report)
            self.download_finished.emit(lang_code)
        except Exception as e:
            if dest.exists():
                dest.unlink()
            self.download_error.emit(lang_code, str(e))
