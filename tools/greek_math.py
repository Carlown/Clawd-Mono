"""Greek and mathematical operators for Clawd Mono."""
import math
from glyphlib import Sk, taper
import latin
from latin import P, loop, lift, LIFT, JOIN, XH, CH, AS, DE, OV, MID, AXIS, bowl_R, bowl_L, n_arch, u_cup

REG = {}
ADV = 550


def g(name, *uni, w=ADV):
    def deco(fn):
        REG[name] = (list(uni), w, fn)
        return fn
    return deco


def same(name, cp, src):
    REG[name] = ([cp], ADV, latin.REG[src][2])


# ------------------------------------------------------------- uppercase
for nm, cp, src in (('Alpha', 0x391, 'A'), ('Beta', 0x392, 'B'), ('Epsilon', 0x395, 'E'), ('Zeta', 0x396, 'Z'),
                    ('Eta', 0x397, 'H'), ('Iota', 0x399, 'I'), ('Kappa', 0x39A, 'K'), ('Mu', 0x39C, 'M'),
                    ('Nu', 0x39D, 'N'), ('Omicron', 0x39F, 'O'), ('Rho', 0x3A1, 'P'), ('Tau', 0x3A4, 'T'),
                    ('Upsilon', 0x3A5, 'Y'), ('Chi', 0x3A7, 'X'), ('omicron', 0x3BF, 'o')):
    same(nm, cp, src)


@g('Gamma', 0x393)
def _Gamma(G, c):
    p = P(c)
    G.stroke(Sk(p.cr + 10, CH - p.hh).L(p.cl + 20, CH - p.hh).L(p.cl + 20, p.sb))


@g('Delta', 0x394, 0x2206)
def _Delta(G, c):
    p = P(c)
    G.stroke(Sk(MID, CH - p.hh + 6).L(p.cor + 6, p.hh).L(p.col - 6, p.hh).Z())


@g('Theta', 0x398)
def _Theta(G, c):
    latin.REG['O'][2](G, c)
    G.line(170, 345, 380, 345)


@g('Lambda', 0x39B)
def _Lambda(G, c):
    p = P(c)
    G.stroke(Sk(p.col - 6, p.sb).L(MID, CH - p.hh + 6).L(p.cor + 6, p.sb))


@g('Xi', 0x39E)
def _Xi(G, c):
    p = P(c)
    G.line(p.cl - 4, CH - p.hh, p.cr + 4, CH - p.hh)
    G.line(p.cl + 40, 352, p.cr - 40, 352)
    G.line(p.cl - 4, p.hh, p.cr + 4, p.hh)


@g('Pi', 0x3A0, 0x220F)
def _Pi(G, c):
    p = P(c)
    G.stroke(Sk(p.cl, p.sb).L(p.cl, CH - p.hh).L(p.cr, CH - p.hh).L(p.cr, p.sb))


@g('Sigma', 0x3A3, 0x2211)
def _Sigma(G, c):
    p = P(c)
    G.stroke(Sk(p.cr + 8, CH - p.hh).L(p.cl, CH - p.hh).L(MID - 10, 352).L(p.cl, p.hh).L(p.cr + 12, p.hh))


@g('Phi', 0x3A6)
def _Phi(G, c):
    p = P(c)
    G.line(MID, p.sb, MID, p.ct)
    G.stroke(loop(MID, 570 - p.hh, 120 + p.hh, p.col, p.cor, 0.6))


@g('Psi', 0x3A8)
def _Psi(G, c):
    p = P(c)
    G.line(MID, p.sb, MID, p.ct)
    G.stroke(Sk(p.col, p.ct).L(p.col, 440).V(MID, 220 + p.hh, 0.58).H(p.cor, 440, 0.58).L(p.cor, p.ct))


@g('Omega', 0x3A9, 0x2126)
def _Omega(G, c):
    p = P(c)
    G.stroke(Sk(p.col - 10, p.hh).L(170, p.hh).T(p.col + 6, 300, 140, 270, 0.42, 0.4) if False else
             Sk(p.col - 4, p.hh).L(165, p.hh).T(p.col + 4, 330, 120, 90, 0.42, 0.45)
             .V(MID, p.cot, 0.58, 0.6).H(p.cor - 4, 330, 0.6, 0.58)
             .T(385, p.hh, 270, 240, 0.45, 0.42).L(p.cor + 4, p.hh))


