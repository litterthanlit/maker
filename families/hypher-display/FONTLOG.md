# FONTLOG for Hypher Display

## Sources

Drawn in code for Hypher Display; no outlines are taken from another font.

- **Michroma** (Copyright 2011 The Michroma Project Authors, https://github.com/googlefonts/Michroma-font, SIL Open Font License 1.1): the Wordmark design's widths, sidebearings, landmark heights and kerning pairs are measured from Michroma Regular 1.100, and its corners were fitted by overlap with Michroma's outlines. Michroma declares no Reserved Font Name. Hypher Display is released under the same licence.
- **Research:** twenty open-licence fonts (Michroma, Orbitron, Audiowide, Unbounded and others) were measured for proportions only, to choose the direction.

## Changelog

- **0.490 (2026-11-16):** the w, in every version, is one outline with a flat middle peak at the x-height. It was two v's laid over each other, and each one's rounded top corner left a notch in the middle.
- **0.480 (2026-11-16):** Hypher Display's e is now Datum's: the crossbar sits lower (0.43 of the x-height), the cut ends are softly rounded, and the letter is a little narrower. It keeps the wordmark's spacing, so words and the logo set as before. Any version can borrow another's e with `e_from`.
- **0.470 (2026-11-16):** the e, in every version: its bottom stroke sweeps up into the terminal instead of standing as a stub, its counters are softer, and its crossbar drops a little as weight grows so Bold keeps an open eye. Corner curves beside a sharp corner may now run the whole side, so every terminal (c, s, 2, 3, 5) runs its curve right up to its cut.
- **0.460 (2026-11-15):** Weld: Datum with the wordmark's hooked y and square stem tops. `lockup.py` exports the logo optically set (pair spacing measured against the font's stem rhythm; mark centred on the x-height, gap from the slant's midpoint) as outlined SVG.
- **0.450 (2026-11-15):** Datum 20: Datum at 93% width, 20% resemblance to Michroma above the genre baseline (57% raw lowercase overlap), kerning re-measured from its own outlines.
- **0.440 (2026-11-15):** Chamfer: Datum with every corner cut straight and letters at 86% width, 50% overlap with Michroma, the genre's floor. `rounded()` gains a `chamfer` option.
- **0.430 (2026-11-15):** Datum: no number from the wordmark font. Its own widths, sidebearings, landmarks and placements, and kerning measured from its own outlines by a new auto-kerner. 70% lowercase overlap with Michroma, by resemblance alone.
- **0.420 (2026-11-15):** Billet and Billet Compact: Hypher's own proportion system with a fifth of the wordmark font blended in; Billet Compact sits at 55% overlap with Michroma, the genre's own level. Landmark heights are now named values (`lm()`) a version can set.
- **0.410 (2026-11-15):** Lathe Wide and Lathe Narrow: Wordmark's proportions with Hypher's own corners, y and width, at about 75% overlap with Michroma (Wordmark is 88%).
- **0.400 (2026-11-15):** capitals A–Z, `& @ %`, the accented letters of Western European languages, and kerning (592 pairs, after Michroma's). The font's copyright notice credits Michroma.
- **0.320 (2026-11-15):** figures 0–9 and punctuation: `. , : ; ! ? - – — ' " ‘ ’ “ ” ( ) [ ] / + = * _ #`, in every version, at 300–700.
- **0.310 (2026-11-15):** renamed Hypher Display (files `HypherDisplay`, folder `families/hypher-display/`), so the font and the product are not one word; the alternates are Hypher Display Mill, Fillet, Polish, Bore, Deburr and Finish.
- **0.300 (2026-11-15):** Wordmark becomes the main design (plain Hypher); Finish becomes a version. The full lowercase a–z, in every version, at 300–700.
- **0.220 (2026-11-15):** named versions: Mill, Fillet, Polish, Bore, Deburr, Finish (the default, plain Hypher) and Wordmark, each its own family. Wordmark redraws the current lockup's letters in this system, its corners fitted to the lockup's outlines.
- **0.210 (2026-11-15):** slightly rounder: corners eased into the sides, radius 0.20 → 0.215, rounder counters, and softly rounded cut ends like the mark's.
- **0.200 (2026-11-15):** machined direction. h y p e r n o and space, drawn from rounded polygons, at 300–700. Replaces 0.100.
- **0.100 (2026-11-15):** prototype on Michroma's outlines (OFL), withdrawn in favour of an original design.
