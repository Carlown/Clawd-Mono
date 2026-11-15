"""Terminal glyphs: box drawing, blocks, shades, braille, Powerline, geometric
shapes, arrows, and the Claude Code interface set (spinner sparks, tool
bullets, prompts, todo boxes, Clawd)."""
import math
import unicodedata
from glyphlib import Sk, taper, Glyph
from geom import rounded_polygon, polygon, reverse_contour, ellipse_contour

REG = {}
ADV = 550
TOP, BOT = 960, -280          # full cell (hhea ascent / descent)
YC = (TOP + BOT) / 2          # 340
XC = ADV / 2
AX = 300                      # math axis / UI symbol centre


def g(name, *uni, w=ADV):
    def deco(fn):
        REG[name] = (list(uni), w, fn)
        return fn
    return deco


def reg(name, uni, fn, w=ADV):
    REG[name] = ([uni] if isinstance(uni, int) else list(uni), w, fn)


def lw(c):
    """Light box-line thickness."""
    return c.H * 0.92


def hw_(c):
    return c.H * 0.92 * 1.85 + 6


# ================================================================== box drawing
DIRS = ('UP', 'DOWN', 'LEFT', 'RIGHT')


def parse_box(name):
    toks = name.replace('BOX DRAWINGS ', '').split()
    arms = {}
    pending = []
    prefix = None
    W = {'LIGHT': 1, 'SINGLE': 1, 'HEAVY': 2, 'DOUBLE': 3}
    for t in toks:
        if t in W:
            if pending:
                for d in pending:
                    arms[d] = W[t]
                pending = []
            else:
                prefix = W[t]
        elif t in DIRS or t in ('VERTICAL', 'HORIZONTAL'):
            ds = [t] if t in DIRS else (['UP', 'DOWN'] if t == 'VERTICAL' else ['LEFT', 'RIGHT'])
            for d in ds:
                if prefix:
                    arms[d] = prefix
                else:
                    pending.append(d)
        elif t == 'AND':
            pass
        else:
            return None
    for d in pending:
        arms[d] = 1
    return arms


def box_glyph(arms):
    def fn(G, c):
        L, Hv = lw(c), hw_(c)
        thick = {1: L, 2: Hv}
        gap = max(L * 1.15, 40)
        d = gap / 2 + L / 2          # offset of each line of a double pair
        perp = {'UP': ('LEFT', 'RIGHT'), 'DOWN': ('LEFT', 'RIGHT'),
                'LEFT': ('DOWN', 'UP'), 'RIGHT': ('DOWN', 'UP')}

        def ext(D2):
            w = arms.get(D2, 0)
            return 0 if not w else (thick[w] / 2 if w in (1, 2) else d + L / 2)

        for D, w in arms.items():
            pa, pb = perp[D]
            if w in (1, 2):
                t = thick[w]
                _arm(G, D, -max(ext(pa), ext(pb)), -t / 2, t / 2)
            else:
                for side, pd, other in ((-1, pa, pb), (1, pb, pa)):
                    wpd = arms.get(pd, 0)
                    if wpd == 3:
                        start = d - L / 2
                    elif wpd:
                        start = -thick[wpd] / 2
                    else:
                        start = -ext(other)
                    _arm(G, D, start, side * d - L / 2, side * d + L / 2)
    return fn


def _arm(G, D, start, o0, o1):
    """Rectangle along direction D from distance `start` (from centre) to the
    cell edge, spanning perpendicular offsets o0..o1."""
    if D == 'RIGHT':
        G.rect(XC + start, YC + o0, ADV, YC + o1)
    elif D == 'LEFT':
        G.rect(0, YC + o0, XC - start, YC + o1)
    elif D == 'UP':
        G.rect(XC + o0, YC + start, XC + o1, TOP)
    else:
        G.rect(XC + o0, BOT, XC + o1, YC - start)


def dash_glyph(horizontal, n, heavy):
    def fn(G, c):
        t = hw_(c) if heavy else lw(c)
        span = ADV if horizontal else (TOP - BOT)
        seg = span / n
        gapf = 0.32 if n > 2 else 0.25
        for i in range(n):
            a = i * seg + seg * gapf / 2
            b = (i + 1) * seg - seg * gapf / 2
            if horizontal:
                G.rect(a, YC - t / 2, b, YC + t / 2)
            else:
                G.rect(XC - t / 2, BOT + a, XC + t / 2, BOT + b)
    return fn


def arc_glyph(kind):
    # kind: which corner the arc connects: 'DR' down&right, 'DL', 'UL', 'UR'
    def fn(G, c):
        t = lw(c)
        R = XC
        pen = (t / 2, t / 2)
        if kind == 'DR':
            sk = Sk(XC, BOT).L(XC, YC - R).V(ADV, YC, 0.552)
        elif kind == 'DL':
            sk = Sk(XC, BOT).L(XC, YC - R).V(0, YC, 0.552)
        elif kind == 'UL':
            sk = Sk(XC, TOP).L(XC, YC + R).V(0, YC, 0.552)
        else:
            sk = Sk(XC, TOP).L(XC, YC + R).V(ADV, YC, 0.552)
        G.stroke(sk, caps=('flat', 'flat'), pen=pen)
    return fn


