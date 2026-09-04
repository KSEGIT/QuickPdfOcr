# QuickPdfOcr Launch Kit

Plain voice. Short sentences. No hype. No emoji in posts.

Links used everywhere:

- Repo: https://github.com/KSEGIT/QuickPdfOcr
- Releases: https://github.com/KSEGIT/QuickPdfOcr/releases/latest
- Site: https://ksegit.github.io/QuickPdfOcr/
- Author: KSEGIT

## 1. Positioning

**Hook:** QuickPdfOcr OCRs scanned PDFs on your own machine — drop the file, click Start OCR, copy the text. Nothing is uploaded anywhere.

**Pillars:**

1. **Local and private by design.** OCR runs on-device. No uploads, no cloud processing, no data collection, no account.
2. **Zero-install on macOS.** On macOS 13+ the app uses the Vision framework built into the OS. The pre-built `.app` bundles Python and PDF rendering (`pypdfium2`). No Homebrew, no Poppler, no Tesseract. Download and run.
3. **Dead-simple GUI.** Drag a PDF in (or use the file picker), click Start OCR, watch the progress bar, copy the text to the clipboard with one click. On macOS you can also drop a PDF on the Dock icon, use Open With, or the Finder Services menu.

Facts to keep straight in every channel:

- No cloud, ever. OCR is on-device on all platforms.
- No Poppler, ever. PDF rendering is bundled (`pypdfium2`) on every platform.
- No Tesseract on macOS. macOS uses Apple Vision. Tesseract is the engine on Windows/Linux only, and it is **not** bundled there — users install it separately.
- macOS build is universal2 (Apple Silicon + Intel), ad-hoc signed, **not notarized** — first launch needs System Settings → Privacy & Security → Open Anyway. Say this when it matters (macOS-focused channels); hiding it causes support threads.
- Requires macOS 13 (Ventura) or later.
- MIT license. Free.

## 2. Show HN

**Title:**

```
Show HN: QuickPdfOcr – local OCR for scanned PDFs with a one-window GUI
```

**First comment (post within minutes of submitting):**

```
Hi HN, I built QuickPdfOcr and I'm happy to answer questions.

What it is: a small desktop app that extracts text from scanned PDFs. You drag a
PDF into the window, click Start OCR, and copy the result to your clipboard. The
whole run stays on your machine — no uploads, no cloud API.

Why I built it: every free OCR path I found was either a web upload (a no-go for
contracts and medical documents) or a CLI chain that meant installing Poppler and
Tesseract first. I wanted a double-clickable app my non-technical family could use
on files they would never upload.

Tech stack: PySide6 (Qt6) for the GUI. On macOS 13+ OCR uses Apple's Vision
framework via pyobjc, so the app needs nothing installed beyond the .app itself.
On Windows and Linux it drives Tesseract. PDF pages are rendered with pypdfium2,
which ships inside the bundle — there is no Poppler dependency on any platform.
The macOS build is a universal2 binary covering Apple Silicon and Intel.

Honest caveats: the macOS build is ad-hoc signed, not notarized, so first launch
needs one "Open Anyway" click in Privacy & Security. Windows/Linux builds require
installing Tesseract separately.

What's next: batch OCR of multiple files in one run, and a searchable-PDF output
mode (text layer written back into the PDF) instead of clipboard-only.

Repo: https://github.com/KSEGIT/QuickPdfOcr
Download (macOS/Windows/Linux): https://github.com/KSEGIT/QuickPdfOcr/releases/latest
```

Rules to respect: post Tue–Thu, 8–10am PT. One shot — the post must work on its own. Never ask for upvotes, in the post or in comments. Answer every comment with substance.

## 3. Product Hunt

**Tagline (57 chars, limit 60):**

```
OCR scanned PDFs on your Mac. Nothing leaves the machine.
```

**Description (347 chars, limit 500):**

