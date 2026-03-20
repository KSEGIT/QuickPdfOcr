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
