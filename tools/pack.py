"""Package fonts + README + license into ClawdMono-v1.0.zip (and small per-part zips for the specimen)."""
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def add(z, path, arc):
    z.write(path, arc, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main():
    fonts = os.path.join(ROOT, 'fonts')
    lic = os.path.join(ROOT, 'data', 'license', 'ARPHIC-PL.txt')
    readme = os.path.join(ROOT, 'README.md')
    out = os.path.join(ROOT, 'ClawdMono-v1.0.zip')
    with zipfile.ZipFile(out, 'w') as z:
        for f in sorted(os.listdir(fonts)):
            p = os.path.join(fonts, f)
            if os.path.isfile(p):
                add(z, p, f'ClawdMono/{f}')
        st = os.path.join(fonts, 'static')
        for f in sorted(os.listdir(st)):
            add(z, os.path.join(st, f), f'ClawdMono/static/{f}')
        add(z, readme, 'ClawdMono/README.md')
        add(z, lic, 'ClawdMono/LICENSE-ARPHIC.txt')
    print(out, round(os.path.getsize(out) / 1e6, 1), 'MB')
    # per-part zips for the specimen downloads (each must stay < 15 MB)
    dist = os.path.join(ROOT, 'specimen', 'dist', 'fonts')
    os.makedirs(dist, exist_ok=True)
    parts = {
        'ClawdMono-variable.zip': [os.path.join(fonts, 'ClawdMono[wght].ttf')],
        'ClawdMono-static.zip': [os.path.join(st, f) for f in sorted(os.listdir(st))],
    }
    for name, paths in parts.items():
        p = os.path.join(dist, name)
        with zipfile.ZipFile(p, 'w') as z:
            for q in paths:
                add(z, q, os.path.basename(q))
            add(z, readme, 'README.md')
            add(z, lic, 'LICENSE-ARPHIC.txt')
        print(p, round(os.path.getsize(p) / 1e6, 1), 'MB')


if __name__ == '__main__':
    main()
