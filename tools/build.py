"""Build Clawd Mono.

python tools/build.py test [chars]   -> Latin(+symbols) + a few CJK, static masters
python tools/build.py all            -> full family (see release.py)
"""
import os
import sys
import time
import pickle
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from glyphlib import Glyph, Ctx
from geom import PLAN, PLAN_MODE, reverse_contour
import fontout

MASTERS = {
    # stem W, horizontal H (Latin);  Wc/Hc for CJK strokes
    'Thin': dict(wght=100, W=22, H=20, Wc=22, Hc=20),
    'Regular': dict(wght=400, W=78, H=67, Wc=78, Hc=67),
    'ExtraBold': dict(wght=800, W=138, H=116, Wc=138, Hc=116),
}
ORDER = ['Regular', 'Thin', 'ExtraBold']   # Regular first: it records the plan
CTX = {m: Ctx(**v) for m, v in MASTERS.items()}

SAMPLE_CJK = "你好我是克劳德爪迹等宽永和九年岁在癸丑暮春之初会于稽山阴兰亭字体中文汉写代码一二三四五六七八九十的了是不人有这个上们来到"


def notdef(ctx):
    nd = Glyph('.notdef', ctx)
    nd.rpoly([(80, 0), (80, 690), (470, 690), (470, 0)], 20)
    inner = Glyph('nd2', ctx)
    inner.rpoly([(80 + ctx.W, ctx.H), (80 + ctx.W, 690 - ctx.H), (470 - ctx.W, 690 - ctx.H),
                 (470 - ctx.W, ctx.H)], 8)
    nd.contours.append(reverse_contour(inner.contours[0]))
    return nd.contours


def latin_jobs(which=('latin', 'symbols')):
    jobs = []
    import latin
    regs = [latin.REG]
    import latin_ext
    regs.append(latin_ext.REG)
    import greek_math
    regs.append(greek_math.REG)
    if 'symbols' in which:
        import symbols
        regs.append(symbols.REG)
        import cjk_punct
        regs.append(cjk_punct.REG)
    for reg in regs:
        for name, (unis, w, fn) in reg.items():
            jobs.append((name, unis, w, fn))
    return jobs


def cjk_jobs(chars):
    import cjk
    data = cjk.data()
    jobs = []
    seen = set()
    for ch in chars:
        if ch in data and ch not in seen:
            seen.add(ch)
            jobs.append((cjk.glyph_name(ch), [ord(ch)], cjk.ADV, ('cjk', ch)))
    return jobs


def run_job(job):
    name, unis, w, fn = job
    PLAN.clear()
    res = {}
    for m in ORDER:
        ctx = CTX[m]
        PLAN_MODE['record'] = (m == 'Regular')
        G = Glyph(name, ctx, w)
        if isinstance(fn, tuple) and fn[0] == 'cjk':
            import cjk
            cjk.draw(G, ctx, fn[1])
        else:
            fn(G, ctx)
        res[m] = G.contours
    bad = [m for m in ('Thin', 'ExtraBold') if not compatible(res['Regular'], res[m])]
    return name, unis, w, res, bad


def compatible(ca, cb):
    if len(ca) != len(cb):
        return False
    for x, y in zip(ca, cb):
        if len(x) != len(y) or any(p[2] != q[2] for p, q in zip(x, y)):
            return False
    return True


def build_all(jobs, procs=1, chunks=8):
    t = time.time()
    if procs > 1:
        # functions aren't picklable across processes for latin; only CJK goes to the pool
        cj = [j for j in jobs if isinstance(j[3], tuple)]
        lj = [j for j in jobs if not isinstance(j[3], tuple)]
        out = [run_job(j) for j in lj]
        with Pool(procs) as pool:
            out += pool.map(run_job, cj, chunksize=chunks)
    else:
        out = [run_job(j) for j in jobs]
    bad = [(o[0], o[4]) for o in out if o[4]]
    if bad:
        print('INCOMPATIBLE:', bad[:30], '...' if len(bad) > 30 else '')
    print(f'built {len(out)} glyphs in {time.time() - t:.1f}s')
    return out


def masters_from(out):
    order = ['.notdef']
    cmap = {}
    masters = {m: {'.notdef': (notdef(CTX[m]), 550)} for m in MASTERS}
    for name, unis, w, res, bad in out:
        order.append(name)
        for u in unis:
            cmap[u] = name
        for m in MASTERS:
            masters[m][name] = (res[m], w)
    return order, cmap, masters


def test_build(extra_chars=SAMPLE_CJK, which=('latin', 'symbols')):
    jobs = latin_jobs(which) + cjk_jobs(extra_chars)
    out = build_all(jobs, procs=4 if len(extra_chars) > 40 else 1)
    order, cmap, masters = masters_from(out)
    os.makedirs(os.path.join(ROOT, 'build', 'test'), exist_ok=True)
    for m in MASTERS:
        path = os.path.join(ROOT, 'build', 'test', f'test-{m}.ttf')
        fontout.build_font(order, masters[m], cmap, style=m, weight=MASTERS[m]['wght'], path=path)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'test'
    if cmd == 'test':
        test_build(sys.argv[2] if len(sys.argv) > 2 else SAMPLE_CJK)
