"""CJK ideographs for Clawd Mono, written with the same pen as the Latin.

Skeletons come from Make Me a Hanzi's stroke medians (derived from Arphic PL
KaitiM GB / UKai, Arphic Public License).  For each stroke we
  1. drop the kaiti entry/exit ticks (tiny pen-landing hooks),
  2. re-extend both ends by ray-casting against the original stroke outline,
     so that the round pen tip lands exactly where the brush stroke ended
     (depends on the master's pen radius -> outer extents stay constant),
  3. split at real corners (zhe) and over-tight turns, smooth the rest with
     a chord-scaled Catmull-Rom spline,
  4. draw with the Latin pen, with optical relief for dense characters.
"""
import json
import math
import os
import re
import numpy as np
from glyphlib import Sk

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(os.path.dirname(HERE), 'data', 'mmah', 'graphics.txt')

ADV = 1100
SCALE = 0.995          # Slightly enlarge the ink within the unchanged 1100-unit cell.
CX, CY = 550, 352      # where MMAH's em centre (512, 388) lands
CORNER_DEG = 54
TIGHT_R = 44           # MMAH units: turns tighter than this become corners

_DATA = None


def data():
    global _DATA
    if _DATA is None:
        _DATA = {}
        with open(DATA_PATH, encoding='utf-8') as f:
            for line in f:
                d = json.loads(line)
                _DATA[d['character']] = d
    return _DATA


# ------------------------------------------------------------------ svg outline
_tok = re.compile(r'[MLQCZ]|-?\d+(?:\.\d+)?')


def parse_outline(path, steps=6):
    toks = _tok.findall(path)
    pts = []
    i = 0
    cur = None
    start = None
    while i < len(toks):
        t = toks[i]
        i += 1
        if t == 'M':
            cur = np.array([float(toks[i]), float(toks[i + 1])])
            i += 2
            start = cur
            pts.append(cur)
        elif t == 'L':
            cur = np.array([float(toks[i]), float(toks[i + 1])])
            i += 2
            pts.append(cur)
        elif t == 'Q':
            c1 = np.array([float(toks[i]), float(toks[i + 1])])
            p = np.array([float(toks[i + 2]), float(toks[i + 3])])
            i += 4
            for k in range(1, steps + 1):
                u = k / steps
                pts.append((1 - u) ** 2 * cur + 2 * u * (1 - u) * c1 + u * u * p)
            cur = p
        elif t == 'C':
            c1 = np.array([float(toks[i]), float(toks[i + 1])])
            c2 = np.array([float(toks[i + 2]), float(toks[i + 3])])
            p = np.array([float(toks[i + 4]), float(toks[i + 5])])
            i += 6
            for k in range(1, steps + 1):
                u = k / steps
                pts.append((1 - u) ** 3 * cur + 3 * u * (1 - u) ** 2 * c1 + 3 * u * u * (1 - u) * c2 + u ** 3 * p)
            cur = p
        elif t == 'Z':
            pass
    return np.array(pts)


_OUT = {}


def _outline_cached(ch, path):
    k = (ch, path)
    if k not in _OUT:
        if len(_OUT) > 4000:
            _OUT.clear()
        _OUT[k] = parse_outline(path)
    return _OUT[k]


def point_in_poly(p, poly):
    x, y = p
    xs, ys = poly[:, 0], poly[:, 1]
    xj, yj = np.roll(xs, 1), np.roll(ys, 1)
    cond = ((ys > y) != (yj > y))
    with np.errstate(divide='ignore', invalid='ignore'):
        xint = (xj - xs) * (y - ys) / (yj - ys) + xs
    return bool(np.sum(cond & (x < xint)) % 2)


