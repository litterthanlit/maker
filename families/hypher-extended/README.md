# Hypher Extended (prototype)

A wide, caps-only display face, the second Hypher family. It is drawn in code after a reference wordmark (`proof/reference.png`, the word NITROUS). The reference sits near Eurostile Extended and Microgramma, but it differs from them. Stems, bars and cut ends are square. Only the corners of bowls are round, and the counters are tight. The N's diagonal runs between its stems' inner edges, and the R's leg drops straight down and is filleted into the bowl. No outline comes from another font.

- **Weights:** variable `wght` 300–700; Light, Regular, Medium, SemiBold and Bold instances. The reference's weight falls near SemiBold.
- **Characters:** A–Z (the lowercase keys type the capitals), figures 0–9, `. , : ; ! ? - – — ' " ‘ ’ “ ” ( ) [ ] / + = _ & %` and the space.
- **Metrics:** 1000 UPM · cap height 700 · round letters overshoot by 12.

## Using it

```css
@font-face {
  font-family: "Hypher Extended";
  src: url("/fonts/HypherExtended[wght].woff2") format("woff2");
  font-weight: 300 700;
  font-display: swap;
}
.headline { font-family: "Hypher Extended", sans-serif; font-weight: 600; }
```

## How it is drawn

Every glyph is a few polygons from `rounded()` in `src/core/geometry.py`. Everything derives from the stem, one number per master (`MASTERS` in `build.py`: 70, 104, 180):

- **Measured from the reference** at its stem of 165: the widths of N T R O U S, horizontals at 0.93 of the stem, the R's bowl bottom (0.278 cap heights), its leg fillet (one stem), and the 1.7% overshoot.
- **Fitted to the reference** by `proof/fit.py`, which draws N I T R O U S, rasterises them at the reference's scale and scores each letter's overlap with it. The corners (`RADIUS`, `SMOOTH`, `INNER`, `INNER_MIN` in `glyphs.py`) were grid-searched. The score barely moves near the chosen values, so the corners are as close as the source image can show. A plain rectangle (the I) scores 0.91, and that is the ceiling the blurred image allows.
- **Drawn to match** for the letters the reference doesn't show. A is the U turned over. K, M and Z reuse the N's diagonal. V, W, X and Y take a diagonal 0.86 stems thick. C, G and the figures end their bars square at full width, as the S does.

## Build and check

```bash
python3 families/hypher-extended/build.py
python3 families/hypher-extended/proof/check_outlines.py   # no outline runs backwards, at any master
python3 families/hypher-extended/proof/fit.py --png fit.png # overlap with the reference, per letter
python3 families/hypher-extended/proof/specimen.py         # proof/specimen.png
```
