"""Compile glyph contours into TrueType fonts (static masters + variable)."""
import array
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph as TTGlyph, GlyphCoordinates
from fontTools.ttLib.tables import ttProgram
from fontTools.fontBuilder import FontBuilder

FAMILY = "Clawd Mono"
FAMILY_ZH = "爪迹等宽"
VERSION = "1.000"

ASC, DESC = 960, 280
UPM = 1000


def to_ttglyph(contours, overlap_flag=True):
    g = TTGlyph()
    if not contours:
        g.numberOfContours = 0
        return g
    coords, flags, ends = [], [], []
    for c in contours:
        for x, y, on in c:
            coords.append((int(round(x)), int(round(y))))
            flags.append(1 if on else 0)
        ends.append(len(coords) - 1)
    if overlap_flag:
        flags[0] |= 0x40   # OVERLAP_SIMPLE
    g.numberOfContours = len(contours)
    g.coordinates = GlyphCoordinates(coords)
    g.flags = array.array('B', flags)
    g.endPtsOfContours = ends
    g.program = ttProgram.Program()
    g.program.fromBytecode(b"")
    return g


def build_font(glyph_order, glyphs, cmap, style="Regular", weight=400, path=None,
               extra_names=None, fea=None, post_names=True):
    """glyphs: name -> (contours, advance)."""
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    ttg = {n: to_ttglyph(glyphs[n][0]) for n in glyph_order}
    fb.setupGlyf(ttg)
    glyf = fb.font['glyf']
    metrics = {}
    for n in glyph_order:
        g = glyf[n]
        g.recalcBounds(glyf)
        lsb = getattr(g, 'xMin', 0) if g.numberOfContours else 0
        metrics[n] = (glyphs[n][1], lsb)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=-DESC, lineGap=0)
    ps_family = FAMILY.replace(" ", "")
    names = {
        "familyName": FAMILY,
        "styleName": style,
        "uniqueFontIdentifier": f"{ps_family}-{style};{VERSION}",
        "fullName": f"{FAMILY} {style}",
        "psName": f"{ps_family}-{style}",
        "version": f"Version {VERSION}",
        "copyright": "Clawd Mono, designed by Claude. Unofficial fan typeface.",
        "designer": "Claude (an AI model by Anthropic)",
        "description": "A monospaced handwriting typeface for Claude: one pen draws every Latin, CJK and terminal glyph.",
        "licenseDescription": "Arphic Public License (CJK skeletons derived from Make Me a Hanzi / Arphic PL KaitiM GB & UKai). Latin, symbols and pen engine designed from scratch.",
    }
    if extra_names:
        names.update(extra_names)
    fb.setupNameTable(names)
    # Chinese localized names
    nt = fb.font['name']
    for nid, s in ((1, FAMILY_ZH if style in ("Regular", "Bold") else f"{FAMILY_ZH} {style}"),
                   (2, style if style in ("Regular", "Bold") else "Regular"),
                   (4, f"{FAMILY_ZH} {style}"), (16, FAMILY_ZH), (17, style)):
        nt.setName(s, nid, 3, 1, 0x804)
    fb.setupOS2(
        sTypoAscender=ASC, sTypoDescender=-DESC, sTypoLineGap=0,
        usWinAscent=ASC, usWinDescent=DESC,
        sxHeight=510, sCapHeight=690, usWeightClass=weight,
        xAvgCharWidth=550, achVendID="CLWD",
        fsSelection=(1 << 7) | ((1 << 6) if style == "Regular" else (1 << 5 if style == "Bold" else 0)),
        panose=_panose(weight),
        ulCodePageRange1=(1 << 0) | (1 << 1) | (1 << 18) | (1 << 20),
        ulCodePageRange2=0,
        version=4,
    )
    fb.setupPost(isFixedPitch=1, underlinePosition=-120, underlineThickness=60,
                 keepGlyphNames=post_names)
    fb.font['head'].macStyle = 1 if style == "Bold" else 0
    if fea:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        addOpenTypeFeaturesFromString(fb.font, fea)
    gasp = newTable('gasp')
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    fb.font['gasp'] = gasp
    fb.font['OS/2'].recalcUnicodeRanges(fb.font)
    if path:
        fb.save(path)
    return fb.font


def _panose(weight):
    from fontTools.ttLib.tables.O_S_2f_2 import Panose
    p = Panose()
    p.bFamilyType = 2
    p.bSerifStyle = 11      # normal sans
    p.bWeight = max(2, min(11, round(weight / 100) + 1))
    p.bProportion = 9       # monospaced
    p.bContrast = 2
    p.bStrokeVariation = 2
    p.bArmStyle = 2
    p.bLetterForm = 2
    p.bMidline = 2
    p.bXHeight = 4
    return p