```
QuickPdfOcr extracts text from scanned PDFs on your desktop. Drop a PDF, click
Start OCR, copy the text to your clipboard. Everything runs locally — no uploads,
no cloud, no account. On macOS 13+ it uses the Vision framework built into the OS,
so there is nothing to install. Windows and Linux builds use Tesseract OCR. Free
and open source (MIT).
```

**Maker first comment:**

```
Hi Product Hunt, maker here.

I built QuickPdfOcr because the free OCR options split into two bad camps: web
tools that make you upload the document, and command-line setups that need Poppler
and Tesseract installed first. I wanted a desktop app that does the job locally
and that anyone can run by double-clicking.

Who it's for: anyone with scanned contracts, receipts, or paper archives they
don't want on someone else's server. On macOS it's the zero-setup option — OCR
comes from the Vision framework already in macOS 13+, so the .app is the whole
install. Windows and Linux builds work too, with Tesseract as the engine.

What it does today: drag-and-drop or file picker, a live progress bar while it
runs, one click to copy the extracted text, and retry/start-over when a file
fails. On macOS it also hooks into the Dock, Open With, and Finder Services.

It's free and MIT-licensed: https://github.com/KSEGIT/QuickPdfOcr

I'd love feedback on two things: is batch OCR (a folder of PDFs in one run) or
searchable-PDF output more useful to you? And if you hit a PDF it chokes on, I
want to know.
```

Ask for feedback, never for upvotes.

**Gallery asset checklist:**

| Slot | Asset | Size | Status |
|---|---|---|---|
| Thumbnail | `resources/icon_512.png` downscaled to 240×240, <3MB. First frame must work static — the icon does. | 240×240 | needs export |
| Gallery 1 | Promo GIF `docs/assets/quickpdfocr-demo.gif` re-rendered at 1270×760 (drop → Start OCR → progress → "4,812 words copied"). No strobing. | 1270×760 | in production |
| Gallery 2 | Real-app screenshot: main window mid-OCR with progress bar, on macOS, light and dark chrome cropped out. | 1270×760 | to capture |
| Gallery 3 | Screenshot of the clipboard result — pasted text in a text editor, plus the app's copy button visible. | 1270×760 | to capture |

Launch at 12:01am PT to get the full day on the front page.

## 4. X/Twitter

Both posts attach the promo GIF `docs/assets/quickpdfocr-demo.gif` (≤2MB, under the 15MB limit; 1200×675 is the right aspect). The first frame must read on its own: it shows the app window with the PDF card dropping toward the empty drop zone, before the beam moves.

**Variant 1 — launch (240 chars, limit 280):**

```
$ QuickPdfOcr — OCR scanned PDFs on your own machine. No cloud, no uploads. On
macOS 13+ it uses the built-in Vision framework: download the .app and run,
nothing to install. Free and open source (MIT).
https://github.com/KSEGIT/QuickPdfOcr
```

**Variant 2 — feature angle (240 chars, limit 280):**

```
No Poppler. No Tesseract install on macOS. QuickPdfOcr bundles PDF rendering
(pypdfium2) and uses the Vision framework built into macOS 13+. Drag a PDF in,
click Start OCR, text lands on your clipboard.
https://ksegit.github.io/QuickPdfOcr/
```

Hashtags: at most one, `#opensource`, and only if the post is short. Skip them otherwise.

## 5. Reddit

One tailored post per sub. Do not cross-post identical copy. Keep the account's self-promotion ratio at or under 1 in 10 by participating in each sub before posting. Every post carries a disclosure line.

### r/macapps — angle: native macOS citizen

**Title:** `[Free & Open Source] QuickPdfOcr — OCR scanned PDFs locally with the Vision framework; Dock, Open With and Finder Services support`

**Body:**

