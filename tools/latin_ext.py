"""Latin-1 Supplement, Latin Extended-A, pinyin, special letters, Latin-1
symbols and general punctuation for Clawd Mono."""
import math
import unicodedata
from glyphlib import Sk, taper, Ctx
from geom import transform_contour, reverse_contour
import latin
from latin import P, loop, lift, LIFT, JOIN, XH, CH, AS, DE, OV, MID, AXIS, bowl_R, bowl_L, n_arch

REG = {}
ADV = 550


def g(name, *uni, w=ADV):
    def deco(fn):
        REG[name] = (list(uni), w, fn)
        return fn
    return deco


def base_fn(name):
    if name in REG:
        return REG[name][2]
    return latin.REG[name][2]


# ================================================================== marks
LC_BASE, UC_BASE = 588, 752


def m_acute(G, c, mx, my, s=1.0):
    G.stroke(Sk(mx - 52 * s, my + 8).L(mx + 64 * s, my + 8 + 132 * s), prof=taper(start=(0.72, 90)), scale=0.92)


def m_grave(G, c, mx, my, s=1.0):
    G.stroke(Sk(mx + 52 * s, my + 8).L(mx - 64 * s, my + 8 + 132 * s), prof=taper(start=(0.72, 90)), scale=0.92)


def m_circ(G, c, mx, my, s=1.0):
    G.stroke(Sk(mx - 128, my + 8).L(mx, my + 8 + 128 * s).L(mx + 128, my + 8), scale=0.9)


def m_caron(G, c, mx, my, s=1.0):
    G.stroke(Sk(mx - 128, my + 8 + 128 * s).L(mx, my + 8).L(mx + 128, my + 8 + 128 * s), scale=0.9)


def m_dier(G, c, mx, my, s=1.0):
    d = c.W * 1.22
    G.dot(mx - 108, my + 48 * s + d * 0.2, d)
    G.dot(mx + 108, my + 48 * s + d * 0.2, d)


def m_dot(G, c, mx, my, s=1.0):
    d = c.W * 1.25
    G.dot(mx, my + 48 * s + d * 0.2, d)


def m_tilde(G, c, mx, my, s=1.0):
    y = my + 62 * s
    a = 44 * s
    G.stroke(Sk(mx - 150, y - a * 0.5).T(mx - 72, y + a, 64, 0, 0.4, 0.4).T(mx + 72, y - a, 0, 0, 0.5, 0.5)
             .T(mx + 150, y + a * 0.5, 0, 64, 0.4, 0.4), scale=0.9)


def m_macron(G, c, mx, my, s=1.0):
    G.line(mx - 140, my + 52 * s, mx + 140, my + 52 * s, scale=0.92)


def m_breve(G, c, mx, my, s=1.0):
    G.stroke(Sk(mx - 122, my + 8 + 125 * s).T(mx, my + 14, 280, 0, 0.45, 0.5).T(mx + 122, my + 8 + 125 * s, 0, 80, 0.5, 0.45),
             scale=0.9)


def m_ring(G, c, mx, my, s=1.0):
    r = 64 * min(1, s * 1.05)
    cy = my + 10 + r
    G.stroke(Sk(mx, cy + r).H(mx + r, cy, 0.552).V(mx, cy - r, 0.552).H(mx - r, cy, 0.552).V(mx, cy + r, 0.552).Z(),
             scale=0.8)


def m_dacute(G, c, mx, my, s=1.0):
    m_acute(G, c, mx - 78, my, s * 0.92)
    m_acute(G, c, mx + 78, my, s * 0.92)


def m_cedilla(G, c, mx, my=0, s=1.0):
    G.stroke(Sk(mx + 4, 30).L(mx + 4, -62).T(mx + 102, -136, 0, 270, 0.5, 0.4).T(mx - 72, -212, 270, 190, 0.5, 0.4),
             scale=0.8, prof=taper(end=(0.8, 80)))


def m_ogonek(G, c, mx, my=0, s=1.0):
    G.stroke(Sk(mx, 40).T(mx - 82, -128, 240, 270, 0.45, 0.4).T(mx + 30, -212, 270, 10, 0.45, 0.4),
             scale=0.84, prof=taper(start=(0.85, 30), end=(0.75, 80)))


def m_commabelow(G, c, mx, my=0, s=1.0):
    d = c.W * 1.15
    G.dot(mx + 6, -92, d)
    G.stroke(Sk(mx + 6 + d * 0.22, -96).T(mx - 48, -240, 270, 225, 0.5, 0.3),
             prof=taper(start=(0.95, 10), end=(0.55, 110)), scale=0.9)


