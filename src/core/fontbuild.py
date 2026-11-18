"""The build pipeline every family shares.

A family describes itself with a Family: its names, metrics, masters and glyph
table. build() draws each master, converts the outlines to compatible TrueType
curves, compiles the features, merges the masters with varLib and writes:

    <out>/variable/<file>[wght].ttf + .woff2
    <out>/static/<file>-<Style>.ttf + .woff2

Set SOURCE_DATE_EPOCH for byte-reproducible output (it fixes head.modified).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fontTools.cu2qu import curves_to_quadratic
from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.otlLib.builder import buildStatTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import build as build_variable
from fontTools.varLib.instancer import instantiateVariableFont, OverlapMode

from .geometry import reverse, translate


@dataclass
class Family:
    name: str  # "Litt Grotesk"
    file: str  # "LittGrotesk"
    version: str  # "1.040"
    copyright: str
    glyphs: dict  # name -> (char or None, fn(params) -> (contours, ink, (lsb, rsb)))
    params: Callable  # wght -> the params object the glyph functions take
    masters: list  # weights drawn, e.g. [300, 400, 700]
    default: int
    instances: dict  # wght -> style name
    ascent: int
    descent: int
    x_height: int
    cap_height: int
    features: Callable  # wght -> feature file text
    out: Path
    upm: int = 1000
    hint: dict = None  # ttfautohint options for the statics; None leaves them unhinted
    code_pages: tuple = ()  # OS/2 code page bits to declare, e.g. (0, 1) for Latin 1 and Latin 2
    windows_names_only: bool = False  # leave out the old Macintosh name records
    smart_dropout: bool = False  # a prep program that keeps thin parts from dropping out when unhinted
    fs_type: int = None  # OS/2 fsType; None keeps fontTools' default (4, preview and print); open fonts want 0
    description: str = None  # name ID 10
    meta_scripts: str = None  # e.g. "Latn": the meta table's design and supported languages
    win_all_masters: bool = False  # set usWin* from the tallest and deepest glyph at any weight, so no instance clips


def draw_master(fam, wght):
    p = fam.params(wght)
    out = {}
    for name, (char, fn) in fam.glyphs.items():
        contours, ink, (lsb, rsb) = fn(p)
        out[name] = (translate(contours, lsb), round(lsb + ink + rsb))
    return out


def quadratic_glyphs(fam, masters):
    """Convert every glyph to TrueType outlines, keeping all masters compatible."""
    weights = list(masters)
    result = {w: {} for w in weights}
    for name in fam.glyphs:
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
                    for pen, spl, s in zip(pens, splines, segs):
                        # cu2qu rounds the end point through complex numbers; keep the
                        # exact one, so a contour that closes on its start always does
                        pen.qCurveTo(*spl[1:-1], s[-1])
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


def build_master(fam, wght, gl, path, win=None):
    order = [".notdef"] + list(fam.glyphs)
    glyf = {".notdef": notdef()[0]}
    metrics = {".notdef": (500, 50)}
    cmap = {}
    for name, (char, _) in fam.glyphs.items():
        g, adv = gl[name]
        glyf[name] = g
        g.recalcBounds(None) if hasattr(g, "recalcBounds") else None
        lsb = g.xMin if g.numberOfContours else 0
        metrics[name] = (adv, lsb)
        if char:
            cmap[ord(char)] = name

    ys = [(g.yMin, g.yMax) for g, _ in gl.values() if g.numberOfContours]
    if win is None:
        win = (min(y[0] for y in ys), max(y[1] for y in ys))  # Windows clips outside these
    style = fam.instances.get(wght, str(wght))
    fb = FontBuilder(fam.upm, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=fam.ascent, descent=fam.descent, lineGap=0)
    fb.setupNameTable({
        "familyName": fam.name,
        "styleName": style,
        "uniqueFontIdentifier": f"{fam.file}-{style};{fam.version}",
        "fullName": f"{fam.name} {style}",
        "psName": f"{fam.file}-{style}",
        "version": f"Version {fam.version}",
        "copyright": fam.copyright,
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
        "licenseInfoURL": "https://openfontlicense.org",
        **({"description": fam.description} if fam.description else {}),
    }, **({"mac": False} if fam.windows_names_only else {}))
    fb.setupOS2(
        sTypoAscender=fam.ascent, sTypoDescender=fam.descent, sTypoLineGap=0,
        usWinAscent=max(fam.ascent, win[1]), usWinDescent=max(-fam.descent, -win[0]),
        sxHeight=fam.x_height, sCapHeight=fam.cap_height,
        usWeightClass=wght, achVendID="NONE", fsSelection=0x80 | (0x40 if wght == 400 else 0),
        **({"fsType": fam.fs_type} if fam.fs_type is not None else {}),
    )
    fb.font["OS/2"].version = 4
    if fam.code_pages:
        fb.font["OS/2"].ulCodePageRange1 = sum(1 << b for b in fam.code_pages if b < 32)
        fb.font["OS/2"].ulCodePageRange2 = sum(1 << (b - 32) for b in fam.code_pages if b >= 32)
    fb.setupPost()
    fb.setupHead(unitsPerEm=fam.upm, fontRevision=float(fam.version))
    addOpenTypeFeaturesFromString(fb.font, fam.features(wght))
    fb.save(path)


def build(fam, tmp):
    """Build the variable font and its static instances; returns the variable font's path."""
    tmp.mkdir(exist_ok=True)
    (fam.out / "variable").mkdir(parents=True, exist_ok=True)
    (fam.out / "static").mkdir(parents=True, exist_ok=True)

    drawn = {w: draw_master(fam, w) for w in fam.masters}
    quads = quadratic_glyphs(fam, drawn)

    ds = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.tag, axis.name = "wght", "Weight"
    axis.minimum, axis.default, axis.maximum = min(fam.masters), fam.default, max(fam.masters)
    ds.addAxis(axis)
    win = None
    if fam.win_all_masters:
        gs = [g for w in fam.masters for g, _ in quads[w].values() if g.numberOfContours]
        for g in gs:
            g.recalcBounds(None)
        ys = [(g.yMin, g.yMax) for g in gs]
        win = (min(y[0] for y in ys), max(y[1] for y in ys))
    for w in fam.masters:
        path = tmp / f"{fam.file}-master-{w}.ttf"
        build_master(fam, w, quads[w], str(path), win)
        src = SourceDescriptor()
        src.path, src.location = str(path), {"Weight": w}
        src.styleName = fam.instances[w]
        ds.addSource(src)
    for w, style in fam.instances.items():
        inst = InstanceDescriptor()
        inst.familyName, inst.styleName, inst.location = fam.name, style, {"Weight": w}
        ds.addInstance(inst)

    vf, _, _ = build_variable(ds, exclude=["MVAR"])
    buildStatTable(vf, [{
        "tag": "wght", "name": "Weight",
        "values": [{"value": w, "name": s, **({"flags": 0x2} if w == fam.default else {})}
                   for w, s in fam.instances.items()],
    }])
    gasp = newTable("gasp")
    gasp.gaspRange = {0xFFFF: 0x000F}  # smooth and grid-fit at every size
    vf["gasp"] = gasp
    if fam.meta_scripts:
        meta = newTable("meta")
        meta.data = {"dlng": fam.meta_scripts, "slng": fam.meta_scripts}
        vf["meta"] = meta
    if fam.windows_names_only:  # varLib adds its axis and instance names on both platforms
        vf["name"].names = [n for n in vf["name"].names if n.platformID != 1]
    if fam.smart_dropout:
        from fontTools.ttLib.tables import ttProgram
        prep = newTable("prep")
        prep.program = ttProgram.Program()
        prep.program.fromAssembly(["PUSHW[ ]", "511", "SCANCTRL[ ]", "PUSHB[ ]", "4", "SCANTYPE[ ]"])
        vf["prep"] = prep
    vf_path = fam.out / "variable" / f"{fam.file}[wght].ttf"
    vf.save(vf_path)
    vf.flavor = "woff2"
    vf.save(vf_path.with_suffix(".woff2"))
    print("variable:", vf_path)

    for w, style in fam.instances.items():
        inst = instantiateVariableFont(TTFont(vf_path), {"wght": w}, updateFontNames=True,
                                       overlap=OverlapMode.REMOVE)
        inst["OS/2"].usWeightClass = w
        if fam.windows_names_only:
            inst["name"].names = [n for n in inst["name"].names if n.platformID != 1]
        sp = fam.out / "static" / f"{fam.file}-{style}.ttf"
        inst.save(sp)
        if fam.hint is not None:
            autohint(sp, fam.hint)
        inst = TTFont(sp)
        inst.flavor = "woff2"
        inst.save(sp.with_suffix(".woff2"))
        print("static:  ", sp)
    return vf_path


def autohint(path, options):
    """Hint a static font with ttfautohint, for crisp text on Windows."""
    try:
        import ttfautohint
    except ImportError:
        print("  ttfautohint-py not installed; static fonts left unhinted")
        return
    data = ttfautohint.ttfautohint(in_file=str(path), **options)
    Path(path).write_bytes(data)