# ------------------------------------------------------------- lowercase
@g('alpha', 0x3B1)
def _alpha(G, c):
    p = P(c)
    r = p.r
    G.stroke(bowl_L(p, r - 10, p.xt, p.xb, p.ol, yj_top=XH - 90, yj_bot=120), prof=taper(start=JOIN, end=JOIN))
    G.stroke(Sk(r - 10, p.st).L(r - 10, 120).V(r + 40, p.xb + 6, 0.55, 0.5).L(r + 60, p.xb + 6),
             prof=lift())


@g('beta', 0x3B2)
def _beta(G, c):
    p = P(c)
    G.stroke(Sk(p.l, DE + p.hh).L(p.l, AS - 200).V(MID, AS + OV - p.hh, 0.58, 0.58)
             .H(p.or_ - 26, AS - 175, 0.58, 0.56).V(MID - 20, 420, 0.56, 0.56))
    G.stroke(Sk(MID - 20, 420).H(p.or_, 210, 0.6, 0.58).V(MID - 10, p.xb, 0.58, 0.56).T(p.l, 110, 180, 120, 0.45, 0.4),
             prof=taper(end=JOIN))


@g('gamma', 0x3B3)
def _gamma(G, c):
    p = P(c)
    G.line(p.ol - 6, p.st, MID + 10, 10)
    G.stroke(Sk(p.or_ + 6, p.st).L(MID - 46, DE + p.hh + 6))


@g('delta', 0x3B4)
def _delta(G, c):
    p = P(c)
    G.stroke(loop(MID, 430 - p.hh, p.xb, p.ol, p.or_, 0.6))
    G.stroke(Sk(MID + 20, 420 - p.hh).T(200, 600, 135, 90, 0.42, 0.4).T(p.or_ - 20, AS - 20, 90, 20, 0.5, 0.42),
             prof=taper(end=LIFT))


@g('epsilon', 0x3B5)
def _epsilon(G, c):
    p = P(c)
    G.stroke(Sk(p.or_ - 8, 432).T(MID + 10, p.xt, 130, 180, 0.34, 0.45).H(p.ol + 26, 392, 0.58, 0.58)
             .V(MID + 14, 275, 0.6, 0.6), prof=taper(start=LIFT))
    G.stroke(Sk(MID + 14, 275).H(p.ol, 140, 0.6, 0.6).V(MID + 10, p.xb, 0.6, 0.6).T(p.or_ - 4, 100, 0, 48, 0.45, 0.32),
             prof=lift())


@g('zeta', 0x3B6)
def _zeta(G, c):
    p = P(c)
    G.stroke(Sk(p.ol + 10, AS - p.hh).L(p.or_ - 10, AS - p.hh).T(p.ol, 200, 225, 270, 0.4, 0.45)
             .V(MID, 0 + p.hh, 0.6, 0.6).T(MID + 60, -180, 0, 260, 0.45, 0.4), prof=lift())


@g('eta', 0x3B7)
def _eta(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.st)
    G.stroke(n_arch(p, p.l, p.r, bottom=DE + p.hh), prof=taper(start=JOIN))


@g('theta', 0x3B8)
def _theta(G, c):
    p = P(c)
    G.stroke(loop(MID, AS + OV - p.hh, p.xb, p.ol + 6, p.or_ - 6, 0.6))
    G.line(p.ol + 10, 370, p.or_ - 10, 370)


@g('iota', 0x3B9)
def _iota(G, c):
    p = P(c)
    G.stroke(Sk(MID - 30, p.st).L(MID - 30, 130).V(MID + 60, p.xb, 0.6, 0.56).L(MID + 130, p.xb + 4), prof=lift())


@g('kappa', 0x3BA)
def _kappa(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.st)
    G.stroke(Sk(p.or_ - 18, p.st).L(p.l + 8, 200), prof=taper(end=(0.7, 120)))
    G.stroke(Sk(p.l + 120, 268).L(p.or_ - 4, p.sb), prof=taper(start=(0.7, 100)))