def _diag_poly(G, t, rising):
    """Band of thickness t along the cell diagonal, clipped to the cell."""
    import math as _m
    L = _m.hypot(ADV, TOP - BOT)
    dx, dy = ADV / L, (TOP - BOT) / L
    a = (t / 2) / dx            # vertical half-thickness at x = 0 / ADV
    b = (t / 2) / dy            # horizontal half-thickness at y = BOT / TOP
    pts = [(0, BOT), (0, BOT + a), (ADV - b, TOP), (ADV, TOP), (ADV, TOP - a), (b, BOT)]
    if not rising:
        pts = [(x, TOP + BOT - y) for x, y in pts]
    G.poly(pts)


def diag_glyph(which):
    def fn(G, c):
        t = lw(c)
        if which in ('/', 'X'):
            _diag_poly(G, t, True)
        if which in ('\\', 'X'):
            _diag_poly(G, t, False)
    return fn


for cp in range(0x2500, 0x2580):
    nm = unicodedata.name(chr(cp), '')
    gname = 'uni%04X' % cp
    if 'ARC' in nm:
        k = {'DOWN AND RIGHT': 'DR', 'DOWN AND LEFT': 'DL', 'UP AND LEFT': 'UL', 'UP AND RIGHT': 'UR'}
        for key, v in k.items():
            if key in nm:
                reg(gname, cp, arc_glyph(v))
    elif 'DIAGONAL' in nm:
        if 'CROSS' in nm:
            reg(gname, cp, diag_glyph('X'))
        elif 'UPPER RIGHT TO LOWER LEFT' in nm:
            reg(gname, cp, diag_glyph('/'))
        else:
            reg(gname, cp, diag_glyph('\\'))
    elif 'DASH' in nm:
        n = 2 if 'DOUBLE DASH' in nm else 3 if 'TRIPLE' in nm else 4
        reg(gname, cp, dash_glyph('HORIZONTAL' in nm, n, 'HEAVY' in nm))
    else:
        arms = parse_box(nm)
        if arms:
            reg(gname, cp, box_glyph(arms))


# ================================================================== blocks
def rect_fn(*rects):
    def fn(G, c):
        for x0, y0, x1, y1 in rects:
            G.rect(x0, y0, x1, y1)
    return fn


H8 = (TOP - BOT) / 8
W8 = ADV / 8
reg('uni2580', 0x2580, rect_fn((0, YC, ADV, TOP)))
for k in range(1, 8):
    reg('uni%04X' % (0x2580 + k), 0x2580 + k, rect_fn((0, BOT, ADV, BOT + k * H8)))
reg('uni2588', 0x2588, rect_fn((0, BOT, ADV, TOP)))
for k in range(7, 0, -1):
    cp = 0x2589 + (7 - k)
    reg('uni%04X' % cp, cp, rect_fn((0, BOT, k * W8, TOP)))
reg('uni2590', 0x2590, rect_fn((XC, BOT, ADV, TOP)))
reg('uni2594', 0x2594, rect_fn((0, TOP - H8, ADV, TOP)))
reg('uni2595', 0x2595, rect_fn((ADV - W8, BOT, ADV, TOP)))
Q = {'UL': (0, YC, XC, TOP), 'UR': (XC, YC, ADV, TOP), 'LL': (0, BOT, XC, YC), 'LR': (XC, BOT, ADV, YC)}
for cp, parts in ((0x2596, 'LL'), (0x2597, 'LR'), (0x2598, 'UL'), (0x2599, 'UL LL LR'), (0x259A, 'UL LR'),
                  (0x259B, 'UL UR LL'), (0x259C, 'UL UR LR'), (0x259D, 'UR'), (0x259E, 'UR LL'),
                  (0x259F, 'UR LL LR')):
    reg('uni%04X' % cp, cp, rect_fn(*[Q[p] for p in parts.split()]))


def shade(level):
    def fn(G, c):
        cw, ch = ADV / 4, (TOP - BOT) / 8
        if level == 3:
            G.rect(0, BOT, ADV, TOP)
        for i in range(4):
            for j in range(8):
                x0, y0 = i * cw, BOT + j * ch
                if level == 1 and (i % 2 == 0 and j % 2 == 0):
                    G.rect(x0, y0, x0 + cw, y0 + ch)
                elif level == 2 and (i + j) % 2 == 0:
                    G.rect(x0, y0, x0 + cw, y0 + ch)
                elif level == 3 and (i % 2 == 1 and j % 2 == 1):
                    c2 = polygon([(x0, y0), (x0, y0 + ch), (x0 + cw, y0 + ch), (x0 + cw, y0)])
                    G.contours.append(reverse_contour(c2))
    return fn


for cp, lv in ((0x2591, 1), (0x2592, 2), (0x2593, 3)):
    reg('uni%04X' % cp, cp, shade(lv))


# ================================================================== braille
def braille(bits):
    def fn(G, c):
        d = min(150, c.W * 1.55 + 16)
        xs = (XC - 118, XC + 118)
        step = (TOP - BOT) / 4
        ys = [YC + 1.5 * step - 6, YC + 0.5 * step - 2, YC - 0.5 * step + 2, YC - 1.5 * step + 6]
        pos = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]
        for b in range(8):
            if bits & (1 << b):
                col, row = pos[b]
                G.dot(xs[col], ys[row], d, d)
    return fn


for bits in range(256):
    cp = 0x2800 + bits
    reg('uni%04X' % cp, cp, braille(bits))


