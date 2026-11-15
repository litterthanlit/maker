# FONTLOG for Litt Grotesk

## Basic information

Litt Grotesk is a variable Swiss grotesque (weight 300 to 700) for interfaces, the
type face for litt.md. It is released under the SIL Open Font License 1.1
(`LICENSE.txt`).

## Provenance

- **Drawn for Litt:** every glyph except those below, generated from code in `src/`
  (`glyphs.py`, `extended.py`, `penglyphs.py`). The centre lines of 6 and 9 come from
  averaged measurements of Helvetica-class grotesques (`docs/research/`); no outline
  of any measured font is used.
- **From Archivo (OFL):** the outlines of **s** and **S**, and so of the letters built
  on them (ś ŝ ş š Ś Ŝ Ş Š and $). Archivo is by Omnibus-Type, Copyright 2020 The
  Archivo Project Authors (https://github.com/Omnibus-Type/Archivo). Litt takes them
  from Archivo's variable font (`src/data/base`, subset to s, S and n) following the
  make-font method (design.how): for each Litt master the weight axis is solved so
  Archivo's stem matches Litt's, and the outline is scaled to Litt's x-height and cap
  height. Points are not edited. Archivo's licence: `src/data/base/Archivo-OFL.txt`.
  Archivo has no Reserved Font Name.

## Changelog

- 0.7: s and S from Archivo, fitted to Litt; released under the OFL.
- 0.6: 6 9 s S drawn from research into Helvetica-class grotesques.
- 0.5: curved shapes drawn as pen strokes.
- 0.4: unambiguous defaults, no stylistic sets.
- 0.3: renamed Litt Grotesk; tuned for 12 to 18px.
