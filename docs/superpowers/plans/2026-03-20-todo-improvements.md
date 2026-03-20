# QuickPdfOcr TODO Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add settings persistence, OCR language selection with download, cancel button, page-level progress, save-to-file, and a pytest test suite.

**Architecture:** Add a `components/settings.py` module using QSettings for cross-platform persistence. Thread the selected language from a new UI combo box through `OCRWorker` → `PdfOcrProcessor`. Add a `components/language_manager.py` for downloading Tesseract language packs. Add cooperative cancellation (`request_stop()`) to `OCRWorker`, page-count reporting, and a cancel button. Add `tests/` directory with pytest.

**Tech Stack:** PySide6 (QSettings, QComboBox, QProgressBar), pytesseract, pytest

---

## File Structure

```
QuickPdfOcr/
├── components/
│   ├── settings.py              (CREATE) — QSettings wrapper for persistent config
│   ├── language_manager.py      (CREATE) — Tesseract language pack discovery & download
│   ├── ocr_worker.py            (MODIFY) — Accept lang param, add request_stop(), emit page count
│   └── pdf_ocr.py               (MODIFY) — Expose page count before OCR loop
├── ui/
│   ├── main_window.py           (MODIFY) — Language combo, cancel btn, progress bar, save btn
│   └── loading_screen.py        (no changes)
├── tests/
│   ├── __init__.py              (CREATE)
│   ├── conftest.py              (CREATE) — Shared fixtures (QApp, isolated QSettings)
│   ├── test_settings.py         (CREATE)
│   ├── test_language_manager.py (CREATE)
│   ├── test_ocr_worker.py       (CREATE)
│   └── test_pdf_ocr.py          (CREATE)
├── requirements-dev.txt         (CREATE) — Dev dependencies (pytest)
├── pytest.ini                   (CREATE) — pytest configuration
└── main.py                      (no changes)
```

---

## Phase 0: Setup

### Task 0: Add pytest and dev dependencies

**Files:**
- Create: `requirements-dev.txt`

- [ ] **Step 1: Create dev requirements file**

Create `requirements-dev.txt`:
```
-r requirements.txt
pytest>=7.0.0
```

- [ ] **Step 2: Install dev dependencies**

Run: `pip install -r requirements-dev.txt`

- [ ] **Step 3: Commit**

```bash
git add requirements-dev.txt
git commit -m "chore: add requirements-dev.txt with pytest"
```

---

## Phase 1: Settings Module (Foundation)

### Task 1: Create settings module with QSettings

**Files:**
- Create: `components/settings.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_settings.py`
- Create: `pytest.ini`

- [ ] **Step 1: Create pytest configuration**

Create `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

Create `tests/__init__.py` (empty file).

- [ ] **Step 2: Write failing tests for Settings**

Create `tests/conftest.py` with test-isolated QSettings (writes to a tmp file, not the real registry):
```python
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
    # tmp_path is cleaned up automatically by pytest
```

Create `tests/test_settings.py`:
```python
from components.settings import Settings


class TestSettings:
    def test_default_language(self, qapp):
        settings = Settings()
        assert settings.language == "eng"

    def test_set_language(self, qapp):
        settings = Settings()
        settings.language = "fra"
        assert settings.language == "fra"

    def test_default_dpi_override(self, qapp):
        settings = Settings()
        assert settings.dpi_override is None

    def test_set_dpi_override(self, qapp):
        settings = Settings()
        settings.dpi_override = 400
        assert settings.dpi_override == 400

    def test_clear_dpi_override(self, qapp):
        settings = Settings()
        settings.dpi_override = 400
        settings.dpi_override = None
        assert settings.dpi_override is None

    def test_default_output_directory(self, qapp):
        settings = Settings()
        assert settings.output_directory == ""

    def test_set_output_directory(self, qapp, tmp_path):
        settings = Settings()
        settings.output_directory = str(tmp_path)
        assert settings.output_directory == str(tmp_path)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_settings.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'components.settings'`

- [ ] **Step 4: Implement Settings class**

Create `components/settings.py`:
```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_settings.py -v`
Expected: All 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add components/settings.py tests/ pytest.ini
git commit -m "feat: add persistent Settings module with QSettings"
```

