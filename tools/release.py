"""Full build of Clawd Mono.

  python tools/release.py masters     # draw every glyph in all masters -> build/masters.pkl
  python tools/release.py vf          # variable TTF + WOFF2 from masters.pkl
  python tools/release.py statics     # static instances (overlaps removed)
  python tools/release.py all
"""
import os
import sys
import time
import array
import pickle
import gzip
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build
from build import MASTERS, ORDER, notdef, CTX
import fontout

OUT = os.path.join(ROOT, 'fonts')
PKL = os.path.join(ROOT, 'build', 'masters.pkl.gz')
MNAMES = ['Regular', 'Thin', 'ExtraBold']


def pack(contours):
    xs, ys, fl, ends = [], [], [], []
    for c in contours:
        for x, y, on in c:
            xs.append(int(round(x)))
            ys.append(int(round(y)))
            fl.append(1 if on else 0)
        ends.append(len(xs) - 1)
    return (array.array('i', xs), array.array('i', ys), bytes(fl), ends)


def job_packed(job):
    name, unis, w, res, bad = build.run_job(job)
    return name, unis, w, {m: pack(res[m]) for m in res}, bad


def all_jobs(cjk_limit=None):
    import cjk
    jobs = build.latin_jobs(('latin', 'symbols'))
    chars = sorted(cjk.data().keys())
    if cjk_limit:
        chars = chars[:cjk_limit]
    seen = {u for j in jobs for u in j[1]}
    chars = [ch for ch in chars if ord(ch) not in seen]
    return jobs, build.cjk_jobs(''.join(chars))


CJK_PKL = os.path.join(ROOT, 'build', 'cjk.pkl.gz')
LAT_PKL = os.path.join(ROOT, 'build', 'latin.pkl.gz')


def make_masters(cjk_limit=None, procs=4, part='both'):
    t = time.time()
    ljobs, cjobs = all_jobs(cjk_limit)
    if part in ('both', 'latin'):
        out = [job_packed(j) for j in ljobs]
        print(f'latin+symbols: {len(out)} glyphs, {time.time() - t:.0f}s', flush=True)
        _report(out)
        nd = {m: pack(notdef(CTX[m])) for m in MASTERS}
        with gzip.open(LAT_PKL, 'wb', compresslevel=3) as f:
            pickle.dump({'glyphs': out, 'notdef': nd}, f, protocol=4)
    if part in ('both', 'cjk'):
        out = []
        with Pool(procs) as pool:
            for i, r in enumerate(pool.imap(job_packed, cjobs, chunksize=16)):
                out.append(r)
                if i % 1000 == 0:
                    print(f'  cjk {i}/{len(cjobs)}  {time.time() - t:.0f}s', flush=True)
        _report(out)
        with gzip.open(CJK_PKL, 'wb', compresslevel=3) as f:
            pickle.dump({'glyphs': out}, f, protocol=4)
    print(f'masters done in {time.time() - t:.0f}s', flush=True)


def _report(out):
    bad = [(o[0], o[4]) for o in out if o[4]]
    if bad:
        print('INCOMPATIBLE', len(bad), bad[:20], flush=True)


def unpack_glyph(p, overlap=True):
    from fontTools.ttLib.tables._g_l_y_f import Glyph as TTGlyph, GlyphCoordinates
    from fontTools.ttLib.tables import ttProgram
    xs, ys, fl, ends = p
    g = TTGlyph()
    if not ends:
        g.numberOfContours = 0
        return g
    g.numberOfContours = len(ends)
    g.coordinates = GlyphCoordinates(list(zip(xs, ys)))
    flags = array.array('B', fl)
    if overlap:
        flags[0] |= 0x40
    g.flags = flags
    g.endPtsOfContours = list(ends)
    g.program = ttProgram.Program()
    g.program.fromBytecode(b"")
    return g


def load_masters():
    with gzip.open(LAT_PKL, 'rb') as f:
        M = pickle.load(f)
    if os.path.exists(CJK_PKL):
        with gzip.open(CJK_PKL, 'rb') as f:
            C = pickle.load(f)
        have = {g[0] for g in M['glyphs']}
        M['glyphs'] += [g for g in C['glyphs'] if g[0] not in have]
    return M


IUP_TOL = 2.0
INSTANCES = [(100, 'Thin'), (200, 'ExtraLight'), (300, 'Light'), (400, 'Regular'),
             (500, 'Medium'), (600, 'SemiBold'), (700, 'Bold'), (800, 'ExtraBold')]