```
I built QuickPdfOcr, a small app that turns scanned PDFs into copyable text, and
I'm the author.

It does OCR with the Vision framework built into macOS 13+, so the .app is the
entire install — no Homebrew, no Tesseract, no Poppler. Drag a PDF in, click
Start OCR, copy the text.

It also behaves like a proper Mac app: drop a PDF on the Dock icon, right-click →
Open With, or use Finder → Services → "OCR with QuickPdfOcr" (launch the app once
first so macOS registers the service). The build is universal2, so Apple Silicon
and Intel are one download.

Two honest caveats: it's ad-hoc signed, not notarized — first launch needs one
"Open Anyway" in System Settings → Privacy & Security. And it's clipboard-only for
now; searchable-PDF output is on the roadmap.

Everything runs on-device. Free, MIT license.
Download: https://github.com/KSEGIT/QuickPdfOcr/releases/latest
Source: https://github.com/KSEGIT/QuickPdfOcr
```

### r/selfhosted — angle: data never leaves your hardware

**Title:** `QuickPdfOcr: fully offline OCR for scanned PDFs — your documents never leave the machine`

No link in the title. Body first, link at the end.

**Body:**

```
Disclosure: I'm the author.

QuickPdfOcr is a desktop app for OCRing scanned PDFs with zero network traffic.
It does OCR on-device — Apple Vision on macOS, Tesseract on Windows/Linux — so
nothing is uploaded and there is no server component to trust or to maintain.
PDF rendering is bundled (pypdfium2), which removes the usual Poppler dependency.

It's not a service you host; it's the alternative for documents you'd never send
to a hosted OCR API: contracts, medical records, bank statements. If your threat
model is "the file must not leave this machine," that's the whole design.

It's production-ready: pre-built installers for all three platforms, an automated
test suite that runs before every release build, and full docs in the README
including troubleshooting and build-from-source. On macOS 13+ the .app is the
complete install. Windows/Linux need Tesseract installed separately — the one
dependency it doesn't bundle.

Free, MIT license.
Repo, docs, and downloads: https://github.com/KSEGIT/QuickPdfOcr
```

### r/opensource — angle: the stack and the license

**Title:** `QuickPdfOcr (MIT): desktop OCR for scanned PDFs — PySide6 GUI, Apple Vision on macOS, Tesseract on Win/Linux, pypdfium2 rendering`

**Body:**

```
Author here. QuickPdfOcr is an MIT-licensed desktop app that OCRs scanned PDFs
locally and puts the text on your clipboard.

The stack, briefly:

- PySide6 (Qt6) GUI: drag-and-drop, progress bar, one-click copy
- OCR backends: Apple Vision via pyobjc on macOS 13+, pytesseract on Windows/Linux
- PDF rendering: pypdfium2 bundled on every platform — no Poppler anywhere
- Packaging: PyInstaller onedir builds, universal2 on macOS, built in GitHub
  Actions with the pytest suite gating every release

The interesting engineering bit is the backend split: on macOS the OCR engine is
part of the OS, so the shipped binary has zero external dependencies; off-macOS
Tesseract is the one thing users install. The OCR layer sits behind a common
interface, so adding another engine is a small patch.

Contributions welcome — issues and PRs both. Good first areas: batch processing,
searchable-PDF output, additional Tesseract language packs in CI tests.

https://github.com/KSEGIT/QuickPdfOcr
```

### r/SideProject — angle: the story

**Title:** `I built a free desktop app that OCRs scanned PDFs locally, after watching my dad upload a contract to a random website`

**Body:**

