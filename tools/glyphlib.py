"""Glyph construction DSL on top of the pen engine."""
import math
import numpy as np
from geom import (Stroke, Profile, stroke_contours, line_seg, unit, ellipse_contour,
                  polygon, rounded_polygon, signed_area, reverse_contour, transform_contour,
                  PLAN, PLAN_MODE, plan_key)


class Sk:
    """Skeleton (centre-line) path builder.

    M(x,y) start; L line; C cubic; H/V quarter curves; T tangent-directed
    curve; Z close.  Corners (tangent breaks) are split automatically into
    separate pen strokes so the pen produces round joins."""

    def __init__(self, x, y):
        self.start = np.array([x, y], float)
        self.cur = self.start.copy()
        self.segs = []
        self.closed = False

    def _add(self, seg):
        self.segs.append(np.asarray(seg, float))
        self.cur = self.segs[-1][3].copy()
        return self

    def L(self, x, y):
        return self._add(line_seg(self.cur, (x, y)))

    def l(self, dx, dy):
        return self.L(self.cur[0] + dx, self.cur[1] + dy)

    def C(self, x1, y1, x2, y2, x, y):
        return self._add([self.cur, (x1, y1), (x2, y2), (x, y)])

    def H(self, x, y, t=0.552, t2=None):
        """Quarter curve leaving horizontally, arriving vertically."""
        t2 = t if t2 is None else t2
        p0 = self.cur
        dx, dy = x - p0[0], y - p0[1]
        return self._add([p0, (p0[0] + t * dx, p0[1]), (x, y - t2 * dy), (x, y)])

    def V(self, x, y, t=0.552, t2=None):
        """Quarter curve leaving vertically, arriving horizontally."""
        t2 = t if t2 is None else t2
        p0 = self.cur
        dx, dy = x - p0[0], y - p0[1]
        return self._add([p0, (p0[0], p0[1] + t * dy), (x - t2 * dx, y), (x, y)])

    def T(self, x, y, a0, a1, t0=0.36, t1=0.36):
        """Curve to (x,y) leaving at angle a0 (deg) and arriving at angle a1,
        handle lengths as fractions of the chord."""
        p0 = self.cur
        ch = math.hypot(x - p0[0], y - p0[1])
        d0 = np.array([math.cos(math.radians(a0)), math.sin(math.radians(a0))])
        d1 = np.array([math.cos(math.radians(a1)), math.sin(math.radians(a1))])
        return self._add([p0, p0 + d0 * t0 * ch, np.array([x, y]) - d1 * t1 * ch, (x, y)])

    def Tc(self, x, y, a1, t0=0.36, t1=0.36):
        """Like T but leaving along the current tangent (G1 by construction)."""
        last = self.segs[-1]
        d = last[3] - last[2]
        if np.hypot(*d) < 1e-9:
            d = last[3] - last[0]
        a0 = math.degrees(math.atan2(d[1], d[0]))
        return self.T(x, y, a0, a1, t0, t1)

    def Z(self):
        if np.hypot(*(self.cur - self.start)) > 1e-6:
            self.L(*self.start)
        self.closed = True
        return self

    # -- split into smooth pieces
    def pieces(self, tol_deg=2.5):
        segs = self.segs
        if not segs:
            return []

        def t_out(s):
            d = s[1] - s[0]
            if np.hypot(*d) < 1e-9:
                d = s[2] - s[0]
            if np.hypot(*d) < 1e-9:
                d = s[3] - s[0]
            return unit(d)

        def t_in(s):
            d = s[3] - s[2]
            if np.hypot(*d) < 1e-9:
                d = s[3] - s[1]
            if np.hypot(*d) < 1e-9:
                d = s[3] - s[0]
            return unit(d)

        def smooth(s1, s2):
            a, b = t_in(s1), t_out(s2)
            return np.dot(a, b) > math.cos(math.radians(tol_deg))

        groups = [[segs[0]]]
        for s in segs[1:]:
            if smooth(groups[-1][-1], s):
                groups[-1].append(s)
            else:
                groups.append([s])
        if self.closed:
            if smooth(segs[-1], segs[0]):
                if len(groups) == 1:
                    return [(groups[0], True)]
                # merge last group into first
                groups[0] = groups[-1] + groups[0]
                groups.pop()
        return [(g, False) for g in groups]


RECORD = {'on': False, 'items': []}


def _sample_sk(segs, n=10):
    from geom import cubic_eval
    pts = []
    for i, s in enumerate(segs):
        u = np.linspace(0, 1, n)
        P = cubic_eval(s, u)
        if i:
            P = P[1:]
        pts.extend(P.tolist())
    return pts


