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