MARKS = {0x300: m_grave, 0x301: m_acute, 0x302: m_circ, 0x303: m_tilde, 0x304: m_macron, 0x306: m_breve,
         0x307: m_dot, 0x308: m_dier, 0x30A: m_ring, 0x30B: m_dacute, 0x30C: m_caron,
         0x327: m_cedilla, 0x328: m_ogonek, 0x326: m_commabelow}
BELOW = {0x327, 0x328, 0x326}
MARK_H = {0x300: 140, 0x301: 140, 0x302: 136, 0x303: 110, 0x304: 70, 0x306: 136, 0x307: 95, 0x308: 95,
          0x30A: 140, 0x30B: 140, 0x30C: 136}

# mark x anchor per base letter (default MID)
ANCHOR = {'i': MID + 18, 'dotlessi': MID + 18, 'j': MID + 66, 'dotlessj': MID + 66, 'l': MID - 10,
          'a': MID - 8, 'r': 300, 'f': 300, 't': 230, 'J': 300, 'g': MID - 12}
OGONEK_X = {'a': 400, 'e': 330, 'i': 330, 'u': 400, 'o': 330, 'A': 470, 'E': 400, 'I': 330, 'U': 330,
            'dotlessi': 330}
# letters whose ascender pushes above-marks up
TALL = {'b', 'd', 'h', 'k', 'l', 'f', 't'}


def compose(base, marks):
    def fn(G, c):
        base_fn(base)(G, c)
        cap = base[0].isupper() or base in ('dotlessI',)
        y = UC_BASE if cap else LC_BASE
        if base in TALL:
            y = AS + 34
        mx = ANCHOR.get(base, MID)
        s = 0.86 if cap else 1.0
        above = [m for m in marks if m not in BELOW]
        if cap and len(above) >= 2:
            # stacked marks on capitals must stay inside the 960 ascent
            y, s = UC_BASE - 26, 0.64
        first = True
        for m in marks:
            if m in BELOW:
                x = OGONEK_X.get(base, 420) if m == 0x328 else mx
                MARKS[m](G, c, x)
                continue
            if not first:
                y += 18 if s > 0.7 else 8
            MARKS[m](G, c, mx, y, s)
            y += MARK_H.get(m, 130) * s + 10
            first = False
    return fn


def decompose_full(ch):
    """-> (base char, [combining marks]) or None."""
    d = unicodedata.decomposition(ch)
    if not d or d.startswith('<'):
        return None
    parts = [int(x, 16) for x in d.split()]
    base = chr(parts[0])
    marks = parts[1:]
    inner = decompose_full(base)
    if inner:
        return inner[0], inner[1] + marks
    return base, marks


AGL = {}


def gname(ch):
    import fontTools.agl as agl
    n = agl.UV2AGL.get(ord(ch))
    return n or ('uni%04X' % ord(ch))


# ================================================================== special letters
@g('dotlessi', 0x131)
def _dotlessi(G, c):
    p = P(c)
    xs = MID + 22
    G.stroke(Sk(xs - 150, p.st - 2).L(xs, p.st - 2).L(xs, p.sb))
    G.line(xs - 178, p.sb, xs + 160, p.sb)


@g('dotlessj', 0x237)
def _dotlessj(G, c):
    p = P(c)
    xs = MID + 70
    G.stroke(Sk(xs - 175, p.st - 2).L(xs, p.st - 2).L(xs, -45).V(xs - 125, p.dtr, 0.6, 0.56)
             .T(68 + p.hw, DE + 62, 180, 140, 0.4, 0.3), prof=lift())


@g('germandbls', 0xDF)
def _germandbls(G, c):
    p = P(c)
    G.stroke(Sk(p.l, p.sb).L(p.l, AS - 210).V(MID - 4, AS + OV - p.hh, 0.58, 0.58).H(p.or_ - 22, AS - 170, 0.58, 0.56)
             .T(260, 428, 270, 200, 0.45, 0.4).Tc(p.or_, 210, 270, 0.6, 0.5)
             .V(MID - 10, p.xb, 0.58, 0.56).T(205, 40, 180, 160, 0.35, 0.3), prof=taper(end=(0.85, 60)))


