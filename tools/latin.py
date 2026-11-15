"""Latin skeletons for Clawd Mono.

Coordinates are pen centre lines in font units (UPM 1000, advance 550).
Skeletons are pulled inward by half the pen size so that outer edges stay
put across weights; every glyph function receives (G, c) where c carries the
master's pen: c.W (stem width) and c.H (horizontal stroke thickness)."""
import math
from glyphlib import Sk, taper

REG = {}

XH, CH, AS, DE, OV = 510, 690, 742, -212, 11
ADV = 550
MID = 275
AXIS = 300          # math axis (operators)

# pen-lift: terminals thin slightly where the pen leaves the paper
LIFT = (0.80, 120)
JOIN = (0.52, 150)  # branching strokes thin where they leave a stem


def g(name, *uni, w=ADV):
    def deco(fn):
        REG[name] = (list(uni), w, fn)
        return fn
    return deco


class P:
    """Derived positions for a master (centre-line coordinates)."""

    def __init__(self, c):
        self.hw, self.hh = c.W / 2, c.H / 2
        hw, hh = self.hw, self.hh
        self.W, self.H = c.W, c.H
        # lowercase straight stems
        self.l = 76 + hw
        self.r = 474 - hw
        # lowercase rounds
        self.ol = 62 + hw
        self.or_ = 488 - hw
        self.xt = XH + OV - hh          # round top centre line
        self.xb = -OV + hh              # round bottom centre line
        self.st = XH - hh + 3           # stem top end (round cap reaches ~x-height)
        self.sb = hh - 3                # stem bottom end
        self.at = AS - hh + 3           # ascender top end
        self.dt = DE + hh               # descender end
        self.dtr = DE - OV + hh         # round descender bottom
        # caps
        self.cl = 72 + hw
        self.cr = 478 - hw
        self.ct = CH - hh + 3
        self.cot = CH + OV - hh
        self.col = 54 + hw
        self.cor = 496 - hw


def loop(cx, top, bot, left, right, t=0.58, tv=None):
    """Closed superelliptic loop through the four extremes (clockwise)."""
    tv = t if tv is None else tv
    ym = (top + bot) / 2
    return Sk(cx, top).H(right, ym, t, tv).V(cx, bot, tv, t).H(left, ym, t, tv).V(cx, top, tv, t).Z()


def lift(start=None, k=None):
    return taper(start=start, end=k or LIFT)


def bowl_R(p, xs, top, bot, right, yj_top=None, yj_bot=None, apex=0.5, t=0.58):
    """Bowl hanging off a stem on its left (b, p, D-like)."""
    yj_top = XH - 160 if yj_top is None else yj_top
    yj_bot = 105 if yj_bot is None else yj_bot
    ym = (top + bot) / 2
    xa = xs + apex * (right - xs)
    return (Sk(xs, yj_top).T(xa, top, 64, 0, 0.42, 0.5).H(right, ym, t).V(xa, bot, t)
            .T(xs, yj_bot, 180, 118, 0.5, 0.4))


def bowl_L(p, xs, top, bot, left, yj_top=None, yj_bot=None, apex=0.5, t=0.58):
    """Bowl hanging off a stem on its right (d, q, a)."""
    yj_top = XH - 160 if yj_top is None else yj_top
    yj_bot = 105 if yj_bot is None else yj_bot
    ym = (top + bot) / 2
    xa = xs - apex * (xs - left)
    return (Sk(xs, yj_top).T(xa, top, 116, 180, 0.42, 0.5).H(left, ym, t).V(xa, bot, t)
            .T(xs, yj_bot, 0, 62, 0.5, 0.4))


def n_arch(p, l, r, yj=None, apex=0.54, t=0.58, bottom=None, top=None):
    top = p.xt if top is None else top
    yj = XH - 165 if yj is None else yj
    xa = l + apex * (r - l)
    ys = top - (r - xa) * 1.05
    return Sk(l, yj).T(xa, top, 64, 0, 0.42, 0.5).H(r, ys, t).L(r, p.sb if bottom is None else bottom)


def u_cup(p, l, r, yj=None, apex=0.46, t=0.58, top=None):
    """Mirror of n_arch: left stem down, round bottom, rising into right stem."""
    top = p.st if top is None else top
    yj = 165 if yj is None else yj
    xa = l + apex * (r - l)
    ys = p.xb + (xa - l) * 1.05
    return Sk(l, top).L(l, ys).V(xa, p.xb, t).T(r, yj, 0, 64, 0.5, 0.42)


# ================================================================== lowercase
@g('o', 0x6F)
def _o(G, c):
    p = P(c)
    G.stroke(loop(MID, p.xt, p.xb, p.ol, p.or_, 0.6))


@g('n', 0x6E)
def _n(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.st)
    G.stroke(n_arch(p, p.l, p.r), prof=taper(start=JOIN))


@g('h', 0x68)
def _h(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.at)
    G.stroke(n_arch(p, p.l, p.r), prof=taper(start=JOIN))