@g('lambda', 0x3BB)
def _lambda(G, c):
    p = P(c)
    G.stroke(Sk(p.ol + 4, AS - p.hh).T(MID - 40, AS - 60, 0, 300, 0.4, 0.4).L(p.or_ + 4, p.sb))
    G.line(p.ol - 4, p.sb, MID + 8, 390)


@g('nu', 0x3BD)
def _nu(G, c):
    latin.REG['v'][2](G, c)


@g('xi', 0x3BE)
def _xi(G, c):
    p = P(c)
    G.stroke(Sk(p.ol + 30, AS - p.hh).L(p.or_ - 20, AS - p.hh), scale=0.95)
    G.stroke(Sk(p.or_ - 30, AS - p.hh).T(p.ol + 40, 500, 200, 270, 0.4, 0.5).T(p.or_ - 40, 330, 270, 0, 0.5, 0.4))
    G.stroke(Sk(p.or_ - 40, 330).T(p.ol, 160, 180, 270, 0.42, 0.5).V(MID, p.hh, 0.6, 0.6)
             .T(MID + 60, -180, 0, 260, 0.45, 0.4), prof=lift())


@g('pi', 0x3C0)
def _pi(G, c):
    p = P(c)
    G.line(p.ol - 18, XH - p.hh, p.or_ + 18, XH - p.hh)
    G.line(p.l + 30, XH - p.hh, p.l + 20, p.sb)
    G.stroke(Sk(p.r - 30, XH - p.hh).L(p.r - 30, 120).V(p.r + 30, p.xb + 4, 0.55, 0.5), prof=lift())


@g('rho', 0x3C1)
def _rho(G, c):
    p = P(c)
    G.stroke(Sk(p.l, DE + p.hh).L(p.l, 255).V(MID, p.xt, 0.58, 0.6).H(p.or_, 255, 0.6, 0.6)
             .V(MID, p.xb, 0.6, 0.6).T(p.l, 120, 180, 120, 0.45, 0.4), prof=taper(end=JOIN))


@g('sigma1', 0x3C2)
def _sigmafinal(G, c):
    p = P(c)
    G.stroke(Sk(p.or_ - 4, 410).T(MID + 8, p.xt, 128, 180, 0.32, 0.45).H(p.ol, 230, 0.6, 0.6)
             .V(MID + 20, 30, 0.6, 0.6).T(MID + 40, -170, 0, 250, 0.5, 0.4), prof=taper(start=LIFT, end=LIFT))


@g('sigma', 0x3C3)
def _sigma(G, c):
    p = P(c)
    G.stroke(Sk(p.or_ + 10, XH - p.hh).L(MID, XH - p.hh).H(p.ol, 240, 0.58, 0.6).V(MID, p.xb, 0.6, 0.6)
             .H(p.or_ - 10, 240, 0.6, 0.6).V(MID - 20, XH - p.hh, 0.6, 0.6))


@g('tau', 0x3C4)
def _tau(G, c):
    p = P(c)
    G.line(p.ol, XH - p.hh, p.or_, XH - p.hh)
    G.stroke(Sk(MID - 10, XH - p.hh).L(MID - 10, 130).V(MID + 70, p.xb, 0.6, 0.56).L(MID + 130, p.xb + 4), prof=lift())


@g('upsilon', 0x3C5)
def _upsilon(G, c):
    p = P(c)
    G.stroke(Sk(p.l, p.st).L(p.l, 230).V(MID, p.xb, 0.58).H(p.or_ - 6, 260, 0.58).T(p.or_ - 30, XH + 4, 90, 110, 0.4, 0.3),
             prof=lift())


@g('phi', 0x3C6)
def _phi(G, c):
    p = P(c)
    G.line(MID, DE + p.hh, MID, AS - p.hh)
    G.stroke(loop(MID, p.xt, p.xb, p.ol, p.or_, 0.6))


@g('chi', 0x3C7)
def _chi(G, c):
    p = P(c)
    G.line(p.ol, p.st, p.or_, DE + p.hh)
    G.line(p.or_, p.st, p.ol, DE + p.hh)