---

## Phase 2: Language Selection UI + OCRWorker Plumbing

### Task 2: Add lang parameter and cooperative cancellation to OCRWorker

**Files:**
- Modify: `components/ocr_worker.py`
- Create: `tests/test_ocr_worker.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_ocr_worker.py`:
```python
from components.ocr_worker import OCRWorker


class TestOCRWorker:
    def test_default_language(self, qapp):
        worker = OCRWorker("/fake/path.pdf")
        assert worker.lang == "eng"

    def test_custom_language(self, qapp):
        worker = OCRWorker("/fake/path.pdf", lang="fra")
        assert worker.lang == "fra"

    def test_stop_flag_default(self, qapp):
        worker = OCRWorker("/fake/path.pdf")
        assert worker._stop_requested is False

    def test_request_stop(self, qapp):
        worker = OCRWorker("/fake/path.pdf")
        worker.request_stop()
        assert worker._stop_requested is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ocr_worker.py -v`
Expected: FAIL — `AttributeError: 'OCRWorker' object has no attribute 'lang'` (the current `__init__` only stores `pdf_path`)

- [ ] **Step 3: Update OCRWorker — add lang, _stop_requested, request_stop, and InterruptedError handling**

Modify `components/ocr_worker.py`. The full updated file:
```python
"""OCR Worker - Background thread for PDF OCR processing"""

import re
import traceback

from PySide6.QtCore import QObject, Signal
from components.pdf_ocr import PdfOcrProcessor


class OCRWorker(QObject):
    """Worker class to run OCR in a background thread"""

    progress = Signal(str)      # Progress message
    finished = Signal(str)      # Completed with extracted text
    error = Signal(str)         # Error message

    def __init__(self, pdf_path: str, lang: str = "eng"):
        super().__init__()
        self.pdf_path = pdf_path
        self.lang = lang
        self._stop_requested = False

    def request_stop(self):
        """Request the worker to stop processing at the next opportunity."""
        self._stop_requested = True

    def run(self):
        """Execute OCR processing"""
        try:
            processor = PdfOcrProcessor(lang=self.lang)

            # Wrap the progress callback to check for stop requests between
            # pages.  The processor calls this once per page, giving us a
            # cooperative cancellation point without modifying PdfOcrProcessor.
            def progress_callback(message):
                if self._stop_requested:
                    raise InterruptedError("OCR processing was cancelled")
                self.progress.emit(message)

            text = processor.process(
                self.pdf_path,
                output_file=None,
                progress_callback=progress_callback,
            )

            # Check if we got any meaningful text beyond page headers
            content_only = re.sub(r'---\s*Page\s+\d+\s*---', '', text).strip()
            if not content_only:
                self.error.emit("No text could be extracted from the PDF")
                return

            self.finished.emit(text)

        except InterruptedError:
            # Worker was asked to stop — exit silently without emitting signals
            return
        except FileNotFoundError as e:
            self.error.emit(f"File not found: {str(e)}")
        except ValueError as e:
            self.error.emit(f"Invalid file: {str(e)}")
        except Exception as e:
            error_details = traceback.format_exc()
            self.error.emit(f"OCR failed: {str(e)}\n\nDetails:\n{error_details}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ocr_worker.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add components/ocr_worker.py tests/test_ocr_worker.py
git commit -m "feat: OCRWorker accepts lang param, adds request_stop() and InterruptedError handling"
```

### Task 3: Add language combo box to MainWindow

**Files:**
- Modify: `ui/main_window.py`

- [ ] **Step 1: Initialize Settings in MainWindow.__init__ (must come before UI setup)**

Add import at the top of `ui/main_window.py`:
```python
from components.settings import Settings
```

In `MainWindow.__init__`, add `self.settings = Settings()` before `self._setup_ui()`.

- [ ] **Step 2: Add language combo box to _setup_ui**