@g('ae', 0xE6)
def _ae(G, c):
    p = P(c)
    k = 0.78
    hw = p.hw * k
    xm = MID - 4
    # a-part
    G.stroke(Sk(48 + hw + 14, 420).T(170, p.xt, 60, 0, 0.36, 0.42).H(xm, p.xt - 130, 0.55).L(xm, p.sb), scale=k)
    G.stroke(Sk(xm, 290).L(150, 290).H(46 + hw, 150, 0.56, 0.6).V(160, p.xb, 0.6, 0.58).T(xm, 110, 0, 64, 0.48, 0.32),
             scale=k, prof=taper(end=(0.5, 90)))
    # e-part
    G.line(xm, 270, 506 - hw, 270, scale=k)
    G.stroke(Sk(506 - hw, 270).V(400, p.xt, 0.62, 0.58).H(xm, 300, 0.6, 0.6), scale=k)
    G.stroke(Sk(xm, 200).V(400, p.xb, 0.62, 0.6).T(500 - hw, 100, 0, 46, 0.45, 0.32), scale=k, prof=lift())


@g('AE', 0xC6)
def _AE(G, c):
    p = P(c)
    k = 0.85
    hw = p.hw * k
    hh = p.hh * k
    yt = CH - hh
    xs = 300
    G.stroke(Sk(40 + hw, p.sb).L(xs - 40, yt).L(506 - hw, yt), scale=k)
    G.line(xs - 30, yt, xs, hh, scale=k)
    G.line(xs, hh, 510 - hw, hh, scale=k)
    G.line(xs - 10, 360, 480 - hw, 360, scale=k)
    G.line(120, 230, xs - 6, 230, scale=k)


@g('oe', 0x153)
def _oe(G, c):
    p = P(c)
    k = 0.78
    hw = p.hw * k
    xm = MID + 4
    G.stroke(loop(160, p.xt, p.xb, 40 + hw, xm, 0.6), scale=k)
    G.line(xm, 270, 510 - hw, 270, scale=k)
    G.stroke(Sk(510 - hw, 270).V(402, p.xt, 0.62, 0.58).H(xm, 300, 0.6, 0.6), scale=k)
    G.stroke(Sk(xm, 200).V(406, p.xb, 0.62, 0.6).T(504 - hw, 100, 0, 46, 0.45, 0.32), scale=k, prof=lift())


@g('OE', 0x152)
def _OE(G, c):
    p = P(c)
    k = 0.85
    hw = p.hw * k
    hh = p.hh * k
    xs = 300
    G.stroke(Sk(xs, CH - hh).L(190, CH - hh).H(38 + hw, CH / 2, 0.6).V(190, hh, 0.6).L(xs, hh), scale=k)
    G.line(xs, hh, xs, CH - hh, scale=k)
    G.line(xs, CH - hh, 508 - hw, CH - hh, scale=k)
    G.line(xs, hh, 512 - hw, hh, scale=k)
    G.line(xs, 360, 480 - hw, 360, scale=k)


@g('oslash', 0xF8)
def _oslash(G, c):
    base_fn('o')(G, c)
    G.line(450, 560, 100, -50, scale=0.86)


@g('Oslash', 0xD8)
def _Oslash(G, c):
    base_fn('O')(G, c)
    G.line(470, 760, 80, -70, scale=0.86)


@g('Eth', 0xD0, 0x110)
def _Eth(G, c):
    base_fn('D')(G, c)
    p = P(c)
    G.line(28, 352, 250, 352, scale=0.9)


@g('eth', 0xF0)
def _eth(G, c):
    p = P(c)
    top = 420
    G.stroke(loop(MID, top - p.hh + 20, p.xb, p.ol, p.or_, 0.6))
    G.stroke(Sk(MID + 30, top - p.hh + 22).T(p.or_ - 6, 300, 0, 270, 0.4, 0.5) if False else
             Sk(p.or_, 250).T(170, AS - 40, 90, 140, 0.5, 0.4), prof=taper(end=LIFT))
    G.line(170, 640, 410, 720, scale=0.85)


@g('dcroat', 0x111)
def _dcroat(G, c):
    base_fn('d')(G, c)
    G.line(330, 640, 520, 640, scale=0.9)


@g('Thorn', 0xDE)
def _Thorn(G, c):
    p = P(c)
    G.line(p.cl, p.sb, p.cl, p.ct)
    yt, ym = 560, 170
    G.stroke(Sk(p.cl, yt - p.hh).L(272, yt - p.hh).H(p.cor - 4, (yt + ym) / 2, 0.58).V(272, ym + p.hh, 0.58)
             .L(p.cl, ym + p.hh))