# ================================================================== powerline
def pl_tri(right, solid):
    def fn(G, c):
        if solid:
            if right:
                G.poly([(0, BOT), (0, TOP), (ADV, YC)])
            else:
                G.poly([(ADV, BOT), (ADV, TOP), (0, YC)])
            return
        import math as _m
        t = lw(c)
        L = _m.hypot(ADV, TOP - YC)
        cosb, sinb = ADV / L, (TOP - YC) / L
        av = t / cosb          # vertical thickness at the cell edge
        wt = t / sinb          # horizontal thickness at the tip
        pts = [(0, TOP), (ADV, YC), (0, BOT), (0, BOT + av), (ADV - wt, YC), (0, TOP - av)]
        if not right:
            pts = [(ADV - x, y) for x, y in pts]
        G.poly(pts)
    return fn


def pl_round(right, solid):
    def fn(G, c):
        R = (TOP - BOT) / 2
        if solid:
            if right:
                half = [(0, TOP, True)] + _half(0, YC, ADV, R, True) + [(0, BOT, True)]
            else:
                half = [(ADV, BOT, True)] + _half(ADV, YC, ADV, R, False) + [(ADV, TOP, True)]
            G.contours.append(polygon_keep(half))
        else:
            t = lw(c)
            pen = (t / 2, t / 2)
            if right:
                G.stroke(Sk(0, TOP - t / 2).H(ADV - t / 2, YC, 0.552).V(0, BOT + t / 2, 0.552),
                         caps=('flat', 'flat'), pen=pen)
            else:
                G.stroke(Sk(ADV, TOP - t / 2).H(t / 2, YC, 0.552).V(ADV, BOT + t / 2, 0.552),
                         caps=('flat', 'flat'), pen=pen)
    return fn


def _half(cx, cy, rx, ry, right):
    from geom import _arc_ctrl
    import numpy as np
    pts = []
    if right:
        a0, sweep = math.pi / 2, -math.pi
    else:
        a0, sweep = -math.pi / 2, -math.pi
    offs = _arc_ctrl(np.array([0.0, 0.0]), 1.0, a0, sweep, 4)
    for i, o in enumerate(offs):
        pts.append((cx + rx * o[0], cy + ry * o[1], False))
    return pts


def polygon_keep(pts):
    from geom import signed_area
    if signed_area(pts) > 0:
        pts = reverse_contour(pts)
    return pts


reg('uniE0B0', 0xE0B0, pl_tri(True, True))
reg('uniE0B1', 0xE0B1, pl_tri(True, False))
reg('uniE0B2', 0xE0B2, pl_tri(False, True))
reg('uniE0B3', 0xE0B3, pl_tri(False, False))
reg('uniE0B4', 0xE0B4, pl_round(True, True))
reg('uniE0B5', 0xE0B5, pl_round(True, False))
reg('uniE0B6', 0xE0B6, pl_round(False, True))
reg('uniE0B7', 0xE0B7, pl_round(False, False))


@g('uniE0A0', 0xE0A0)
def _pl_branch(G, c):
    k = 0.8
    G.line(170, 40, 170, 640, scale=k)
    G.stroke(Sk(170, 300).T(390, 470, 70, 90, 0.45, 0.4).L(390, 520), scale=k)
    G.stroke(_ring(390, 600, 75), scale=k)
    G.stroke(_ring(170, 690, 75), scale=k)


@g('uniE0A2', 0xE0A2)
def _pl_lock(G, c):
    G.rpoly([(100, 0), (100, 360), (450, 360), (450, 0)], 40)
    G.stroke(Sk(165, 330).L(165, 470).V(275, 600, 0.56).H(385, 470, 0.56).L(385, 330), scale=0.85)


def _ring(cx, cy, r):
    return Sk(cx, cy + r).H(cx + r, cy, 0.552).V(cx, cy - r, 0.552).H(cx - r, cy, 0.552).V(cx, cy + r, 0.552).Z()


# ================================================================== sparks (Claude Code spinner)
# The spinner cycles  ·  ✢  ✳  ✶  ✻  ✽  and back; these are drawn as frames
# of one spark blooming, all centred on the same point.
SC = AX + 20


def petals(G, c, n, r0, r1, wf, rot=90, tear=True, k=1.0):
    for i in range(n):
        a = math.radians(rot + i * 360 / n)
        ca, sa = math.cos(a), math.sin(a)
        sk = Sk(XC + r0 * ca, SC + r0 * sa).L(XC + r1 * ca, SC + r1 * sa)
        if tear:
            G.stroke(sk, prof=taper(start=(0.42, (r1 - r0) * 0.9)), scale=wf * k)
        else:
            G.stroke(sk, scale=wf * k)


@g('uni2722', 0x2722)      # ✢ four teardrop-spoked asterisk
def _sp1(G, c):
    petals(G, c, 4, 20, 128, 1.15)


@g('uni2733', 0x2733)      # ✳ eight spoked asterisk
def _sp2(G, c):
    petals(G, c, 8, 0, 168, 0.72, rot=90, tear=False)


