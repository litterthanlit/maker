"""Build the Litt Grotesk font page from the built font files.

    python3 families/litt-grotesk/proof/build-font-page.py <out.html>

Reads the family's fonts/ (run families/litt-grotesk/build.py first) and fills specimen/font-page-template.html:
every character with its advance at Light, Regular and Bold, its set, and whether
its outline comes from Archivo.
"""

import base64
import json
import sys
import unicodedata as u
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent  # families/litt-grotesk
sys.path.insert(0, str(ROOT.parent.parent / "src"))
sys.path.insert(0, str(ROOT))
import glyphs as G  # noqa: E402
import extended as X  # noqa: E402

var = TTFont(ROOT / "fonts/variable/LittGrotesk[wght].ttf")
static = {w: TTFont(ROOT / f"fonts/static/LittGrotesk-{n}.ttf") for w, n in [(300, "Light"), (400, "Regular"), (700, "Bold")]}
cmap = var.getBestCmap()

ARCHIVO = set(X.ARCHIVO_SYMBOLS) | {"a", "ae", "s", "S"} | set(X.DIGITS)


def from_archivo(name, ch):
    base = u.normalize("NFD", ch)[0]
    return name in ARCHIVO or (base in "asS" and base != ch)


def which_set(ch):
    c = u.category(ch)
    ascii_ = ord(ch) < 0x80
    if c in ("Lu", "Lt"):
        return "Uppercase" if ascii_ else "Extended"
    if c[0] == "L":
        return "Lowercase" if ascii_ else "Extended"
    if c[0] == "N":
        return "Figures"
    if c[0] == "P":
        return "Punctuation"
    if c[0] == "S":
        return "Symbols"
    return None


data = []
for cp, name in sorted(cmap.items()):
    ch = chr(cp)
    s = which_set(ch)
    if not s:
        continue
    data.append({"c": ch, "n": name, "s": s, "a": int(from_archivo(name, ch)),
                 "w": [static[w]["hmtx"][name][0] for w in (300, 400, 700)]})

feats = set()
for tag in ("GSUB", "GPOS"):
    if tag in var:
        feats |= {fr.FeatureTag for fr in var[tag].table.FeatureList.FeatureRecord}
version = var["name"].getDebugName(5).replace("Version ", "").split(";")[0]
version = f"{float(version):.2f}"

page = (ROOT / "specimen/font-page-template.html").read_text()
woff = base64.b64encode((ROOT / "fonts/variable/LittGrotesk[wght].woff2").read_bytes()).decode()
for k, v in {"__LITT__": "data:font/woff2;base64," + woff, "__GLYPH_DATA__": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
             "__VERSION__": version, "__CHARS__": str(len(cmap)), "__GLYPHS_N__": str(var["maxp"].numGlyphs),
             "__FEATS_N__": str(len(feats))}.items():
    page = page.replace(k, v)
Path(sys.argv[1]).write_text(page)
print(f"{len(data)} characters shown, {len(cmap)} mapped, {var['maxp'].numGlyphs} glyphs, features {sorted(feats)}, v{version}, {len(page)//1024} KB")
