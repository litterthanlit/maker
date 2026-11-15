# Kanton Grotesk

A variable Swiss grotesque inspired by Neue Haas Grotesk, drawn entirely in code.
It keeps the traits of the genre and changes the details, so it isn't a copy of any existing typeface.

- **Weights:** variable `wght` axis from 300 (Light) to 700 (Bold), with Light, Regular, Medium, SemiBold and Bold instances
- **Character set:** 370 characters: Basic Latin, Latin-1 and Latin Extended-A (names in 40+ languages), plus typographic quotes and dashes, € £ ¥ ¢, arrows, math signs, © ® ™, superscripts and fractions
- **Metrics:** 1000 UPM · cap height 720 · x-height 528 · ascender 748 · descender −212

## Using it in UI

- **Optical centring.** Ascent 960 and descent −240 are identical on every platform (hhea, typo and win, with `USE_TYPO_METRICS` on). The line box centres on the capitals, so labels sit in the middle of buttons and inputs.
- **Tabular figures by default,** so prices and IDs line up in tables. `pnum` gives a proportional 1.
- **OpenType features**
  | Feature | What it does | When to use |
  | --- | --- | --- |
  | `ss01` | Tailed l, serifed I, slashed zero | Inputs, passwords, codes, IDs |
  | `case` | Raises ( ) [ ] { } – — « » · to cap height | Uppercase labels and buttons |
  | `zero` | Slashed zero only | Data tables |
  | `ccmp` | Turns decomposed text (e + ◌́) into precomposed é | Always on; fixes macOS file names |
  | `kern` | ~30 class pairs; accented letters kern like their base | Always on |
- **Hinting.** The static fonts are autohinted with ttfautohint, for crisp text on Windows. The variable font is unhinted and carries a `gasp` table; it renders cleanly on macOS, iOS, Android and modern browsers.
- **Recommended CSS**
  ```css
  .small   { letter-spacing: 0.01em; }        /* below 15px */
  h1       { letter-spacing: -0.02em; }       /* headlines */
  .caps    { text-transform: uppercase; letter-spacing: 0.06em; font-feature-settings: "case"; }
  input    { font-feature-settings: "ss01"; }
  ```

## Build

```bash
pip install -r requirements.txt   # fonttools, skia-pathops, ttfautohint-py
python3 src/build.py
```

Output:

| Path | What |
| --- | --- |
| `fonts/variable/KantonGrotesk[wght].ttf` / `.woff2` | Variable font (use this on the web) |
| `fonts/static/KantonGrotesk-<Style>.ttf` / `.woff2` | Static instances with overlaps removed (for desktop apps) |
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