@g('m', 0x6D)
def _m(G, c):
    p = P(c)
    k = 0.86
    hw = p.hw * k
    l, r = 44 + hw, 506 - hw
    mm = (l + r) / 2
    G.line(l, p.sb, l, p.st, scale=k)
    G.stroke(n_arch(p, l, mm, yj=XH - 125, apex=0.52, t=0.6), prof=taper(start=(0.5, 105), scale=k))
    G.stroke(n_arch(p, mm, r, yj=XH - 125, apex=0.52, t=0.6), prof=taper(start=(0.5, 105), scale=k))


@g('u', 0x75)
def _u(G, c):
    p = P(c)
    G.line(p.r, p.sb, p.r, p.st)
    G.stroke(u_cup(p, p.l, p.r), prof=taper(end=JOIN))


@g('r', 0x72)
def _r(G, c):
    p = P(c)
    xs = 132 + p.hw
    G.line(xs, p.sb, xs, p.st)
    sk = Sk(xs, XH - 175).T(xs + 175, p.xt, 66, 0, 0.42, 0.45).T(p.or_ + 4, XH - 92, 0, -42, 0.38, 0.3)
    G.stroke(sk, prof=taper(start=JOIN, end=LIFT))


@g('e', 0x65)
def _e(G, c):
    p = P(c)
    ybar = 262
    xr, xl = p.or_, p.ol
    G.line(xl, ybar, xr, ybar)
    sk = (Sk(xr, ybar).V(MID + 4, p.xt, 0.62, 0.58).H(xl, 245, 0.6, 0.6)
          .V(MID + 10, p.xb, 0.62, 0.6).T(xr - 4, 106, 0, 46, 0.45, 0.32))
    G.stroke(sk, prof=lift())


@g('c', 0x63)
def _c(G, c):
    p = P(c)
    sk = (Sk(p.or_ - 4, 402).T(MID + 8, p.xt, 128, 180, 0.32, 0.45).H(p.ol, 250, 0.6, 0.6)
          .V(MID + 10, p.xb, 0.6, 0.6).T(p.or_ - 2, 106, 0, 48, 0.45, 0.32))
    G.stroke(sk, prof=taper(start=LIFT, end=LIFT))


@g('a', 0x61)
def _a(G, c):
    p = P(c)
    r = p.r
    sk = Sk(p.ol + 22, 424).T(MID - 4, p.xt, 52, 0, 0.36, 0.42).H(r, p.xt - 150, 0.55).L(r, p.sb)
    G.stroke(sk, prof=taper(start=LIFT))
    yb = 292
    sk2 = (Sk(r, yb).L(MID - 10, yb).H(p.ol + 2, 148, 0.56, 0.6).V(MID - 2, p.xb, 0.6, 0.58)
           .T(r, 104, 0, 64, 0.48, 0.32))
    G.stroke(sk2, prof=taper(start=(0.62, 90), end=(0.5, 110)))


@g('s', 0x73)
def _s(G, c):
    p = P(c)
    xl, xr = p.ol + 16, p.or_ - 16
    sk = (Sk(xr - 2, 420).T(MID + 6, p.xt, 124, 180, 0.32, 0.42)
          .H(xl, 383, 0.56, 0.62)
          .T(MID, 262, 270, 340, 0.4, 0.42)
          .T(xr + 4, 128, 340, 270, 0.42, 0.4)
          .V(MID - 6, p.xb, 0.62, 0.56)
          .T(xl - 6, 98, 180, 126, 0.42, 0.32))
    G.stroke(sk, prof=taper(start=LIFT, end=LIFT))


@g('b', 0x62)
def _b(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.at)
    G.stroke(bowl_R(p, p.l, p.xt, p.xb, p.or_), prof=taper(start=JOIN, end=JOIN))


@g('p', 0x70)
def _p(G, c):
    p = P(c)
    G.line(p.l, p.dt, p.l, p.st)
    G.stroke(bowl_R(p, p.l, p.xt, p.xb, p.or_), prof=taper(start=JOIN, end=JOIN))


@g('d', 0x64)
def _d(G, c):
    p = P(c)
    G.line(p.r, p.sb, p.r, p.at)
    G.stroke(bowl_L(p, p.r, p.xt, p.xb, p.ol), prof=taper(start=JOIN, end=JOIN))


@g('q', 0x71)
def _q(G, c):
    p = P(c)
    G.line(p.r, p.dt, p.r, p.st)
    G.stroke(bowl_L(p, p.r, p.xt, p.xb, p.ol), prof=taper(start=JOIN, end=JOIN))


@g('g', 0x67)
def _g(G, c):
    p = P(c)
    r = p.r
    G.stroke(Sk(r, p.st).L(r, -40).V(MID - 10, p.dtr, 0.58, 0.58).T(p.ol + 4, DE + 88, 180, 128, 0.4, 0.3),
             prof=lift())
    G.stroke(bowl_L(p, r, p.xt, p.xb + 8, p.ol, yj_bot=112), prof=taper(start=JOIN, end=JOIN))