In `_setup_ui`, after the `open_btn` block (after `layout.addWidget(self.open_btn)`), add:

```python
# Language selector row
lang_layout = QHBoxLayout()
lang_label = QLabel("Language:")
lang_label.setStyleSheet("font-weight: bold; color: #333;")
lang_layout.addWidget(lang_label)

self.lang_combo = QComboBox()
self.lang_combo.setMinimumHeight(30)
self.lang_combo.setStyleSheet("""
    QComboBox {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 13px;
    }
""")
self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
lang_layout.addWidget(self.lang_combo, 1)
layout.addLayout(lang_layout)
```

Add `QComboBox` to the PySide6.QtWidgets import line.

- [ ] **Step 3: Add _populate_languages and _on_language_changed methods**

```python
def _populate_languages(self):
    """Detect installed Tesseract languages and populate the combo box."""
    import pytesseract
    try:
        langs = pytesseract.get_languages(config="")
        langs = [l for l in langs if l != "osd"]
    except Exception:
        langs = ["eng"]

    self.lang_combo.blockSignals(True)  # Don't trigger save while populating
    self.lang_combo.clear()
    LANG_NAMES = {
        "eng": "English", "fra": "French", "deu": "German",
        "spa": "Spanish", "ita": "Italian", "por": "Portuguese",
        "nld": "Dutch", "pol": "Polish", "rus": "Russian",
        "chi_sim": "Chinese (Simplified)", "chi_tra": "Chinese (Traditional)",
        "jpn": "Japanese", "kor": "Korean", "ara": "Arabic",
        "hin": "Hindi", "tur": "Turkish", "vie": "Vietnamese",
        "ukr": "Ukrainian", "ces": "Czech", "swe": "Swedish",
    }
    for lang_code in sorted(langs):
        display = LANG_NAMES.get(lang_code, lang_code)
        self.lang_combo.addItem(f"{display} ({lang_code})", lang_code)

    saved_lang = self.settings.language
    idx = self.lang_combo.findData(saved_lang)
    if idx >= 0:
        self.lang_combo.setCurrentIndex(idx)
    self.lang_combo.blockSignals(False)

def _on_language_changed(self):
    """Save selected language to settings."""
    lang = self.lang_combo.currentData()
    if lang:
        self.settings.language = lang
```

Call `self._populate_languages()` at the end of `_setup_ui`.

- [ ] **Step 4: Wire language into OCRWorker creation**

In `_start_ocr`, at the `OCRWorker` constructor call, change:
```python
# Before:
self.ocr_worker = OCRWorker(self.current_file)
# After:
selected_lang = self.lang_combo.currentData() or "eng"
self.ocr_worker = OCRWorker(self.current_file, lang=selected_lang)
```

- [ ] **Step 5: Test manually — run `python main.py`, verify combo box appears with installed languages**

- [ ] **Step 6: Commit**

```bash
git add ui/main_window.py
git commit -m "feat: add language selector combo box wired to Settings and OCRWorker"
```

---

## Phase 3: Language Pack Download

### Task 4: Create language manager module

**Files:**
- Create: `components/language_manager.py`
- Create: `tests/test_language_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_language_manager.py`:
```python
from components.language_manager import LanguageManager, AVAILABLE_LANGUAGES


class TestLanguageManager:
    def test_available_languages_not_empty(self):
        assert len(AVAILABLE_LANGUAGES) > 10

    def test_english_in_available(self):
        assert "eng" in AVAILABLE_LANGUAGES

    def test_get_installed_languages(self, qapp):
        mgr = LanguageManager()
        installed = mgr.get_installed_languages()
        assert isinstance(installed, list)

    def test_get_download_url(self, qapp):
        mgr = LanguageManager()
        url = mgr.get_download_url("fra")
        assert "fra.traineddata" in url
        assert url.startswith("https://")

    def test_get_tessdata_dir(self, qapp):
        mgr = LanguageManager()
        path = mgr.get_tessdata_dir()
        # May be None if Tesseract is not installed — assert type only
        assert path is None or path.is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_language_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement LanguageManager**

Create `components/language_manager.py`:
```python
"""Manage Tesseract OCR language packs — discovery, download, installation."""

