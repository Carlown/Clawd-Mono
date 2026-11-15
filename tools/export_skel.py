"""Export pen skeletons (Regular master) for the specimen's writing animation."""
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build
from glyphlib import Glyph, RECORD
from geom import PLAN, PLAN_MODE


def export(text, out):
    jobs = {}
    for j in build.latin_jobs() + build.cjk_jobs(text):
        for u in j[1]:
            jobs[chr(u)] = j
    res = {}
    ctx = build.CTX['Regular']
    for ch in dict.fromkeys(text):
        if ch not in jobs or ch in res:
            continue
        name, unis, w, fn = jobs[ch]
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
        strokes = []
        for it in RECORD['items']:
            pts = [[round(x, 1), round(y, 1)] for x, y in it['pts']]
            strokes.append({'p': pts, 'w': round(it['w'], 1), 'h': round(it['h'], 1)})
        res[ch] = {'adv': w, 'strokes': strokes}
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, separators=(',', ':'))
    print(len(res), 'glyphs ->', out, os.path.getsize(out), 'bytes')


if __name__ == '__main__':
    export(sys.argv[1], sys.argv[2])
