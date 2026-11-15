"""Render proofs of a TTF with FreeType (unhinted, grayscale)."""
import sys
import freetype
from PIL import Image, ImageDraw


def render_lines(font_path, lines, size=48, pad=24, line_h=None, coords=None, bg=255, fg=0,
                 width=None, guides=False):
    face = freetype.Face(font_path)
    if coords is not None:
        face.set_var_design_coords(coords)
    face.set_char_size(int(size * 64))
    upm = face.units_per_EM
    asc = 960 * size / upm
    desc = 280 * size / upm
    line_h = line_h or int(round(asc + desc))
    adv_px = 550 * size / upm
    rows = []
    maxw = 0
    for ln in lines:
        w = 0
        for ch in ln:
            gi = face.get_char_index(ch)
            face.load_glyph(gi, freetype.FT_LOAD_NO_HINTING)
            w += face.glyph.advance.x / 64
        maxw = max(maxw, w)
    W = int(width or maxw + 2 * pad)
    H = int(len(lines) * line_h + 2 * pad)
    img = Image.new('L', (W, H), bg)
    dr = ImageDraw.Draw(img)
    for li, ln in enumerate(lines):
        x = pad
        base = pad + li * line_h + asc
        if guides:
            for yy, col in ((0, 200), (510, 220), (690, 220), (740, 230), (-210, 230)):
                py = int(round(base - yy * size / upm))
                dr.line([(0, py), (W, py)], fill=col)
        for ch in ln:
            gi = face.get_char_index(ch)
            face.load_glyph(gi, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            g = face.glyph
            bm = g.bitmap
            if bm.width and bm.rows:
                gl = Image.frombytes('L', (bm.width, bm.rows), bytes(bm.buffer))
                if bm.pitch != bm.width:
                    gl = Image.frombuffer('L', (bm.width, bm.rows), bytes(bm.buffer), 'raw', 'L', bm.pitch, 1)
                ox = int(round(x + g.bitmap_left))
                oy = int(round(base - g.bitmap_top))
                if fg == 0:
                    ink = Image.new('L', gl.size, 0)
                    img.paste(ink, (ox, oy), gl)
                else:
                    ink = Image.new('L', gl.size, fg)
                    img.paste(ink, (ox, oy), gl)
            x += g.advance.x / 64
    return img


def stack(imgs, gap=0):
    W = max(i.width for i in imgs)
    H = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new('L', (W, H), 255)
    y = 0
    for i in imgs:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


if __name__ == '__main__':
    path, out = sys.argv[1], sys.argv[2]
    text = sys.argv[3].split('\\n')
    size = float(sys.argv[4]) if len(sys.argv) > 4 else 48
    render_lines(path, text, size=size).save(out)