def make_vf():
    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables.TupleVariation import TupleVariation
    from fontTools.varLib.iup import iup_delta_optimize
    from fontTools.fontBuilder import FontBuilder
    t = time.time()
    M = load_masters()
    glyphs = M['glyphs']
    order = ['.notdef'] + [g[0] for g in glyphs]
    cmap = {}
    for name, unis, w, res, bad in glyphs:
        for u in unis:
            cmap[u] = name
    widths = {'.notdef': 550}
    widths.update({g[0]: g[2] for g in glyphs})
    reg = {'.notdef': M['notdef']['Regular']}
    reg.update({g[0]: g[3]['Regular'] for g in glyphs})
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    ttg = {n: unpack_glyph(reg[n]) for n in order}
    fb.setupGlyf(ttg)
    glyf = fb.font['glyf']
    metrics = {}
    for n in order:
        g = glyf[n]
        g.recalcBounds(glyf)
        metrics[n] = (widths[n], g.xMin if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=fontout.ASC, descent=-fontout.DESC, lineGap=0)
    fontout_names(fb, 'Regular')
    fb.setupOS2(sTypoAscender=fontout.ASC, sTypoDescender=-fontout.DESC, sTypoLineGap=0,
                usWinAscent=fontout.ASC, usWinDescent=fontout.DESC, sxHeight=510, sCapHeight=690,
                usWeightClass=400, xAvgCharWidth=550, achVendID="CLWD", fsSelection=(1 << 7) | (1 << 6),
                panose=fontout._panose(400), ulCodePageRange1=(1 << 0) | (1 << 1) | (1 << 18) | (1 << 20),
                ulCodePageRange2=0, version=4)
    fb.setupPost(isFixedPitch=1, underlinePosition=-120, underlineThickness=60, keepGlyphNames=False)
    axes = [('wght', 100, 400, 800, 'Weight')]
    inst = [{'location': {'wght': w}, 'stylename': s} for w, s in INSTANCES]
    fb.setupFvar(axes, inst)
    # gvar
    print('gvar...', flush=True)
    gvar = newTable('gvar')
    gvar.version = 1
    gvar.reserved = 0
    gvar.variations = {}
    src = {'.notdef': M['notdef']}
    for gg in glyphs:
        src[gg[0]] = gg[3]
    for n in order:
        r = src[n]['Regular']
        xs, ys, fl, ends = r
        if not ends:
            continue
        coords = list(zip(xs, ys)) + [(0, 0), (widths[n], 0), (0, 0), (0, 0)]
        tvs = []
        for mname, peak in (('Thin', -1.0), ('ExtraBold', 1.0)):
            m = src[n][mname]
            deltas = [(a - x, b - y) for a, b, x, y in zip(m[0], m[1], xs, ys)]
            if not any(dx or dy for dx, dy in deltas):
                continue
            deltas += [(0, 0)] * 4
            opt = iup_delta_optimize(deltas, coords, list(ends), tolerance=IUP_TOL)
            tvs.append(TupleVariation({'wght': (min(peak, 0), peak, max(peak, 0))}, list(opt)))
        if tvs:
            gvar.variations[n] = tvs
    fb.font['gvar'] = gvar
    from fontTools.otlLib.builder import buildStatTable
    buildStatTable(fb.font, [dict(tag='wght', name='Weight', values=[
        dict(value=w, name=s, **({'flags': 0x2} if w == 400 else {})) for w, s in INSTANCES])])
    gasp = newTable('gasp')
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    fb.font['gasp'] = gasp
    add_features(fb.font)
    fb.font['OS/2'].recalcUnicodeRanges(fb.font)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'ClawdMono[wght].ttf')
    fb.save(path)
    print(f'VF saved {os.path.getsize(path) / 1e6:.1f} MB in {time.time() - t:.0f}s', flush=True)
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    f.flavor = 'woff2'
    f.save(os.path.join(OUT, 'ClawdMono[wght].woff2'))
    print(f'woff2 {os.path.getsize(os.path.join(OUT, "ClawdMono[wght].woff2")) / 1e6:.1f} MB')


