"""Full-width CJK punctuation (simplified-Chinese positions) and full-width
forms, drawn with the CJK pen."""
import math
from glyphlib import Sk, taper, Ctx
from geom import polygon, signed_area, reverse_contour

REG = {}
ADV = 1100
# ideographic em box in font units (MMAH em mapped by cjk.SCALE)
EL, EB, EM = 61, -137, 978


def nx(x):
    return EL + x * EM / 1000


def ny(y):
    return EB + (y + 120) * EM / 1000


def g(name, *uni, w=ADV):
    def deco(fn):
        REG[name] = (list(uni), w, fn)
        return fn
    return deco


def cpen(c):
    return (c.Wc / 2, c.Hc / 2)


def cctx(c):
    """Context whose Latin pen is the CJK pen (for borrowed Latin shapes)."""
    d = dict(c.__dict__)
    d['W'], d['H'] = c.Wc * 1.08, c.Hc * 1.08
    return Ctx(**d)


def latin_fn(name):
    import latin
    for reg in (latin.REG,):
        if name in reg:
            return reg[name][2]
    try:
        import latin_ext
        if name in latin_ext.REG:
            return latin_ext.REG[name][2]
    except ImportError:
        pass
    return None


def borrow(G, c, name, dx, cjkpen=True, dy=0):
    fn = latin_fn(name)
    n0 = len(G.contours)
    fn(G, cctx(c) if cjkpen else c)
    new = G.contours[n0:]
    del G.contours[n0:]
    from geom import transform_contour
    for cc in new:
        G.contours.append(transform_contour(cc, (1, 0, 0, 1, dx, dy)))


def dot(G, c, x, y, k=1.5):
    d = c.Wc * k
    G.ellipse(x, y, d / 2, d / 2 * (c.Hc / c.Wc) ** 0.5)


def comma_shape(G, c, x, y):
    dot(G, c, x, y, 1.55)
    r = c.Wc * 0.75
    G.stroke(Sk(x + r * 0.45, y - 4).T(x - 70, y - 215, 270, 228, 0.5, 0.3),
             prof=taper(start=(0.95, 10), end=(0.5, 150)), pen=cpen(c))


@g('uni3001', 0x3001)          # 、
def _dun(G, c):
    G.stroke(Sk(nx(120), ny(205)).T(nx(285), ny(10), 315, 300, 0.4, 0.4),
             prof=taper(start=(0.55, 150)), pen=cpen(c), scale=1.15)


@g('uni3002', 0x3002)          # 。
def _ju(G, c):
    r = 108
    cx, cy = nx(190), ny(85)
    sk = Sk(cx, cy + r).H(cx + r, cy, 0.552).V(cx, cy - r, 0.552).H(cx - r, cy, 0.552).V(cx, cy + r, 0.552).Z()
    G.stroke(sk, pen=cpen(c))


@g('uniFF0C', 0xFF0C)          # ，
def _comma(G, c):
    comma_shape(G, c, nx(235), ny(150))


@g('uniFF0E', 0xFF0E)          # ．
def _period(G, c):
    dot(G, c, nx(220), ny(70))


@g('uniFF1A', 0xFF1A)          # ：
def _colon(G, c):
    dot(G, c, nx(250), ny(560))
    dot(G, c, nx(250), ny(80))


@g('uniFF1B', 0xFF1B)          # ；
def _semi(G, c):
    dot(G, c, nx(250), ny(560))
    comma_shape(G, c, nx(250), ny(140))


@g('uniFF1F', 0xFF1F)          # ？
def _quest(G, c):
    borrow(G, c, 'question', nx(250) - 275, dy=-12)


@g('uniFF01', 0xFF01)          # ！
def _excl(G, c):
    borrow(G, c, 'exclam', nx(250) - 275, dy=-12)


def paren(G, c, opening):
    top, bot = ny(850), ny(-90)
    xm = (top + bot) / 2
    if opening:
        xo, xi = nx(930), nx(745)
        sk = Sk(xo, top).T(xi, xm, 225, 270, 0.42, 0.55).T(xo, bot, 270, 315, 0.55, 0.42)
    else:
        xo, xi = nx(70), nx(255)
        sk = Sk(xo, top).T(xi, xm, 315, 270, 0.42, 0.55).T(xo, bot, 270, 225, 0.55, 0.42)
    G.stroke(sk, pen=cpen(c))