def ray_exit(E, d, poly):
    """Distance along unit d from E to the polygon boundary (first hit)."""
    A = poly
    B = np.roll(poly, -1, axis=0)
    e = B - A
    # solve E + t d = A + s e
    den = d[0] * e[:, 1] - d[1] * e[:, 0]
    with np.errstate(divide='ignore', invalid='ignore'):
        w = A - E
        t = (w[:, 0] * e[:, 1] - w[:, 1] * e[:, 0]) / den
        s = (w[:, 0] * d[1] - w[:, 1] * d[0]) / den
    ok = (np.abs(den) > 1e-9) & (s >= 0) & (s <= 1) & (t > 1e-6)
    if not np.any(ok):
        return None
    return float(np.min(t[ok]))


# ------------------------------------------------------------------ cleanup
def _ang(v):
    return math.atan2(v[1], v[0])


def _turn(a, b):
    t = math.degrees(_ang(b) - _ang(a))
    return (t + 180) % 360 - 180


def clean(m):
    m = [np.array(p, float) for p in m]
    out = [m[0]]
    for p in m[1:]:
        if np.hypot(*(p - out[-1])) > 3:
            out.append(p)
    m = out
    if len(m) >= 3:
        d0, d1 = m[1] - m[0], m[2] - m[1]
        if np.hypot(*d0) < 42 and abs(_turn(d0, d1)) > 14:
            m = m[1:]
    if len(m) >= 3:
        d0, d1 = m[-2] - m[-3], m[-1] - m[-2]
        L = np.hypot(*d1)
        if L < 34 and abs(_turn(d0, d1)) > 18:
            m = m[:-1]
    return m


def split_corners(m):
    """Return list of index lists (pieces); corners shared between pieces."""
    n = len(m)
    cuts = [0]
    for i in range(1, n - 1):
        a, b = m[i] - m[i - 1], m[i + 1] - m[i]
        t = abs(_turn(a, b))
        corner = t > CORNER_DEG
        if not corner and t > 25:
            # circle through three points: tight turn?
            la, lb, lc = np.hypot(*a), np.hypot(*b), np.hypot(*(m[i + 1] - m[i - 1]))
            area = abs(a[0] * b[1] - a[1] * b[0]) / 2
            if area > 1e-6:
                R = la * lb * lc / (4 * area)
                corner = R < TIGHT_R
        if corner:
            cuts.append(i)
    cuts.append(n - 1)
    return [list(range(cuts[k], cuts[k + 1] + 1)) for k in range(len(cuts) - 1)]


def smooth_sk(pts):
    """Chord-scaled Catmull-Rom through pts -> Sk."""
    P = [np.asarray(p, float) for p in pts]
    n = len(P)
    sk = Sk(*P[0])
    if n == 2:
        return sk.L(*P[1])
    d = [P[i + 1] - P[i] for i in range(n - 1)]
    L = [max(np.hypot(*v), 1e-6) for v in d]
    u = [d[i] / L[i] for i in range(n - 1)]
    T = [None] * n
    for i in range(1, n - 1):
        v = u[i - 1] * L[i] + u[i] * L[i - 1]       # weight toward the shorter side
        T[i] = v / max(np.hypot(*v), 1e-9)
    # natural ends: reflect neighbour tangent about the end chord
    T[0] = 2 * np.dot(u[0], T[1]) * u[0] - T[1]
    T[-1] = 2 * np.dot(u[-1], T[-2]) * u[-1] - T[-2]
    for i in range(n - 1):
        h = L[i] / 3
        c1 = P[i] + T[i] * h
        c2 = P[i + 1] - T[i + 1] * h
        sk.C(c1[0], c1[1], c2[0], c2[1], P[i + 1][0], P[i + 1][1])
    return sk


def to_font(p):
    return np.array([(p[0] - 512) * SCALE + CX, (p[1] - 388) * SCALE + CY])


