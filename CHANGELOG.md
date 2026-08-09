# Changelog

## [1.7.0](https://github.com/KSEGIT/QuickPdfOcr/compare/v1.6.0...v1.7.0) (2026-08-09)


### Features

* add 'OCR with QuickPdfOcr' to the Finder Services menu ([4ce8330](https://github.com/KSEGIT/QuickPdfOcr/commit/4ce833028f6b33b3baf1c11cd7e82e4d20172e22))
* add Apple Vision OCR engine for macOS ([b776939](https://github.com/KSEGIT/QuickPdfOcr/commit/b776939d3024b6b201a13f58e76bd46ff2488ca2))
* add immutableCreate option to release job ([ae83952](https://github.com/KSEGIT/QuickPdfOcr/commit/ae839529f104089690107b37b64e97c90460c709))
* add OcrEngine interface and Tesseract implementation ([5fbaf98](https://github.com/KSEGIT/QuickPdfOcr/commit/5fbaf9810136bce95553551080a933a8b05b1fb1))
* add PageImage boundary type and pytest infrastructure ([89fde09](https://github.com/KSEGIT/QuickPdfOcr/commit/89fde099dbfa513fa1f1780fcfeaf97b8e5a4a5e))
* add pypdfium2 renderer behind a PdfRenderer interface ([5e537b5](https://github.com/KSEGIT/QuickPdfOcr/commit/5e537b50816887ed17e2f5e3cfb17b5e8cbea623))
* brand refresh — new icon, hero image, and rebuilt marketing site ([2c7acb5](https://github.com/KSEGIT/QuickPdfOcr/commit/2c7acb5f497658db59cda2f2b2e227cf6cabfe19))
* open PDFs from Finder, the Dock, and the command line ([76af107](https://github.com/KSEGIT/QuickPdfOcr/commit/76af107ca783796d88d523fcbc78988e2753e8f5))
* refresh brand assets and rebuild marketing site ([a642a3f](https://github.com/KSEGIT/QuickPdfOcr/commit/a642a3f8b560ca8afb1467da027fb0ba4e1a1123))
* select OCR engine by platform and add a language picker ([34e9de9](https://github.com/KSEGIT/QuickPdfOcr/commit/34e9de9e547d27814ae705a1c37569345358e607))


### Bug Fixes

* add stride validation to PageImage ([ddef597](https://github.com/KSEGIT/QuickPdfOcr/commit/ddef597809bc2a0447842b67ad853d406df78e4d))
* apply CodeRabbit auto-fixes ([c283131](https://github.com/KSEGIT/QuickPdfOcr/commit/c283131406a9c80734834cb0f50080ea394ced36))
* apply CodeRabbit auto-fixes ([428b6f5](https://github.com/KSEGIT/QuickPdfOcr/commit/428b6f545cbd8a100876bb7dea1506ff72509dce))
* group Vision observations into visual lines before ordering ([2330145](https://github.com/KSEGIT/QuickPdfOcr/commit/233014526350c274040fc7930285e1fe7448c955))
* implement the Cocoa Services provider NSServices declares ([3f40b1c](https://github.com/KSEGIT/QuickPdfOcr/commit/3f40b1c47d4acaa3a2901d08c4180a5ae951d437))
* prevent the OCR controls from being stranded disabled ([7f0b648](https://github.com/KSEGIT/QuickPdfOcr/commit/7f0b64836e1d7943090114be8c3327b30f63e275))
* propagate FileNotFoundError from detect_optimal_dpi; strengthen page-failure containment test ([18f0e02](https://github.com/KSEGIT/QuickPdfOcr/commit/18f0e028c0024245ca8bf8be77a5bfc2e7313e44))
* refuse open_file() while an OCR run is in progress ([76538eb](https://github.com/KSEGIT/QuickPdfOcr/commit/76538eb37e4a677952a5ba67442d26e96c9015c4))
* release workflow shipped the exact Poppler-bundling defect this plan fixes ([2185ba6](https://github.com/KSEGIT/QuickPdfOcr/commit/2185ba6dd963c63255ea65b43ee81ea8d72ddadb))
* repair the test suite so release builds go green on all platforms ([0223c53](https://github.com/KSEGIT/QuickPdfOcr/commit/0223c53f163eb3f8bab1ebb857c00ccb0135e0a2))
* strip every page header in --selftest, not just page 1 ([ba3c172](https://github.com/KSEGIT/QuickPdfOcr/commit/ba3c17233ee6c04cbb0992c49c8933be471f9a05))
* validate pixel mode comes from library, not hardcoded constant ([c756d97](https://github.com/KSEGIT/QuickPdfOcr/commit/c756d9731bd2467a564fb7eceec376edb252cae1))

## [1.6.0](https://github.com/KSEGIT/QuickPdfOcr/compare/v1.5.0...v1.6.0) (2026-08-09)


### Features

* add 'OCR with QuickPdfOcr' to the Finder Services menu ([4ce8330](https://github.com/KSEGIT/QuickPdfOcr/commit/4ce833028f6b33b3baf1c11cd7e82e4d20172e22))
* add Apple Vision OCR engine for macOS ([b776939](https://github.com/KSEGIT/QuickPdfOcr/commit/b776939d3024b6b201a13f58e76bd46ff2488ca2))
* add OcrEngine interface and Tesseract implementation ([5fbaf98](https://github.com/KSEGIT/QuickPdfOcr/commit/5fbaf9810136bce95553551080a933a8b05b1fb1))
* add PageImage boundary type and pytest infrastructure ([89fde09](https://github.com/KSEGIT/QuickPdfOcr/commit/89fde099dbfa513fa1f1780fcfeaf97b8e5a4a5e))
* add pypdfium2 renderer behind a PdfRenderer interface ([5e537b5](https://github.com/KSEGIT/QuickPdfOcr/commit/5e537b50816887ed17e2f5e3cfb17b5e8cbea623))
* brand refresh — new icon, hero image, and rebuilt marketing site ([2c7acb5](https://github.com/KSEGIT/QuickPdfOcr/commit/2c7acb5f497658db59cda2f2b2e227cf6cabfe19))
* open PDFs from Finder, the Dock, and the command line ([76af107](https://github.com/KSEGIT/QuickPdfOcr/commit/76af107ca783796d88d523fcbc78988e2753e8f5))
* refresh brand assets and rebuild marketing site ([a642a3f](https://github.com/KSEGIT/QuickPdfOcr/commit/a642a3f8b560ca8afb1467da027fb0ba4e1a1123))
* select OCR engine by platform and add a language picker ([34e9de9](https://github.com/KSEGIT/QuickPdfOcr/commit/34e9de9e547d27814ae705a1c37569345358e607))


### Bug Fixes

* add stride validation to PageImage ([ddef597](https://github.com/KSEGIT/QuickPdfOcr/commit/ddef597809bc2a0447842b67ad853d406df78e4d))
* apply CodeRabbit auto-fixes ([c283131](https://github.com/KSEGIT/QuickPdfOcr/commit/c283131406a9c80734834cb0f50080ea394ced36))
* apply CodeRabbit auto-fixes ([428b6f5](https://github.com/KSEGIT/QuickPdfOcr/commit/428b6f545cbd8a100876bb7dea1506ff72509dce))
* group Vision observations into visual lines before ordering ([2330145](https://github.com/KSEGIT/QuickPdfOcr/commit/233014526350c274040fc7930285e1fe7448c955))
* implement the Cocoa Services provider NSServices declares ([3f40b1c](https://github.com/KSEGIT/QuickPdfOcr/commit/3f40b1c47d4acaa3a2901d08c4180a5ae951d437))
* prevent the OCR controls from being stranded disabled ([7f0b648](https://github.com/KSEGIT/QuickPdfOcr/commit/7f0b64836e1d7943090114be8c3327b30f63e275))
* propagate FileNotFoundError from detect_optimal_dpi; strengthen page-failure containment test ([18f0e02](https://github.com/KSEGIT/QuickPdfOcr/commit/18f0e028c0024245ca8bf8be77a5bfc2e7313e44))
* refuse open_file() while an OCR run is in progress ([76538eb](https://github.com/KSEGIT/QuickPdfOcr/commit/76538eb37e4a677952a5ba67442d26e96c9015c4))
* release workflow shipped the exact Poppler-bundling defect this plan fixes ([2185ba6](https://github.com/KSEGIT/QuickPdfOcr/commit/2185ba6dd963c63255ea65b43ee81ea8d72ddadb))
* strip every page header in --selftest, not just page 1 ([ba3c172](https://github.com/KSEGIT/QuickPdfOcr/commit/ba3c17233ee6c04cbb0992c49c8933be471f9a05))
* validate pixel mode comes from library, not hardcoded constant ([c756d97](https://github.com/KSEGIT/QuickPdfOcr/commit/c756d9731bd2467a564fb7eceec376edb252cae1))