@g('uni2736', 0x2736)      # ✶ six pointed black star
def _sp3(G, c):
    R, r = 205, 92
    pts = []
    for i in range(12):
        a = math.radians(90 + i * 30)
        rr = R if i % 2 == 0 else r
        pts.append((XC + rr * math.cos(a), SC + rr * math.sin(a)))
    G.rpoly(pts, [c.W * 0.32 if i % 2 == 0 else 6 for i in range(12)])


@g('uni273B', 0x273B)      # ✻ teardrop-spoked asterisk
def _sp4(G, c):
    petals(G, c, 6, 26, 196, 1.2, rot=90)


@g('uni273D', 0x273D)      # ✽ heavy teardrop-spoked asterisk
def _sp5(G, c):
    petals(G, c, 8, 26, 212, 1.32, rot=90)


@g('uni2217', 0x2217)      # ∗ asterisk operator (centred)
def _astop(G, c):
    for i in range(6):
        a = math.radians(90 + i * 60)
        G.stroke(Sk(XC, AX).L(XC + 150 * math.cos(a), AX + 150 * math.sin(a)), scale=0.92)


@g('uni2731', 0x2731)      # ✱ heavy asterisk
def _hast(G, c):
    petals(G, c, 6, 0, 190, 1.35, tear=False)


@g('uni2732', 0x2732)      # ✲ open centre asterisk
def _ocast(G, c):
    petals(G, c, 8, 70, 196, 0.9, tear=False)


@g('uni2734', 0x2734)      # ✴ eight pointed black star
def _sp8(G, c):
    R, r = 205, 104
    pts = []
    for i in range(16):
        a = math.radians(90 + i * 22.5)
        rr = R if i % 2 == 0 else r
        pts.append((XC + rr * math.cos(a), SC + rr * math.sin(a)))
    G.rpoly(pts, [c.W * 0.25 if i % 2 == 0 else 4 for i in range(16)])


@g('uni2726', 0x2726)      # ✦ black four pointed star
def _star4(G, c):
    R, r = 220, 62
    pts = []
    for i in range(8):
        a = math.radians(90 + i * 45)
        rr = R if i % 2 == 0 else r
        pts.append((XC + rr * math.cos(a), SC + rr * math.sin(a)))
    G.rpoly(pts, [c.W * 0.2 if i % 2 == 0 else 30 for i in range(8)])


@g('uni2727', 0x2727)      # ✧ white four pointed star
def _star4w(G, c):
    R, r = 220, 62
    pts = []
    for i in range(8):
        a = math.radians(90 + i * 45)
        rr = R if i % 2 == 0 else r
        pts.append((XC + rr * math.cos(a), SC + rr * math.sin(a)))
    pts.append(pts[0])
    sk = Sk(*pts[0])
    for p in pts[1:]:
        sk.L(*p)
    G.stroke(sk, scale=0.7)


@g('uni2605', 0x2605)      # ★
def _star5(G, c):
    R, r = 235, 98
    pts = []
    for i in range(10):
        a = math.radians(90 + i * 36)
        rr = R if i % 2 == 0 else r
        pts.append((XC + rr * math.cos(a), SC + rr * math.sin(a)))
    G.rpoly(pts, [c.W * 0.22 if i % 2 == 0 else 6 for i in range(10)])


@g('uni2606', 0x2606)      # ☆
def _star5w(G, c):
    R, r = 228, 96
    pts = []
    for i in range(10):
        a = math.radians(90 + i * 36)
        rr = R if i % 2 == 0 else r
        pts.append((XC + rr * math.cos(a), SC + rr * math.sin(a)))
    sk = Sk(*pts[0])
    for p in pts[1:] + [pts[0]]:
        sk.L(*p)
    G.stroke(sk, scale=0.7)


@g('uni203B', 0x203B)      # ※ reference mark
def _refmark(G, c):
    k = 0.8
    G.line(XC - 170, SC - 170, XC + 170, SC + 170, scale=k)
    G.line(XC - 170, SC + 170, XC + 170, SC - 170, scale=k)
    for dx, dy in ((0, 160), (0, -160), (160, 0), (-160, 0)):
        G.dot(XC + dx, SC + dy, c.W * 1.05)


# ================================================================== bullets & shapes
def disc(G, cx, cy, r):
    G.ellipse(cx, cy, r, r)


def ring(G, c, cx, cy, r, k=0.8):
    G.stroke(_ring(cx, cy, r), scale=k)


@g('uni23FA', 0x23FA)      # ⏺ Claude Code's message bullet
def _rec(G, c):
    disc(G, XC, AX + 30, 150 + c.W * 0.15)


@g('uni25CF', 0x25CF)      # ●
def _bdisc(G, c):
    disc(G, XC, AX + 30, 185 + c.W * 0.1)


@g('uni25CB', 0x25CB)      # ○
def _wcirc(G, c):
    ring(G, c, XC, AX + 30, 185 + c.W * 0.1 - c.W * 0.35)


@g('uni25EF', 0x25EF)      # ◯ large circle
def _lcirc(G, c):
    ring(G, c, XC, AX + 30, 240 - c.W * 0.3)


@g('uni25C9', 0x25C9)      # ◉ fisheye
def _fisheye(G, c):
    ring(G, c, XC, AX + 30, 200 - c.W * 0.3)
    disc(G, XC, AX + 30, 70 + c.W * 0.15)


@g('uni25CE', 0x25CE)      # ◎ bullseye
def _bullseye(G, c):
    ring(G, c, XC, AX + 30, 205 - c.W * 0.3, k=0.7)
    ring(G, c, XC, AX + 30, 95, k=0.7)