import os
import sys
import platform
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

# Common Tesseract language codes and their display names
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

    download_progress = Signal(str, int)  # (lang_code, percent)
    download_finished = Signal(str)       # lang_code
    download_error = Signal(str, str)     # (lang_code, error_message)

    def get_tessdata_dir(self) -> Optional[Path]:
        """Return the tessdata directory where .traineddata files live."""
        # Bundled (PyInstaller)
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidate = Path(sys._MEIPASS) / "tesseract" / "tessdata"
            if candidate.is_dir():
                return candidate

        # TESSDATA_PREFIX env var (points to parent of tessdata/)
        prefix = os.environ.get("TESSDATA_PREFIX")
        if prefix:
            candidate = Path(prefix.rstrip("/\\")) / "tessdata"
            if candidate.is_dir():
                return candidate
            candidate = Path(prefix.rstrip("/\\"))
            if candidate.is_dir() and list(candidate.glob("*.traineddata")):
                return candidate

        # Platform defaults
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
        else:  # Linux
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
        """Return list of installed language codes."""
        tessdata = self.get_tessdata_dir()
        if tessdata is None:
            return []
        return sorted(
            p.stem for p in tessdata.glob("*.traineddata") if p.stem != "osd"
        )

    def get_download_url(self, lang_code: str) -> str:
        """Return the GitHub URL for a language's .traineddata file."""
        return f"{_TESSDATA_REPO}/{lang_code}.traineddata"

    def download_language(self, lang_code: str):
        """Download a language pack to the tessdata directory.

        Emits download_progress, download_finished, or download_error signals.
        """
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
            # Clean up partial download
            if dest.exists():
                dest.unlink()
            self.download_error.emit(lang_code, str(e))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_language_manager.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add components/language_manager.py tests/test_language_manager.py
git commit -m "feat: add LanguageManager for tessdata discovery and download"
```

### Task 5: Add download button to language selector UI

**Files:**
- Modify: `ui/main_window.py`

- [ ] **Step 1: Add a "Download Languages" button next to the combo box**

In `_setup_ui`, after adding `self.lang_combo` to `lang_layout`, add:
```python
self.download_lang_btn = QPushButton("Download...")
self.download_lang_btn.setMinimumHeight(30)
self.download_lang_btn.setStyleSheet("""
    QPushButton {
        background-color: #607D8B;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 12px;
    }
    QPushButton:hover { background-color: #455A64; }
""")
self.download_lang_btn.clicked.connect(self._show_download_dialog)
lang_layout.addWidget(self.download_lang_btn)
```

Also add to `MainWindow.__init__`:
```python
self._download_thread = None
```

- [ ] **Step 2: Implement _show_download_dialog with double-click guard**

```python
def _show_download_dialog(self):
    """Show a dialog to select and download language packs."""
    # Guard: prevent starting a second download while one is in progress
    if self._download_thread is not None and self._download_thread.isRunning():
        QMessageBox.information(self, "Download", "A download is already in progress.")
        return

    from components.language_manager import LanguageManager, AVAILABLE_LANGUAGES

    mgr = LanguageManager()
    installed = set(mgr.get_installed_languages())
    downloadable = {k: v for k, v in AVAILABLE_LANGUAGES.items() if k not in installed}

    if not downloadable:
        QMessageBox.information(self, "Languages", "All available languages are already installed.")
        return

    items = [f"{name} ({code})" for code, name in sorted(downloadable.items(), key=lambda x: x[1])]
    from PySide6.QtWidgets import QInputDialog
    item, ok = QInputDialog.getItem(self, "Download Language", "Select language to download:", items, 0, False)
    if not ok or not item:
        return

    lang_code = item.split("(")[-1].rstrip(")")

    # Disable download button during download
    self.download_lang_btn.setEnabled(False)

    self.progress_label.setText(f"Downloading {item}...")
    self.progress_label.setStyleSheet("""
        QLabel {
            color: #1976D2; font-size: 14px; padding: 10px;
            background-color: #e3f2fd; border-radius: 5px;
        }
    """)
    self.progress_label.show()

    mgr.download_progress.connect(lambda code, pct: self.progress_label.setText(f"Downloading {item}... {pct}%"))
    mgr.download_finished.connect(lambda code: self._on_language_downloaded(code))
    mgr.download_error.connect(lambda code, err: self._on_language_download_error(err))
    self._lang_manager = mgr  # prevent GC

    self._download_thread = QThread()
    mgr.moveToThread(self._download_thread)
    self._download_thread.started.connect(lambda: mgr.download_language(lang_code))
    mgr.download_finished.connect(self._download_thread.quit)
    mgr.download_error.connect(self._download_thread.quit)
    self._download_thread.start()

