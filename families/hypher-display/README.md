# Hypher Display (prototype)

The display face for the Hypher wordmark and headlines, drawn in code. Its main design redraws the letters of today's Hypher logo (set in Michroma) in a corner system of its own: wide, flat-sided letters whose curves live only in their corners, after the Hypher mark. No outline comes from another font; widths, spacing, landmark heights and kerning are measured from Michroma (SIL Open Font License 1.1), which is credited in the font and in `FONTLOG.md`.

- **Weights:** variable `wght` 300–700; Light, Regular, Medium, SemiBold and Bold instances
- **Characters:** A–Z, a–z, figures 0–9, `. , : ; ! ? - – — ' " ‘ ’ “ ” ( ) [ ] / + = * _ # & @ %`, the space, and the accented letters of Western European languages (à–ÿ, À–Ý: grave, acute, circumflex, tilde, dieresis, ring, cedilla), 145 in all
- **Kerning:** 592 pairs; accented letters kern like their base letter
- **Metrics:** 1000 UPM · x-height 560 · ascender 740 (1.32 x-heights) · descender −185 (0.33)

## Using it

```css
@font-face {
  font-family: "Hypher Display";
  src: url("/fonts/HypherDisplay[wght].woff2") format("woff2");
  font-weight: 300 700;
  font-display: swap;
}
.wordmark { font-family: "Hypher Display", sans-serif; font-weight: 400; }
```

The lockup's loose tracking is built into the spacing, so set it with `letter-spacing: 0`.

## Versions

Each version is a named set of numbers in `STYLES` (`glyphs.py`) and builds as its own family. The six alternates are kept for comparison and for future use; Hypher Display itself is the Wordmark design.

| Version | Family | What it is |
| --- | --- | --- |
| **Wordmark** | **Hypher Display** | Today's logo letters redrawn in this system. Widths, spacing and landmark heights are measured from the lockup's font; the corners were fitted by overlap with its outlines (h 93%, r 93%, p 91%, e 85%, y 71%) |
| Mill | Hypher Display Mill | The first machined design: radius 0.20 x-heights, circular corners, sharp cut ends |
| Fillet | Hypher Display Fillet | Bigger corners, radius 0.235 |
| Polish | Hypher Display Polish | Corners eased into the sides instead of joined as circles |
| Bore | Hypher Display Bore | Rounder counters |
| Deburr | Hypher Display Deburr | Cut ends rounded, as every corner of the mark is |
| Finish | Hypher Display Finish | A little of each: radius 0.215, eased 0.6, rounder counters, soft ends |
| Lathe Wide | Hypher Display Lathe Wide | Wordmark's landmarks, spacing and kerning with Hypher's own machined corners and straight y, 6% wider |
| Lathe Narrow | Hypher Display Lathe Narrow | The same, 5% narrower |
| Billet | Hypher Display Billet | Hypher's own proportion system (widths by shape family, sidebearings by side shape, terminals at 0.30 and 0.70, bars centred, f at the ascender, g at the descender), blended 80/20 with the wordmark font's measurements; Hypher's corners, straight y and round stem tops |
| Billet Compact | Hypher Display Billet Compact | Billet at 90% width: about as close to Michroma as any font of the genre |
| Datum | Hypher Display Datum | None of the wordmark font: every width, sidebearing, landmark and placement is Hypher's own rule, and kerning is measured from Datum's own outlines (`autokern.py`) |

**How close each is to Michroma** (share of letter area both cover, lowercase a–z, at the same x-height): Wordmark 88%, Lathe Wide and Lathe Narrow 75%, Billet 73%, Datum 70%, Mill and Finish 67%, Billet Compact 55%. Unrelated wide or futuristic fonts land at 41–54% (Krona One 54%, Orbitron 52%, Audiowide 44%). Corners barely move the number; width moves it most. Datum shows the number measures resemblance, not borrowing: it takes nothing from Michroma, yet its own rules are wide too, and wide letters resemble each other.

To try a mix without editing, set `HYPHER_STYLE` to a version and any of `HYPHER_RADIUS`, `HYPHER_SMOOTH`, `HYPHER_INNER` or `HYPHER_TERM` to override its numbers, then build.

## How it is drawn

Every glyph is a few polygons from `rounded()` in `src/core/geometry.py`: corners with a radius each, sides straight. Everything derives from the stem, one number per master (`MASTERS` in `build.py`: 60, 92, 150), and from the version's numbers:

- **radius:** the outer corner, in x-heights. The mark's own 0.043 read as pixel type at letter size and 0.26 drifted back to a squircle.
- **smooth:** 0 joins a corner to its sides as a circle; higher starts the curve further back and eases it in.
- **inner:** how far inside the outer corner a counter's corner sits, in stems; smaller reads rounder.
- **term:** the radius on cut ends (stem feet, terminals, the r's arm).
- **Horizontals** are 0.86 of the stem, so they look equal to it, and **width** grows by twice the stem's gain, so Bold's counters stay open.
- **k:** the outer edges of arm and leg meet the stem at fixed heights and the crotch falls where the inner edges cross, so the diagonals never cross on thin weights.
- **y:** a symmetric V that meets on the baseline; in the Wordmark design its tail hooks left into a flat foot.
- **Figures** are lining, at cap height, as wide as the lowercase bowls. Their landmarks (the 2's middle bar, the 3's and 5's terminals, the 6's bowl, the 4's crossbar) are measured from the lockup's font; the 9 is the 6 turned.
- **Comma and quotes** are a wedge, wide at the top; the opening quotes turn it so their wide end is low, so “ and ” point opposite ways.
- **Capitals** stand at the ascender. B's top bowl is narrower than its lower one, E's middle bar is shorter than its top, K's arm and leg leave a short stub on the stem, M's V dips almost to the baseline, and Y's arms meet at 0.42 of the cap height, all as in the lockup's font.
- **Accents** are drawn once (`mark()`) and hung over the base letter; i takes them on a dotless i.
- **Kerning** (`kerning.py`) is Michroma's own pair list, scaled. The Wordmark design shares Michroma's widths and spacing, so its pairs fit.

## Files

| File | Role |
| --- | --- |
| `glyphs.py` | Every glyph as a function of the weight, plus the versions in `STYLES` |
| `kerning.py` | The kerning pairs, after Michroma |
| `autokern.py` | Kerning measured from a version's own outlines (Datum) |
| `build.py` | Family names, masters, kerning; `--versions` builds every version |
| `proof/check_outlines.py` | Fails if any glyph's outline runs backwards over itself, at any master |
| `proof/lockup.html` | The mark beside the word at each weight, with today's lockup for reference |
| `fonts/` | Built fonts; `fonts/versions/<Name>/` holds the alternates |

## Build and check

```bash
python3 families/hypher-display/build.py              # Hypher Display
python3 families/hypher-display/build.py --versions   # and every named version, into fonts/versions/
HYPHER_STYLE=Wordmark python3 families/hypher-display/proof/check_outlines.py
```
