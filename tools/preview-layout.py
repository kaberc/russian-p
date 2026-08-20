#!/usr/bin/env python3
"""Render a .keylayout as an SVG picture of an ANSI keyboard.

Each keycap shows four layers: unshifted bottom-left, shift top-left, and the
Option pair down the right in a lighter colour. Option glyphs that merely repeat
the layer below them are dropped, so only the ones that add a character show up.
"""
import argparse
import pathlib
import re
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAYOUT = ROOT / 'src' / 'Resources' / 'Russian US Punctuation.keylayout'
PREVIEW = ROOT / 'docs' / 'preview.svg'
STRINGS = ROOT / 'src' / 'Resources' / 'en.lproj' / 'InfoPlist.strings'

C0_REF = re.compile(r'&#x00([01][0-9A-Fa-f]);', re.IGNORECASE)

U = 116          # key unit in px
GAP = 6
PAD = 22

# (width in units, virtual key code or None, static label)
ROWS = [
    [(1, 50), (1, 18), (1, 19), (1, 20), (1, 21), (1, 23), (1, 22),
     (1, 26), (1, 28), (1, 25), (1, 29), (1, 27), (1, 24), (2, None, 'delete')],
    [(1.5, None, 'tab'), (1, 12), (1, 13), (1, 14), (1, 15), (1, 17), (1, 16),
     (1, 32), (1, 34), (1, 31), (1, 35), (1, 33), (1, 30), (1.5, 42)],
    [(1.75, None, 'caps lock'), (1, 0), (1, 1), (1, 2), (1, 3), (1, 5), (1, 4),
     (1, 38), (1, 40), (1, 37), (1, 41), (1, 39), (2.25, None, 'return')],
    [(2.25, None, 'shift'), (1, 6), (1, 7), (1, 8), (1, 9), (1, 11), (1, 45),
     (1, 46), (1, 43), (1, 47), (1, 44), (2.75, None, 'shift')],
    [(1.25, None, 'control'), (1.25, None, 'option'), (1.25, None, 'command'),
     (7.5, None, ''), (1.25, None, 'command'), (1.25, None, 'option'),
     (1.25, None, 'control')],
]

CYRILLIC = re.compile(r'[\u0400-\u04FF]')


def load(path):
    with open(path, encoding='utf-8') as source:
        raw = source.read()
    src = C0_REF.sub(lambda m: f'&#xE0{m.group(1)};', raw)
    src = src.replace('<?xml version="1.1"', '<?xml version="1.0"')
    return ET.fromstring(re.sub(r'<!DOCTYPE[^>]*>', '', src))


def resolve_actions(kb):
    terminators = {w.get('state'): w.get('output')
                   for w in kb.findall('terminators/when')}
    plain, dead = {}, {}
    for action in kb.iter('action'):
        for when in action.findall('when'):
            if when.get('state') != 'none':
                continue
            if when.get('next') is not None:
                dead[action.get('id')] = terminators.get(when.get('next'), '\u00b4')
            elif when.get('output') is not None:
                plain[action.get('id')] = when.get('output')
    return plain, dead


def displayable(text):
    text = ''.join(chr(ord(c) - 0xE000) if 0xE000 <= ord(c) <= 0xE01F else c
                   for c in text)
    if not text or ord(text[0]) < 0x20 or ord(text[0]) == 0x7F:
        return ''
    # a lone combining mark needs a base to sit on, or it attaches to the glyph
    # drawn before it; U+25CC DOTTED CIRCLE is the Unicode convention for this
    if 0x0300 <= ord(text[0]) <= 0x036F:
        return '\u25cc' + text
    return text


def layers(kb):
    plain, dead_actions = resolve_actions(kb)
    out, dead = {}, set()
    layout = kb.find('layouts/layout')
    map_set_id = layout.get('mapSet')
    map_set = kb.find(f"keyMapSet[@id='{map_set_id}']")
    for km in map_set.findall('keyMap'):
        index = int(km.get('index'))
        table = {}
        for key in km.findall('key'):
            code = int(key.get('code'))
            action = key.get('action')
            if action in dead_actions:
                table[code] = displayable(dead_actions[action])
                dead.add((index, code))
                continue
            text = key.get('output')
            if text is None:
                text = plain.get(action)
            if text is None:
                continue
            text = displayable(text)
            if text:
                table[code] = text
        out[index] = table
    return out, dead