@g('thorn', 0xFE)
def _thorn(G, c):
    p = P(c)
    G.line(p.l, p.dt, p.l, p.at)
    G.stroke(bowl_R(p, p.l, p.xt, p.xb, p.or_), prof=taper(start=JOIN, end=JOIN))


@g('Hbar', 0x126)
def _Hbar(G, c):
    base_fn('H')(G, c)
    G.line(24, 560, 526, 560, scale=0.85)


@g('hbar', 0x127)
def _hbar(G, c):
    base_fn('h')(G, c)
    G.line(30, 640, 300, 640, scale=0.85)


@g('Tbar', 0x166)
def _Tbar(G, c):
    base_fn('T')(G, c)
    G.line(150, 352, 400, 352, scale=0.9)


@g('tbar', 0x167)
def _tbar(G, c):
    base_fn('t')(G, c)
    G.line(120, 300, 330, 300, scale=0.85)


@g('Lslash', 0x141)
def _Lslash(G, c):
    base_fn('L')(G, c)
    p = P(c)
    G.line(p.cl - 70, 280, p.cl + 150, 470, scale=0.88)


@g('lslash', 0x142)
def _lslash(G, c):
    base_fn('l')(G, c)
    G.line(MID - 130, 330, MID + 120, 510, scale=0.88)


@g('Ldot', 0x13F)
def _Ldot(G, c):
    base_fn('L')(G, c)
    G.dot(380, 360, c.W * 1.3)


@g('ldot', 0x140)
def _ldot(G, c):
    p = P(c)
    xs = MID - 70
    G.stroke(Sk(xs - 110, p.at - 2).L(xs, p.at - 2).L(xs, 152).V(xs + 110, p.xb + 2, 0.6, 0.55)
             .L(xs + 170, p.xb + 4), prof=lift())
    G.dot(440, 360, c.W * 1.3)


@g('kgreenlandic', 0x138)
def _kra(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.st)
    G.stroke(Sk(p.or_ - 18, p.st).L(p.l + 8, 170), prof=taper(end=(0.7, 120)))
    G.stroke(Sk(p.l + 140, 290).L(p.or_ - 4, p.sb), prof=taper(start=(0.7, 100)))


@g('Eng', 0x14A)
def _Eng(G, c):
    p = P(c)
    G.line(p.cl, p.sb, p.cl, p.ct)
    G.stroke(Sk(p.cl, CH - 200).T(MID + 10, p.cot, 64, 0, 0.42, 0.5).H(p.cr, CH - 260, 0.58).L(p.cr, 0)
             .V(MID + 20, -140 + p.hh, 0.56, 0.56).T(170, -100, 180, 140, 0.4, 0.3), prof=taper(start=JOIN, end=LIFT))


@g('eng', 0x14B)
def _eng(G, c):
    p = P(c)
    G.line(p.l, p.sb, p.l, p.st)
    G.stroke(Sk(p.l, XH - 165).T(p.l + 0.54 * (p.r - p.l), p.xt, 64, 0, 0.42, 0.5)
             .H(p.r, p.xt - (p.r - p.l) * 0.46 * 1.05, 0.58).L(p.r, -60).V(MID + 20, p.dtr, 0.56, 0.56)
             .T(150, DE + 70, 180, 140, 0.4, 0.3), prof=taper(start=JOIN, end=LIFT))


@g('longs', 0x17F)
def _longs(G, c):
    p = P(c)
    xs = 232
    G.stroke(Sk(xs, p.sb).L(xs, AS - 175).V(xs + 120, AS + OV - p.hh, 0.58, 0.55)
             .T(p.or_ + 6, AS - 70, 0, -38, 0.36, 0.3), prof=lift())


@g('IJ', 0x132)
def _IJ(G, c):
    p = P(c)
    k = 0.85
    G.line(150, p.sb, 150, p.ct, scale=k)
    G.stroke(Sk(400, p.ct).L(400, 200).V(300, -OV + p.hh * k, 0.58, 0.58).T(210, 100, 180, 130, 0.42, 0.3), scale=k)


@g('ij', 0x133)
def _ij(G, c):
    p = P(c)
    k = 0.85
    G.line(150, p.sb, 150, p.st, scale=k)
    G.dot(150, XH + 200, c.W * 1.1)
    G.stroke(Sk(400, p.st).L(400, -50).V(290, p.dtr, 0.6, 0.56).T(190, DE + 70, 180, 140, 0.4, 0.3), scale=k)
    G.dot(400, XH + 200, c.W * 1.1)