@g('f', 0x66)
def _f(G, c):
    p = P(c)
    xs = 232
    G.stroke(Sk(xs, p.sb).L(xs, AS - 175).V(xs + 120, AS + OV - p.hh, 0.58, 0.55)
             .T(p.or_ + 6, AS - 70, 0, -38, 0.36, 0.3), prof=lift())
    G.line(92 + p.hw * 0.4, XH - p.hh, 452 - p.hw * 0.4, XH - p.hh)


@g('t', 0x74)
def _t(G, c):
    p = P(c)
    xs = 220
    G.stroke(Sk(xs, 668 - p.hh).L(xs, 150).V(xs + 112, p.xb, 0.58, 0.56).T(p.or_ - 4, 64, 0, 36, 0.4, 0.3),
             prof=lift())
    G.line(84 + p.hw * 0.4, XH - p.hh, 448 - p.hw * 0.4, XH - p.hh)


@g('i', 0x69)
def _i(G, c):
    p = P(c)
    xs = MID + 22
    G.stroke(Sk(xs - 150, p.st - 2).L(xs, p.st - 2).L(xs, p.sb))
    G.line(xs - 178, p.sb, xs + 160, p.sb)
    G.dot(xs - 4, XH + 200)


@g('j', 0x6A)
def _j(G, c):
    p = P(c)
    xs = MID + 70
    G.stroke(Sk(xs - 175, p.st - 2).L(xs, p.st - 2).L(xs, -45).V(xs - 125, p.dtr, 0.6, 0.56)
             .T(68 + p.hw, DE + 62, 180, 140, 0.4, 0.3), prof=lift())
    G.dot(xs - 4, XH + 200)


@g('l', 0x6C)
def _l(G, c):
    p = P(c)
    xs = MID - 8
    G.stroke(Sk(xs - 152, p.at - 2).L(xs, p.at - 2).L(xs, 152).V(xs + 128, p.xb + 2, 0.6, 0.55)
             .L(xs + 208, p.xb + 4), prof=lift())


@g('k', 0x6B)
def _k(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.at)
    xj = p.l + 8
    yj = 200
    G.stroke(Sk(p.or_ - 18, p.st).L(xj, yj), prof=taper(end=(0.7, 120)))
    xm = p.l + 0.40 * (p.or_ - 18 - p.l)
    ym = yj + 0.40 * (p.st - yj)
    G.stroke(Sk(xm - 6, ym - 10).L(p.or_ - 4, p.sb), prof=taper(start=(0.7, 100)))


@g('v', 0x76)
def _v(G, c):
    p = P(c)
    G.stroke(Sk(p.ol - 4, p.st).L(MID, p.sb + 2).L(p.or_ + 4, p.st))


@g('w', 0x77)
def _w(G, c):
    p = P(c)
    k = 0.88
    hw = p.hw * k
    l, r = 34 + hw, 516 - hw
    G.stroke(Sk(l, p.st).L(150, p.sb + 2).L(MID, 390).L(400, p.sb + 2).L(r, p.st), scale=k)


@g('x', 0x78)
def _x(G, c):
    p = P(c)
    G.line(p.ol, p.st, p.or_, p.sb)
    G.line(p.or_, p.st, p.ol, p.sb)


@g('y', 0x79)
def _y(G, c):
    p = P(c)
    G.line(p.ol - 4, p.st, MID + 6, 30)
    G.stroke(Sk(p.or_ + 4, p.st).L(MID - 36, -120).Tc(84 + p.hw, p.dt + 4, 180, 0.4, 0.4), prof=lift())


@g('z', 0x7A)
def _z(G, c):
    p = P(c)
    l, r = p.ol + 10, p.or_ - 6
    G.stroke(Sk(l, XH - p.hh).L(r, XH - p.hh).L(l + 4, p.hh).L(r + 4, p.hh))


# ================================================================== uppercase
@g('H', 0x48)
def _H(G, c):
    p = P(c)
    G.line(p.cl, p.sb, p.cl, p.ct)
    G.line(p.cr, p.sb, p.cr, p.ct)
    G.line(p.cl, 352, p.cr, 352)


@g('O', 0x4F)
def _O(G, c):
    p = P(c)
    G.stroke(loop(MID, p.cot, -OV + p.hh, p.col, p.cor, 0.6))


@g('A', 0x41)
def _A(G, c):
    p = P(c)
    G.stroke(Sk(p.col - 6, p.sb).L(MID, CH - p.hh + 6).L(p.cor + 6, p.sb))
    y = 228
    f = (y - p.sb) / (CH - p.hh - p.sb)
    xl = p.col - 6 + f * (MID - p.col + 6)
    xr = p.cor + 6 - f * (p.cor + 6 - MID)
    G.line(xl, y, xr, y)