def esc(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def render(kb, title):
    maps, dead = layers(kb)
    legend = 'black = Latin · blue = Cyrillic · pale = Option / Shift-Option'
    if dead:
        legend += ' · orange = dead key'
    width = int(15 * U + 2 * PAD)
    height = int(len(ROWS) * U + 2 * PAD + 74)
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" font-family="Helvetica Neue,Helvetica,Arial,'
            'DejaVu Sans,sans-serif">'
        ),
        f'<rect width="{width}" height="{height}" rx="18" fill="#f6f6f4"/>',
        f'<text x="{PAD}" y="{PAD + 30}" font-size="26" fill="#1a1a1a">{esc(title)}</text>',
        (
            f'<text x="{width - PAD}" y="{PAD + 30}" font-size="17" fill="#8a8a8a" '
            f'text-anchor="end">{esc(legend)}</text>'
        ),
    ]
    top = PAD + 56
    for row, keys in enumerate(ROWS):
        x = PAD
        for spec in keys:
            span, code = spec[0], spec[1]
            label = spec[2] if len(spec) > 2 else None
            w = span * U - GAP
            y = top + row * U
            h = U - GAP
            parts.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
                         'rx="11" fill="#ffffff" stroke="#d3d3cd" stroke-width="2"/>')
            if code is None:
                if label:
                    parts.append(f'<text x="{x + 13:.0f}" y="{y + h - 14:.0f}" font-size="18" '
                                 f'fill="#9a9a92">{esc(label)}</text>')
            else:
                base = maps.get(0, {}).get(code, '')
                shift = maps.get(1, {}).get(code, '')
                opt = maps.get(2, {}).get(code, '')
                sopt = maps.get(3, {}).get(code, '')
                if opt in (base, shift):
                    opt = ''
                if sopt in (base, shift, opt):
                    sopt = ''
                lx, rx = x + 15, x + w - 13
                colour = '#0b5cad' if CYRILLIC.match(base or ' ') else '#1a1a1a'
                if shift:
                    parts.append(f'<text x="{lx:.0f}" y="{y + 40:.0f}" font-size="31" '
                                 f'fill="{colour}">{esc(shift)}</text>')
                if base:
                    parts.append(f'<text x="{lx:.0f}" y="{y + h - 15:.0f}" font-size="31" '
                                 f'fill="{colour}">{esc(base)}</text>')
                if sopt:
                    parts.append(f'<text x="{rx:.0f}" y="{y + 38:.0f}" font-size="24" '
                                 f'fill="{"#c2410c" if (3, code) in dead else "#5b8ec4"}" '
                                 f'text-anchor="end">{esc(sopt)}</text>')
                if opt:
                    parts.append(f'<text x="{rx:.0f}" y="{y + h - 16:.0f}" font-size="24" '
                                 f'fill="{"#c2410c" if (2, code) in dead else "#5b8ec4"}" '
                                 f'text-anchor="end">{esc(opt)}</text>')
            x += span * U
    parts.append('</svg>')
    return '\n'.join(parts)


def display_name(internal):
    # The keyboard's name is an identifier -- it must match the file stem and
    # the KLInfo_ key or macOS ignores the bundle's metadata. Users see the
    # localized string keyed on it, which is what belongs in the title.
    try:
        text = STRINGS.read_text(encoding='utf-8')
    except OSError:
        return internal
    localized = re.search(rf'"{re.escape(internal)}"\s*=\s*"([^"]*)"', text)
    return localized.group(1) if localized else internal


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('keylayout', nargs='?', default=LAYOUT)
    ap.add_argument('-o', '--output', default=PREVIEW)
    args = ap.parse_args()

    kb = load(args.keylayout)
    name = kb.get('name')
    svg = render(kb, display_name(name) if name else str(args.keylayout))
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