reg_items = []


def reg(name, uni, fn):
    REG[name] = ([uni], ADV, fn)


reg('uniFF08', 0xFF08, lambda G, c: paren(G, c, True))
reg('uniFF09', 0xFF09, lambda G, c: paren(G, c, False))


def tortoise(G, c, opening):
    top, bot = ny(852), ny(-92)
    if opening:
        a, b = nx(950), nx(800)
        sk = Sk(a, top).L(b, top - 110).L(b, bot + 110).L(a, bot)
    else:
        a, b = nx(50), nx(200)
        sk = Sk(a, top).L(b, top - 110).L(b, bot + 110).L(a, bot)
    G.stroke(sk, pen=cpen(c))


reg('uni3014', 0x3014, lambda G, c: tortoise(G, c, True))
reg('uni3015', 0x3015, lambda G, c: tortoise(G, c, False))


def square_br(G, c, opening):
    top, bot = ny(846), ny(-86)
    if opening:
        a, b = nx(940), nx(760)
    else:
        a, b = nx(60), nx(240)
    G.stroke(Sk(a, top).L(b, top).L(b, bot).L(a, bot), pen=cpen(c))


reg('uniFF3B', 0xFF3B, lambda G, c: square_br(G, c, True))
reg('uniFF3D', 0xFF3D, lambda G, c: square_br(G, c, False))


def lenticular(G, c, opening, white=False):
    top, bot = ny(846), ny(-86)
    ym = (top + bot) / 2
    t = c.Wc
    if opening:
        x0, x1, xi = nx(690) - t * 0.4, nx(965), nx(800) + t * 0.2
    else:
        x0, x1, xi = nx(310) + t * 0.4, nx(35), nx(200) - t * 0.2
    if white:
        sk = Sk(x1, top).L(x0, top).L(x0, bot).L(x1, bot)
        G.stroke(sk, pen=cpen(c))
        sgn = 1 if opening else -1
        G.stroke(Sk(x1, top).Tc(x0 + sgn * 70, ym, 270, 0.35, 0.5) if False else
                 Sk(x1 - sgn * 10, top - 4).T(xi, ym, 270 - sgn * 50 if opening else 270 + 50, 270, 0.4, 0.5)
                 .T(x1 - sgn * 10, bot + 4, 270, 270 + sgn * 50 if opening else 270 - 50, 0.5, 0.4),
                 pen=cpen(c), scale=0.8)
        return
    r = c.Wc * 0.4
    pts = [(x1, top, True), (x0, top, True), (x0, bot, True), (x1, bot, True),
           (xi, ym, False)]
    if signed_area(pts) > 0:
        pts = reverse_contour(pts)
    G.contours.append(pts)


reg('uni3010', 0x3010, lambda G, c: lenticular(G, c, True))
reg('uni3011', 0x3011, lambda G, c: lenticular(G, c, False))
reg('uni3016', 0x3016, lambda G, c: lenticular(G, c, True, True))
reg('uni3017', 0x3017, lambda G, c: lenticular(G, c, False, True))


def angle(G, c, opening, double):
    top, bot = ny(846), ny(-86)
    ym = (top + bot) / 2
    if opening:
        tips = [nx(560)] if not double else [nx(545), nx(700)]
        out = nx(950)
        for tx in tips:
            G.stroke(Sk(out - (nx(700) - tx if double else 0), top).L(tx, ym).L(out - (nx(700) - tx if double else 0), bot),
                     pen=cpen(c))
    else:
        tips = [nx(440)] if not double else [nx(455), nx(300)]
        out = nx(50)
        for tx in tips:
            G.stroke(Sk(out + (tx - nx(300) if double else 0), top).L(tx, ym).L(out + (tx - nx(300) if double else 0), bot),
                     pen=cpen(c))


reg('uni3008', 0x3008, lambda G, c: angle(G, c, True, False))
reg('uni3009', 0x3009, lambda G, c: angle(G, c, False, False))
reg('uni300A', 0x300A, lambda G, c: angle(G, c, True, True))
reg('uni300B', 0x300B, lambda G, c: angle(G, c, False, True))


