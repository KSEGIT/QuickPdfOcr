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
        assert path is None or path.is_dir()