def fontout_names(fb, style):
    names = {
        "familyName": fontout.FAMILY,
        "styleName": style,
        "uniqueFontIdentifier": f"ClawdMono-{style};{fontout.VERSION}",
        "fullName": f"{fontout.FAMILY} {style}",
        "psName": f"ClawdMono-{style}",
        "version": f"Version {fontout.VERSION}",
        "copyright": "Clawd Mono. Designed by Claude, an AI model by Anthropic. Unofficial fan typeface.",
        "designer": "Claude (an AI model by Anthropic)",
        "description": "A monospaced handwriting typeface for Claude: one virtual pen draws every Latin, CJK and terminal glyph.",
        "licenseDescription": "Arphic Public License. CJK skeletons derived from Make Me a Hanzi (Arphic PL KaitiM GB & UKai); Latin, symbols and the pen engine were designed from scratch.",
        "licenseInfoURL": "http://ftp.gnu.org/non-gnu/chinese-fonts-truetype/LICENSE",
    }
    fb.setupNameTable(names)
    nt = fb.font['name']
    nt.setName(fontout.FAMILY_ZH, 1, 3, 1, 0x804)
    nt.setName(style if style in ('Regular', 'Bold') else 'Regular', 2, 3, 1, 0x804)
    nt.setName(f"{fontout.FAMILY_ZH} {style}", 4, 3, 1, 0x804)


def add_features(font):
    import features
    from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
    fea = features.fea(set(font.getGlyphOrder()))
    if fea.strip():
        addOpenTypeFeaturesFromString(font, fea)


def make_statics(weights=(400, 700)):
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.ttLib.removeOverlaps import removeOverlaps
    vf_path = os.path.join(OUT, 'ClawdMono[wght].ttf')
    for w in weights:
        t = time.time()
        style = dict(INSTANCES)[w]
        vf = TTFont(vf_path)
        inst = instantiateVariableFont(vf, {'wght': w}, updateFontNames=False)
        removeOverlaps(inst)
        rib = style in ('Regular', 'Bold')
        fam = fontout.FAMILY if rib else f"{fontout.FAMILY} {style}"
        sub = style if rib else 'Regular'
        nt = inst['name']
        for rec in list(nt.names):
            if rec.nameID in (1, 2, 3, 4, 6, 16, 17, 25) or rec.nameID >= 256:
                nt.removeNames(nameID=rec.nameID)
        nt.setName(fam, 1, 3, 1, 0x409)
        nt.setName(sub, 2, 3, 1, 0x409)
        nt.setName(f"ClawdMono-{style};{fontout.VERSION}", 3, 3, 1, 0x409)
        nt.setName(f"{fontout.FAMILY} {style}", 4, 3, 1, 0x409)
        nt.setName(f"ClawdMono-{style}", 6, 3, 1, 0x409)
        if not rib:
            nt.setName(fontout.FAMILY, 16, 3, 1, 0x409)
            nt.setName(style, 17, 3, 1, 0x409)
        nt.setName(fontout.FAMILY_ZH if rib else f"{fontout.FAMILY_ZH} {style}", 1, 3, 1, 0x804)
        nt.setName(sub, 2, 3, 1, 0x804)
        nt.setName(f"{fontout.FAMILY_ZH} {style}", 4, 3, 1, 0x804)
        if not rib:
            nt.setName(fontout.FAMILY_ZH, 16, 3, 1, 0x804)
            nt.setName(style, 17, 3, 1, 0x804)
        os2 = inst['OS/2']
        # Instancing recalculates the average; preserve the half-width cell metric.
        os2.xAvgCharWidth = vf['OS/2'].xAvgCharWidth
        os2.usWeightClass = w
        os2.fsSelection = (os2.fsSelection & ~0b1100001) | (1 << 7) | (
            (1 << 6) if style == 'Regular' else (1 << 5) if style == 'Bold' else 0)
        if style not in ('Regular', 'Bold'):
            os2.fsSelection &= ~(1 << 6)
        inst['head'].macStyle = 1 if style == 'Bold' else 0
        os2.panose.bWeight = max(2, min(11, round(w / 100) + 1))
        for tag in ('STAT',):
            if tag in inst:
                del inst[tag]
        p = os.path.join(OUT, 'static', f'ClawdMono-{style}.ttf')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        inst.save(p)
        print(f'{style}: {os.path.getsize(p) / 1e6:.1f} MB  {time.time() - t:.0f}s', flush=True)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if cmd in ('masters', 'all'):
        make_masters(lim)
    if cmd == 'latin':
        make_masters(part='latin')
        make_vf()
    if cmd == 'cjk':
        make_masters(lim, part='cjk')
    if cmd in ('vf', 'all'):
        make_vf()
    if cmd in ('statics', 'all'):
        make_statics()
