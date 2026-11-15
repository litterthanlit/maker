"""Assemble the self-contained Litt Grotesk specimen (specimen/litt-template.html).

    S=<dir with captures and reference fonts> python3 proof/build-litt-specimen.py <out.html>

$S holds: c-{press,flat}-{arial|geist,litt}-{light,dark}.png from litt-card.js,
inter.woff2 and geist.woff2 (reference fonts) and v02.woff2 (the previous version).
Measured values in the legibility table come from the built font, not by hand.
"""
import base64, io, json, os, sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
S = Path(os.environ["S"])
f = instantiateVariableFont(TTFont(ROOT / "fonts/variable/LittGrotesk[wght].ttf"), {"wght": 400})
cm, hm, gs = f.getBestCmap(), f["hmtx"], f.getGlyphSet()
lcw = round(sum(hm[cm[ord(c)]][0] for c in "abcdefghijklmnopqrstuvwxyz") / 26)
pen = BoundsPen(gs); gs["n"].draw(pen); nsb = round(pen.bounds[0])


def img(name):
    out = io.BytesIO(); Image.open(S / name).save(out, "WEBP", quality=90)
    return "data:image/webp;base64," + base64.b64encode(out.getvalue()).decode()


def font(path):
    return "data:font/woff2;base64," + base64.b64encode(Path(path).read_bytes()).decode()


shots = {f"{w}-{face}-{t}": img(f"c-{w}-{face}-{t}.png")
         for w, base in (("press", "arial"), ("flat", "geist")) for face in (base, "litt") for t in ("light", "dark")}
t = (ROOT / "specimen/litt-template.html").read_text()
for k, v in {"__LITT__": font(ROOT / "fonts/variable/LittGrotesk[wght].woff2"), "__INTER__": font(S / "inter.woff2"),
             "__GEIST__": font(S / "geist.woff2"), "__KANTON__": font(S / "v02.woff2"),
             "__LCW__": str(lcw), "__NSB__": str(nsb), "__SHOTS__": json.dumps(shots)}.items():
    t = t.replace(k, v)
Path(sys.argv[1]).write_text(t)
print(f"lowercase width {lcw}, n sidebearing {nsb}, {len(t) // 1024} KB")