class Ctx:
    """Master parameters."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    @property
    def pen(self):
        return (self.W / 2, self.H / 2)


class Glyph:
    def __init__(self, name, ctx, width=550):
        self.name = name
        self.ctx = ctx
        self.width = width
        self.contours = []
        self._n = 0

    def _key(self, *extra):
        self._n += 1
        return f"{self.name}#{self._n}" + ''.join(f'.{e}' for e in extra)

    def stroke(self, sk, prof=None, caps=('round', 'round'), scale=1.0, pen=None, merge=False):
        pen = pen or self.ctx.pen
        base = self._key()
        pcs = sk.pieces()
        if RECORD['on']:
            pts = _sample_sk(sk.segs)
            RECORD['items'].append({'pts': pts, 'w': 2 * pen[0] * scale, 'h': 2 * pen[1] * scale,
                                    'closed': sk.closed})
        for pi, (segs, closed) in enumerate(pcs):
            c = caps
            if len(pcs) > 1:
                # internal corner ends always round
                c = (caps[0] if pi == 0 else 'round', caps[1] if pi == len(pcs) - 1 else 'round')
            st = Stroke(segs, closed=closed, caps=c, prof=prof if len(pcs) == 1 else _sub_prof(prof, pi, len(pcs)),
                        scale=scale, merge=merge and not closed)
            cs = stroke_contours(st, pen, f"{base}.{pi}")
            self._add_oriented(cs, closed, f"{base}.{pi}")
        return self

    def _add_oriented(self, cs, closed, key):
        k = plan_key('orient', key)
        if PLAN_MODE['record'] or k not in PLAN:
            if closed and len(cs) == 2:
                a0, a1 = signed_area(cs[0]), signed_area(cs[1])
                outer = 0 if abs(a0) >= abs(a1) else 1
                flips = []
                for i, c in enumerate(cs):
                    a = signed_area(c)
                    want_cw = (i == outer)
                    flips.append((a > 0) if want_cw else (a < 0))
            else:
                flips = [signed_area(c) > 0 for c in cs]
            PLAN[k] = flips
        flips = PLAN[k]
        for c, f in zip(cs, flips):
            self.contours.append(reverse_contour(c) if f else c)

    def line(self, x0, y0, x1, y1, **kw):
        return self.stroke(Sk(x0, y0).L(x1, y1), **kw)

    def dot(self, x, y, d=None, dy=None):
        """Round dot.  d = diameter (default 1.22 * stem)."""
        d = d if d is not None else self.ctx.W * 1.22
        dy = dy if dy is not None else d * (self.ctx.H / self.ctx.W) ** 0.5
        self.contours.append(ellipse_contour(x, y, d / 2, dy / 2))
        if RECORD['on']:
            RECORD['items'].append({'pts': [[x, y], [x, y]], 'w': d, 'h': dy, 'closed': False})
        return self

    def ellipse(self, x, y, rx, ry):
        self.contours.append(ellipse_contour(x, y, rx, ry))
        return self

    def poly(self, pts):
        self.contours.append(polygon(pts))
        return self

    def rpoly(self, pts, r):
        self.contours.append(rounded_polygon(pts, r))
        return self

    def rect(self, x0, y0, x1, y1):
        return self.poly([(x0, y0), (x0, y1), (x1, y1), (x1, y0)])

    def hole(self, contour_fn, *a):
        """Add a counter-clockwise (subtractive) contour."""
        before = len(self.contours)
        contour_fn(*a)
        c = self.contours.pop()
        self.contours.append(reverse_contour(c))
        return self

    def add(self, other, dx=0, dy=0, sx=1, sy=1):
        for c in other.contours:
            c2 = transform_contour(c, (sx, 0, 0, sy, dx, dy))
            if sx * sy < 0:
                c2 = reverse_contour(c2)
            self.contours.append(c2)
        return self

    def transform(self, m):
        a, b, c, d, e, f = m
        det = a * d - b * c
        out = []
        for cc in self.contours:
            c2 = transform_contour(cc, m)
            out.append(reverse_contour(c2) if det < 0 else c2)
        self.contours = out
        return self


def _sub_prof(prof, i, n):
    """Width profile for piece i of n after corner splitting: tapers that were
    declared for the whole stroke apply to the first/last piece only."""
    if prof is None:
        return None
    return Profile(start=prof.start if i == 0 else None,
                   end=prof.end if i == n - 1 else None,
                   mid=None, scale=prof.scale)


def taper(start=None, end=None, scale=1.0):
    return Profile(start=start, end=end, scale=scale)