@g('napostrophe', 0x149)
def _napos(G, c):
    p = P(c)
    k = 0.9
    hw = p.hw * k
    l = 210 + hw
    G.line(l, p.sb, l, p.st, scale=k)
    G.stroke(n_arch(p, l, 490 - hw, apex=0.56), prof=taper(start=JOIN, scale=k))
    G.stroke(Sk(90, CH + 10).L(70, 480), prof=taper(end=(0.6, 200)), scale=0.9)


@g('a.single', 0x251)      # ɑ (pinyin a, single-storey)
def _asingle(G, c):
    p = P(c)
    G.line(p.r, p.sb, p.r, p.st)
    G.stroke(bowl_L(p, p.r, p.xt, p.xb, p.ol), prof=taper(start=JOIN, end=JOIN))


@g('g.single', 0x261)      # ɡ script g
def _gsingle(G, c):
    base_fn('g')(G, c)


# ================================================================== Latin-1 symbols
@g('exclamdown', 0xA1)
def _exclamdown(G, c):
    p = P(c)
    d = latin._dotd(c)
    G.stroke(Sk(MID, XH - 220).L(MID, DE + p.hh + 10), prof=taper(start=(0.72, 300)))
    G.dot(MID, XH - d * 0.42, d)


@g('questiondown', 0xBF)
def _questiondown(G, c):
    p = P(c)
    d = latin._dotd(c)
    G.stroke(Sk(p.cor - 22, -60).T(MID - 2, DE + OV + p.hh, 250, 180, 0.36, 0.46)
             .H(p.col + 10, 0, 0.58, 0.56).T(MID, 170, 90, 70, 0.5, 0.3).L(MID + 6, 260),
             prof=taper(start=LIFT, end=(0.8, 100)))
    G.dot(MID + 4, XH - d * 0.42, d)


@g('cent', 0xA2)
def _cent(G, c):
    base_fn('c')(G, c)
    G.line(MID + 10, XH + 110, MID + 10, -100, scale=0.85)


@g('sterling', 0xA3)
def _sterling(G, c):
    p = P(c)
    G.stroke(Sk(p.cor - 12, CH - 140).T(330, p.cot, 120, 180, 0.35, 0.45).T(200, CH - 160, 180, 270, 0.45, 0.5)
             .L(200, 230).T(110, p.hh + 4, 270, 200, 0.5, 0.4), prof=taper(start=LIFT))
    G.line(110, p.hh, p.cor + 6, p.hh)
    G.line(92, 360, 380, 360)


@g('currency', 0xA4)
def _currency(G, c):
    k = 0.8
    G.stroke(loop(MID, 480, 120, 145, 405, 0.58), scale=k)
    for dx, dy in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        G.line(MID + dx * 150, 300 + dy * 150, MID + dx * 215, 300 + dy * 215, scale=k)


@g('yen', 0xA5)
def _yen(G, c):
    p = P(c)
    G.stroke(Sk(p.col - 4, p.ct).L(MID, 330).L(p.cor + 4, p.ct))
    G.line(MID, p.sb, MID, 330)
    G.line(110, 300, 440, 300, scale=0.9)
    G.line(110, 160, 440, 160, scale=0.9)


@g('brokenbar', 0xA6)
def _brokenbar(G, c):
    G.line(MID, -205, MID, 220)
    G.line(MID, 380, MID, 805)


@g('section', 0xA7)
def _section(G, c):
    p = P(c)
    k = 0.85
    G.stroke(Sk(p.or_ - 20, CH - 70).T(MID, p.cot, 124, 180, 0.32, 0.42).H(p.ol + 20, CH - 150, 0.56, 0.6)
             .V(MID, 400, 0.6, 0.6).H(p.or_ - 10, 280, 0.6, 0.6).V(MID, 160, 0.6, 0.6), scale=k)
    G.stroke(Sk(MID, 400).H(p.ol + 10, 280, 0.6, 0.6).V(MID, 160, 0.6, 0.6).H(p.or_ - 20, 40, 0.6, 0.6)
             .V(MID, -110 + p.hh, 0.6, 0.6).T(p.ol + 20, -40, 180, 124, 0.42, 0.32), scale=k)


@g('dieresis', 0xA8)
def _dieresis(G, c):
    m_dier(G, c, MID, LC_BASE)


@g('macron', 0xAF)
def _macron(G, c):
    m_macron(G, c, MID, LC_BASE)


@g('acute', 0xB4)
def _acute(G, c):
    m_acute(G, c, MID, LC_BASE)