@g('uni25E6', 0x25E6)      # ◦ white bullet
def _wbullet(G, c):
    ring(G, c, XC, 255, 72, k=0.62)


@g('bullet', 0x2022)       # •
def _bullet(G, c):
    disc(G, XC, 255, 72 + c.W * 0.32)


@g('uni2219', 0x2219)      # ∙ bullet operator
def _bulop(G, c):
    disc(G, XC, AX, c.W * 0.62)


@g('uni22C5', 0x22C5)      # ⋅ dot operator
def _dotop(G, c):
    disc(G, XC, AX, c.W * 0.62)


def square(G, c, s, filled, cy=AX + 30, r=None):
    r = c.W * 0.45 if r is None else r
    x0, x1, y0, y1 = XC - s, XC + s, cy - s, cy + s
    if filled:
        G.rpoly([(x0, y0), (x0, y1), (x1, y1), (x1, y0)], r)
    else:
        G.stroke(Sk(x0, y0).L(x0, y1).L(x1, y1).L(x1, y0).Z(), scale=0.78)


@g('uni25A0', 0x25A0)
def _bsq(G, c):
    square(G, c, 200, True)


@g('uni25A1', 0x25A1)
def _wsq(G, c):
    square(G, c, 200 - c.W * 0.35, False)


@g('uni25AA', 0x25AA)
def _bssq(G, c):
    square(G, c, 105, True, cy=AX)


@g('uni25AB', 0x25AB)
def _wssq(G, c):
    square(G, c, 105 - c.W * 0.3, False, cy=AX)


@g('uni25FC', 0x25FC)      # ◼
def _bmsq(G, c):
    square(G, c, 165, True)


@g('uni25FB', 0x25FB)      # ◻
def _wmsq(G, c):
    square(G, c, 165 - c.W * 0.32, False)


@g('uni25FE', 0x25FE)
def _bmssq(G, c):
    square(G, c, 132, True)


@g('uni25FD', 0x25FD)
def _wmssq(G, c):
    square(G, c, 132 - c.W * 0.3, False)


@g('uni2610', 0x2610)      # ☐ todo pending
def _ballot(G, c):
    square(G, c, 205 - c.W * 0.32, False)


@g('uni2611', 0x2611)      # ☑
def _ballotc(G, c):
    square(G, c, 205 - c.W * 0.32, False)
    G.stroke(Sk(XC - 120, AX + 30).L(XC - 30, AX - 70).L(XC + 130, AX + 150), scale=0.85)


@g('uni2612', 0x2612)      # ☒ todo done
def _ballotx(G, c):
    square(G, c, 205 - c.W * 0.32, False)
    G.line(XC - 105, AX - 75, XC + 105, AX + 135, scale=0.8)
    G.line(XC - 105, AX + 135, XC + 105, AX - 75, scale=0.8)


def tri(G, c, direction, s, filled, cy=AX + 30):
    if direction == 'R':
        pts = [(XC - s * 0.8, cy - s), (XC - s * 0.8, cy + s), (XC + s * 0.95, cy)]
    elif direction == 'L':
        pts = [(XC + s * 0.8, cy - s), (XC + s * 0.8, cy + s), (XC - s * 0.95, cy)]
    elif direction == 'U':
        pts = [(XC - s, cy - s * 0.8), (XC, cy + s * 0.95), (XC + s, cy - s * 0.8)]
    else:
        pts = [(XC - s, cy + s * 0.8), (XC, cy - s * 0.95), (XC + s, cy + s * 0.8)]
    if filled:
        G.rpoly(pts, c.W * 0.35)
    else:
        sk = Sk(*pts[0])
        for p in pts[1:]:
            sk.L(*p)
        sk.Z()
        G.stroke(sk, scale=0.75)


for cp, d, s, f in ((0x25B6, 'R', 215, True), (0x25B7, 'R', 205, False), (0x25B8, 'R', 120, True),
                    (0x25B9, 'R', 115, False), (0x25BA, 'R', 190, True), (0x25C0, 'L', 215, True),
                    (0x25C1, 'L', 205, False), (0x25C2, 'L', 120, True), (0x25C3, 'L', 115, False),
                    (0x25C4, 'L', 190, True), (0x25B2, 'U', 220, True), (0x25B3, 'U', 210, False),
                    (0x25B4, 'U', 125, True), (0x25B5, 'U', 120, False), (0x25BC, 'D', 220, True),
                    (0x25BD, 'D', 210, False), (0x25BE, 'D', 125, True), (0x25BF, 'D', 120, False)):
    reg('uni%04X' % cp, cp, (lambda d, s, f: (lambda G, c: tri(G, c, d, s, f)))(d, s, f))


# media controls used by Claude Code's mode line: ⏵⏵ accept edits, ⏸ plan mode
@g('uni23F5', 0x23F5)
def _play(G, c):
    tri(G, c, 'R', 150, True, cy=AX + 20)


@g('uni23F4', 0x23F4)
def _playl(G, c):
    tri(G, c, 'L', 150, True, cy=AX + 20)


@g('uni23F6', 0x23F6)
def _playu(G, c):
    tri(G, c, 'U', 150, True, cy=AX + 20)


