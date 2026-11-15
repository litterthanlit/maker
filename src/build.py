"""Build the variable font, static instances and web fonts.

    python3 src/build.py

Writes to fonts/:
    variable/<Family>[wght].ttf + .woff2
    static/<Family>-<Style>.ttf + .woff2
"""

import os
import sys
from pathlib import Path

from fontTools.cu2qu import curves_to_quadratic
from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.otlLib.builder import buildStatTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import build as build_variable
from fontTools.varLib.instancer import instantiateVariableFont, OverlapMode

sys.path.insert(0, os.path.dirname(__file__))
import glyphs as G  # noqa: E402
import extended as X  # noqa: E402  (registers the extended character set)
from geometry import reverse, translate  # noqa: E402

FAMILY = "Litt Grotesk"
FILE = "LittGrotesk"
VERSION = "1.010"
UPM = 1000

# Vertical metrics, chosen for UI: one set shared by every platform, no line
# gap, and a line box whose centre (960 - 240) / 2 = 360 is the centre of the
# capitals. Text in a button or input then sits optically centred.
ASCENT, DESCENT = 960, -240

# weight -> lowercase stem width. Everything else derives from the stem.
MASTERS = {300: 46, 400: 84, 700: 140}
DEFAULT = 400
INSTANCES = {300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fonts"
TMP = ROOT / "build"


def draw_master(wght):
    p = G.P(wght, MASTERS[wght])
    out = {}
    for name, (char, fn) in G.GLYPHS.items():
        contours, ink, (lsb, rsb) = fn(p)
        out[name] = (translate(contours, lsb), round(lsb + ink + rsb))
    return out


def quadratic_glyphs(masters):
    """Convert every glyph to TrueType outlines, keeping all masters compatible."""
    weights = list(masters)
    result = {w: {} for w in weights}
    for name in G.GLYPHS:
        sets = [masters[w][name][0] for w in weights]
        pens = [TTGlyphPen(None) for _ in weights]
        for ci in range(len(sets[0])):
            cons = [reverse(s[ci]) for s in sets]  # TrueType runs outer contours clockwise
            for pen, con in zip(pens, cons):
                pen.moveTo(con[0])
            cur = [con[0] for con in cons]
            for si in range(1, len(cons[0])):
                segs = [con[si] for con in cons]
                kinds = {s[0] for s in segs}
                assert len(kinds) == 1, f"{name}: incompatible segment in contour {ci}"
                if segs[0][0] == "l":
                    for pen, s in zip(pens, segs):
                        pen.lineTo(s[1])
                else:
                    cubics = [(c,) + s[1:] for c, s in zip(cur, segs)]
                    splines = curves_to_quadratic(cubics, [0.5] * len(cubics))
                    for pen, spl in zip(pens, splines):
                        pen.qCurveTo(*spl[1:])
                cur = [s[-1] for s in segs]
            for pen in pens:
                pen.closePath()
        for w, pen in zip(weights, pens):
            g = pen.glyph()
            if g.numberOfContours > 0:
                g.flags[0] |= 0x40  # OVERLAP_SIMPLE: contours overlap by design
            result[w][name] = (g, masters[w][name][1])
    return result


def notdef(width=500):
    pen = TTGlyphPen(None)
    for pts in ([(50, 0), (50, 700), (450, 700), (450, 0)], [(100, 50), (400, 50), (400, 650), (100, 650)]):
        pen.moveTo(pts[0])
        for q in pts[1:]:
            pen.lineTo(q)
        pen.closePath()
    return pen.glyph(), width


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


def build_master(wght, gl, path):
    order = [".notdef"] + list(G.GLYPHS)
    glyf = {".notdef": notdef()[0]}
    metrics = {".notdef": (500, 50)}
    cmap = {}
    for name, (char, _) in G.GLYPHS.items():
        g, adv = gl[name]
        glyf[name] = g
        g.recalcBounds(None) if hasattr(g, "recalcBounds") else None
        lsb = g.xMin if g.numberOfContours else 0
        metrics[name] = (adv, lsb)
        if char:
            cmap[ord(char)] = name

    ys = [(g.yMin, g.yMax) for g, _ in gl.values() if g.numberOfContours]
    win = (min(y[0] for y in ys), max(y[1] for y in ys))  # Windows clips outside these
    style = INSTANCES.get(wght, str(wght))
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT, lineGap=0)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": style,
        "uniqueFontIdentifier": f"{FILE}-{style};{VERSION}",
        "fullName": f"{FAMILY} {style}",
        "psName": f"{FILE}-{style}",
        "version": f"Version {VERSION}",
        "copyright": "Copyright 2026 The Litt Grotesk Project Authors; s, S and figures 0-9 from Archivo, Copyright 2020 The Archivo Project Authors",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(
        sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
        usWinAscent=max(ASCENT, win[1]), usWinDescent=max(-DESCENT, -win[0]), sxHeight=G.XH, sCapHeight=G.CH,
        usWeightClass=wght, achVendID="NONE", fsSelection=0x80 | (0x40 if wght == 400 else 0),
    )
    fb.font["OS/2"].version = 4
    fb.setupPost()
    fb.setupHead(unitsPerEm=UPM, fontRevision=float(VERSION))
    addOpenTypeFeaturesFromString(fb.font, gsub_fea() + "\n" + kern_fea(wght))
    fb.save(path)


