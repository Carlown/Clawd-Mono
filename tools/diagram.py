"""SVG construction diagrams for the specimen: outline + pen skeleton + pen
stamps + TrueType points, straight from the engine (Regular master)."""
import json
import math
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build
from glyphlib import Glyph, RECORD
from geom import PLAN, PLAN_MODE


def tt_to_svg(contours):
    out = []
    for c in contours:
        n = len(c)
        if n == 0:
            continue
        # start at an on-curve point
        start = next((i for i, p in enumerate(c) if p[2]), None)
        if start is None:
            a, b = c[0], c[1]
            first = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            pts = c[1:] + c[:1]
        else:
            first = c[start][:2]
            pts = c[start + 1:] + c[:start]
        d = [f'M{first[0]:.1f} {first[1]:.1f}']
        pend = None
        for x, y, on in pts + [(first[0], first[1], True)]:
            if on:
                if pend is None:
                    d.append(f'L{x:.1f} {y:.1f}')
                else:
                    d.append(f'Q{pend[0]:.1f} {pend[1]:.1f} {x:.1f} {y:.1f}')
                    pend = None
            else:
                if pend is not None:
                    mx, my = (pend[0] + x) / 2, (pend[1] + y) / 2
                    d.append(f'Q{pend[0]:.1f} {pend[1]:.1f} {mx:.1f} {my:.1f}')
                pend = (x, y)
        d.append('Z')
        out.append(''.join(d))
    return ' '.join(out)


def glyph_data(ch, master='Regular'):
    jobs = {}
    for j in build.latin_jobs() + build.cjk_jobs(ch):
        for u in j[1]:
            jobs[chr(u)] = j
    name, unis, w, fn = jobs[ch]
    ctx = build.CTX[master]
    PLAN.clear()
    PLAN_MODE['record'] = True
    RECORD['on'] = True
    RECORD['items'] = []
    G = Glyph(name, ctx, w)
    if isinstance(fn, tuple):
        import cjk
        cjk.draw(G, ctx, fn[1])
    else:
        fn(G, ctx)
    RECORD['on'] = False
    pts = [(round(x, 1), round(y, 1), on) for c in G.contours for x, y, on in c]
    return {
        'ch': ch, 'adv': w,
        'outline': tt_to_svg(G.contours),
        'points': [[x, y, 1 if on else 0] for x, y, on in pts],
        'skeleton': [{'p': [[round(x, 1), round(y, 1)] for x, y in it['pts']], 'w': round(it['w'], 1),
                      'h': round(it['h'], 1)} for it in RECORD['items']],
    }


if __name__ == '__main__':
    out = {}
    for ch in sys.argv[1]:
        out[ch] = glyph_data(ch)
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote', sys.argv[2], os.path.getsize(sys.argv[2]))