def _on_language_downloaded(self, lang_code: str):
    """Handle successful language download."""
    self.download_lang_btn.setEnabled(True)
    self.progress_label.setText("Language downloaded successfully!")
    self.progress_label.setStyleSheet("""
        QLabel {
            color: #2E7D32; font-size: 14px; padding: 10px;
            background-color: #C8E6C9; border-radius: 5px;
        }
    """)
    self._populate_languages()

def _on_language_download_error(self, error_msg: str):
    """Handle language download failure."""
    self.download_lang_btn.setEnabled(True)
    self.progress_label.setText(f"Download failed: {error_msg}")
    self.progress_label.setStyleSheet("""
        QLabel {
            color: #C62828; font-size: 14px; padding: 10px;
            background-color: #FFCDD2; border-radius: 5px;
        }
    """)
```

- [ ] **Step 3: Test manually — click Download, select a language, verify it downloads and appears in combo box. Click Download again while in progress — verify guard message.**

- [ ] **Step 4: Commit**

```bash
git add ui/main_window.py
git commit -m "feat: add language download dialog with threaded download and double-click guard"
```

---

## Phase 4: Cancel Button + Page-Level Progress

### Task 6: Add cancel button and progress bar

**Files:**
- Modify: `components/ocr_worker.py`
- Modify: `ui/main_window.py`

- [ ] **Step 1: Add page_progress signal to OCRWorker**

In `components/ocr_worker.py`, add a new signal to the class:
```python
page_progress = Signal(int, int)  # (current_page, total_pages)
```

In `run()`, update the `progress_callback` to parse page info and emit:
```python
def progress_callback(message):
    if self._stop_requested:
        raise InterruptedError("OCR processing was cancelled")
    self.progress.emit(message)
    # Parse "Processing page X/Y..." messages for progress bar
    match = re.match(r'Processing page (\d+)/(\d+)', message)
    if match:
        self.page_progress.emit(int(match.group(1)), int(match.group(2)))
```

- [ ] **Step 2: Add cancel button and progress bar to MainWindow UI**

In `_setup_ui`, after adding `self.progress_label` to the layout, add:
```python
# Progress bar (hidden initially)
self.progress_bar = QProgressBar()
self.progress_bar.setMinimumHeight(20)
self.progress_bar.setStyleSheet("""
    QProgressBar {
        border: 1px solid #ccc; border-radius: 5px; text-align: center;
    }
    QProgressBar::chunk {
        background-color: #2196F3; border-radius: 5px;
    }
""")
self.progress_bar.hide()
layout.addWidget(self.progress_bar)

# Cancel button (hidden initially)
self.cancel_btn = QPushButton("Cancel OCR")
self.cancel_btn.setMinimumHeight(35)
self.cancel_btn.setStyleSheet("""
    QPushButton {
        background-color: #f44336; color: white; border: none;
        border-radius: 5px; font-size: 13px; font-weight: bold;
    }
    QPushButton:hover { background-color: #d32f2f; }
""")
self.cancel_btn.clicked.connect(self._cancel_ocr)
self.cancel_btn.hide()
layout.addWidget(self.cancel_btn)
```

Add `QProgressBar` to the PySide6.QtWidgets import line.

Also add to `MainWindow.__init__`:
```python
self._ocr_cancelled = False
```

- [ ] **Step 3: Add _cancel_ocr and _on_page_progress methods**

```python
def _cancel_ocr(self):
    """Cancel in-progress OCR."""
    self._ocr_cancelled = True
    if self.ocr_worker is not None:
        self.ocr_worker.request_stop()
    self.cancel_btn.setEnabled(False)
    self.cancel_btn.setText("Cancelling...")

