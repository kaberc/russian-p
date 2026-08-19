#!/usr/bin/env python3
"""Structural check for an Apple .keylayout file.

macOS parses keylayouts without validating them, so a malformed file installs
quietly and misbehaves later. This checks the things that actually bite, and
handles the XML 1.1 control-character references that keylayouts legitimately
use for the function and arrow keys -- an XML 1.0 parser rejects those outright.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

XML_NAME = re.compile(r'^[A-Za-z_:][-A-Za-z0-9_:.]*$')
C0_REF = re.compile(r'&#x00([01][0-9A-Fa-f]);', re.I)
ROOT = pathlib.Path(__file__).resolve().parent.parent
DTD = ROOT / 'reference' / 'vendor' / 'KeyboardLayout.dtd'
LAYOUT = ROOT / 'src' / 'Resources' / 'Russian US Punctuation.keylayout'


def normalize(raw):
    # C0 controls are legal in XML 1.1 but not 1.0, and every validator here
    # speaks only 1.0, so park them in a private-use block. Length is preserved
    # and these live in CDATA, so neither parsing nor validity is affected.
    src = C0_REF.sub(lambda m: '&#xE0%s;' % m.group(1), raw)
    src = src.replace('<?xml version="1.1"', '<?xml version="1.0"')
    return re.sub(r'<!DOCTYPE[^>]*>', '', src)


def parse(path):
    with open(path, encoding='utf-8') as source:
        normalized = normalize(source.read())
    return normalized, ET.fromstring(normalized)


def dtd_validate(src):
    if not DTD.exists():
        return 'skipped; run ./tools/fetch-reference.sh', []
    try:
        from lxml import etree
    except ImportError:
        pass
    else:
        with DTD.open('rb') as source:
            dtd = etree.DTD(source)
        if dtd.validate(etree.fromstring(src.encode())):
            return 'lxml', []
        return 'lxml', [e.message for e in dtd.error_log.filter_from_errors()]

    xmllint = shutil.which('xmllint')
    if xmllint is None:
        return 'skipped; install xmllint or lxml', []
    with tempfile.NamedTemporaryFile('w', suffix='.xml', encoding='utf-8') as tmp:
        tmp.write(src)
        tmp.flush()
        done = subprocess.run([xmllint, '--noout', '--nonet', '--dtdvalid', str(DTD),
                               tmp.name], capture_output=True, text=True, check=False)
    if done.returncode == 0:
        return 'xmllint', []
    return 'xmllint', [line.split(': ', 1)[-1]
                       for line in done.stderr.splitlines() if line.strip()]


def utf16_units(text):
    return len(text.encode('utf-16-le')) // 2


def check(kb):
    errors = []

    ids = {}
    for el in kb.iter():
        if el.tag in ('modifierMap', 'keyMapSet', 'action') and el.get('id') is not None:
            value = el.get('id')
            if not XML_NAME.match(value):
                errors.append(f'<{el.tag} id="{value}"> is not a valid XML Name; '
                              'an ID cannot start with a digit')
            ids.setdefault(el.tag, set()).add(value)

    for layout in kb.findall('layouts/layout'):
        for attr, target in (('modifiers', 'modifierMap'), ('mapSet', 'keyMapSet')):
            ref = layout.get(attr)
            if ref not in ids.get(target, ()):
                errors.append(f'<layout {attr}="{ref}"> matches no <{target} id=...>')

    for mm in kb.findall('modifierMap'):
        found = sorted(int(k.get('mapIndex')) for k in mm.findall('keyMapSelect'))
        if found != list(range(len(found))):
            errors.append(f'modifierMap "{mm.get("id")}" mapIndex values are not '
                          f'contiguous from 0: {found}')

    for kms in kb.findall('keyMapSet'):
        indices = sorted(int(k.get('index')) for k in kms.findall('keyMap'))
        if indices != list(range(len(indices))):
            errors.append(f'keyMapSet "{kms.get("id")}" keyMap indices are not '
                          f'contiguous from 0: {indices}')
        for km in kms.findall('keyMap'):
            codes = [k.get('code') for k in km.findall('key')]
            repeats = sorted({c for c in codes if codes.count(c) > 1}, key=int)
            if repeats:
                errors.append(f'keyMap index="{km.get("index")}" repeats code(s) {repeats}')

    # every mapIndex the modifierMap can select needs a keyMap to land on
    for layout in kb.findall('layouts/layout'):
        mm = kb.find('modifierMap[@id="%s"]' % layout.get('modifiers'))
        kms = kb.find('keyMapSet[@id="%s"]' % layout.get('mapSet'))
        if mm is None or kms is None:
            continue
        available = {int(k.get('index')) for k in kms.findall('keyMap')}
        for sel in mm.findall('keyMapSelect'):
            if int(sel.get('mapIndex')) not in available:
                errors.append(f'keyMapSelect mapIndex="{sel.get("mapIndex")}" has no '
                              f'matching keyMap in keyMapSet "{kms.get("id")}"')

    # key -> action -> pending state -> terminator: every state a dead key arms
    # needs a terminator, or a pending accent vanishes instead of being emitted.
    actions = {a.get('id'): a for a in kb.iter('action') if a.get('id') is not None}
    for key in kb.iter('key'):
        out, act = key.get('output'), key.get('action')
        if (out is None) == (act is None):
            errors.append(f'key code="{key.get("code")}" needs exactly one of '
                          'output= or action=')
        if act is not None and act not in actions:
            errors.append(f'key code="{key.get("code")}" references action="{act}", '
                          'which is not defined')

    armed = set()
    terminated = {w.get('state') for w in kb.findall('terminators/when')}
    for aid, action in actions.items():
        whens = action.findall('when')
        if not any(w.get('state') == 'none' for w in whens):
            errors.append(f'<action id="{aid}"> has no state="none" branch, so its '
                          'key emits nothing when no dead key is pending')
        armed |= {w.get('next') for w in whens if w.get('next') is not None}
    for state in sorted(armed - terminated):
        errors.append(f'dead-key state "{state}" has no <terminators> entry, so a '
                      'pending accent would be dropped silently')

    maxout = kb.get('maxout')
    if maxout is not None:
        limit = int(maxout)
        emitters = [(f'key code="{k.get("code")}"', k.get('output')) for k in kb.iter('key')]
        emitters += [(f'<action id="{aid}"> branch state="{w.get("state")}"', w.get('output'))
                     for aid, action in actions.items() for w in action.findall('when')]
        for label, out in emitters:
            if out is not None and utf16_units(out) > limit:
                errors.append(f'{label} emits {utf16_units(out)} UTF-16 units, '
                              f'over maxout="{maxout}"')
    return errors


def main():
    if len(sys.argv) > 2:
        sys.exit('usage: check-keylayout.py [FILE.keylayout]')
    path = sys.argv[1] if len(sys.argv) == 2 else LAYOUT
    try:
        normalized, kb = parse(path)
    except ET.ParseError as exc:
        sys.exit(f'{path}: not well-formed: {exc}')

    validator, dtd_errors = dtd_validate(normalized)
    errors = [f'DTD: {err}' for err in dtd_errors] + check(kb)
    if errors:
        for err in errors:
            print(f'{path}: {err}', file=sys.stderr)
        sys.exit(f'{len(errors)} problem(s) found')
    keys = sum(1 for _ in kb.iter('key'))
    print(f'{path}: ok -- {keys} keys, id={kb.get("id")}, maxout={kb.get("maxout")}')
    print(f'  dtd: {validator}')


if __name__ == '__main__':
    main()
