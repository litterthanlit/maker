# FONTLOG for Litt Grotesk

## Basic information

Litt Grotesk is a variable Swiss grotesque (weight 300 to 700) for interfaces, the
type face for litt.md. It is released under the SIL Open Font License 1.1
(`LICENSE.txt`).

## Provenance

- **Drawn for Litt:** every glyph except those below, generated from code in `src/`
  (`glyphs.py`, `extended.py`, `penglyphs.py`). No outline of any measured font is used.
- **From Archivo (OFL):** the outlines of the curved and complex letters **a b c d e f g j o p q s t y**,
  **G K R S**, **æ œ ȷ ŧ þ đ**, **& @ % €** and **all ten figures 0–9**, and so of the glyphs built on them (their accented forms, ¢, $, the tabular
  figures, the slashed zero, superscripts ² ³ ¹ and the fractions ¼ ½ ¾). Archivo is by Omnibus-Type, Copyright 2020 The
  Archivo Project Authors (https://github.com/Omnibus-Type/Archivo). Litt takes them
  from Archivo's variable font (`src/data/base`, subset to those glyphs and n) following the
  make-font method (design.how): for each Litt master the weight axis is solved so
  Archivo's stem matches Litt's, and the outline is scaled to Litt's x-height and cap
  height. Points are not edited. The figures are centred in Litt's shared figure
  width, not stretched. The & is Archivo's classic alternate (`ampersand.alt`), not its default
  Et form, which reads as an E at UI sizes. Archivo's 4 is open at the top, its 1 has a foot and its 7 a curved
  stem; Litt's earlier figures were closed, footless and straight.
  At Light, Archivo's thinnest weight is a touch heavier than Litt's Light stem, so
  these glyphs run slightly heavy there. Archivo's licence: `src/data/base/Archivo-OFL.txt`.
  Archivo has no Reserved Font Name.

## Changelog

- 0.98: o b d p q, þ and đ from Archivo.
- 0.97: c e f g j t y, G K R, & (classic alternate), @, ȷ ŧ œ from Archivo; the
  straight letters stay Litt's own.
- 0.96: a, æ, % and € from Archivo. `LITT_BORROW_ALL=1` builds an opt-in preview
  with every basic letter from Archivo.
- 0.95: 0, 1, 7 and 8 from Archivo: all ten figures now come from it.
- 0.9: 2, 3, 4 and 5 from Archivo, fitted to Litt.
- 0.8: 6 and 9 from Archivo, fitted to Litt.
- 0.7: s and S from Archivo, fitted to Litt; released under the OFL.
- 0.6: 6 9 s S drawn from research into Helvetica-class grotesques.
- 0.5: curved shapes drawn as pen strokes.
- 0.4: unambiguous defaults, no stylistic sets.
- 0.3: renamed Litt Grotesk; tuned for 12 to 18px.