@g('cedilla', 0xB8)
def _cedilla(G, c):
    m_cedilla(G, c, MID)


@g('copyright', 0xA9)
def _copyright(G, c):
    k = 0.7
    G.stroke(loop(MID, 640, 40, 40, 510, 0.56), scale=k)
    G.stroke(Sk(375, 440).T(MID + 6, 490, 128, 180, 0.32, 0.45).H(170, 340, 0.6, 0.6).V(MID + 6, 190, 0.6, 0.6)
             .T(375, 240, 0, 50, 0.45, 0.32), scale=k)


@g('registered', 0xAE)
def _registered(G, c):
    k = 0.7
    G.stroke(loop(MID, 640, 40, 40, 510, 0.56), scale=k)
    G.stroke(Sk(200, 180).L(200, 490).L(300, 490).H(370, 420, 0.56).V(300, 350, 0.56).L(200, 350), scale=k)
    G.line(290, 350, 370, 180, scale=k)


def _small(G, c, name, s, dx, dy, k=0.82):
    """Draw latin glyph `name` scaled by s (skeleton), pen ~k*W."""
    d = dict(c.__dict__)
    d['W'], d['H'] = c.W * k / s, c.H * k / s
    c2 = Ctx(**d)
    n0 = len(G.contours)
    base_fn(name)(G, c2)
    new = G.contours[n0:]
    del G.contours[n0:]
    for cc in new:
        G.contours.append(transform_contour(cc, (s, 0, 0, s, dx, dy)))


@g('ordfeminine', 0xAA)
def _ordf(G, c):
    _small(G, c, 'a', 0.6, 110, 400)
    G.line(140, 340, 410, 340, scale=0.7)


@g('ordmasculine', 0xBA)
def _ordm(G, c):
    _small(G, c, 'o', 0.6, 110, 400)
    G.line(140, 340, 410, 340, scale=0.7)


@g('guillemotleft', 0xAB)
def _gleft(G, c):
    for dx in (-80, 80):
        G.stroke(Sk(MID + dx + 75, AXIS + 140).L(MID + dx - 75, AXIS).L(MID + dx + 75, AXIS - 140), scale=0.92)


@g('guillemotright', 0xBB)
def _gright(G, c):
    for dx in (-80, 80):
        G.stroke(Sk(MID + dx - 75, AXIS + 140).L(MID + dx + 75, AXIS).L(MID + dx - 75, AXIS - 140), scale=0.92)


@g('logicalnot', 0xAC)
def _lnot(G, c):
    G.stroke(Sk(92, AXIS + 80).L(450, AXIS + 80).L(450, AXIS - 110))


@g('uni00AD', 0xAD)
def _shy(G, c):
    latin.REG['hyphen'][2](G, c)


@g('degree', 0xB0)
def _degree(G, c):
    G.stroke(loop(MID, 690, 470, 165, 385, 0.56), scale=0.8)


@g('plusminus', 0xB1)
def _plusminus(G, c):
    G.line(92, AXIS + 60, 458, AXIS + 60)
    G.line(MID, AXIS + 60 - 160, MID, AXIS + 60 + 160)
    G.line(92, AXIS - 200, 458, AXIS - 200)


@g('mu', 0xB5, 0x3BC)
def _mu(G, c):
    p = P(c)
    G.line(p.r, p.sb, p.r, p.st)
    G.stroke(Sk(p.l, DE + p.hh).L(p.l, p.st))
    G.stroke(Sk(p.l, 250).V(p.l + 0.46 * (p.r - p.l), p.xb, 0.58).T(p.r, 165, 0, 64, 0.5, 0.42),
             prof=taper(end=JOIN))


@g('paragraph', 0xB6)
def _paragraph(G, c):
    k = 0.9
    G.stroke(Sk(330, 330).L(250, 330).H(90, 510, 0.56, 0.56).V(250, CH - 40, 0.56, 0.56).L(450, CH - 40), scale=k)
    G.line(330, -150, 330, CH - 40, scale=k)
    G.line(440, -150, 440, CH - 40, scale=k)


@g('periodcentered', 0xB7)
def _periodcentered(G, c):
    d = latin._dotd(c)
    G.dot(MID, AXIS + 20, d)


def _sup(G, c, name):
    _small(G, c, name, 0.56, 121, 380, k=0.78)


def _sub(G, c, name):
    _small(G, c, name, 0.56, 121, -150, k=0.78)