@g('uni23F7', 0x23F7)
def _playd(G, c):
    tri(G, c, 'D', 150, True, cy=AX + 20)


@g('uni23F8', 0x23F8)      # ⏸
def _pause(G, c):
    for x in (XC - 85, XC + 85):
        G.rpoly([(x - 45, AX - 150), (x - 45, AX + 190), (x + 45, AX + 190), (x + 45, AX - 150)], c.W * 0.35)


@g('uni23F9', 0x23F9)      # ⏹
def _stop(G, c):
    square(G, c, 165, True, cy=AX + 20)


@g('uni25C6', 0x25C6)      # ◆
def _bdiam(G, c):
    G.rpoly([(XC, AX + 260), (XC + 210, AX + 30), (XC, AX - 200), (XC - 210, AX + 30)], c.W * 0.35)


@g('uni25C7', 0x25C7)      # ◇
def _wdiam(G, c):
    G.stroke(Sk(XC, AX + 245).L(XC + 196, AX + 30).L(XC, AX - 185).L(XC - 196, AX + 30).Z(), scale=0.75)


# ⎿ Claude Code's tool-result connector: a corner that hangs from the
# bullet above and points at the result text.
@g('uni23BF', 0x23BF)
def _dent(G, c):
    t = lw(c)
    pen = (t / 2, t / 2)
    G.stroke(Sk(XC - 120, TOP).L(XC - 120, AX + 40 + 60).V(XC - 60, AX + 40, 0.552).L(ADV + 2, AX + 40),
             pen=pen, caps=('flat', 'flat'))


@g('uni23BE', 0x23BE)      # ⎾
def _dent2(G, c):
    t = lw(c)
    pen = (t / 2, t / 2)
    G.stroke(Sk(XC - 120, BOT).L(XC - 120, AX + 40 - 60).V(XC - 60, AX + 40, 0.552).L(ADV + 2, AX + 40),
             pen=pen, caps=('flat', 'flat'))


# prompts and pointers
@g('uni276F', 0x276F)      # ❯
def _hrangle(G, c):
    G.stroke(Sk(160, AX + 230).L(400, AX + 20).L(160, AX - 190), scale=1.12)


@g('uni276E', 0x276E)      # ❮
def _hlangle(G, c):
    G.stroke(Sk(390, AX + 230).L(150, AX + 20).L(390, AX - 190), scale=1.12)


@g('uni2771', 0x2771)      # ❱
def _hrangle2(G, c):
    G.stroke(Sk(170, AX + 210).L(390, AX + 20).L(170, AX - 170), scale=0.95)


@g('uni2770', 0x2770)
def _hlangle2(G, c):
    G.stroke(Sk(380, AX + 210).L(160, AX + 20).L(380, AX - 170), scale=0.95)


@g('uni203A', 0x203A)      # ›
def _rsaquo(G, c):
    G.stroke(Sk(190, AX + 150).L(370, AX).L(190, AX - 150))


@g('uni2039', 0x2039)      # ‹
def _lsaquo(G, c):
    G.stroke(Sk(360, AX + 150).L(180, AX).L(360, AX - 150))


# checks and crosses
@g('uni2713', 0x2713)
def _check(G, c):
    G.stroke(Sk(70, AX + 20).L(205, AX - 150).T(480, AX + 380, 52, 68, 0.4, 0.4), prof=taper(end=(0.8, 120)))


@g('uni2714', 0x2714)
def _hcheck(G, c):
    G.stroke(Sk(80, AX + 20).L(205, AX - 140).T(470, AX + 360, 52, 68, 0.4, 0.4),
             prof=taper(end=(0.8, 120)), scale=1.45)


@g('uni2717', 0x2717)
def _ballotx2(G, c):
    G.stroke(Sk(95, AX + 330).T(450, AX - 170, 300, 310, 0.4, 0.4), prof=taper(end=(0.8, 100)))
    G.stroke(Sk(440, AX + 330).T(110, AX - 170, 238, 225, 0.4, 0.4), prof=taper(end=(0.8, 100)))


@g('uni2718', 0x2718)
def _hballotx(G, c):
    G.stroke(Sk(105, AX + 320).T(445, AX - 160, 300, 310, 0.4, 0.4), prof=taper(end=(0.8, 100)), scale=1.4)
    G.stroke(Sk(435, AX + 320).T(115, AX - 160, 238, 225, 0.4, 0.4), prof=taper(end=(0.8, 100)), scale=1.4)


@g('uni26A0', 0x26A0)      # ⚠
def _warn(G, c):
    k = 0.72
    G.stroke(Sk(XC, AX + 310).L(XC + 255, AX - 160).L(XC - 255, AX - 160).Z(), scale=k)
    G.stroke(Sk(XC, AX + 160).L(XC, AX - 20), scale=k)
    G.dot(XC, AX - 90, c.W * 0.95)


@g('uni26A1', 0x26A1)      # ⚡
def _bolt(G, c):
    G.rpoly([(330, AX + 330), (130, AX - 10), (275, AX - 10), (210, AX - 300), (430, AX + 90),
             (290, AX + 90), (370, AX + 330)], c.W * 0.2)


@g('uni29C9', 0x29C9)      # ⧉ two joined squares
def _joined(G, c):
    k = 0.66
    G.stroke(Sk(100, AX - 160).L(100, AX + 120).L(370, AX + 120).L(370, AX - 160).Z(), scale=k)
    G.stroke(Sk(180, AX + 120).L(180, AX + 220).L(450, AX + 220).L(450, AX - 60).L(370, AX - 60), scale=k)