def corner(G, c, opening, white):
    if opening:
        a, b, top, low = nx(955), nx(690), ny(846), ny(200)
        G.stroke(Sk(a, top).L(b, top).L(b, low), pen=cpen(c))
        if white:
            G.stroke(Sk(a, top - 130).L(b + 130, top - 130).L(b + 130, low), pen=cpen(c), scale=0.8)
            G.stroke(Sk(a, top).L(a, top - 130), pen=cpen(c), scale=0.8)
            G.stroke(Sk(b, low).L(b + 130, low), pen=cpen(c), scale=0.8)
    else:
        a, b, bot, high = nx(45), nx(310), ny(-86), ny(560)
        G.stroke(Sk(a, bot).L(b, bot).L(b, high), pen=cpen(c))
        if white:
            G.stroke(Sk(a, bot + 130).L(b - 130, bot + 130).L(b - 130, high), pen=cpen(c), scale=0.8)
            G.stroke(Sk(a, bot).L(a, bot + 130), pen=cpen(c), scale=0.8)
            G.stroke(Sk(b, high).L(b - 130, high), pen=cpen(c), scale=0.8)


reg('uni300C', 0x300C, lambda G, c: corner(G, c, True, False))
reg('uni300D', 0x300D, lambda G, c: corner(G, c, False, False))
reg('uni300E', 0x300E, lambda G, c: corner(G, c, True, True))
reg('uni300F', 0x300F, lambda G, c: corner(G, c, False, True))


@g('uniFF5E', 0xFF5E, 0x301C)  # ～ 〜
def _wave(G, c):
    y = ny(380)
    G.stroke(Sk(nx(70), y - 30).T(nx(300), y + 70, 60, 0, 0.4, 0.45).T(nx(700), y - 70, 0, 0, 0.55, 0.55)
             .T(nx(930), y + 30, 0, 60, 0.45, 0.4), pen=cpen(c))


@g('uni3007', 0x3007)          # 〇
def _ling(G, c):
    r = 425 - c.Wc / 2
    cx, cy = 550, 352
    sk = Sk(cx, cy + r).H(cx + r, cy, 0.56).V(cx, cy - r, 0.56).H(cx - r, cy, 0.56).V(cx, cy + r, 0.56).Z()
    G.stroke(sk, pen=cpen(c))


@g('uni3003', 0x3003)          # 〃
def _ditto(G, c):
    for dx in (0, 150):
        G.stroke(Sk(nx(330) + dx, ny(700)).T(nx(420) + dx, ny(520), 300, 290, 0.4, 0.4),
                 prof=taper(end=(0.6, 120)), pen=cpen(c))


@g('uni30FB', 0x30FB)          # ・
def _nakaguro(G, c):
    dot(G, c, 550, ny(380), 1.7)


@g('uni3000', 0x3000)          # ideographic space
def _idsp(G, c):
    pass


@g('uniFFE5', 0xFFE5)          # ￥
def _yen(G, c):
    k = 1.0
    G.stroke(Sk(nx(200), ny(760)).L(550, ny(380)).L(nx(800), ny(760)), pen=cpen(c))
    G.stroke(Sk(550, ny(380)).L(550, ny(0)), pen=cpen(c))
    G.stroke(Sk(nx(290), ny(360)).L(nx(710), ny(360)), pen=cpen(c))
    G.stroke(Sk(nx(290), ny(200)).L(nx(710), ny(200)), pen=cpen(c))


# ---------------------------------------------------------------- full-width forms
SPECIAL = {0xFF01, 0xFF08, 0xFF09, 0xFF0C, 0xFF0E, 0xFF1A, 0xFF1B, 0xFF1F, 0xFF3B, 0xFF3D, 0xFF5E}


def _fw(src):
    def fn(G, c):
        borrow(G, c, src, 275, cjkpen=False)
    return fn


def register_fullwidth():
    import latin
    try:
        import latin_ext
        ext = latin_ext.REG
    except ImportError:
        ext = {}
    by_uni = {}
    for reg_ in (latin.REG, ext):
        for name, (unis, w, fn) in reg_.items():
            for u in unis:
                by_uni[u] = name
    for cp in range(0xFF01, 0xFF5F):
        if cp in SPECIAL:
            continue
        half = cp - 0xFEE0
        if half in by_uni:
            REG['uni%04X' % cp] = ([cp], ADV, _fw(by_uni[half]))


register_fullwidth()
