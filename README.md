# maker

A font factory. Each family is drawn in code and built by one shared pipeline.

| Family | What | Build |
| --- | --- | --- |
| [Litt Grotesk](families/litt-grotesk/README.md) | Variable Swiss grotesque for UI text, 300–700 | `python3 families/litt-grotesk/build.py` |
| [Hypher Display](families/hypher-display/README.md) | Wide, machined display face for the Hypher wordmark and headlines, 300–700 (prototype) | `python3 families/hypher-display/build.py` |
| [Hypher Extended](families/hypher-extended/README.md) | Wide, caps-only display face with square stems and tight round bowls, 300–700 (prototype) | `python3 families/hypher-extended/build.py` |

```bash
pip install -r requirements.txt   # fonttools, skia-pathops, ttfautohint-py
```

## Layout

| Path | Role |
| --- | --- |
| `src/core/geometry.py` | Outline primitives every family draws with |
| `src/core/borrowed.py` | Takes glyphs from an OFL variable font and fits them to a family's stem and heights |
| `src/core/fontbuild.py` | The pipeline: masters, TrueType curves, features, `varLib`, statics, woff2 |
| `families/<name>/` | One family: its glyph code, `build.py` (settings, kerning, features), data, fonts, specimen and proofs |

Builds are byte-reproducible with `SOURCE_DATE_EPOCH` set, which fixes the fonts' timestamp.
All fonts are licensed under the SIL Open Font License 1.1 (`LICENSE.txt`).
