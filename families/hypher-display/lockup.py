"""The Hypher logo, optically set: the mark beside "hypher", as outlined SVG.

    python3 families/hypher-display/lockup.py            # writes lockup/*.svg

Two layers of adjustment, both measured, none by eye:

- Inside the word: the white space of each pair (h-y, y-p, p-h, h-e, e-r) is
  measured row by row through the x-height (autokern.profile), looking only
  DEPTH into each letter's open space, since the eye does not read a deep
  counter or the y's open triangles at full value. Every pair is moved toward
  the font's own rhythm, the space between two straight stems (n-n), so no gap
  reads larger than its neighbours: the y pairs and e-r, open on both sides,
  close up; p-h, two stems, stays.
- Mark to word: the mark is centred on the x-height (the ascender of the h
  and the descenders of y and p balance about it), the gap is measured from
  the midpoint of the mark's slanted edge (where the eye reads that edge), and
  both the gap and the mark grow a little as the word gets heavier.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))
sys.path.insert(0, str(HERE))

import autokern  # noqa: E402
import build  # noqa: E402
import glyphs as G  # noqa: E402
from core.geometry import translate  # noqa: E402

WORD = "hypher"
MARK = Path(HERE / "proof" / "hypher-mark.svg").read_text().split(' d="')[1].split('"')[0]
MARK_H, MARK_SLANT_MID = 94, 431.5  # the mark's height and its slanted edge at half height, in its own units
OPTICAL = 0.75  # how far each pair moves toward the reference gap
DEPTH = 0.18  # how far into a letter's open space the eye counts, in x-heights


def stem(wght):
    """The stem at any weight, as the variable font interpolates it."""
    (w0, s0), (w1, s1), (w2, s2) = sorted(build.MASTERS.items())
    if wght <= w1:
        return s0 + (wght - w0) * (s1 - s0) / (w1 - w0)
    return s1 + (wght - w1) * (s2 - s1) / (w2 - w1)


def word(style, wght, optical=True):
    """[(contours, x)] for each letter, and the word's ink width."""
    G.set_style(style)
    p = G.P(wght, stem(wght))
    drawn = [G.GLYPHS[c][1](p) for c in WORD]
    kern = build.kern_pairs()
    pairs = list(zip(WORD, WORD[1:]))

    def gap(l, r, dl, dr):
        (cl, wl, (_, rsb)), (cr, _, (lsb, _)) = dl, dr
        pl, pr = autokern.profile(cl, 0, G.XH), autokern.profile(cr, 0, G.XH)
        rows = [y for y in pl if y in pr]
        d = DEPTH * G.XH
        recess = sum(min(wl - pl[y][1], d) + min(pr[y][0], d) for y in rows) / len(rows)
        return rsb + lsb + kern.get((l, r), 0) + recess

    gaps = [gap(l, r, dl, dr) for (l, r), dl, dr in zip(pairs, drawn, drawn[1:])]
    n = G.GLYPHS["n"][1](p)
    target = gap("n", "n", n, n)
    shift = [OPTICAL * (target - g) if optical else 0 for g in gaps]
    out, x = [], 0
    for i, (contours, ink, (lsb, rsb)) in enumerate(drawn):
        if i:
            l, r = pairs[i - 1]
            x += kern.get((l, r), 0) + shift[i - 1]
        x += lsb
        out.append((contours, x))
        x += ink + rsb
    ink_right = out[-1][1] + drawn[-1][1]
    return out, ink_right, shift


def path_d(contours, dx=0, dy=0, flip=True):
    """SVG path data for maker contours, y flipped for SVG."""
    parts = []
    f = (lambda pt: (pt[0] + dx, -(pt[1]) + dy)) if flip else (lambda pt: (pt[0] + dx, pt[1] + dy))
    for c in contours:
        x, y = f(c[0])
        parts.append(f"M{x:.1f} {y:.1f}")
        for s in c[1:]:
            pts = [f(q) for q in s[1:]]
            parts.append(("L" if s[0] == "l" else "C") + " ".join(f"{a:.1f} {b:.1f}" for a, b in pts))
        parts.append("Z")
    return "".join(parts)


def lockup_svg(style, wght, optical=True, color="#1c1c1c"):
    letters, ink_right, _ = word(style, wght, optical)
    V = stem(wght)
    k = (V - build.MASTERS[400]) / (build.MASTERS[700] - build.MASTERS[400])
    mark_h = 1.34 * G.XH * ((1 + 0.06 * k) if optical else 1)
    s = mark_h / MARK_H
    mark_top = G.XH / 2 + mark_h / 2  # in font units, y up: centred on the x-height
    gap = 0.85 * G.XH + 0.6 * (V - build.MASTERS[400]) if optical else 0.7 * G.XH
    edge = MARK_SLANT_MID * s if optical else 445.1 * s
    x0 = edge + gap  # where the h's ink starts
    first_ink = letters[0][1]
    body = "".join(f'<path d="{path_d(c, x0 - first_ink + x, 0)}"/>' for c, x in [(c, x) for c, x in letters])
    top, bottom = max(G.ASC, mark_top), min(G.DSC, mark_top - mark_h)
    width = x0 - first_ink + ink_right
    mark = f'<path transform="translate(0 {-mark_top:.1f}) scale({s:.4f})" d="{MARK}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-top:.0f} {width:.0f} {top - bottom:.0f}" '
            f'fill="{color}">{mark}{body}</svg>')


if __name__ == "__main__":
    out = HERE / "lockup"
    out.mkdir(exist_ok=True)
    for style, name in (("Weld", "weld"), ("Wordmark", "wordmark"), ("Datum", "datum")):
        for wght in (300, 400, 500, 700):
            (out / f"hypher-lockup-{name}-{wght}.svg").write_text(lockup_svg(style, wght))
        _, _, shift = word(style, 400)
        print(f"{style:9} optical shifts at 400:", " ".join(f"{a}{b} {s:+.0f}" for (a, b), s in zip(zip(WORD, WORD[1:]), shift)))
    print("wrote", len(list(out.glob("*.svg"))), "lockups to", out)
