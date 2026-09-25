"""Shared brand palette for the desktop UI.

Single source of truth for the dark terminal palette used by both
MainWindow (ui/main_window.py) and LoadingScreen (ui/loading_screen.py) --
the desktop half of the same design system whose web half lives in
docs/index.html's :root block (see tests/test_site_theme.py there).

Every hex value below is exact per the brand spec. tests/test_ui_theme.py
pins these constants and re-derives the contrast ratio of every
foreground/background pair actually used in ui/ from them, rather than
trusting a hardcoded expectation -- that is the check whose absence let the
site ship a --bar/--bar-ink confusion (2.84:1 used as a text colour) before
it was measured.

Provenance: BG, SURFACE, FRAME, ACCENT, BAR, BAR_INK, TEXT, and DIM are the
eight tokens specs/2026-08-15-ascii-terminal-brand-design.md and
docs/index.html's :root both declare -- copied verbatim from there, not
re-picked. OK, WARN, and ERR are new semantic-state colours this desktop UI
task introduced; they do not appear in that spec doc or the site's CSS (as
of this writing, neither defines any success/warning/error token at all).
FRAME_HOVER and FRAME_PRESSED are two more additions beyond that set of
eight, both hover/press fills for buttons rather than page-design tokens:
FRAME_HOVER is docs/index.html's own --indigo-hover, reused verbatim (not
re-picked) at its already-measured 8.96:1; FRAME_PRESSED is a new tint
picked and measured the same way (4.89:1) since the site has no equivalent
:active/:pressed state to reuse.
"""

BG = "#0F172A"        # window / page ground
SURFACE = "#1E293B"   # raised panels, cards
FRAME = "#818CF8"     # indigo ink: borders, outlines        -- 5.98:1 on BG
ACCENT = "#22D3EE"    # cyan: focus, active, scan states     -- 9.88:1 on BG
BAR = "#7C3AED"       # violet FILL only, never text         -- 3.13:1 on BG
BAR_INK = "#A78BFA"   # violet ink where violet must be text -- 6.56:1 on BG
TEXT = "#E2E8F0"      # primary text                         -- 14.48:1 on BG
DIM = "#94A3B8"       # secondary text                       -- 6.96:1 on BG
OK = "#22C55E"        # success -- new for this task, not in the site's CSS
WARN = "#F59E0B"      # warning -- new for this task, not in the site's CSS
ERR = "#EF4444"       # error   -- new for this task, not in the site's CSS

# Reused verbatim from docs/index.html's --indigo-hover -- not re-picked
# here, so the desktop button hover state matches the site's own finding
# instead of inventing a second, independently-measured one.
FRAME_HOVER = "#A5B4FC"

# A third, darker indigo tint for the button :pressed state -- the site has
# no equivalent state to reuse (its .btn-primary:hover only moves a shadow,
# never recolours), so this is measured the same way FRAME/FRAME_HOVER
# were: BG (dark ink) on top of it clears 4.5:1 (4.89:1), and it sits
# visibly darker than FRAME/FRAME_HOVER for the "pushed in" cue.
FRAME_PRESSED = "#727AF0"