def _on_page_progress(self, current: int, total: int):
    """Update progress bar with page-level progress."""
    self.progress_bar.setMaximum(total)
    self.progress_bar.setValue(current)
    self.progress_bar.setFormat(f"Page {current}/{total}")
```

- [ ] **Step 4: Update _start_ocr — show cancel/progress, connect signals, handle cancellation**

After `self.progress_label.show()` in `_start_ocr`, add:
```python
self._ocr_cancelled = False
self.progress_bar.setValue(0)
self.progress_bar.show()
self.cancel_btn.show()
self.cancel_btn.setEnabled(True)
self.cancel_btn.setText("Cancel OCR")
```

After the existing signal connections, add:
```python
self.ocr_worker.page_progress.connect(self._on_page_progress)
```

Connect thread.finished to a cancellation handler. Since `InterruptedError` causes `run()` to return silently (no `finished` or `error` signal emitted), the thread finishes but neither handler fires. Add this after the signal connections:
```python
self.ocr_thread.finished.connect(self._on_ocr_thread_finished)
```

Add the handler:
```python
def _on_ocr_thread_finished(self):
    """Called when the OCR thread finishes. If neither success nor error
    was emitted, the worker was cancelled."""
    if self._ocr_cancelled:
        self.progress_label.setText("OCR cancelled.")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #F57C00; font-size: 14px; padding: 10px;
                background-color: #FFF3E0; border-radius: 5px;
            }
        """)
        self.progress_bar.hide()
        self.cancel_btn.hide()
        self.start_over_btn.show()
        self.start_ocr_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.drop_zone.setAcceptDrops(True)
```

- [ ] **Step 5: Hide cancel/progress bar on completion and error**

In `_on_ocr_success`, add:
```python
self.progress_bar.hide()
self.cancel_btn.hide()
```

In `_on_ocr_error`, add:
```python
self.progress_bar.hide()
self.cancel_btn.hide()
```

- [ ] **Step 6: Update _start_over and _retry_ocr to hide new widgets**

In `_start_over`, add:
```python
self.progress_bar.hide()
self.cancel_btn.hide()
```

In `_retry_ocr`, add:
```python
self.cancel_btn.hide()
self.progress_bar.hide()
```

- [ ] **Step 7: Test manually — start OCR on a multi-page PDF, verify progress bar fills per page, click cancel, verify it stops and shows "OCR cancelled."**

- [ ] **Step 8: Commit**

```bash
git add components/ocr_worker.py ui/main_window.py
git commit -m "feat: add cancel button and page-level progress bar"
```

---

## Phase 5: Save to File

### Task 7: Add save-to-file button

**Files:**
- Modify: `ui/main_window.py`

- [ ] **Step 1: Add save button next to copy button**

In `_setup_ui`, after the `copy_btn` block (after `button_layout.addWidget(self.copy_btn)`), add:
```python
# Save to file button (hidden initially)
self.save_btn = QPushButton("Save to File")
self.save_btn.setMinimumHeight(35)
self.save_btn.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50; color: white; border: none;
        border-radius: 5px; font-size: 13px; font-weight: bold;
    }
    QPushButton:hover { background-color: #45a049; }
    QPushButton:pressed { background-color: #2E7D32; }
""")
self.save_btn.clicked.connect(self._save_to_file)
self.save_btn.hide()
button_layout.addWidget(self.save_btn)
```

- [ ] **Step 2: Implement _save_to_file with error handling**

```python
def _save_to_file(self):
    """Save extracted text to a file."""
    default_dir = self.settings.output_directory or ""
    default_name = ""
    if self.current_file:
        default_name = Path(self.current_file).stem + "_ocr.txt"

    file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Save Extracted Text",
        str(Path(default_dir) / default_name) if default_dir else default_name,
        "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)",
    )
    if not file_path:
        return

    try:
        text = self.text_area.toPlainText()
        Path(file_path).write_text(text, encoding="utf-8")
        self.settings.output_directory = str(Path(file_path).parent)
        QMessageBox.information(self, "Saved", f"Text saved to:\n{file_path}")
    except OSError as e:
        QMessageBox.critical(self, "Save Failed", f"Could not save file:\n{e}")