@g('B', 0x42)
def _B(G, c):
    p = P(c)
    ym = 372
    yt, yb = CH - p.hh, p.hh
    G.line(p.cl, yb, p.cl, yt)
    G.stroke(Sk(p.cl, yt).L(272, yt).H(p.cr - 18, (yt + ym) / 2, 0.58).V(272, ym, 0.58).L(p.cl, ym))
    G.stroke(Sk(p.cl, ym).L(282, ym).H(p.cor - 4, (ym + yb) / 2, 0.58).V(282, yb, 0.58).L(p.cl, yb))


@g('C', 0x43)
def _C(G, c):
    p = P(c)
    sk = (Sk(p.cor - 6, CH - 128).T(MID + 14, p.cot, 126, 180, 0.32, 0.45).H(p.col, CH / 2, 0.6, 0.6)
          .V(MID + 14, -OV + p.hh, 0.6, 0.6).T(p.cor - 4, 128, 0, 52, 0.45, 0.32))
    G.stroke(sk, prof=taper(start=LIFT, end=LIFT))


@g('D', 0x44)
def _D(G, c):
    p = P(c)
    yt, yb = CH - p.hh, p.hh
    G.line(p.cl, yb, p.cl, yt)
    G.stroke(Sk(p.cl, yt).L(250, yt).H(p.cor, CH / 2, 0.6).V(250, yb, 0.6).L(p.cl, yb))


@g('E', 0x45)
def _E(G, c):
    p = P(c)
    yt, yb = CH - p.hh, p.hh
    G.stroke(Sk(p.cr + 6, yt).L(p.cl, yt).L(p.cl, yb).L(p.cr + 10, yb))
    G.line(p.cl, 362, p.cr - 26, 362)


@g('F', 0x46)
def _F(G, c):
    p = P(c)
    yt = CH - p.hh
    G.stroke(Sk(p.cr + 6, yt).L(p.cl, yt).L(p.cl, p.sb))
    G.line(p.cl, 352, p.cr - 26, 352)


@g('G', 0x47)
def _G(G, c):
    p = P(c)
    sk = (Sk(p.cor - 6, CH - 128).T(MID + 14, p.cot, 126, 180, 0.32, 0.45).H(p.col, CH / 2, 0.6, 0.6)
          .V(MID + 18, -OV + p.hh, 0.6, 0.58).H(p.cor, 150, 0.56, 0.6).L(p.cor, 312).L(MID + 30, 312))
    G.stroke(sk, prof=taper(start=LIFT))


@g('I', 0x49)
def _I(G, c):
    p = P(c)
    yt, yb = CH - p.hh, p.hh
    G.line(MID, yb, MID, yt)
    G.line(122 + p.hw * 0.3, yt, 428 - p.hw * 0.3, yt)
    G.line(122 + p.hw * 0.3, yb, 428 - p.hw * 0.3, yb)


@g('J', 0x4A)
def _J(G, c):
    p = P(c)
    xs = p.cr - 18
    yt = CH - p.hh
    G.stroke(Sk(xs - 200, yt).L(xs, yt).L(xs, 205).V(MID - 22, -OV + p.hh, 0.58, 0.58)
             .T(p.cl - 20, 128, 180, 130, 0.42, 0.3), prof=lift())


@g('K', 0x4B)
def _K(G, c):
    p = P(c)
    G.line(p.cl, p.sb, p.cl, p.ct)
    yj = 262
    G.stroke(Sk(p.cr + 2, p.ct).L(p.cl + 8, yj), prof=taper(end=(0.7, 130)))
    xm = p.cl + 0.36 * (p.cr - p.cl)
    ym = yj + 0.36 * (p.ct - yj)
    G.stroke(Sk(xm - 6, ym - 12).L(p.cr + 10, p.sb), prof=taper(start=(0.7, 110)))


@g('L', 0x4C)
def _L(G, c):
    p = P(c)
    G.stroke(Sk(p.cl, p.ct).L(p.cl, p.hh).L(p.cr + 12, p.hh))


@g('M', 0x4D)
def _M(G, c):
    p = P(c)
    k = 0.9
    hw = p.hw * k
    l, r = 48 + hw, 502 - hw
    G.stroke(Sk(l, p.sb).L(l, p.ct).L(MID, 238).L(r, p.ct).L(r, p.sb), scale=k)


@g('N', 0x4E)
def _N(G, c):
    p = P(c)
    G.stroke(Sk(p.cl, p.sb).L(p.cl, p.ct).L(p.cr, p.sb).L(p.cr, p.ct), scale=0.94)


@g('P', 0x50)
def _P(G, c):
    p = P(c)
    yt = CH - p.hh
    ym = 300
    G.line(p.cl, p.sb, p.cl, yt)
    G.stroke(Sk(p.cl, yt).L(272, yt).H(p.cor - 4, (yt + ym) / 2, 0.58).V(272, ym, 0.58).L(p.cl, ym))


@g('Q', 0x51)
def _Q(G, c):
    p = P(c)
    G.stroke(loop(MID, p.cot, -OV + p.hh, p.col, p.cor, 0.6))
    G.stroke(Sk(MID + 40, 118).T(p.cor + 14, -150, 300, 300, 0.4, 0.4), prof=taper(end=(0.75, 100)))


