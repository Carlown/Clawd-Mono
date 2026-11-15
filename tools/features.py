"""OpenType features for Clawd Mono (feaLib source, filtered to existing glyphs)."""


def fea(glyphs):
    out = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;', 'languagesystem hani dflt;']

    def have(*names):
        return all(n in glyphs for n in names)

    subs = []
    if have('zero', 'zero.slash'):
        out.append('feature zero { sub zero by zero.slash; } zero;')
    ss = {
        'ss01': [('a', 'a.single')],
        'ss04': [('g', 'g.double')],
        'ss02': [('zero', 'zero.slash')],
        'ss03': [('i', 'i.spark'), ('j', 'j.spark')],
    }
    for tag, pairs in ss.items():
        rules = [f'  sub {a} by {b};' for a, b in pairs if have(a, b)]
        if rules:
            out.append(f'feature {tag} {{\n' + '\n'.join(rules) + f'\n}} {tag};')
    return '\n'.join(out) + '\n'