for i, nm in enumerate(['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']):
    sup_cp = {0: 0x2070, 1: 0xB9, 2: 0xB2, 3: 0xB3}.get(i, 0x2070 + i)
    REG[f'{nm}.sup'] = ([sup_cp], ADV, (lambda n: (lambda G, c: _sup(G, c, n)))(nm))
    REG[f'{nm}.sub'] = ([0x2080 + i], ADV, (lambda n: (lambda G, c: _sub(G, c, n)))(nm))
REG['n.sup'] = ([0x207F], ADV, lambda G, c: _sup(G, c, 'n'))
REG['plus.sup'] = ([0x207A], ADV, lambda G, c: _small(G, c, 'plus', 0.56, 121, 460, k=0.78))
REG['minus.sup'] = ([0x207B], ADV, lambda G, c: _small(G, c, 'hyphen', 0.56, 121, 460, k=0.78))


def _frac(num, den):
    def fn(G, c):
        _small(G, c, num, 0.48, 40, 360, k=0.72)
        _small(G, c, den, 0.48, 250, -20, k=0.72)
        G.line(430, 640, 120, 60, scale=0.72)
    return fn


REG['onequarter'] = ([0xBC], ADV, _frac('one', 'four'))
REG['onehalf'] = ([0xBD], ADV, _frac('one', 'two'))
REG['threequarters'] = ([0xBE], ADV, _frac('three', 'four'))


@g('multiply', 0xD7)
def _multiply(G, c):
    r = 150
    G.line(MID - r, AXIS - r, MID + r, AXIS + r)
    G.line(MID - r, AXIS + r, MID + r, AXIS - r)


@g('divide', 0xF7)
def _divide(G, c):
    G.line(92, AXIS, 458, AXIS)
    d = c.W * 1.25
    G.dot(MID, AXIS + 170, d)
    G.dot(MID, AXIS - 170, d)


# ================================================================== general punctuation
@g('endash', 0x2013)
def _endash(G, c):
    G.line(60, AXIS, 490, AXIS)


@g('emdash', 0x2014, 0x2015)
def _emdash(G, c):
    t = c.H
    G.rect(-2, AXIS - t / 2, 552, AXIS + t / 2)


@g('figuredash', 0x2012, 0x2010, 0x2011)
def _figdash(G, c):
    latin.REG['hyphen'][2](G, c)


@g('minus', 0x2212)
def _minus(G, c):
    G.line(92, AXIS, 458, AXIS)


def _qcomma(G, c, x, y, flip=False, k=1.0):
    d = c.W * 1.22 * k
    if not flip:   # 9-shape (closing / ’)
        G.dot(x, y, d)
        G.stroke(Sk(x + d * 0.22, y - 4).T(x - 52, y - 175, 270, 228, 0.5, 0.3),
                 prof=taper(start=(0.95, 10), end=(0.55, 120)), scale=k)
    else:          # 6-shape (opening / ‘)
        G.dot(x, y, d)
        G.stroke(Sk(x - d * 0.22, y + 4).T(x + 52, y + 175, 90, 48, 0.5, 0.3),
                 prof=taper(start=(0.95, 10), end=(0.55, 120)), scale=k)


@g('quoteleft', 0x2018)
def _ql(G, c):
    _qcomma(G, c, MID, 520, flip=True)


@g('quoteright', 0x2019)
def _qr(G, c):
    _qcomma(G, c, MID, CH - 10)


@g('quotesinglbase', 0x201A)
def _qsb(G, c):
    _qcomma(G, c, MID, 60)


@g('quotedblleft', 0x201C)
def _qdl(G, c):
    _qcomma(G, c, MID - 95, 520, flip=True, k=0.95)
    _qcomma(G, c, MID + 95, 520, flip=True, k=0.95)


@g('quotedblright', 0x201D)
def _qdr(G, c):
    _qcomma(G, c, MID - 95, CH - 10, k=0.95)
    _qcomma(G, c, MID + 95, CH - 10, k=0.95)


@g('quotedblbase', 0x201E)
def _qdb(G, c):
    _qcomma(G, c, MID - 95, 60, k=0.95)
    _qcomma(G, c, MID + 95, 60, k=0.95)


@g('dagger', 0x2020)
def _dagger(G, c):
    G.line(MID, -120, MID, CH + 30)
    G.line(110, 470, 440, 470)


@g('daggerdbl', 0x2021)
def _daggerdbl(G, c):
    G.line(MID, -120, MID, CH + 30)
    G.line(110, 500, 440, 500)
    G.line(110, 140, 440, 140)


