# Hypher (prototype)

The display face for the Hypher wordmark. Hypher Regular is Michroma (OFL) with the brand lockup's spacing built in, so `hypher` set in it reproduces `hypher-web/public/brand/hypher-lockup.svg` to within 0.08 units per letter. The weight axis runs 300 to 700, so the site can set the word heavier without stroking the outline.

- **Weights:** variable `wght` 300–700; Light, Regular, Medium, SemiBold and Bold instances
- **Characters:** a–z, space, period, hyphen (prototype)
- **Metrics:** Michroma's, at 2048 UPM · x-height 1152 · ascender 1536 · descender −384
- **Spacing:** every glyph carries half of the lockup's +0.080em on each side; `kern` tightens e–r by 37 units (2.5 at the lockup's size), where both letters open to the right

## How the weights are made

Regular is Michroma's outline, read from `data/base`. Light and Bold move every edge in or out by the same distance (64 and 54 units on the stems, three quarters of that on the horizontals), then pull the baseline, x-height and ascender back to where they were. Points are moved, never added, so all three masters interpolate. Sharp corners get special cases in `glyphs.py`:

- a curve that doubles back into a stem (the a) slides with the stem rather than the bisector, which would fold it into a hook
- straight corners take the full miter (the k's arm tips), but never move more than 0.45 of the way to the nearest other corner (the k's crotch, 58 units tall)
- straight segments under 2 units are dropped from the source (the m's middle stem has a 1-unit step)

## Build and check

```bash
python3 families/hypher/build.py
python3 families/hypher/proof/check_outlines.py   # fails on any reversed loop the offset made
```

`proof/lockup.html` shows the lockup, Hypher Regular over it, the three weights beside the mark, and the lowercase. `proof/lockup.png` is its last capture.