@g('R', 0x52)
def _R(G, c):
    p = P(c)
    yt = CH - p.hh
    ym = 318
    G.line(p.cl, p.sb, p.cl, yt)
    G.stroke(Sk(p.cl, yt).L(266, yt).H(p.cor - 8, (yt + ym) / 2, 0.58).V(266, ym, 0.58).L(p.cl, ym))
    G.line(250, ym, p.cr + 10, p.sb)


@g('S', 0x53)
def _S(G, c):
    p = P(c)
    xl, xr = p.col + 12, p.cor - 12
    sk = (Sk(xr - 4, CH - 118).T(MID + 6, p.cot, 124, 180, 0.32, 0.42)
          .H(xl, 528, 0.56, 0.62)
          .T(MID, 360, 270, 338, 0.4, 0.42)
          .T(xr + 6, 168, 338, 270, 0.42, 0.4)
          .V(MID - 6, -OV + p.hh, 0.62, 0.56)
          .T(xl - 8, 118, 180, 128, 0.42, 0.32))
    G.stroke(sk, prof=taper(start=LIFT, end=LIFT))


@g('T', 0x54)
def _T(G, c):
    p = P(c)
    yt = CH - p.hh
    G.line(52 + p.hw, yt, 498 - p.hw, yt)
    G.line(MID, p.sb, MID, yt)


@g('U', 0x55)
def _U(G, c):
    p = P(c)
    G.stroke(Sk(p.cl, p.ct).L(p.cl, 232).V(MID, -OV + p.hh, 0.58).H(p.cr, 232, 0.58).L(p.cr, p.ct))


@g('V', 0x56)
def _V(G, c):
    p = P(c)
    G.stroke(Sk(p.col - 8, p.ct).L(MID, p.sb + 4).L(p.cor + 8, p.ct))


@g('W', 0x57)
def _W(G, c):
    p = P(c)
    k = 0.88
    hw = p.hw * k
    G.stroke(Sk(30 + hw, p.ct).L(148, p.sb + 2).L(MID, 470).L(402, p.sb + 2).L(520 - hw, p.ct), scale=k)


@g('X', 0x58)
def _X(G, c):
    p = P(c)
    G.line(p.col, p.ct, p.cor, p.sb)
    G.line(p.cor, p.ct, p.col, p.sb)


@g('Y', 0x59)
def _Y(G, c):
    p = P(c)
    G.stroke(Sk(p.col - 4, p.ct).L(MID, 320).L(p.cor + 4, p.ct))
    G.line(MID, p.sb, MID, 320)


@g('Z', 0x5A)
def _Z(G, c):
    p = P(c)
    l, r = p.col + 8, p.cor - 8
    G.stroke(Sk(l, CH - p.hh).L(r, CH - p.hh).L(l, p.hh).L(r + 6, p.hh))


# ================================================================== figures
@g('zero', 0x30)
def _zero(G, c):
    p = P(c)
    G.stroke(loop(MID, p.cot, -OV + p.hh, 64 + p.hw, 486 - p.hw, 0.6))
    cw = (486 - 64) - 2 * c.W          # counter width
    dw = min(c.W * 1.05, cw * 0.36)
    G.dot(MID, 346, dw, min(dw * 1.75, 150))


@g('one', 0x31)
def _one(G, c):
    p = P(c)
    xs = MID + 22
    G.stroke(Sk(112 + p.hw, CH - 178).T(xs, p.ct, 36, 72, 0.45, 0.3).L(xs, p.hh))
    G.line(108, p.hh, 452, p.hh)


@g('two', 0x32)
def _two(G, c):
    p = P(c)
    sk = (Sk(p.col + 14, 560).T(MID + 2, p.cot, 70, 0, 0.36, 0.46).H(p.cor - 8, 488, 0.58, 0.56)
          .T(p.col + 6, p.hh, 270, 222, 0.32, 0.36).L(p.cor + 4, p.hh))
    G.stroke(sk, prof=taper(start=LIFT))


@g('three', 0x33)
def _three(G, c):
    p = P(c)
    ym = 388
    G.stroke(Sk(p.col + 10, 575).T(MID, p.cot, 66, 0, 0.36, 0.46).H(p.cor - 22, 538, 0.58, 0.56)
             .V(MID - 22, ym, 0.56, 0.56), prof=taper(start=LIFT))
    G.stroke(Sk(MID - 22, ym).H(p.cor, 200, 0.6, 0.58).V(MID - 4, -OV + p.hh, 0.58, 0.56)
             .T(p.col - 4, 122, 180, 130, 0.42, 0.3), prof=lift())


@g('four', 0x34)
def _four(G, c):
    p = P(c)
    xs = p.cr - 24
    G.stroke(Sk(xs, p.ct).L(p.col - 6, 222).L(p.cor + 14, 222))
    G.line(xs, p.sb, xs, p.ct)