def strokes_for(ch, r_mmah):
    """(cleaned median, end-corrected median) pairs in MMAH units."""
    d = data()[ch]
    out = []
    for path, med in zip(d['strokes'], d['medians']):
        m = clean(med)
        if len(m) < 2:
            m = [np.array(med[0], float), np.array(med[-1], float)]
        poly = _outline_cached(ch, path)
        m0 = [p.copy() for p in m]
        m = [p.copy() for p in m]
        orig_len = sum(np.hypot(*(m[i + 1] - m[i])) for i in range(len(m) - 1))
        for end in (0, -1):
            E = m[end]
            nb = m[1] if end == 0 else m[-2]
            dvec = E - nb
            dl = np.hypot(*dvec)
            if dl < 1e-6:
                continue
            dvec = dvec / dl
            if not point_in_poly(E, poly):
                # pull inside first
                continue
            t = ray_exit(E, dvec, poly)
            if t is None:
                continue
            ext = t - r_mmah
            # never shrink a segment below 30% of its length
            ext = max(ext, -0.7 * dl)
            m[end] = E + dvec * ext
        out.append((m0, m))
    return out


def _thin(m, min_gap=26.0):
    """Drop interior points crowding their predecessor (keeps ends)."""
    out = [m[0]]
    for p in m[1:-1]:
        if np.hypot(*(p - out[-1])) >= min_gap:
            out.append(p)
    out.append(m[-1])
    return out


_DENS = {}
WC_REG, HC_REG = 78, 67


def density_factor(ch):
    """1.0 for open characters, down to 0.2 for the densest: how much of the
    heavy master's extra stroke width this character can take."""
    if ch not in _DENS:
        t = 0.0
        for m in data()[ch]['medians']:
            m = np.array(m, float)
            t += float(np.sum(np.hypot(*np.diff(m, axis=0).T)))
        s = 860.0 ** 2 / max(t, 1.0)
        _DENS[ch] = min(1.0, max(0.2, (s - 105.0) / (190.0 - 105.0)))
    return _DENS[ch]


def pen_for(c, ch):
    f = density_factor(ch)
    # Open characters use the same pen as Latin. Dense regulars get up to
    # 8% relief; the heavy master's extra ink still follows the density.
    relief = 0.90 + 0.10 * f
    if c.Wc <= WC_REG:
        # Fade optical relief out toward the thin master.
        blend = min(1.0, max(0.0, (c.Wc - 22) / (WC_REG - 22)))
        k = 1.0 - blend * (1.0 - relief)
        return c.Wc * k, c.Hc * k
    return (WC_REG * relief + (c.Wc - WC_REG) * f,
            HC_REG * relief + (c.Hc - HC_REG) * f)


def _draw(G, c, ch):
    from geom import quad_stroke
    Wc, Hc = pen_for(c, ch)
    r_mmah = (Wc / 2) / SCALE
    pen = (Wc / 2, Hc / 2)
    for m0, m in strokes_for(ch, r_mmah):
        keep = _thin_idx(m0)
        m0 = [m0[i] for i in keep]
        m = [m[i] for i in keep]
        for piece in split_corners(m0):
            ctrl0 = [m0[i] for i in piece]
            ctrl = [to_font(m[i]) for i in piece]
            # structure from the uncorrected skeleton: which spans to refine
            ref = _refine_plan(ctrl0)
            ctrl = _apply_refine(ctrl, ref)
            G.contours.append(quad_stroke(ctrl, pen))
            from glyphlib import RECORD
            if RECORD['on']:
                RECORD['items'].append({'pts': _sample_quad(ctrl), 'w': 2 * pen[0], 'h': 2 * pen[1],
                                        'closed': False, 'piece': True})


_XFIT = {}


def _ink_bounds(contours):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.pointPen import PointToSegmentPen
    bounds = BoundsPen(None)
    points = PointToSegmentPen(bounds)
    for contour in contours:
        if not contour:
            continue
        points.beginPath()
        for x, y, on in contour:
            points.addPoint((x, y), segmentType='qcurve' if on else None)
        points.endPath()
    return bounds.bounds


