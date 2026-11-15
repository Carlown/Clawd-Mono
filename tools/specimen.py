"""Assemble the specimen page: inject data + subset font into index.src.html."""
import base64
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

SRC = os.path.join(ROOT, 'specimen', 'index.src.html')
DIST = os.path.join(ROOT, 'specimen', 'dist')
VF = os.path.join(ROOT, 'fonts', 'ClawdMono[wght].ttf')
VF2 = os.path.join(ROOT, 'fonts', 'ClawdMono[wght].woff2')


def is_cjk(cp):
    return 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF


def charset_groups(cmap):
    have = set(cmap)

    def pick(cps):
        return ''.join(chr(c) for c in cps if c in have)

    latin = list(range(0x21, 0x7F)) + list(range(0xA1, 0x100)) + list(range(0x100, 0x180))
    latin = [c for c in latin if c != 0xAD]
    pinyin = [ord(c) for c in 'āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüêɑɡĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛÜÊ']
    greek = list(range(0x391, 0x3AA)) + list(range(0x3B1, 0x3CA))
    math_ = [c for c in sorted(have) if 0x2200 <= c <= 0x22FF or 0x2308 <= c <= 0x230B or c in (0x27E8, 0x27E9, 0xB1, 0xD7, 0xF7, 0x2016)]
    sym = [c for c in sorted(have) if (0x2010 <= c <= 0x2044 or 0x20A0 <= c <= 0x20CF or 0x2100 <= c <= 0x21FF or
                                       0x2070 <= c <= 0x209F) and c not in (0x2026,)]
    cc = [ord(c) for c in '·✢✳✶✻✽∗⏺⎿❯❮›‹⏵⏴⏶⏷⏸⏹☐☑☒✓✔✗✘∴∵…⋯⋮⧉⚠⚡●○◯◉◎■□▪▫◼◻◾◽▶▷▸▹▼▽▾▿◀◁◆◇★☆✦✧✱✲✴※•◦⌘⌥⌃⇧⎋⌫⏎↵↻↺'] + [0xE000, 0xE001, 0xE0A0, 0xE0A2, 0xE0B0, 0xE0B1, 0xE0B2, 0xE0B3, 0xE0B4, 0xE0B5, 0xE0B6, 0xE0B7]
    box = list(range(0x2500, 0x2580))
    blocks = list(range(0x2580, 0x25A0)) + list(range(0x2800, 0x2900))
    punct = [c for c in sorted(have) if 0x3000 <= c <= 0x303F or 0xFF00 <= c <= 0xFFEF or c == 0x30FB]
    hanzi = '永和九年岁在癸丑暮春之初会于会稽山阴之兰亭修禊事也群贤毕至少长咸集此地有崇山峻岭茂林修竹又有清流激湍映带左右引以为流觞曲水列坐其次虽无丝竹管弦之盛一觞一咏亦足以畅叙幽情是日也天朗气清惠风和畅仰观宇宙之大俯察品类之盛所以游目骋怀足以极视听之娱信可乐也爪迹等宽克劳德写字代码终端笔画骨架鬱爨齉龘靐'
    return {
        '西文': pick(latin),
        '拼音': pick(pinyin),
        '希腊': pick(greek),
        '数学': pick(math_),
        '标点符号': pick(sym),
        'Claude Code': pick(cc),
        '框线': pick(box),
        '方块与盲文': pick(blocks),
        '中文标点': pick(punct),
        '汉字（节选）': ''.join(dict.fromkeys(c for c in hanzi if ord(c) in have)),
    }


def subset_woff2(text, path):
    from fontTools import subset
    from fontTools.ttLib import TTFont
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['*']
    opts.name_IDs = ['*']
    opts.notdef_outline = True
    opts.glyph_names = False
    opts.drop_tables += ['DSIG']
    f = TTFont(path)
    s = subset.Subsetter(opts)
    s.populate(unicodes=sorted({ord(c) for c in text}))
    # alternates reached through features
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = 'woff2'
    f.save(buf)
    return buf.getvalue()


def main():
    from fontTools.ttLib import TTFont
    import export_skel
    import diagram
    os.makedirs(os.path.join(DIST, 'fonts'), exist_ok=True)
    tmp = os.path.join(ROOT, 'build', 'skel.json')
    export_skel.export('爪迹Clawd Mono', tmp)
    skel = open(tmp, encoding='utf-8').read()
    diag = json.dumps({ch: diagram.glyph_data(ch) for ch in 'ag永'}, ensure_ascii=False, separators=(',', ':'))
    font = TTFont(VF)
    cmap = font.getBestCmap()
    groups = charset_groups(cmap)
    noncjk = sum(1 for g in font.getGlyphOrder()) - sum(1 for c in cmap if is_cjk(c))
    files = []
    dfonts = os.path.join(DIST, 'fonts')
    for f_ in os.listdir(dfonts):
        os.remove(os.path.join(dfonts, f_))
    shutil.copy(VF, os.path.join(dfonts, 'ClawdMono-VF.ttf'))
    files.append({'name': 'ClawdMono[wght].ttf', 'path': 'fonts/ClawdMono-VF.ttf',
                  'note': f'可变字体 · 字重 100–800 · 推荐 · {os.path.getsize(VF) / 1e6:.1f} MB'})
    for st in ('Regular', 'Bold'):
        p = os.path.join(ROOT, 'fonts', 'static', f'ClawdMono-{st}.ttf')
        shutil.copy(p, os.path.join(dfonts, f'ClawdMono-{st}.ttf'))
        files.append({'name': f'ClawdMono-{st}.ttf', 'path': f'fonts/ClawdMono-{st}.ttf',
                      'note': f'静态 {st}（已去重叠）· 给不认可变字体的程序 · {os.path.getsize(p) / 1e6:.1f} MB'})
    shutil.copy(VF2, os.path.join(dfonts, 'ClawdMono-VF.woff2'))
    src = open(SRC, encoding='utf-8').read()
    src = src.replace('__NONCJK__', f'{noncjk:,}')
    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    page_text = src + ''.join(groups.values())
    # every character the page can show at rest (plus ASCII and the alternates' bases)
    chars = set(c for c in page_text if ord(c) >= 0x20) | set(chr(c) for c in range(0x20, 0x7F))
    chars |= set('ɑɡ')
    sub = subset_woff2(''.join(chars), VF)
    b64 = base64.b64encode(sub).decode()
    face = ("@font-face { font-family: 'Clawd Mono'; src: url(data:font/woff2;base64," + b64 +
            ") format('woff2'); font-weight: 100 800; font-display: block; }\n"
            "@font-face { font-family: 'Clawd Mono Full'; src: url('fonts/ClawdMono-VF.woff2') format('woff2'); "
            "font-weight: 100 800; font-display: swap; }")
    src = src.replace('/*__FONTFACE__*/', face)
    src = src.replace('/*__SKEL__*/{}', skel).replace('/*__DIAG__*/{}', diag)
    src = src.replace('/*__FILES__*/[]', js(files)).replace('/*__CHARSET__*/{}', js(groups))
    out = os.path.join(DIST, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(src)
    print('page', os.path.getsize(out) / 1e6, 'MB; subset font', len(sub) / 1e3, 'KB; non-CJK glyphs', noncjk)
    for k, v in groups.items():
        print(' ', k, len(v))


if __name__ == '__main__':
    main()