def main():
    TMP.mkdir(exist_ok=True)
    (OUT / "variable").mkdir(parents=True, exist_ok=True)
    (OUT / "static").mkdir(parents=True, exist_ok=True)

    drawn = {w: draw_master(w) for w in MASTERS}
    quads = quadratic_glyphs(drawn)

    ds = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.tag, axis.name = "wght", "Weight"
    axis.minimum, axis.default, axis.maximum = min(MASTERS), DEFAULT, max(MASTERS)
    ds.addAxis(axis)
    for w in MASTERS:
        path = TMP / f"{FILE}-master-{w}.ttf"
        build_master(w, quads[w], str(path))
        src = SourceDescriptor()
        src.path, src.location = str(path), {"Weight": w}
        src.styleName = INSTANCES[w]
        ds.addSource(src)
    for w, style in INSTANCES.items():
        inst = InstanceDescriptor()
        inst.familyName, inst.styleName, inst.location = FAMILY, style, {"Weight": w}
        ds.addInstance(inst)

    vf, _, _ = build_variable(ds, exclude=["MVAR"])
    buildStatTable(vf, [{
        "tag": "wght", "name": "Weight",
        "values": [{"value": w, "name": s, **({"flags": 0x2} if w == DEFAULT else {})} for w, s in INSTANCES.items()],
    }])
    gasp = newTable("gasp")
    gasp.gaspRange = {0xFFFF: 0x000F}  # smooth and grid-fit at every size
    vf["gasp"] = gasp
    vf_path = OUT / "variable" / f"{FILE}[wght].ttf"
    vf.save(vf_path)
    vf.flavor = "woff2"
    vf.save(vf_path.with_suffix(".woff2"))
    print("variable:", vf_path)

    for w, style in INSTANCES.items():
        inst = instantiateVariableFont(TTFont(vf_path), {"wght": w}, updateFontNames=True,
                                       overlap=OverlapMode.REMOVE)
        inst["OS/2"].usWeightClass = w
        sp = OUT / "static" / f"{FILE}-{style}.ttf"
        inst.save(sp)
        autohint(sp)
        inst = TTFont(sp)
        inst.flavor = "woff2"
        inst.save(sp.with_suffix(".woff2"))
        print("static:  ", sp)

    write_specimen(vf_path.with_suffix(".woff2"))


def autohint(path):
    """Hint a static font with ttfautohint, for crisp text on Windows."""
    try:
        import ttfautohint
    except ImportError:
        print("  ttfautohint-py not installed; static fonts left unhinted")
        return
    data = ttfautohint.ttfautohint(in_file=str(path), hint_composites=True,
                                   increase_x_height=14, windows_compatibility=True)
    Path(path).write_bytes(data)


def write_specimen(woff2, embed_to=None):
    """specimen/index.html for local viewing; optionally a self-contained copy."""
    tpl = (ROOT / "specimen" / "template.html").read_text()
    head = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    rel = "../fonts/variable/" + woff2.name.replace("[", "%5B").replace("]", "%5D")
    (ROOT / "specimen" / "index.html").write_text(head + tpl.replace("__FONT_SRC__", rel))
    if embed_to:
        import base64
        uri = "data:font/woff2;base64," + base64.b64encode(woff2.read_bytes()).decode()
        Path(embed_to).write_text(tpl.replace("__FONT_SRC__", uri))


if __name__ == "__main__":
    main()
    if len(sys.argv) > 1:  # optional path for a self-contained specimen
        write_specimen(OUT / "variable" / f"{FILE}[wght].woff2", sys.argv[1])