@g('perthousand', 0x2030)
def _perthousand(G, c):
    k = 0.66
    G.stroke(loop(150, 690, 470, 70, 230, 0.62), scale=k)
    G.stroke(loop(150, 230, 10, 50, 230, 0.62), scale=k)
    G.stroke(loop(400, 230, 10, 320, 500, 0.62), scale=k)
    G.line(440, 690, 110, 230, scale=k)


@g('minute', 0x2032)
def _minute(G, c):
    G.stroke(Sk(MID + 40, CH + 20).L(MID - 40, 470), prof=taper(end=(0.6, 200)))


@g('second', 0x2033)
def _second(G, c):
    for dx in (-80, 80):
        G.stroke(Sk(MID + 40 + dx, CH + 20).L(MID - 40 + dx, 470), prof=taper(end=(0.6, 200)))


@g('exclamdbl', 0x203C)
def _exclamdbl(G, c):
    d = latin._dotd(c)
    for dx in (-100, 100):
        G.stroke(Sk(MID + dx, CH - c.H / 2).L(MID + dx, 235), prof=taper(end=(0.72, 300)), scale=0.92)
        G.dot(MID + dx, d * 0.42, d * 0.92)


@g('fraction', 0x2044)
def _fraction(G, c):
    G.line(470, 700, 80, -20)


@g('Euro', 0x20AC)
def _euro(G, c):
    p = P(c)
    sk = (Sk(p.cor - 6, CH - 128).T(MID + 40, p.cot, 126, 180, 0.32, 0.45).H(p.col + 60, CH / 2, 0.6, 0.6)
          .V(MID + 40, -OV + p.hh, 0.6, 0.6).T(p.cor - 4, 128, 0, 52, 0.45, 0.32))
    G.stroke(sk, prof=taper(start=LIFT, end=LIFT))
    G.line(50, 410, 340, 410, scale=0.88)
    G.line(50, 270, 340, 270, scale=0.88)


@g('trademark', 0x2122)
def _trademark(G, c):
    k = 0.62
    G.line(40, CH - 20, 230, CH - 20, scale=k)
    G.line(135, CH - 20, 135, 380, scale=k)
    G.stroke(Sk(280, 380).L(280, CH - 20).L(390, 520).L(500, CH - 20).L(500, 380), scale=k)


@g('uni2103', 0x2103)      # ℃ degree Celsius
def _celsius(G, c):
    k = 0.75
    G.stroke(loop(118, 690, 540, 50, 186, 0.56), scale=k)
    G.stroke(Sk(520, CH - 140).T(390, CH + OV - 30, 126, 180, 0.32, 0.45).H(240, CH / 2 - 20, 0.6, 0.6)
             .V(390, 0, 0.6, 0.6).T(522, 110, 0, 52, 0.45, 0.32), scale=k)


@g('uni2116', 0x2116)      # №
def _numero(G, c):
    k = 0.72
    G.stroke(Sk(60, 20).L(60, CH - 30).L(290, 20).L(290, CH - 30), scale=k)
    G.stroke(loop(420, 440, 170, 340, 500, 0.6), scale=k)
    G.line(340, 70, 500, 70, scale=k)


# ================================================================== generate accented letters
TARGET = list(range(0xC0, 0x100)) + list(range(0x100, 0x180)) + list(range(0x1CD, 0x1DD)) + \
    [0x1F4, 0x1F5, 0x1F8, 0x1F9, 0x218, 0x219, 0x21A, 0x21B, 0x1E3E, 0x1E3F, 0x1EBC, 0x1EBD]


def _register_accented():
    by_char = {}
    for reg in (latin.REG, REG):
        for name, (unis, w, fn) in reg.items():
            for u in unis:
                by_char.setdefault(chr(u), name)
    for cp in TARGET:
        ch = chr(cp)
        if ch in by_char:
            continue
        dec = decompose_full(ch)
        if not dec:
            continue
        base, marks = dec
        if any(m not in MARKS for m in marks):
            continue
        bname = by_char.get(base)
        if base == 'i' and any(m not in BELOW for m in marks):
            bname = 'dotlessi'
        if base == 'j' and any(m not in BELOW for m in marks):
            bname = 'dotlessj'
        if not bname:
            continue
        name = gname(ch)
        if name in REG or name in latin.REG:
            name = 'uni%04X' % cp
        REG[name] = ([cp], ADV, compose(bname, marks))
        by_char[ch] = name


_register_accented()