@g('five', 0x35)
def _five(G, c):
    p = P(c)
    yt = CH - p.hh
    G.stroke(Sk(p.cor - 10, yt).L(p.cl + 18, yt).L(p.cl + 4, 384))
    G.stroke(Sk(p.cl + 4, 384).T(MID + 4, 456 - p.hh, 30, 0, 0.4, 0.45).H(p.cor, 228, 0.58, 0.58)
             .V(MID - 4, -OV + p.hh, 0.58, 0.56).T(p.col - 6, 118, 180, 130, 0.42, 0.3),
             prof=taper(start=(0.7, 80), end=LIFT))


@g('six', 0x36)
def _six(G, c):
    p = P(c)
    top = 452 - p.hh
    bot = -OV + p.hh
    G.stroke(loop(MID + 4, top, bot, p.col + 6, p.cor, 0.6))
    G.stroke(Sk(p.cor - 30, CH - 52).T(MID + 40, p.cot, 150, 175, 0.3, 0.4)
             .T(p.col + 6, (top + bot) / 2, 190, 270, 0.42, 0.55), prof=taper(start=LIFT))


@g('seven', 0x37)
def _seven(G, c):
    p = P(c)
    yt = CH - p.hh
    G.stroke(Sk(p.col + 6, yt).L(p.cor - 2, yt).T(MID - 30, p.sb, 242, 260, 0.45, 0.3))


@g('eight', 0x38)
def _eight(G, c):
    p = P(c)
    ym = 392
    G.stroke(loop(MID, p.cot, ym, p.col + 34, p.cor - 34, 0.6))
    G.stroke(loop(MID, ym + p.hh * 0.6, -OV + p.hh, p.col + 4, p.cor - 4, 0.6))


@g('nine', 0x39)
def _nine(G, c):
    p = P(c)
    top = CH + OV - p.hh
    bot = 238 + p.hh
    G.stroke(loop(MID - 4, top, bot, p.col, p.cor - 6, 0.6))
    G.stroke(Sk(p.cor - 6, (top + bot) / 2).T(MID - 40, -OV + p.hh, 270, 190, 0.55, 0.42)
             .T(p.col + 30, 50, 185, 150, 0.4, 0.3), prof=taper(end=LIFT))


# ================================================================== punctuation
def _dotd(c):
    return c.W * 1.32


@g('period', 0x2E)
def _period(G, c):
    d = _dotd(c)
    G.dot(MID, d * 0.42, d)


@g('comma', 0x2C)
def _comma(G, c):
    d = _dotd(c)
    G.dot(MID + 6, d * 0.42 + 8, d)
    G.stroke(Sk(MID + 6 + d * 0.22, d * 0.42 + 6).T(MID - 62, -150, 270, 225, 0.5, 0.3),
             prof=taper(start=(0.95, 10), end=(0.55, 140)))


@g('colon', 0x3A)
def _colon(G, c):
    d = _dotd(c)
    G.dot(MID, d * 0.42, d)
    G.dot(MID, XH - d * 0.42, d)


@g('semicolon', 0x3B)
def _semicolon(G, c):
    d = _dotd(c)
    G.dot(MID, XH - d * 0.42, d)
    G.dot(MID + 6, d * 0.42 + 8, d)
    G.stroke(Sk(MID + 6 + d * 0.22, d * 0.42 + 6).T(MID - 62, -150, 270, 225, 0.5, 0.3),
             prof=taper(start=(0.95, 10), end=(0.55, 140)))


@g('exclam', 0x21)
def _exclam(G, c):
    p = P(c)
    d = _dotd(c)
    G.stroke(Sk(MID, p.ct).L(MID, 235), prof=taper(end=(0.72, 300)))
    G.dot(MID, d * 0.42, d)


@g('question', 0x3F)
def _question(G, c):
    p = P(c)
    d = _dotd(c)
    G.stroke(Sk(p.col + 22, 562).T(MID + 2, p.cot, 70, 0, 0.36, 0.46).H(p.cor - 10, 500, 0.58, 0.56)
             .T(MID, 340, 270, 250, 0.5, 0.3).L(MID - 6, 236), prof=taper(start=LIFT, end=(0.8, 100)))
    G.dot(MID - 4, d * 0.42, d)


@g('quotesingle', 0x27)
def _quotesingle(G, c):
    G.stroke(Sk(MID, CH + 20).L(MID, 470), prof=taper(end=(0.62, 220)))


@g('quotedbl', 0x22)
def _quotedbl(G, c):
    G.stroke(Sk(MID - 92, CH + 20).L(MID - 92, 470), prof=taper(end=(0.62, 220)))
    G.stroke(Sk(MID + 92, CH + 20).L(MID + 92, 470), prof=taper(end=(0.62, 220)))


@g('grave', 0x60)
def _grave(G, c):
    G.stroke(Sk(MID - 70, 700).L(MID + 60, 590), prof=taper(end=(0.7, 140)))


@g('hyphen', 0x2D)
def _hyphen(G, c):
    G.line(128, AXIS, 422, AXIS)


