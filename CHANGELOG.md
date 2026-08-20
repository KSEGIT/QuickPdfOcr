# Changelog

## [1.8.0](https://github.com/KSEGIT/QuickPdfOcr/compare/v1.7.1...v1.8.0) (2026-08-20)


### Features

* add terminal chrome to nav, section titles and buttons ([cda987c](https://github.com/KSEGIT/QuickPdfOcr/commit/cda987ca2cb89a9a3d11b4506eb05a1434a89312))
* pivot brand to a terminal/ASCII aesthetic ([ac57424](https://github.com/KSEGIT/QuickPdfOcr/commit/ac57424582116992dc0529c5bdd655c51ffb1b07))
* re-author icon masters as terminal window plus small-size mark ([de07ef1](https://github.com/KSEGIT/QuickPdfOcr/commit/de07ef1ee5fb95960dfaf656d94e91ccbe6f58eb))
* regenerate hero image as terminal scene for og:image ([4803a9f](https://github.com/KSEGIT/QuickPdfOcr/commit/4803a9fe6053defa30e88ed309be54a02a248b61))
* remap site palette to the terminal skin ([7cbe906](https://github.com/KSEGIT/QuickPdfOcr/commit/7cbe906bc659e15065b70f9a11451120ff8178cc))
* render icons from two masters so small sizes stay legible ([cba1dd1](https://github.com/KSEGIT/QuickPdfOcr/commit/cba1dd154b43beca93220d85cac8063cc522fecc))
* replace hero image with live ASCII terminal ([10a1492](https://github.com/KSEGIT/QuickPdfOcr/commit/10a149209e0a38db159a2b58b74c07071f88b8c4))
* replace inline SVG icons with ASCII character-grid art ([6a23691](https://github.com/KSEGIT/QuickPdfOcr/commit/6a2369191ab39ca74111170bbf499b03d8168681))


### Bug Fixes

* address 7 post-review defects on brand refresh (a11y, overflow, hover guard, favicon) ([cac5559](https://github.com/KSEGIT/QuickPdfOcr/commit/cac55595112f272374059a663c7afb60b2f2a748))
* address 8 max-effort review findings on the icon pipeline and docs layout ([da42f77](https://github.com/KSEGIT/QuickPdfOcr/commit/da42f7794fb0d0866e894473052494cf08d6d4e1))
* address code-review findings on the site-fix commits ([37c7366](https://github.com/KSEGIT/QuickPdfOcr/commit/37c7366de71933c01d9a00cc7105ebc86c693968))
* address CodeRabbit findings on brand-refresh icon pipeline and site radii ([903d2f5](https://github.com/KSEGIT/QuickPdfOcr/commit/903d2f5c8d9c22edb9a1cb25f1adc0086611f9f0))
* address self-review findings on the icon pipeline fix commit ([285e912](https://github.com/KSEGIT/QuickPdfOcr/commit/285e912d502b24aed60e4aeb92bfd6de81ab11d4))
* address self-review findings on the post-review fix commit ([0e80080](https://github.com/KSEGIT/QuickPdfOcr/commit/0e800801b272327dc058bac0d07122bde1e12756))
* address six site-level review findings on brand-refresh ([c0c5177](https://github.com/KSEGIT/QuickPdfOcr/commit/c0c5177e63f6390d96ee570e3941393e265808ed))
* address whole-branch review findings on terminal brand refresh ([321dfcb](https://github.com/KSEGIT/QuickPdfOcr/commit/321dfcb784e46d08333d2e0dbbe7395aa6fe6982))
* apply CodeRabbit auto-fixes ([3b517c0](https://github.com/KSEGIT/QuickPdfOcr/commit/3b517c0ee5b3aa6b69ef6706422de64a66681172))
* apply corrected terminal palette and retarget fills-only guard to --bar ([f1de195](https://github.com/KSEGIT/QuickPdfOcr/commit/f1de1959ce2f8af90da4854a026ec7bdda9def9b))
* close self-review gaps in the icon/hero fix commit ([7d6c6a9](https://github.com/KSEGIT/QuickPdfOcr/commit/7d6c6a98c17fea05bccb1c27a9c08378b66fbcd2))
* draw hero box edges as continuous rects, not per-row glyphs ([d7bd460](https://github.com/KSEGIT/QuickPdfOcr/commit/d7bd4605b9cb6be1a4d5083a769ba5b446b98a48))
* guard Playwright import and assert exact icon-colour token mapping ([0c9bd10](https://github.com/KSEGIT/QuickPdfOcr/commit/0c9bd10b31d8fe62a5f480a8098b258b8b74f658))
* install Qt system libraries in the browser-tests job ([2272c2c](https://github.com/KSEGIT/QuickPdfOcr/commit/2272c2cbd441d73f56b0ecc7060e1b33407c085a))
* invert filled buttons to dark ink and lift --border-color off --surface ([d12f217](https://github.com/KSEGIT/QuickPdfOcr/commit/d12f217fbb186acbadf018ee44ad9db352ffbc40))
* let per-card icon colour classes reach the ASCII art ([2c18704](https://github.com/KSEGIT/QuickPdfOcr/commit/2c18704d925cb07d409240abe092a5add49f6cfe))
* make the two-master split test runnable in CI ([a023ba3](https://github.com/KSEGIT/QuickPdfOcr/commit/a023ba3882453516db3aec66ee1a850739b3e635))
* prevent hero terminal clipping between 769px and ~1130px ([b63991d](https://github.com/KSEGIT/QuickPdfOcr/commit/b63991dd0dba8c3fb15b26226cf055444144bcf2))
* purge --frame text-colour violations and close alias hole in guard test ([0573157](https://github.com/KSEGIT/QuickPdfOcr/commit/05731570edb1495815ff69913ee2b5b5bdffcaea))
* split ink/fill tokens per hue, finish Step 6 sweep, guard the gradient ([70e3fa0](https://github.com/KSEGIT/QuickPdfOcr/commit/70e3fa0fdf57ce32ca0d5813716edfe0b977eada))
* wait for the hover transition to settle before reading border colour ([819bc8e](https://github.com/KSEGIT/QuickPdfOcr/commit/819bc8e15cb50407343f50e50c3a03553ba5db6e))

## [1.7.1](https://github.com/KSEGIT/QuickPdfOcr/compare/v1.6.0...v1.7.1) (2026-08-09)

Re-release of 1.7.0 with working release automation. The v1.6.0/v1.7.0
tag names are permanently retired: they belonged to immutable releases
that were deleted while the pipeline was being repaired, and GitHub
never allows such tag names to be reused.

### Bug Fixes

* repair the test suite so release builds go green on all platforms ([0223c53](https://github.com/KSEGIT/QuickPdfOcr/commit/0223c53))

### CI

* run the test suite on PRs and pushes to main so a broken suite can no longer block a release at build time
* publish the release automatically once binaries are attached ([1c9a0d0](https://github.com/KSEGIT/QuickPdfOcr/commit/1c9a0d0))
* create release-please releases as drafts so binaries can be attached under immutable releases ([7cb1130](https://github.com/KSEGIT/QuickPdfOcr/commit/7cb1130))
* install Qt runtime libraries and run Linux tests offscreen ([e101a3c](https://github.com/KSEGIT/QuickPdfOcr/commit/e101a3c))
* fix tag-exists guard for release-please-triggered builds ([4fb3133](https://github.com/KSEGIT/QuickPdfOcr/commit/4fb3133))

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
