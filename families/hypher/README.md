# Hypher (prototype)

The display face for the Hypher wordmark, drawn in code after the Hypher mark: wide, flat-sided letters whose curves live only in their corners. It sits where the research found an open spot among futuristic faces, wide and square and light (the wide ones are round, like Michroma and Unbounded; the square ones are narrow, like Orbitron and Aldrich).

- **Weights:** variable `wght` 300–700; Light, Regular, Medium, SemiBold and Bold instances
- **Characters:** h y p e r n o and space (prototype)
- **Metrics:** 1000 UPM · x-height 560 · ascender 740 (1.32 x-heights) · descender −185 (0.33)

## How it is drawn

Every letter is a few polygons from `rounded()` in `src/core/geometry.py`: corners with a radius each, sides straight. Everything derives from the stem, one number per master (`MASTERS` in `build.py`: 60, 92, 150).

- **Corners:** outer radius 0.20 x-heights; counters follow it one stroke inside. The mark's own 0.043 read as pixel type at letter size and 0.26 drifted back to a squircle (`HYPHER_RADIUS` overrides it for a comparison proof).
- **Horizontals** are 0.86 of the stem, so they look equal to it.
- **Width** grows by twice the stem's gain, so Bold's counters stay open.
- **y** is two straight arms; a u-shaped y read as a g and broke the word's rhythm.

## Build and check

```bash
python3 families/hypher/build.py
python3 families/hypher/proof/check_outlines.py   # fails on any outline that runs backwards over itself
```
