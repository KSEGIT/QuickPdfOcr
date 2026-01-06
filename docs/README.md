# QuickPdfOcr Website

This directory contains the static website for QuickPdfOcr, hosted on GitHub Pages.

## Website URL

The website is accessible at: https://ksegit.github.io/QuickPdfOcr/

## Structure

- `index.html` - Main landing page with modern design
- Embedded CSS for styling and responsive design
- Uses emojis for icons and visual elements

## Features

The website includes:
- Hero section with primary and secondary CTAs
- What it does section
- Key features showcase (8 feature cards)
- Privacy and offline processing emphasis
- Download section for all platforms (Windows, macOS, Linux)
- Developer section with tech stack and quick start guide
- Footer with links and license information

## Updating the Website

To update the website:
1. Edit `index.html` in this directory
2. Commit and push changes to the main branch
3. GitHub Pages will automatically deploy the changes

## GitHub Pages Configuration

To enable GitHub Pages for this repository:
1. Go to repository Settings
2. Navigate to Pages section
3. Set Source to "Deploy from a branch"
4. Select branch: `main` (or your default branch)
5. Select folder: `/docs`
6. Save

The website will be available at `https://ksegit.github.io/QuickPdfOcr/` within a few minutes.

## Local Development

To test the website locally:

```bash
cd docs
python -m http.server 8000
```

Then open http://localhost:8000/index.html in your browser.

## Design Notes

- Fully responsive design (mobile, tablet, desktop)
- Modern gradient hero section
- Clean, professional UI with good contrast
- All external links open in new tabs where appropriate
- SEO-friendly with proper meta tags
- Accessible HTML structure