@g('uni2026', 0x2026)      # … ellipsis
def _ellipsis(G, c):
    d = c.W * 1.12
    for x in (XC - 175, XC, XC + 175):
        G.dot(x, d * 0.42, d)


@g('uni22EF', 0x22EF)      # ⋯
def _ctdots(G, c):
    d = c.W * 1.1
    for x in (XC - 175, XC, XC + 175):
        G.dot(x, AX, d)


@g('uni22EE', 0x22EE)      # ⋮
def _vdots(G, c):
    d = c.W * 1.1
    for y in (AX - 230, AX, AX + 230):
        G.dot(XC, y, d)


@g('uni2234', 0x2234)      # ∴ (Claude Code's thinking marker)
def _therefore(G, c):
    d = c.W * 1.2
    G.dot(XC, 420, d)
    G.dot(XC - 150, 90, d)
    G.dot(XC + 150, 90, d)


@g('uni2235', 0x2235)      # ∵
def _because(G, c):
    d = c.W * 1.2
    G.dot(XC, 90, d)
    G.dot(XC - 150, 420, d)
    G.dot(XC + 150, 420, d)


# keyboard symbols
@g('uni2318', 0x2318)      # ⌘
def _cmd(G, c):
    k = 0.72
    a, b = 175, 375
    y0, y1 = AX - 100, AX + 100
    G.stroke(Sk(a, y0).L(a, y1), scale=k)
    G.stroke(Sk(b, y0).L(b, y1), scale=k)
    G.stroke(Sk(a, y0).L(b, y0), scale=k)
    G.stroke(Sk(a, y1).L(b, y1), scale=k)
    for cx, cy in ((a - 55, y1 + 55), (b + 55, y1 + 55), (a - 55, y0 - 55), (b + 55, y0 - 55)):
        G.stroke(_ring(cx, cy, 55), scale=k)


@g('uni2325', 0x2325)      # ⌥
def _opt(G, c):
    k = 0.8
    G.stroke(Sk(70, AX + 170).L(200, AX + 170).L(340, AX - 150).L(480, AX - 150), scale=k)
    G.line(320, AX + 170, 480, AX + 170, scale=k)


@g('uni2303', 0x2303)      # ⌃
def _ctrl(G, c):
    G.stroke(Sk(120, AX + 40).L(XC, AX + 230).L(430, AX + 40))


@g('uni21E7', 0x21E7)      # ⇧
def _shift(G, c):
    G.stroke(Sk(XC, AX + 260).L(480, AX + 30).L(370, AX + 30).L(370, AX - 190).L(180, AX - 190)
             .L(180, AX + 30).L(70, AX + 30).Z(), scale=0.72)


@g('uni238B', 0x238B)      # ⎋
def _esc(G, c):
    k = 0.75
    G.stroke(Sk(410, AX + 220).T(110, AX + 120, 150, 225, 0.4, 0.4).T(XC, AX - 210, 270, 0, 0.5, 0.5)
             .T(470, AX + 40, 0, 90, 0.5, 0.4), scale=k)
    G.line(100, AX + 250, 250, AX + 100, scale=k)
    G.stroke(Sk(100, AX + 130).L(100, AX + 250).L(220, AX + 250), scale=k)


@g('uni232B', 0x232B)      # ⌫
def _bksp(G, c):
    k = 0.72
    G.stroke(Sk(160, AX - 150).L(500, AX - 150).L(500, AX + 210).L(160, AX + 210).L(40, AX + 30).Z(), scale=k)
    G.line(250, AX - 50, 390, AX + 110, scale=k)
    G.line(250, AX + 110, 390, AX - 50, scale=k)


@g('uni23CE', 0x23CE)      # ⏎
def _ret(G, c):
    k = 0.85
    G.stroke(Sk(440, AX + 260).L(440, AX - 60).L(110, AX - 60), scale=k)
    G.stroke(Sk(230, AX + 70).L(100, AX - 60).L(230, AX - 190), scale=k)


@g('uni21B5', 0x21B5)      # ↵
def _crarrow(G, c):
    k = 0.85
    G.stroke(Sk(440, AX + 240).L(440, AX - 60).L(110, AX - 60), scale=k)
    G.stroke(Sk(220, AX + 60).L(100, AX - 60).L(220, AX - 180), scale=k)


# ================================================================== arrows
def arrow(G, c, x0, y0, x1, y1, head=150, k=1.0, double=False):
    G.line(x0, y0, x1, y1, scale=k)
    ang = math.atan2(y1 - y0, x1 - x0)
    for sgn in (1, -1):
        a = ang + math.pi + sgn * math.radians(42)
        G.line(x1, y1, x1 + head * math.cos(a), y1 + head * math.sin(a), scale=k)
    if double:
        ang2 = ang + math.pi
        for sgn in (1, -1):
            a = ang2 + math.pi + sgn * math.radians(42)
            G.line(x0, y0, x0 + head * math.cos(a), y0 + head * math.sin(a), scale=k)