@g('underscore', 0x5F)
def _underscore(G, c):
    G.rpoly([(-4, -150 - c.H / 2), (-4, -150 + c.H / 2), (554, -150 + c.H / 2), (554, -150 - c.H / 2)], 0)


@g('plus', 0x2B)
def _plus(G, c):
    G.line(92, AXIS, 458, AXIS)
    G.line(MID, AXIS - 183, MID, AXIS + 183)


@g('equal', 0x3D)
def _equal(G, c):
    G.line(92, AXIS + 100, 458, AXIS + 100)
    G.line(92, AXIS - 100, 458, AXIS - 100)


@g('less', 0x3C)
def _less(G, c):
    G.stroke(Sk(452, AXIS + 190).L(102, AXIS).L(452, AXIS - 190))


@g('greater', 0x3E)
def _greater(G, c):
    G.stroke(Sk(98, AXIS + 190).L(448, AXIS).L(98, AXIS - 190))


@g('asciicircum', 0x5E)
def _asciicircum(G, c):
    G.stroke(Sk(110, 420).L(MID, CH - c.H / 2 + 4).L(440, 420))


@g('asciitilde', 0x7E)
def _asciitilde(G, c):
    G.stroke(Sk(88, AXIS - 22).T(190, AXIS + 52, 64, 0, 0.4, 0.4).T(360, AXIS - 52, 0, 0, 0.5, 0.5)
             .T(462, AXIS + 22, 0, 64, 0.4, 0.4))


@g('slash', 0x2F)
def _slash(G, c):
    G.line(452, 800, 98, -110)


@g('backslash', 0x5C)
def _backslash(G, c):
    G.line(98, 800, 452, -110)


@g('bar', 0x7C)
def _bar(G, c):
    G.line(MID, -205, MID, 805)


def _paren(G, c, sgn):
    hw = c.W / 2
    x_out = MID + sgn * 108
    x_in = MID - sgn * 70
    sk = Sk(x_out, 815).T(x_in, 300, 180 if sgn > 0 else 0, 270, 0.32, 0.4) if False else None
    top, bot = 818 - c.H / 2, -218 + c.H / 2
    ym = (top + bot) / 2
    a_out = 180 + sgn * 0  # unused
    if sgn > 0:   # '('
        sk = Sk(x_out, top).T(x_in, ym, 228, 270, 0.42, 0.55).T(x_out, bot, 270, 312, 0.55, 0.42)
    else:
        sk = Sk(x_out, top).T(x_in, ym, 312, 270, 0.42, 0.55).T(x_out, bot, 270, 228, 0.55, 0.42)
    G.stroke(sk)


@g('parenleft', 0x28)
def _parenleft(G, c):
    _paren(G, c, +1)


@g('parenright', 0x29)
def _parenright(G, c):
    _paren(G, c, -1)


@g('bracketleft', 0x5B)
def _bracketleft(G, c):
    top, bot = 818 - c.H / 2, -218 + c.H / 2
    x = 190 + c.W / 2
    G.stroke(Sk(410, top).L(x, top).L(x, bot).L(410, bot))


@g('bracketright', 0x5D)
def _bracketright(G, c):
    top, bot = 818 - c.H / 2, -218 + c.H / 2
    x = 360 - c.W / 2
    G.stroke(Sk(140, top).L(x, top).L(x, bot).L(140, bot))


def _brace(G, c, sgn):
    top, bot = 818 - c.H / 2, -218 + c.H / 2
    ym = (top + bot) / 2
    x_tip = MID - sgn * 170
    x_st = MID - sgn * 20
    x_end = MID + sgn * 150
    s = sgn
    sk = (Sk(x_end, top).T(x_st, top - 110, 180 if s > 0 else 0, 270, 0.6, 0.4).L(x_st, ym + 95)
          .T(x_tip, ym, 270, 180 if s > 0 else 0, 0.5, 0.5))
    sk2 = (Sk(x_tip, ym).T(x_st, ym - 95, 0 if s > 0 else 180, 270, 0.5, 0.5).L(x_st, bot + 110)
           .T(x_end, bot, 270, 0 if s > 0 else 180, 0.4, 0.6))
    G.stroke(sk)
    G.stroke(sk2)


@g('braceleft', 0x7B)
def _braceleft(G, c):
    _brace(G, c, +1)


@g('braceright', 0x7D)
def _braceright(G, c):
    _brace(G, c, -1)


@g('numbersign', 0x23)
def _numbersign(G, c):
    G.line(205, 650, 168, 40)
    G.line(382, 650, 345, 40)
    G.line(80, 452, 470, 452)
    G.line(70, 240, 460, 240)


@g('dollar', 0x24)
def _dollar(G, c):
    p = P(c)
    xl, xr = p.col + 26, p.cor - 26
    top, bot = 650 - p.hh, 30 + p.hh
    sk = (Sk(xr - 2, top - 92).T(MID + 6, top, 124, 180, 0.32, 0.42)
          .H(xl, top - 112, 0.56, 0.62)
          .T(MID, (top + bot) / 2, 270, 336, 0.4, 0.42)
          .T(xr + 6, bot + 120, 336, 270, 0.42, 0.4)
          .V(MID - 6, bot, 0.62, 0.56)
          .T(xl - 8, bot + 92, 180, 128, 0.42, 0.32))
    G.stroke(sk, prof=taper(start=LIFT, end=LIFT))
    G.line(MID, 762, MID, top + 20)
    G.line(MID, bot - 20, MID, -82)