@g('psi', 0x3C8)
def _psi(G, c):
    p = P(c)
    G.line(MID, DE + p.hh, MID, AS - p.hh)
    G.stroke(Sk(p.ol, p.st).L(p.ol, 240).V(MID, p.xb + 10, 0.58).H(p.or_, 240, 0.58).L(p.or_, p.st))


@g('omega', 0x3C9)
def _omega(G, c):
    p = P(c)
    k = 0.9
    hw = p.hw * k
    l, r = 40 + hw, 510 - hw
    G.stroke(Sk(l + 30, p.st).T(l, 200, 240, 270, 0.4, 0.45).V(160, p.xb, 0.58, 0.58).H(MID, 210, 0.58, 0.58)
             .L(MID, 290), scale=k)
    G.stroke(Sk(MID, 210).V(390, p.xb, 0.58, 0.58).H(r, 200, 0.58, 0.58).T(r - 30, p.st, 90, 120, 0.45, 0.4), scale=k)


# ------------------------------------------------------------- math
@g('notequal', 0x2260)
def _ne(G, c):
    G.line(92, AXIS + 100, 458, AXIS + 100)
    G.line(92, AXIS - 100, 458, AXIS - 100)
    G.line(380, AXIS + 250, 170, AXIS - 250)


@g('approxequal', 0x2248)
def _approx(G, c):
    for dy in (95, -95):
        y = AXIS + dy
        G.stroke(Sk(88, y - 22).T(190, y + 52, 64, 0, 0.4, 0.4).T(360, y - 52, 0, 0, 0.5, 0.5)
                 .T(462, y + 22, 0, 64, 0.4, 0.4))


@g('equivalence', 0x2261)
def _equiv(G, c):
    for dy in (165, 0, -165):
        G.line(92, AXIS + dy, 458, AXIS + dy)


@g('lessequal', 0x2264)
def _le(G, c):
    G.stroke(Sk(452, AXIS + 260).L(102, AXIS + 90).L(452, AXIS - 80))
    G.line(102, AXIS - 200, 452, AXIS - 200)


@g('greaterequal', 0x2265)
def _ge(G, c):
    G.stroke(Sk(98, AXIS + 260).L(448, AXIS + 90).L(98, AXIS - 80))
    G.line(98, AXIS - 200, 448, AXIS - 200)


@g('infinity', 0x221E)
def _inf(G, c):
    k = 0.85
    G.stroke(Sk(MID, AXIS).T(140, AXIS + 120, 45, 180, 0.4, 0.5).T(140, AXIS - 120, 180, 0, 0.9, 0.9)
             .T(MID, AXIS, 0, 45, 0.5, 0.4).T(410, AXIS + 120, 45, 0, 0.4, 0.5).T(410, AXIS - 120, 0, 180, 0.9, 0.9)
             .T(MID, AXIS, 180, 135, 0.5, 0.4), scale=k)


@g('radical', 0x221A)
def _radical(G, c):
    G.stroke(Sk(40, AXIS + 40).L(130, AXIS + 90).L(250, -60).L(410, CH + 60).L(520, CH + 60), scale=0.9)


@g('integral', 0x222B)
def _integral(G, c):
    G.stroke(Sk(440, AS - 40).T(360, AS + 40, 135, 180, 0.4, 0.4).T(290, AS - 100, 200, 270, 0.4, 0.4)
             .L(260, -60).T(190, DE + 40, 270, 200, 0.4, 0.4).T(110, DE + 110, 180, 135, 0.4, 0.4), prof=lift())


@g('partialdiff', 0x2202)
def _partial(G, c):
    p = P(c)
    G.stroke(loop(MID - 10, 430, p.xb, p.ol, p.or_ - 20, 0.6))
    G.stroke(Sk(p.or_ - 20, 220).T(MID + 20, CH + 10, 90, 160, 0.6, 0.4).T(130, CH - 70, 180, 230, 0.4, 0.3),
             prof=lift())


@g('nabla', 0x2207)
def _nabla(G, c):
    p = P(c)
    G.stroke(Sk(MID, p.hh - 6).L(p.cor + 6, CH - p.hh).L(p.col - 6, CH - p.hh).Z())