ARROWS = {
    0x2190: (480, AX, 70, AX, False), 0x2192: (70, AX, 480, AX, False),
    0x2191: (XC, AX - 280, XC, AX + 330, False), 0x2193: (XC, AX + 330, XC, AX - 280, False),
    0x2194: (70, AX, 480, AX, True), 0x2195: (XC, AX - 280, XC, AX + 330, True),
    0x2196: (450, AX - 180, 110, AX + 160, False), 0x2197: (100, AX - 180, 440, AX + 160, False),
    0x2198: (100, AX + 180, 440, AX - 160, False), 0x2199: (450, AX + 180, 110, AX - 160, False),
}
for cp, (x0, y0, x1, y1, dbl) in ARROWS.items():
    reg('uni%04X' % cp, cp, (lambda a: (lambda G, c: arrow(G, c, *a)))((x0, y0, x1, y1, 160, 1.0, dbl)))


def darrow(G, c, direction):
    k = 0.8
    if direction == 'R':
        G.line(70, AX + 90, 400, AX + 90, scale=k)
        G.line(70, AX - 90, 400, AX - 90, scale=k)
        G.stroke(Sk(300, AX + 230).L(480, AX).L(300, AX - 230), scale=k)
    elif direction == 'L':
        G.line(150, AX + 90, 480, AX + 90, scale=k)
        G.line(150, AX - 90, 480, AX - 90, scale=k)
        G.stroke(Sk(250, AX + 230).L(70, AX).L(250, AX - 230), scale=k)
    else:
        G.line(150, AX + 90, 400, AX + 90, scale=k)
        G.line(150, AX - 90, 400, AX - 90, scale=k)
        G.stroke(Sk(320, AX + 220).L(490, AX).L(320, AX - 220), scale=k)
        G.stroke(Sk(230, AX + 220).L(60, AX).L(230, AX - 220), scale=k)


reg('uni21D2', 0x21D2, lambda G, c: darrow(G, c, 'R'))
reg('uni21D0', 0x21D0, lambda G, c: darrow(G, c, 'L'))
reg('uni21D4', 0x21D4, lambda G, c: darrow(G, c, 'B'))


@g('uni21BB', 0x21BB)      # ↻
def _cw(G, c):
    k = 0.85
    G.stroke(Sk(XC + 30, AX + 240).T(XC + 220, AX + 20, 0, 270, 0.5, 0.45).T(XC, AX - 210, 270, 180, 0.45, 0.5)
             .T(XC - 220, AX + 20, 180, 90, 0.5, 0.45).T(XC - 60, AX + 230, 90, 20, 0.4, 0.4), scale=k)
    G.stroke(Sk(XC - 20, AX + 370).L(XC + 60, AX + 240).L(XC - 50, AX + 130), scale=k)


@g('uni21BA', 0x21BA)      # ↺
def _ccw(G, c):
    k = 0.85
    G.stroke(Sk(XC - 30, AX + 240).T(XC - 220, AX + 20, 180, 270, 0.5, 0.45).T(XC, AX - 210, 270, 0, 0.45, 0.5)
             .T(XC + 220, AX + 20, 0, 90, 0.5, 0.45).T(XC + 60, AX + 230, 90, 160, 0.4, 0.4), scale=k)
    G.stroke(Sk(XC + 20, AX + 370).L(XC - 60, AX + 240).L(XC + 50, AX + 130), scale=k)


# ================================================================== Clawd
# Clawd in square pixels (from the Claude Code banner block art):
# body 12x8, eyes 1x2 at body cols 2 and 9, arms at body rows 4-5 out to
# +-2 cols, four legs (cols 1, 3, 8, 10) 2 px tall.
def clawd_pixels(pose='stand'):
    px = set()
    for x in range(12):
        for y in range(8):
            px.add((x, y))
    for y in (2, 3):
        px.discard((2, y))
        px.discard((9, y))
    arm_rows = (4, 5)
    for y in arm_rows:
        px.add((-1, y))
        px.add((12, y))
    if pose == 'stand':
        for y in arm_rows:
            px.add((-2, y))
            px.add((13, y))
    elif pose == 'wave':
        for y in arm_rows:
            px.add((-2, y))
        px.discard((12, 4))
        px.discard((12, 5))
        for (x, y) in ((12, 3), (13, 2), (13, 1), (14, 1)):
            px.add((x, y))
    for x in (1, 3, 8, 10):
        px.add((x, 8))
        px.add((x, 9))
    return px


def draw_clawd(G, c, pose='stand', cell=ADV):
    pix = clawd_pixels(pose)
    xs = [p[0] for p in pix]
    ys = [p[1] for p in pix]
    cols = max(xs) - min(xs) + 1
    s = min((cell - 40) / cols, 50)
    ox = (cell - cols * s) / 2 - min(xs) * s
    top = AX + 5 * s
    # merge horizontal runs to keep contour count low
    for y in sorted(set(ys)):
        row = sorted(x for x, yy in pix if yy == y)
        runs = []
        for x in row:
            if runs and x == runs[-1][1] + 1:
                runs[-1][1] = x
            else:
                runs.append([x, x])
        for a, b in runs:
            G.rect(ox + a * s, top - (y + 1) * s, ox + (b + 1) * s, top - y * s)


@g('clawd', 0xE000)
def _clawd(G, c):
    draw_clawd(G, c)


@g('clawd.wave', 0xE001)
def _clawd_wave(G, c):
    draw_clawd(G, c, 'wave')
