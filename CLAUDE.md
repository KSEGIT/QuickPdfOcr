# QuickPdfOcr — repo notes for agentic workers

## `docs/` is the public GitHub Pages publish root

GitHub Pages serves this repo from `main:/docs` (Settings → Pages → "Deploy
from a branch" → `main` / `/docs`). `docs/.nojekyll` disables Jekyll, which
also removes Jekyll's `exclude:` mechanism — so there is no way to keep a
file under `docs/` out of the published site. Anything committed under
`docs/` on `main` is live, world-readable, and indexable at
`https://ksegit.github.io/QuickPdfOcr/...` within minutes of merging.

**Do not place internal documents under `docs/`.** That includes agent
planning/spec documents, design-review scratch, screenshots kept only as
review evidence, and anything else not meant for the public site. Internal
planning documents live in `plans/` (implementation plans and their specs)
and `design/` (design briefs) at the repo root — both outside the Pages
root, so they stay private to the repository.

Before adding a new file under `docs/`, confirm it is meant to be public.
Two kinds of file belong there:

1. The marketing site itself — `docs/index.html`, `docs/assets/`, and
   `docs/README.md` documenting the site.
2. **Public user documentation** — the guides the README links out to
   (`docs/installation.md`, `docs/usage.md`, `docs/troubleshooting.md`,
   `docs/building.md`). Each guide contains public content and must be
   reviewed as public content before publication.

Note what `.nojekyll` does to those `.md` files: Pages serves them
**unrendered**, as `content-type: text/markdown` (verified — `curl -I
https://ksegit.github.io/QuickPdfOcr/README.md`). They read correctly on
github.com, which is where the README's links point, and the raw copies on
the Pages domain are harmless clutter. Do not add markdown under `docs/`
expecting it to render as a web page.

Anything that is neither of those two kinds belongs somewhere else.

This was a real incident: an earlier branch added `docs/superpowers/` and
`docs/design/` (agent-tooling plans/specs/design briefs, including commit
SHAs and written narration of the repo's CI weaknesses) and they were
published live before anyone noticed. They were relocated to `plans/` and
`design/` on `feature/brand-refresh` (commit `da42f77` and its follow-ups —
search `git log --follow plans/ design/` for the full history) to fix it.
Keep it that way.