@g('element', 0x2208)
def _element(G, c):
    G.stroke(Sk(450, AXIS + 230).L(310, AXIS + 230).H(110, AXIS, 0.6).V(310, AXIS - 230, 0.6).L(450, AXIS - 230))
    G.line(110, AXIS, 430, AXIS)


@g('notelement', 0x2209)
def _notelement(G, c):
    _element(G, c)
    G.line(400, AXIS + 330, 180, AXIS - 330)


@g('intersection', 0x2229)
def _cap(G, c):
    p = P(c)
    G.stroke(Sk(110, AXIS - 230).L(110, AXIS + 40).V(MID, AXIS + 230, 0.6).H(440, AXIS + 40, 0.6).L(440, AXIS - 230))


@g('union', 0x222A)
def _cup(G, c):
    G.stroke(Sk(110, AXIS + 230).L(110, AXIS - 40).V(MID, AXIS - 230, 0.6).H(440, AXIS - 40, 0.6).L(440, AXIS + 230))


@g('propersubset', 0x2282)
def _subset(G, c):
    G.stroke(Sk(450, AXIS + 220).L(320, AXIS + 220).H(110, AXIS, 0.6).V(320, AXIS - 220, 0.6).L(450, AXIS - 220))


@g('propersuperset', 0x2283)
def _superset(G, c):
    G.stroke(Sk(100, AXIS + 220).L(230, AXIS + 220).H(440, AXIS, 0.6).V(230, AXIS - 220, 0.6).L(100, AXIS - 220))


@g('reflexsubset', 0x2286)
def _subseteq(G, c):
    G.stroke(Sk(450, AXIS + 280).L(320, AXIS + 280).H(110, AXIS + 100, 0.6).V(320, AXIS - 80, 0.6).L(450, AXIS - 80))
    G.line(110, AXIS - 220, 450, AXIS - 220)


@g('reflexsuperset', 0x2287)
def _supseteq(G, c):
    G.stroke(Sk(100, AXIS + 280).L(230, AXIS + 280).H(440, AXIS + 100, 0.6).V(230, AXIS - 80, 0.6).L(100, AXIS - 80))
    G.line(100, AXIS - 220, 440, AXIS - 220)


@g('logicaland', 0x2227)
def _land(G, c):
    G.stroke(Sk(110, AXIS - 230).L(MID, AXIS + 250).L(440, AXIS - 230))


@g('logicalor', 0x2228)
def _lor(G, c):
    G.stroke(Sk(110, AXIS + 250).L(MID, AXIS - 230).L(440, AXIS + 250))


@g('universal', 0x2200)
def _forall(G, c):
    p = P(c)
    G.stroke(Sk(p.col, p.ct).L(MID, p.sb + 4).L(p.cor, p.ct))
    G.line(150, 400, 400, 400)


@g('existential', 0x2203)
def _exists(G, c):
    p = P(c)
    G.stroke(Sk(p.cl, CH - p.hh).L(p.cr, CH - p.hh).L(p.cr, p.hh).L(p.cl, p.hh))
    G.line(p.cl + 30, 352, p.cr, 352)


@g('emptyset', 0x2205)
def _emptyset(G, c):
    G.stroke(loop(MID, 580, 40, 80, 470, 0.58))
    G.line(450, 700, 100, -80, scale=0.9)


@g('orthogonal', 0x22A5)
def _perp(G, c):
    G.line(MID, AXIS - 240, MID, AXIS + 280)
    G.line(80, AXIS - 240, 470, AXIS - 240)


@g('circleplus', 0x2295)
def _oplus(G, c):
    G.stroke(loop(MID, AXIS + 230, AXIS - 230, 50, 500, 0.56), scale=0.8)
    G.line(70, AXIS, 480, AXIS, scale=0.8)
    G.line(MID, AXIS - 210, MID, AXIS + 210, scale=0.8)


@g('circlemultiply', 0x2297)
def _otimes(G, c):
    G.stroke(loop(MID, AXIS + 230, AXIS - 230, 50, 500, 0.56), scale=0.8)
    G.line(MID - 150, AXIS - 150, MID + 150, AXIS + 150, scale=0.8)
    G.line(MID - 150, AXIS + 150, MID + 150, AXIS - 150, scale=0.8)