@g('percent', 0x25)
def _percent(G, c):
    k = 0.82
    G.stroke(loop(150, 660, 430, 70, 230, 0.62), scale=k)
    G.stroke(loop(400, 250, 20, 320, 480, 0.62), scale=k)
    G.line(440, 650, 110, 30, scale=k)


@g('ampersand', 0x26)
def _ampersand(G, c):
    p = P(c)
    k = 0.96
    sk = (Sk(p.cor + 6, p.sb).L(214, 446).Tc(196, 598, 72, 0.4, 0.4)
          .T(282, p.cot, 72, 0, 0.42, 0.55).T(368, 590, 0, 260, 0.55, 0.42)
          .T(168, 382, 238, 220, 0.42, 0.42).Tc(p.col + 4, 168, 268, 0.4, 0.42)
          .V(238, -OV + p.hh, 0.56, 0.6).T(p.cor - 14, 300, 0, 64, 0.5, 0.4))
    G.stroke(sk, prof=taper(end=LIFT), scale=k)


@g('at', 0x40)
def _at(G, c):
    p = P(c)
    k = 0.8
    hw = p.hw * k
    hh = p.hh * k
    # inner bowl + stem
    xs = 372
    G.stroke(loop(276, 452 - hh, 168 + hh, 178 + hw, xs - hw * 0.2, 0.6), scale=k)
    sk = (Sk(xs, 462 - hh).L(xs, 214).V(428, 154 + hh, 0.6, 0.6).H(512 - hw, 300, 0.55, 0.6)
          .V(MID, 650 - hh, 0.6, 0.6).H(38 + hw, 280, 0.6, 0.6).V(270, -86 + hh, 0.6, 0.6)
          .T(466, -50, 0, 30, 0.4, 0.4))
    G.stroke(sk, scale=k, prof=taper(end=LIFT))


@g('asterisk', 0x2A)
def _asterisk(G, c):
    # five rounded petals: a small spark
    cx, cy = MID, 516
    R = 166
    for i in range(5):
        a = math.radians(90 + i * 72)
        G.stroke(Sk(cx, cy).L(cx + R * math.cos(a), cy + R * math.sin(a)))


@g('space', 0x20)
def _space(G, c):
    pass


# ================================================================== alternates
def spark(G, c, x, y, size=None):
    """Tiny four-point spark used as an alternate tittle (ss03)."""
    R = size if size is not None else c.W * 1.05 + 22
    r = R * 0.36
    pts = []
    for i in range(8):
        a = math.radians(90 + i * 45)
        rr = R if i % 2 == 0 else r
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    G.rpoly(pts, [R * 0.14 if i % 2 == 0 else r * 0.6 for i in range(8)])


@g('zero.slash')
def _zero_slash(G, c):
    p = P(c)
    G.stroke(loop(MID, p.cot, -OV + p.hh, 64 + p.hw, 486 - p.hw, 0.6))
    G.line(388, 560, 162, 130, scale=0.86)


@g('g.double')
def _g_double(G, c):
    p = P(c)
    k = 0.92
    top, bot = p.xt, 205
    G.stroke(loop(MID - 18, top, bot + p.hh * 0.4, p.ol + 12, p.or_ - 48, 0.6), scale=k)
    G.stroke(Sk(MID + 70, top - 10).T(p.or_ + 8, XH + 12, 30, 20, 0.4, 0.3), scale=k * 0.9)
    G.stroke(Sk(MID - 80, bot + 8).T(p.ol + 30, 115, 220, 270, 0.4, 0.4).T(MID + 40, 52, 340, 0, 0.4, 0.4)
             .H(p.or_, -70, 0.56, 0.6).V(MID, p.dtr, 0.6, 0.6).H(p.ol, -60, 0.6, 0.56).V(MID - 20, 30, 0.56, 0.6),
             scale=k)


@g('i.spark')
def _i_spark(G, c):
    p = P(c)
    xs = MID + 22
    G.stroke(Sk(xs - 150, p.st - 2).L(xs, p.st - 2).L(xs, p.sb))
    G.line(xs - 178, p.sb, xs + 160, p.sb)
    spark(G, c, xs - 4, XH + 205)


@g('j.spark')
def _j_spark(G, c):
    p = P(c)
    xs = MID + 70
    G.stroke(Sk(xs - 175, p.st - 2).L(xs, p.st - 2).L(xs, -45).V(xs - 125, p.dtr, 0.6, 0.56)
             .T(68 + p.hw, DE + 62, 180, 140, 0.4, 0.3), prof=lift())
    spark(G, c, xs - 4, XH + 205)