```
Author disclosure: this is my project.

The story: my dad needed text out of a scanned contract. His first instinct was a
free OCR website — upload the file, download the text. The alternatives I pointed
him at were CLI tools that wanted Poppler and Tesseract installed first. Neither
was acceptable, so I built the thing in between.

QuickPdfOcr is a one-window desktop app. Drag a PDF in, click Start OCR, copy the
text. On macOS 13+ it uses the Vision framework that ships with the OS, so the
.app is the whole install — that was the hardest and most valuable decision, and
it's why macOS users never touch a package manager. Windows and Linux builds use
Tesseract (installed separately). PDF rendering is bundled via pypdfium2 on all
platforms.

It's free and open source (MIT). What's next: batch OCR and searchable-PDF
output. Feedback very welcome — especially from anyone who's tried to OCR on a
machine where they can't install system packages.

Site: https://ksegit.github.io/QuickPdfOcr/
Code: https://github.com/KSEGIT/QuickPdfOcr
```

Do not post to zero-tolerance subs (r/programming and similar). Participate there in comments only, without pitching.

## 6. Launch sequence

Ordered checklist. One channel at a time; fix what each channel surfaces before the next.

- [ ] **T-7 days:** Confirm the promo GIF exists at `docs/assets/quickpdfocr-demo.gif` and its first frame reads standing alone. Export the PH thumbnail (240×240) from `resources/icon_512.png`. Capture PH gallery screenshots 2 and 3. Verify download links on the site and in this kit point at `releases/latest`.
- [ ] **T-7 to T-1 days:** Build reddit karma and history in r/macapps, r/selfhosted, r/opensource, r/SideProject by commenting helpfully, not promoting. Get the account above each sub's minimums and inside the 9:1 guideline.
- [ ] **Day 0, Tue–Thu, 8–10am PT: Show HN.** Submit the title from §2. Post the first comment within minutes. Stay in the thread all day; never mention upvotes.
- [ ] **Day 0–2:** Answer every HN comment. Note every bug report and complaint; these feed the iteration before PH.
- [ ] **Same week: Reddit.** Post r/macapps first (strongest fit), then r/SideProject (story), then r/opensource (stack), then r/selfhosted (privacy). Space them by at least a day; tailor, never cross-post.
- [ ] **Day 0, whenever scheduled: X/Twitter.** Post variant 1 with the GIF at Show HN time. Post variant 2 two to three days later.
- [ ] **Following week: fix, then PH.** Ship fixes for what HN and reddit surfaced. Launch on Product Hunt at 12:01am PT with the maker comment from §3 posted immediately.
- [ ] **PH day:** Maker active in comments all day. Ask for feedback, never upvotes.
- [ ] **After:** Write up results (traffic, stars, feedback themes) and fold the learnings back into the README and site copy.

## 7. Asset inventory

| Asset | Path | Size / dims | Use |
|---|---|---|---|
| Promo GIF | `docs/assets/quickpdfocr-demo.gif` | 1200×675, ~9s loop, ≤2MB | X posts, PH gallery (re-render at 1270×760), README later |
| og:image | `resources/quick_pdf_hero_small.jpg` | 1920×1080, 94KB | Link previews (already wired into the site) |
| App icon, large master | `resources/icon.svg` → `resources/icon_512.png` | 512×512, 112KB | PH thumbnail source (export at 240×240), press/avatar |
| App icon, runtime | `resources/icon.png` | 256×256, 35KB | In-app icon; site logo is `docs/assets/logo.png` (64×64) |
| Favicon | `resources/favicon.png` | 32×32, 1.3KB | Site only; not a marketing asset |
| Platform icons | `resources/icon.icns`, `resources/icon.ico` | 1MB / 51KB | Packaging only |

**To capture later:**

- PH gallery screenshot 2 (1270×760): the real app mid-OCR, progress bar visible. The GIF covers the flow, but PH reviewers expect at least one static shot of the actual UI.
- PH gallery screenshot 3 (1270×760): pasted OCR result next to the app, proving the clipboard step.
- Optional: a 15–30s narrated MP4 walkthrough for the PH "video" slot, cut from the same screen recording as the GIF.
- Windows and Linux screenshots, if a cross-platform post is planned later — all current assets show the macOS build.

---
This kit supports the promo GIF at `docs/assets/quickpdfocr-demo.gif`.