@g('ringoperator', 0x2218)
def _ring(G, c):
    G.stroke(loop(MID, AXIS + 105, AXIS - 105, MID - 100, MID + 100, 0.56), scale=0.85)


@g('similar', 0x223C)
def _sim(G, c):
    latin.REG['asciitilde'][2](G, c)


@g('proportional', 0x221D)
def _prop(G, c):
    k = 0.85
    G.stroke(Sk(480, AXIS + 150).T(MID, AXIS, 200, 225, 0.4, 0.3).T(140, AXIS - 140, 225, 180, 0.4, 0.4)
             .T(70, AXIS, 180, 90, 0.5, 0.5).T(140, AXIS + 140, 90, 0, 0.5, 0.5).T(MID, AXIS, 0, 315, 0.4, 0.4)
             .T(480, AXIS - 150, 315, 340, 0.3, 0.4), scale=k)


@g('angle', 0x2220)
def _angle(G, c):
    G.stroke(Sk(450, AXIS + 250).L(100, AXIS - 220).L(470, AXIS - 220))


@g('uni2213', 0x2213)
def _mp(G, c):
    G.line(92, AXIS + 200, 458, AXIS + 200)
    G.line(92, AXIS - 60, 458, AXIS - 60)
    G.line(MID, AXIS - 60 - 160, MID, AXIS - 60 + 160)


@g('uni2245', 0x2245)
def _cong(G, c):
    y = AXIS + 180
    G.stroke(Sk(88, y - 22).T(190, y + 52, 64, 0, 0.4, 0.4).T(360, y - 52, 0, 0, 0.5, 0.5).T(462, y + 22, 0, 64, 0.4, 0.4))
    G.line(92, AXIS, 458, AXIS)
    G.line(92, AXIS - 170, 458, AXIS - 170)


@g('uni226A', 0x226A)
def _ll(G, c):
    for dx in (-80, 80):
        G.stroke(Sk(MID + dx + 100, AXIS + 180).L(MID + dx - 100, AXIS).L(MID + dx + 100, AXIS - 180), scale=0.9)


@g('uni226B', 0x226B)
def _gg(G, c):
    for dx in (-80, 80):
        G.stroke(Sk(MID + dx - 100, AXIS + 180).L(MID + dx + 100, AXIS).L(MID + dx - 100, AXIS - 180), scale=0.9)


def _ceilfloor(G, c, left, top):
    t, b = 818 - c.H / 2, -218 + c.H / 2
    x = 190 + c.W / 2 if left else 360 - c.W / 2
    x2 = 410 if left else 140
    if top:
        G.stroke(Sk(x2, t).L(x, t).L(x, b))
    else:
        G.stroke(Sk(x, t).L(x, b).L(x2, b))


REG['uni2308'] = ([0x2308], ADV, lambda G, c: _ceilfloor(G, c, True, True))
REG['uni2309'] = ([0x2309], ADV, lambda G, c: _ceilfloor(G, c, False, True))
REG['uni230A'] = ([0x230A], ADV, lambda G, c: _ceilfloor(G, c, True, False))
REG['uni230B'] = ([0x230B], ADV, lambda G, c: _ceilfloor(G, c, False, False))


@g('uni27E8', 0x27E8)
def _langle(G, c):
    G.stroke(Sk(400, 818 - c.H / 2).L(170, 300).L(400, -218 + c.H / 2))


@g('uni27E9', 0x27E9)
def _rangle(G, c):
    G.stroke(Sk(150, 818 - c.H / 2).L(380, 300).L(150, -218 + c.H / 2))


@g('uni2016', 0x2016)       # ‖
def _dbar(G, c):
    G.line(MID - 80, -205, MID - 80, 805)
    G.line(MID + 80, -205, MID + 80, 805)


@g('uni2113', 0x2113)       # ℓ
def _ell(G, c):
    p = P(c)
    G.stroke(Sk(160, 180).T(330, 520, 40, 70, 0.4, 0.4).T(300, AS - p.hh, 90, 180, 0.5, 0.5)
             .T(230, 520, 180, 270, 0.4, 0.4).L(230, 150).V(320, p.xb, 0.6, 0.55).L(420, p.xb + 20), prof=lift())
