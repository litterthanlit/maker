# Hypher (prototype)

The display face for the Hypher wordmark, drawn in code after the Hypher mark: wide, flat-sided letters whose curves live only in their corners. It sits where the research found an open spot among futuristic faces, wide and square and light (the wide ones are round, like Michroma and Unbounded; the square ones are narrow, like Orbitron and Aldrich).

- **Weights:** variable `wght` 300–700; Light, Regular, Medium, SemiBold and Bold instances
- **Characters:** a–z and space (prototype)
- **Metrics:** 1000 UPM · x-height 560 · ascender 740 (1.32 x-heights) · descender −185 (0.33)

## Versions

Each version is a named set of numbers in `STYLES` (`glyphs.py`) and builds as its own family. Plain **Hypher** is Wordmark. To try a mix without editing, set `HYPHER_STYLE` to a version and any of `HYPHER_RADIUS`, `HYPHER_SMOOTH`, `HYPHER_INNER` or `HYPHER_TERM` to override its numbers, then build.

| Version | Family | What changes |
| --- | --- | --- |
| Mill | Hypher Mill | Crisp: radius 0.20 x-heights, circular corners, sharp cut ends (was 0.200) |
| Fillet | Hypher Fillet | Bigger corners, radius 0.235 |
| Polish | Hypher Polish | Corners eased into the sides instead of joined as circles |
| Bore | Hypher Bore | Rounder counters |
| Deburr | Hypher Deburr | Cut ends rounded, as every corner of the mark is |
| Finish | Hypher Finish | A little of each: radius 0.215, eased 0.6, rounder counters, soft ends |
| **Wordmark** | **Hypher** | The current wordmark's letters (Michroma) redrawn in this system: its widths, spacing, square stem tops and hooked y, with corners fitted to its outlines (85–93% overlap per letter, the y 71%). The rest of a–z takes its widths, spacing and landmark heights from the same font, measured, and its shapes from this system |

## How it is drawn

Every letter is a few polygons from `rounded()` in `src/core/geometry.py`: corners with a radius each, sides straight. Everything derives from the stem, one number per master (`MASTERS` in `build.py`: 60, 92, 150), and from the version's numbers:

- **radius:** the outer corner, in x-heights. The mark's own 0.043 read as pixel type at letter size and 0.26 drifted back to a squircle.
- **smooth:** 0 joins a corner to its sides as a circle; higher starts the curve further back and eases it in.
- **inner:** how far inside the outer corner a counter's corner sits, in stems; smaller reads rounder.
- **term:** the radius on cut ends (stem feet, terminals, the r's arm).
- **Horizontals** are 0.86 of the stem, so they look equal to it, and **width** grows by twice the stem's gain, so Bold's counters stay open.
- **y** is a symmetric V that meets on the baseline, its right arm running on into the descender; a u-shaped y read as a g.

## Build and check

```bash
python3 families/hypher/build.py              # Hypher (Wordmark)
python3 families/hypher/build.py --versions   # and every named version, into fonts/versions/
HYPHER_STYLE=Wordmark python3 families/hypher/proof/check_outlines.py   # fails on any outline that runs backwards over itself
```