def horizontal_fit(ch):
    """Use one optical fit for every master, retaining the 1100-unit grid."""
    if ch not in _XFIT:
        from build import CTX
        from glyphlib import Glyph, RECORD
        recording = RECORD['on']
        RECORD['on'] = False
        try:
            bounds = {}
            for name, context in CTX.items():
                glyph = Glyph(glyph_name(ch), context, ADV)
                _draw(glyph, context, ch)
                bounds[name] = _ink_bounds(glyph.contours)
        finally:
            RECORD['on'] = recording
        regular = bounds['Regular']
        left = min(b[0] for b in bounds.values())
        right = max(b[2] for b in bounds.values())
        # Most characters reach a 950-unit ink width. The stretch limit
        # preserves naturally narrow forms; the master union protects edges.
        scale = min(1.14, max(1.0, 950 / (regular[2] - regular[0])),
                    (ADV - 60) / (right - left))
        shift = ADV / 2 - scale * (regular[0] + regular[2]) / 2
        shift = max(30 - scale * left, min(shift, ADV - 30 - scale * right))
        _XFIT[ch] = scale, shift
    return _XFIT[ch]


def draw(G, c, ch):
    from glyphlib import RECORD
    first_contour = len(G.contours)
    first_record = len(RECORD['items'])
    _draw(G, c, ch)
    scale, shift = horizontal_fit(ch)
    for i in range(first_contour, len(G.contours)):
        G.contours[i] = [(x * scale + shift, y, on) for x, y, on in G.contours[i]]
    if RECORD['on']:
        for item in RECORD['items'][first_record:]:
            item['pts'] = [[x * scale + shift, y] for x, y in item['pts']]
            item['w'] *= scale


def _dp(P, idx, tol):
    """Douglas-Peucker over P[idx] -> kept indices (ends kept)."""
    if len(idx) < 3:
        return list(idx)
    a, b = P[idx[0]], P[idx[-1]]
    d = b - a
    L = float(np.hypot(*d))
    best, bi = -1.0, None
    for k in idx[1:-1]:
        v = P[k] - a
        dist = abs(v[0] * d[1] - v[1] * d[0]) / L if L > 1e-9 else float(np.hypot(*v))
        if dist > best:
            best, bi = dist, k
    if best > tol:
        j = idx.index(bi)
        left = _dp(P, idx[:j + 1], tol)
        right = _dp(P, idx[j:], tol)
        return left[:-1] + right
    return [idx[0], idx[-1]]


def _thin_idx(m, min_gap=26.0, tol=3.2):
    keep = [0]
    for i in range(1, len(m) - 1):
        if np.hypot(*(m[i] - m[keep[-1]])) >= min_gap:
            keep.append(i)
    keep.append(len(m) - 1)
    return _dp(m, keep, tol)


def _refine_plan(P, max_turn_deg=36.0):
    """Indices of interior control points whose span gets split."""
    flags = []
    n = len(P) - 1
    for i in range(1, n):
        a, b = P[i] - P[i - 1], P[i + 1] - P[i]
        flags.append(abs(_turn(a, b)) > max_turn_deg)
    return flags


def _apply_refine(P, flags):
    """Uniform subdivision of every quadratic piece (keeps the TrueType
    implied-midpoint structure valid); only when some turn is sharp."""
    P = [np.asarray(p, float) for p in P]
    n = len(P) - 1
    if n < 2 or not any(flags):
        return P
    out = [P[0]]
    for i in range(1, n):
        A = P[0] if i == 1 else (P[i - 1] + P[i]) / 2
        B = P[n] if i == n - 1 else (P[i] + P[i + 1]) / 2
        out.append((A + P[i]) / 2)
        out.append((P[i] + B) / 2)
    out.append(P[n])
    return out


def _sample_quad(P, n=8):
    P = [np.asarray(p, float) for p in P]
    if len(P) == 2:
        return [P[0].tolist(), P[1].tolist()]
    out = [P[0].tolist()]
    m = len(P) - 2
    for i in range(1, len(P) - 1):
        a = P[0] if i == 1 else (P[i - 1] + P[i]) / 2
        b = P[-1] if i == len(P) - 2 else (P[i] + P[i + 1]) / 2
        for k in range(1, n + 1):
            t = k / n
            out.append(((1 - t) ** 2 * a + 2 * t * (1 - t) * P[i] + t * t * b).tolist())
    return out


def glyph_name(ch):
    return 'uni%04X' % ord(ch)
