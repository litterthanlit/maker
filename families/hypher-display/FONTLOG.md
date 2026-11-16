# FONTLOG for Hypher Display

## Sources

Drawn in code for Hypher Display; no outlines are taken from another font.

- **Michroma** (Copyright 2011 The Michroma Project Authors, https://github.com/googlefonts/Michroma-font, SIL Open Font License 1.1): the Wordmark design's widths, sidebearings, landmark heights and kerning pairs are measured from Michroma Regular 1.100, and its corners were fitted by overlap with Michroma's outlines. Michroma declares no Reserved Font Name. Hypher Display is released under the same licence.
- **Research:** twenty open-licence fonts (Michroma, Orbitron, Audiowide, Unbounded and others) were measured for proportions only, to choose the direction.

## Changelog

- **0.550 (2026-11-16):** overshoot on round letters and figures, after Michroma (1.9% of the x-height, 2.1% of the cap height). Square stem ends no longer leave a notch beside the bowl or arch (n m h r p b d q u g a, and the m's middle stem); the Z's and z's bars are sharp where the diagonal leaves; the 1's flag runs on from a sharp corner. Three-way joints (B, m, 6, 9) and counters beside square corners are capped so Light stays even. The &'s upper stem sits into the bowl's side, so Bold is lighter. The tilde is one wave; the ring sits higher. New `proof/check_shapes.py` finds steps, notches and heavy spots: 0 in the Wordmark design.
- **0.540 (2026-11-16):** the & redrawn after Michroma's construction, in every version: the lower bowl's left side rises and runs on as the diagonal, out past the bowl to a flat cut; the upper loop's stem comes down into the same diagonal with a fillet, and the loop opens at the lower right into a terminal. It was a closed box on a bowl with a separate bar laid across both.
- **0.530 (2026-11-16):** every curve in Hypher Display follows its e (Datum's): corners of radius 0.215 eased 0.6 inside and out, softly rounded cut ends, and counters half again as round as the bowls, capped at 0.85 of the outer corner so Light does not go heavy at the corners. The logo changes with it. The 3's and 8's middle pinch now takes only the room its side has, so their outer corners keep their full size, in every version. Lowercase overlap with Michroma: 87%.
- **0.520 (2026-11-16):** figures 3, 4, 7 and 8 redrawn after Michroma's construction. The 3 and 8 are two bowls stacked on the middle bar, each rounding its own corner there (`waist()`), so their sides pinch in at the middle instead of running straight. The 4 and 7 are each one outline whose diagonal leaves the bar at its corner, so the bar no longer steps out past it; the 4's diagonal meets the stem flush at the top.
- **0.510 (2026-11-16):** a pass for broken shapes. The y's tops are cut flat like the v's, so the logo's y changes too. Z: the diagonal no longer pokes past the end of the top bar. 8 and e: a counter's corner against a crossbar is no rounder than 1.3 bars (`joint()`), so Light has no dark blobs where two counters meet across a thin bar; Regular and Bold are unchanged. @: the inner bowl is square where the stem rises through it, so no tick sticks up.
- **0.500 (2026-11-16):** v and w cut every end flat, as the x does; the rounded outer ears are gone. The capital W is one outline too, like the w.
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
