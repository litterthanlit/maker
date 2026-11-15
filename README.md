# Litt Grotesk

The type face for [litt.md](https://github.com/litterthanlit/litt.md): a variable Swiss grotesque inspired by Neue Haas Grotesk, drawn entirely in code and tuned for 12–18px UI text, where it reads as openly as Inter and Geist.
It keeps the traits of the genre and changes the details, so it isn't a copy of any existing typeface.

- **Weights:** variable `wght` axis from 300 (Light) to 700 (Bold), with Light, Regular, Medium, SemiBold and Bold instances
- **Character set:** 370 characters: Basic Latin, Latin-1 and Latin Extended-A (names in 40+ languages), plus typographic quotes and dashes, € £ ¥ ¢, arrows, math signs, © ® ™, superscripts and fractions
- **Metrics:** 1000 UPM · cap height 720 · x-height 528 · ascender 748 · descender −212

## Principles

Less, but better. Every part of the font has to make reading or using it easier.

- **Clear by default.** The 1 has a flag and the l rises above the capitals; braces curve to a point, so `{}` never reads as `[]`. Nothing needs a feature turned on.
- **Drawn as strokes.** S, s, 2, 3, 5, 6, 9, & @ ? ~ ( ) { } are pen paths (`src/penglyphs.py`): a skeleton expanded by an elliptical pen, as a type designer draws them. The curved letters, symbols and figures are taken from Archivo (OFL) and fitted to Litt's numbers with the make-font method (`src/borrowed.py`); `docs/research` holds the earlier measurement study: the averaged, landmark-aligned centre lines of Helvetica-class grotesques ([docs/research](docs/research/README.md)).
- **No stylistic sets.** If an alternate is better, it becomes the default; if it isn't, it doesn't ship. The features that remain do one job each: `kern`, `ccmp`, `case`, `tnum`, `zero`.
- **Open at small sizes.** Wide enough, spaced enough and open enough to read at 13px, measured against Inter and Geist.
- **Thorough to the last detail.** & @ { } and the figures are drawn as carefully as the letters; strokes meet along their own curves, without corners.

## On litt.md

Every litt world reads `--font-choice` first, so Litt Grotesk takes over Press and Flat with one line and no change to litt. It needs no `ss` or `cv` features, as litt's type rules ask.

```css
@font-face {
  font-family: "Litt Grotesk";
  src: url("/fonts/LittGrotesk[wght].woff2") format("woff2");
  font-weight: 400 600;
  font-display: swap;
}
:root { --font-choice: "Litt Grotesk"; }
[data-material="device"] { --font-choice: initial; }  /* Device keeps Geist Mono */
```

Press asks for Helvetica Neue, which only Apple systems have; elsewhere it falls back to Arial. Litt Grotesk keeps the Haas look on every platform. `proof/litt-card.js` captures the real gallery with any face injected, and `proof/build-litt-specimen.py` builds the brand specimen from those captures.

Legibility at 400, per 1000 units (v0.3 changes: lowercase ×1.05, sidebearings 60→70, x-height 528→540, open terminals on c e s a C G S 3 5 6):

| | Lowercase width | n sidebearing | x-height / cap |
| --- | --- | --- | --- |
| v0.2 | 474 | 60 | 0.733 |
| **Litt Grotesk 0.3** | **504** | **70** | **0.750** |
| Inter | 536 | 77 | 0.750 |
| Geist | 534 | 80 | 0.746 |

## Using it in UI

- **Optical centring.** Ascent 960 and descent −240 are identical on every platform (hhea, typo and win, with `USE_TYPO_METRICS` on). The line box centres on the capitals, so labels sit in the middle of buttons and inputs.
- **Figures are proportional by default** (a 1 in `fra1` or a hash sets tight) and **tabular under `tnum`**, which CSS `tabular-nums` turns on for values and counts.
- **OpenType features**
  | Feature | What it does | When to use |
  | --- | --- | --- |
  | `case` | Raises ( ) [ ] { } – — « » · to cap height | Uppercase labels and buttons |
  | `tnum` | Tabular figures, one width | Values, counts, table columns |
| `zero` | Slashed zero only | Data tables |
  | `ccmp` | Turns decomposed text (e + ◌́) into precomposed é | Always on; fixes macOS file names |
  | `kern` | ~30 class pairs; accented letters kern like their base | Always on |
- **Hinting.** The static fonts are autohinted with ttfautohint, for crisp text on Windows. The variable font is unhinted and carries a `gasp` table; it renders cleanly on macOS, iOS, Android and modern browsers.
- **Recommended CSS**
  ```css
  .small   { letter-spacing: 0.01em; }        /* below 15px */
  h1       { letter-spacing: -0.02em; }       /* headlines */
  .caps    { text-transform: uppercase; letter-spacing: 0.06em; font-feature-settings: "case"; }
  ```

## Licence

SIL Open Font License 1.1 (`LICENSE.txt`). The curved and complex letters (a b c d e f g j o p q s t y, G K R S, & @ % €) and all ten figures are Archivo's (OFL, Omnibus-Type); the straight letters are Litt's own, fitted to Litt's stem and heights; everything else is drawn for Litt. Provenance and changelog: `FONTLOG.md`.

## Build

```bash
pip install -r requirements.txt   # fonttools, skia-pathops, ttfautohint-py
python3 src/build.py
```

Output:

| Path | What |
| --- | --- |
| `fonts/variable/LittGrotesk[wght].ttf` / `.woff2` | Variable font (use this on the web) |
| `fonts/static/LittGrotesk-<Style>.ttf` / `.woff2` | Static instances with overlaps removed (for desktop apps) |
| `specimen/index.html` | Type specimen; open it in a browser |

## How it works

| File | Role |
| --- | --- |
| `src/geometry.py` | Primitives: rectangles, diagonal strokes, superellipse bowls, open bands with horizontal or vertical cuts |
| `src/glyphs.py` | Basic Latin: one function per glyph. It takes the weight parameters (stem, horizontals, sidebearings) and returns outlines |
| `src/extended.py` | Accent marks, accented letters composed from Unicode decompositions, special letters (ß Æ Ø Ł Ð Þ), UI symbols and feature alternates |
| `src/build.py` | Draws three masters (300 / 400 / 700), converts them to compatible TrueType curves, adds kerning, and merges them with `varLib` |

Everything derives from one number per master: the lowercase stem width (`MASTERS` in `build.py`).
Every primitive emits the same point structure at any weight, so the masters always interpolate.

To change the design, edit the constants at the top of `glyphs.py` (`XH`, `CH`, `K` for squareness) or a single glyph function, then rebuild.
`proof/` has quick Playwright proof sheets: `node proof/shot.js $PWD/proof/proof.html out.png 300,400,700`.

## Known gaps (v0.2)

- No Greek, Cyrillic or Vietnamese yet; no ŉ or ſ (deprecated and archaic)
- `&`, `@` and the braces `{}` are still rough drafts
- No mark-positioning (`mark`) feature: decomposed text resolves through `ccmp` only for letters that have a precomposed form
- Kerning covers about 30 key class pairs; a full kerning pass is the next quality step
