# Kanton Grotesk

A variable Swiss grotesque inspired by Neue Haas Grotesk, drawn entirely in code.
It keeps the traits of the genre and changes the details, so it isn't a copy of any existing typeface.

- **Weights:** variable `wght` axis from 300 (Light) to 700 (Bold), with Light, Regular, Medium, SemiBold and Bold instances
- **Character set:** Basic Latin, all 95 printable ASCII characters, with kerning
- **Metrics:** 1000 UPM · cap height 720 · x-height 528 · ascender 748 · descender −212

## Build

```bash
pip install -r requirements.txt
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
| `src/glyphs.py` | One function per glyph. It takes the weight parameters (stem, horizontals, sidebearings) and returns outlines |
| `src/build.py` | Draws three masters (300 / 400 / 700), converts them to compatible TrueType curves, adds kerning, and merges them with `varLib` |

Everything derives from one number per master: the lowercase stem width (`MASTERS` in `build.py`).
Every primitive emits the same point structure at any weight, so the masters always interpolate.

To change the design, edit the constants at the top of `glyphs.py` (`XH`, `CH`, `K` for squareness) or a single glyph function, then rebuild.
`proof/` has quick Playwright proof sheets: `node proof/shot.js $PWD/proof/proof.html out.png 300,400,700`.

## Known gaps (v0.1)

- No accented letters, € or typographic quotes and dashes yet
- `&`, `@` and the braces `{}` are rough drafts
- Kerning covers about 30 key class pairs
