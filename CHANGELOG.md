# Changelog

## [1.8.0](https://github.com/KSEGIT/QuickPdfOcr/compare/v1.7.1...v1.8.0) (2026-09-29)


### Features

* add 'OCR with QuickPdfOcr' to the Finder Services menu ([dd7f33f](https://github.com/KSEGIT/QuickPdfOcr/commit/dd7f33f106323ccc6778680f65862cf2d9c1306a))
* add animated demo GIF, site demo section, and launch marketing kit ([3bdd6dd](https://github.com/KSEGIT/QuickPdfOcr/commit/3bdd6ddd41603eee0d95b2093d39f2d338d6760e))
* add Apple Vision OCR engine for macOS ([d50f5ca](https://github.com/KSEGIT/QuickPdfOcr/commit/d50f5cabdd47408eb09de65625e1d3d22f78d2c9))
* add immutableCreate option to release job ([f8464b6](https://github.com/KSEGIT/QuickPdfOcr/commit/f8464b6add3dd72374a7ce69a6ad225eee6ab7e6))
* add OcrEngine interface and Tesseract implementation ([512f8a1](https://github.com/KSEGIT/QuickPdfOcr/commit/512f8a155a42965d676bb9f54f68c46779aac55c))
* add PageImage boundary type and pytest infrastructure ([eef29b2](https://github.com/KSEGIT/QuickPdfOcr/commit/eef29b2cc799bba283eea3be21a018a703f6d558))
* add pypdfium2 renderer behind a PdfRenderer interface ([96c00da](https://github.com/KSEGIT/QuickPdfOcr/commit/96c00da4bc69db982d8097c96dbdab27a624eb61))
* add terminal chrome to nav, section titles and buttons ([d5d1051](https://github.com/KSEGIT/QuickPdfOcr/commit/d5d10514cee26dd393190349b6e6667a6b52b452))
* align the desktop UI with the terminal brand ([aa5edf5](https://github.com/KSEGIT/QuickPdfOcr/commit/aa5edf5422ddcdd724a50eb121d427c90fdae896))
* align the desktop UI with the terminal brand, and fix Dock icon proportions ([ffc53f3](https://github.com/KSEGIT/QuickPdfOcr/commit/ffc53f3df7fa9394785add2a56b9a60c3aca11e4))
* animated demo GIF, site demo section, launch marketing kit ([5d2bb51](https://github.com/KSEGIT/QuickPdfOcr/commit/5d2bb51015e3c4ab44c849e25aa054ad12875007))
* brand refresh — new icon, hero image, and rebuilt marketing site ([db7ca2c](https://github.com/KSEGIT/QuickPdfOcr/commit/db7ca2c1a891ebed9615a4c81b77822f16438096))
* open PDFs from Finder, the Dock, and the command line ([b5cacee](https://github.com/KSEGIT/QuickPdfOcr/commit/b5cacee1b910202743473e6b8508889e5d95f8ec))
* pivot brand to a terminal/ASCII aesthetic ([b5a24af](https://github.com/KSEGIT/QuickPdfOcr/commit/b5a24af2be4f1f5f15e2a8465d247a209fdc1640))
* re-author icon masters as terminal window plus small-size mark ([b64c967](https://github.com/KSEGIT/QuickPdfOcr/commit/b64c96704d127e63b78269a479871109e5cf2024))
* refresh brand assets and rebuild marketing site ([69f469e](https://github.com/KSEGIT/QuickPdfOcr/commit/69f469e1d9990e3f4a7600b0e34aad4185e992de))
* regenerate hero image as terminal scene for og:image ([1f4d7fb](https://github.com/KSEGIT/QuickPdfOcr/commit/1f4d7fbe5a0067639a6088ffc71f8159a4c99b78))
* remap site palette to the terminal skin ([11b7eb8](https://github.com/KSEGIT/QuickPdfOcr/commit/11b7eb8b04a4657bfeaae4e0b157478cf652d07e))
* render icons from two masters so small sizes stay legible ([55b4c18](https://github.com/KSEGIT/QuickPdfOcr/commit/55b4c18b8a730afe15d9649dcd44b0758ef223db))
* replace hero image with live ASCII terminal ([a92dd08](https://github.com/KSEGIT/QuickPdfOcr/commit/a92dd08b8df22974cb9fa69037ffeb609e163a8e))
* replace inline SVG icons with ASCII character-grid art ([8b94adc](https://github.com/KSEGIT/QuickPdfOcr/commit/8b94adc6fbd370bd79f5b1b36700c116092c3a98))
* select OCR engine by platform and add a language picker ([5c52b50](https://github.com/KSEGIT/QuickPdfOcr/commit/5c52b50cd80b937cd9f5feaf31259c5ed81a8f0c))


### Bug Fixes

* add stride validation to PageImage ([334e19b](https://github.com/KSEGIT/QuickPdfOcr/commit/334e19b1b5089e5b7d40f2b2b0323c03dc611793))
* address 7 post-review defects on brand refresh (a11y, overflow, hover guard, favicon) ([4f221a4](https://github.com/KSEGIT/QuickPdfOcr/commit/4f221a4b25c9ee2214828be7972b3b7d2d83b81a))
* address 8 max-effort review findings on the icon pipeline and docs layout ([a9889c1](https://github.com/KSEGIT/QuickPdfOcr/commit/a9889c1918e5784b12f65463d434abafa497e7f7))
* address code-review findings on the site-fix commits ([4e1febc](https://github.com/KSEGIT/QuickPdfOcr/commit/4e1febccac1e5accaa48b137220a358a24285cf2))
* address CodeRabbit findings on brand-refresh icon pipeline and site radii ([340f229](https://github.com/KSEGIT/QuickPdfOcr/commit/340f22991667b4b657502a8049d854b61e9b3c7b))
* address self-review findings on the icon pipeline fix commit ([1bf70ca](https://github.com/KSEGIT/QuickPdfOcr/commit/1bf70cad113a9473b1d21e9b2aff1bd5319a7484))
* address self-review findings on the post-review fix commit ([f12b467](https://github.com/KSEGIT/QuickPdfOcr/commit/f12b467e82f50554c77a41db88c645a5f0b60d0b))
* address six site-level review findings on brand-refresh ([d7a286c](https://github.com/KSEGIT/QuickPdfOcr/commit/d7a286cb27aea17cbb35ee4e584e55e23937d641))
* address whole-branch review findings on terminal brand refresh ([d5a9987](https://github.com/KSEGIT/QuickPdfOcr/commit/d5a9987defa89822e1ddd373eb24e9c052fb8fed))
* apply CodeRabbit auto-fixes ([7def04a](https://github.com/KSEGIT/QuickPdfOcr/commit/7def04a1a1b6608ebd6dbe3ba8306da0ae631338))
* apply CodeRabbit auto-fixes ([5e36f9f](https://github.com/KSEGIT/QuickPdfOcr/commit/5e36f9f4fa9cea53c175ebce64ed1b6ef38a99f8))
* apply CodeRabbit auto-fixes ([1fdfe12](https://github.com/KSEGIT/QuickPdfOcr/commit/1fdfe1270156f7f22747c2d8659a12c6b618695d))
* apply corrected terminal palette and retarget fills-only guard to --bar ([17e9567](https://github.com/KSEGIT/QuickPdfOcr/commit/17e956771ff0b36f73797d23d83a1111ed7c9ed4))
* bundle the Lucide SVGs and restore drop-zone state on drag-leave ([a63fc67](https://github.com/KSEGIT/QuickPdfOcr/commit/a63fc67a985699f122033d21345a26218f48a5f6))
* close self-review gaps in the icon/hero fix commit ([20cf1ec](https://github.com/KSEGIT/QuickPdfOcr/commit/20cf1ec4545ba2745fb4dafb0b991ffc216b764d))
* draw hero box edges as continuous rects, not per-row glyphs ([e54867a](https://github.com/KSEGIT/QuickPdfOcr/commit/e54867a5809e3dff906efe1c16b58b1ce87338ab))
* group Vision observations into visual lines before ordering ([ddba057](https://github.com/KSEGIT/QuickPdfOcr/commit/ddba057cc498749fec03120452ae41076636a867))
* guard Playwright import and assert exact icon-colour token mapping ([6665f0b](https://github.com/KSEGIT/QuickPdfOcr/commit/6665f0b87ca9d973405019f5d8d5b5df8c73c1c0))
* implement the Cocoa Services provider NSServices declares ([b33d19b](https://github.com/KSEGIT/QuickPdfOcr/commit/b33d19b1a0fec198deaa8fc9037ff212038d2bcd))
* inset the macOS Dock icon's squircle to match neighbouring apps ([56239b3](https://github.com/KSEGIT/QuickPdfOcr/commit/56239b31e76b898edf3be4fc09572a2d35c2a566))
* install Qt system libraries in the browser-tests job ([6f2bd06](https://github.com/KSEGIT/QuickPdfOcr/commit/6f2bd06ff23a5b9f7c2b6bd564f822909d704d15))
* invert filled buttons to dark ink and lift --border-color off --surface ([0dc269a](https://github.com/KSEGIT/QuickPdfOcr/commit/0dc269a3b743bafcd1b704a72ab16df15c154b97))
* let per-card icon colour classes reach the ASCII art ([828f8aa](https://github.com/KSEGIT/QuickPdfOcr/commit/828f8aaa89c8593a73cdb903e9f2745c8187a22e))
* make the two-master split test runnable in CI ([9f92e86](https://github.com/KSEGIT/QuickPdfOcr/commit/9f92e864a14ee70bbeccbcad00c4ae70d22619f7))
* prevent hero terminal clipping between 769px and ~1130px ([c4beb8c](https://github.com/KSEGIT/QuickPdfOcr/commit/c4beb8cdd049fd4c0440b6f4efe1fb32b6cb5c64))
* prevent the OCR controls from being stranded disabled ([2a514b9](https://github.com/KSEGIT/QuickPdfOcr/commit/2a514b975d7dd4ecfa5d44111e07b29dafc61f1c))
* propagate FileNotFoundError from detect_optimal_dpi; strengthen page-failure containment test ([bf8ac71](https://github.com/KSEGIT/QuickPdfOcr/commit/bf8ac713ab21267a32307f35f5321917a744bdff))
* purge --frame text-colour violations and close alias hole in guard test ([a18cc74](https://github.com/KSEGIT/QuickPdfOcr/commit/a18cc74e108ec4487c476b3e0957ed4b18e414c8))
* refuse open_file() while an OCR run is in progress ([28a5ba0](https://github.com/KSEGIT/QuickPdfOcr/commit/28a5ba05f18dff96408e04474301be35ca24dafd))
* reject mismatched rasters in _abs_diff instead of truncating ([fd26fc0](https://github.com/KSEGIT/QuickPdfOcr/commit/fd26fc025d0fa7801b69332e7b48d175c48cd62a))
* release workflow shipped the exact Poppler-bundling defect this plan fixes ([cf74389](https://github.com/KSEGIT/QuickPdfOcr/commit/cf74389af086714316b70597228415326ce292a1))
* repair the test suite so release builds go green on all platforms ([4135aa5](https://github.com/KSEGIT/QuickPdfOcr/commit/4135aa557f44b2a321e2e144287a933e2643106e))
* split ink/fill tokens per hue, finish Step 6 sweep, guard the gradient ([0dfecde](https://github.com/KSEGIT/QuickPdfOcr/commit/0dfecde2c0ee28703dcc6965a316c907a840fa77))
* strip every page header in --selftest, not just page 1 ([c580e33](https://github.com/KSEGIT/QuickPdfOcr/commit/c580e33046abfe1060e5e3010dcc4660a15dced0))
* validate pixel mode comes from library, not hardcoded constant ([b0cd0a0](https://github.com/KSEGIT/QuickPdfOcr/commit/b0cd0a07c252288d049fbf40e429e3a6b4181a0a))
* wait for the hover transition to settle before reading border colour ([c98eea4](https://github.com/KSEGIT/QuickPdfOcr/commit/c98eea4be028cb3e34b33485b3d665df888c0fa3))

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
