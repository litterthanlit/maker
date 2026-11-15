"""Build Litt Grotesk: the variable font, static instances and web fonts.

    python3 families/litt-grotesk/build.py [self-contained-specimen.html]

Writes to families/litt-grotesk/fonts/:
    variable/LittGrotesk[wght].ttf + .woff2
    static/LittGrotesk-<Style>.ttf + .woff2
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))
sys.path.insert(0, str(HERE))

from core.fontbuild import Family, build  # noqa: E402
import glyphs as G  # noqa: E402
import extended as X  # noqa: E402  (registers the extended character set)

# weight -> lowercase stem width. Everything else derives from the stem.
MASTERS = {300: 46, 400: 84, 700: 140}

KERN_CLASSES = {
    "A": "A", "VW": "V W", "T": "T", "Y": "Y", "L": "L", "P": "P", "F": "F", "R": "R",
    "round": "a c d e g o q s", "vwy": "v w y", "punct": "period comma",
    "quote": "quotesingle quotedbl", "rounduc": "C G O Q",
}
KERN_PAIRS = [  # (left, right, value at Regular)
    ("A", "VW", -55), ("A", "T", -62), ("A", "Y", -72), ("A", "vwy", -24), ("A", "quote", -60),
    ("VW", "A", -55), ("T", "A", -62), ("Y", "A", -72), ("F", "A", -40), ("P", "A", -52),
    ("L", "T", -82), ("L", "VW", -68), ("L", "Y", -88), ("L", "quote", -100), ("L", "vwy", -30),
    ("T", "round", -78), ("Y", "round", -80), ("VW", "round", -46), ("T", "vwy", -50),
    ("T", "punct", -88), ("Y", "punct", -88), ("VW", "punct", -74), ("P", "punct", -110),
    ("F", "punct", -80), ("vwy", "punct", -52), ("r", "punct", -60),
    ("rounduc", "A", -18), ("A", "rounduc", -18), ("R", "VW", -20), ("R", "T", -16),
    ("quote", "A", -60), ("punct", "quote", -90),
]


def kern_classes():
    """Kerning classes, extended so accented letters kern like their base."""
    out = {}
    for k, v in KERN_CLASSES.items():
        members = v.split()
        members += [c for c, base in X.BASE.items() if base in members and c not in members]
        out[k] = " ".join(members)
    return out


def gsub_fea():
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;"]
    lines.append("feature ccmp {")
    for base, mark, comp in X.ccmp_pairs():
        lines.append(f"  sub {base} {mark} by {comp};")
    lines.append("} ccmp;")
    for tag, pairs in X.ALT.items():
        lines.append(f"feature {tag} {{")
        for a, b in pairs:
            lines.append(f"  sub {a} by {b};")
        lines.append(f"}} {tag};")
    return "\n".join(lines)


def kern_fea(wght):
    scale = 1 + (MASTERS[wght] - 84) * 0.002
    lines = [f"@{k} = [{v}];" for k, v in kern_classes().items()]
    lines.append("feature kern {")
    for l, r, v in KERN_PAIRS:
        ls = f"@{l}" if l in KERN_CLASSES else l
        rs = f"@{r}" if r in KERN_CLASSES else r
        lines.append(f"  pos {ls} {rs} {round(v * scale)};")
    lines.append("} kern;")
    return "\n".join(lines)


LITT = Family(
    name="Litt Grotesk",
    file="LittGrotesk",
    version="1.040",
    copyright="Copyright 2026 The Litt Grotesk Project Authors; s, S and figures 0-9 from Archivo, Copyright 2020 The Archivo Project Authors",
    glyphs=G.GLYPHS,
    params=lambda w: G.P(w, MASTERS[w]),
    masters=list(MASTERS),
    default=400,
    instances={300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"},
    # Vertical metrics, chosen for UI: one set shared by every platform, no line
    # gap, and a line box whose centre (960 - 240) / 2 = 360 is the centre of the
    # capitals. Text in a button or input then sits optically centred.
    ascent=960,
    descent=-240,
    x_height=G.XH,
    cap_height=G.CH,
    features=lambda w: gsub_fea() + "\n" + kern_fea(w),
    out=HERE / "fonts",
    hint=dict(hint_composites=True, increase_x_height=14, windows_compatibility=True),
)


def write_specimen(woff2, embed_to=None):
    """specimen/index.html for local viewing; optionally a self-contained copy."""
    tpl = (HERE / "specimen" / "template.html").read_text()
    head = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    rel = "../fonts/variable/" + woff2.name.replace("[", "%5B").replace("]", "%5D")
    (HERE / "specimen" / "index.html").write_text(head + tpl.replace("__FONT_SRC__", rel))
    if embed_to:
        import base64
        uri = "data:font/woff2;base64," + base64.b64encode(woff2.read_bytes()).decode()
        Path(embed_to).write_text(tpl.replace("__FONT_SRC__", uri))


if __name__ == "__main__":
    vf = build(LITT, HERE.parent.parent / "build")
    write_specimen(vf.with_suffix(".woff2"), sys.argv[1] if len(sys.argv) > 1 else None)