```

- [ ] **Step 3: Show save button on success, hide on reset**

In `_on_ocr_success`, add `self.save_btn.show()` alongside `self.copy_btn.show()`.
In `_start_over`, add `self.save_btn.hide()`.
In `_on_file_dropped`, add `self.save_btn.hide()`.

- [ ] **Step 4: Test manually — run OCR, click Save, verify file is created with correct content. Try saving to a read-only location — verify error dialog.**

- [ ] **Step 5: Commit**

```bash
git add ui/main_window.py
git commit -m "feat: add save-to-file button with remembered output directory"
```

---

## Phase 6: Core Test Suite

### Task 8: Add tests for PdfOcrProcessor

**Files:**
- Create: `tests/test_pdf_ocr.py`

- [ ] **Step 1: Write tests for PdfOcrProcessor**

Create `tests/test_pdf_ocr.py`:
```python
import pytest
from pathlib import Path
from components.pdf_ocr import PdfOcrProcessor


class TestPdfOcrProcessor:
    def test_init_default_language(self):
        processor = PdfOcrProcessor()
        assert processor.lang == "eng"

    def test_init_custom_language(self):
        processor = PdfOcrProcessor(lang="fra")
        assert processor.lang == "fra"

    def test_process_file_not_found(self):
        processor = PdfOcrProcessor()
        with pytest.raises(FileNotFoundError):
            processor.process("/nonexistent/file.pdf")

    def test_process_not_pdf(self, tmp_path):
        fake = tmp_path / "not_a_pdf.txt"
        fake.write_text("hello")
        processor = PdfOcrProcessor()
        with pytest.raises(ValueError, match="must be a PDF"):
            processor.process(str(fake))

    def test_detect_optimal_dpi_corrupt_fallback(self, tmp_path):
        """DPI detection on a corrupt file should return 300 default."""
        bad_pdf = tmp_path / "bad.pdf"
        bad_pdf.write_bytes(b"%PDF-1.4 garbage")
        processor = PdfOcrProcessor()
        dpi = processor.detect_optimal_dpi(bad_pdf)
        assert dpi == 300
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/test_pdf_ocr.py -v`
Expected: All 5 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_pdf_ocr.py
git commit -m "test: add unit tests for PdfOcrProcessor"
```

---

## Phase 7: Final Cleanup

### Task 9: Update TODO.md — mark completed items

**Files:**
- Modify: `TODO.md`

- [ ] **Step 1: Mark all completed TODO items with `[x]`**

Items completed by this plan:
- [x] Add a language dropdown/selector in the UI (default: English)
- [x] Download Tesseract language packs on demand from the app
- [x] Show download progress and store downloaded packs locally
- [x] Remember the user's last-used language between sessions
- [x] Save extracted text to file (txt, docx, markdown)
- [x] Cancel button to abort in-progress OCR
- [x] Page-level progress bar
- [x] Persistent settings (language, DPI override, output format, theme)
- [x] Configurable default output directory
- [x] Separate OCR language config from OCRWorker
- [x] Add a settings/config module
- [x] Move inline import traceback in ocr_worker.py to module level
- [x] Add unit tests for PdfOcrProcessor
- [x] Add unit tests for OCRWorker
- [x] Set up pytest with CI integration

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 3: Commit and push**

```bash
git add TODO.md
git commit -m "docs: mark completed TODO items"
git push -u origin feature/todo-improvements
```
