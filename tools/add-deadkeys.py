#!/usr/bin/env python3
"""Inject an ABC-style acute dead key into a .keylayout file.

Russian stress marks (ударение: за́мок vs замо́к) have no precomposed Unicode
form, so a stressed vowel is always base letter + U+0301 COMBINING ACUTE.
Apple's own U.S./ABC layout hits the same wall on J/j and solves it the same
way -- a dead-key branch emitting two code points, with maxout="2".

Layout of the transformation:

    Option+E        arms the acute state          (ABC's acute dead key)
    then a vowel    emits <vowel> + U+0301
    then space      emits U+00B4 ACUTE ACCENT     (ABC's spacing clone)
    Shift+Option+E  emits U+0301 on its own       (escape hatch, see below)

Shift+Option+E is not an ABC feature. It replaces an orphaned Macedonian Ќ
and lets you stress a letter you have already typed, or one this script does
not convert.

Running this twice is refused rather than guessed at: the dead key overwrites
whatever Option+E used to emit, and that original is not recoverable from the
transformed file. Re-apply by restoring the layout from git first.
"""
import argparse
import re
import sys

# The nine Russian vowels that take a stress mark. ё is excluded: it is
# inherently stressed, so ё + acute is not a thing anyone types.
VOWELS = "аеиоуыэюя"

DEAD_STATE = "acute"
DEAD_ACTION = "dkAcute"
SPACE_ACTION = "spAcute"
COMBINING_ACUTE = "&#x0301;"
SPACING_ACUTE = "&#x00B4;"

DEAD_KEY_CODE = 14   # physical E
SPACE_CODE = 49
OPTION_MAP = 2       # verified against this layout's <modifierMap>
SHIFT_OPTION_MAP = 3
COMPOSABLE_MAPS = (0, 1, 2, 3)  # base, shift, option, shift+option

# Transliterated so the generated XML IDs stay ASCII Names.
TRANSLIT = {"а": "a", "е": "e", "и": "i", "о": "o", "у": "u",
            "ы": "y", "э": "je", "ю": "ju", "я": "ja"}


def action_id(letter):
    """Stable ASCII XML ID for one letter in one case."""
    base = TRANSLIT[letter.lower()]
    return "acu_%s_%s" % (base, "uc" if letter.isupper() else "lc")


def revert(src):
    """Undo a previous injection so the script is safely re-runnable."""
    if "<actions>" not in src:
        return src, False

    # action id -> its unmodified output, so keys can go back to output=.
    plain = {}
    for m in re.finditer(r'<action id="([^"]+)">(.*?)</action>', src, re.S):
        w = re.search(r'<when state="none" output="([^"]*)"\s*/>', m.group(2))
        if w:
            plain[m.group(1)] = w.group(1)

    def unbind(m):
        code, aid = m.group(1), m.group(2)
        if aid in plain:
            return '<key code="%s" output="%s"/>' % (code, plain[aid])
        if aid == DEAD_ACTION:
            # The dead key consumed a slot; there is nothing to restore it to.
            raise SystemExit(
                "add-deadkeys: cannot revert -- the dead key at code %s "
                "overwrote its original output. Restore from git instead." % code)
        return m.group(0)

    src = re.sub(r'<key code="(\d+)" action="([^"]+)"/>', unbind, src)
    src = re.sub(r"\n[ \t]*<actions>.*?</actions>", "", src, flags=re.S)
    src = re.sub(r"\n[ \t]*<terminators>.*?</terminators>", "", src, flags=re.S)
    return src, True


def inject(src):
    keyboard = re.search(r"<keyboard\b[^>]*>", src)
    if not keyboard:
        sys.exit("add-deadkeys: no <keyboard> element found")

    # --- find every key that types a stressable vowel ---------------------
    letters = set()
    edits = []  # (span, replacement)

    for km in re.finditer(r'<keyMap index="(\d+)"[^>]*>(.*?)</keyMap>', src, re.S):
        index = int(km.group(1))
        if index not in COMPOSABLE_MAPS:
            continue
        body_start = km.start(2)
        for k in re.finditer(r'<key code="(\d+)" output="([^"]*)"/>', km.group(2)):
            code, out = int(k.group(1)), k.group(2)
            span = (body_start + k.start(), body_start + k.end())

            if index == OPTION_MAP and code == DEAD_KEY_CODE:
                edits.append((span, '<key code="%d" action="%s"/>'
                              % (code, DEAD_ACTION)))
            elif index == SHIFT_OPTION_MAP and code == DEAD_KEY_CODE:
                edits.append((span, '<key code="%d" output="%s"/>'
                              % (code, COMBINING_ACUTE)))
            elif code == SPACE_CODE and index in (0, 1):
                edits.append((span, '<key code="%d" action="%s"/>'
                              % (code, SPACE_ACTION)))
            elif len(out) == 1 and out.lower() in VOWELS:
                letters.add(out)
                edits.append((span, '<key code="%d" action="%s"/>'
                              % (code, action_id(out))))

    if not letters:
        sys.exit("add-deadkeys: found no vowel keys to convert")

    for (start, end), replacement in sorted(edits, reverse=True):
        src = src[:start] + replacement + src[end:]

    # --- build the <actions> / <terminators> blocks ------------------------
    lines = ["    <actions>",
             '        <action id="%s">' % DEAD_ACTION,
             '            <when state="none" next="%s"/>' % DEAD_STATE,
             "        </action>",
             '        <action id="%s">' % SPACE_ACTION,
             '            <when state="none" output=" "/>',
             '            <when state="%s" output="%s"/>' % (DEAD_STATE, SPACING_ACUTE),
             "        </action>"]

    for letter in sorted(letters, key=lambda c: (TRANSLIT[c.lower()], c.isupper())):
        lines += ['        <action id="%s">' % action_id(letter),
                  '            <when state="none" output="%s"/>' % letter,
                  '            <when state="%s" output="%s%s"/>'
                  % (DEAD_STATE, letter, COMBINING_ACUTE),
                  "        </action>"]

    lines += ["    </actions>",
              "    <terminators>",
              '        <when state="%s" output="%s"/>' % (DEAD_STATE, SPACING_ACUTE),
              "    </terminators>"]
    block = "\n".join(lines) + "\n"

    src = re.sub(r"(</keyMapSet>\s*\n)", r"\1" + block.replace("\\", "\\\\"),
                 src, count=1)

    # --- a stressed vowel is two code points ------------------------------
    src = re.sub(r'(<keyboard\b[^>]*?)maxout="\d+"', r'\1maxout="2"', src, count=1)

    return src, sorted(letters)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help=".keylayout file to transform")
    ap.add_argument("-o", "--output", help="write here instead of in place")
    args = ap.parse_args()

    src = open(args.path, encoding="utf-8").read()
    src, reverted = revert(src)
    if reverted:
        print("add-deadkeys: reverted a previous injection first")

    src, letters = inject(src)
    dest = args.output or args.path
    open(dest, "w", encoding="utf-8").write(src)

    print("add-deadkeys: %s" % dest)
    print("  dead key   : Option+E arms %r, terminator U+00B4" % DEAD_STATE)
    print("  escape key : Shift+Option+E emits U+0301 alone")
    print("  composable : %d keys over %d letters -- %s"
          % (len(letters), len({c.lower() for c in letters}), " ".join(letters)))
    print("  maxout     : 2")


if __name__ == "__main__":
    main()
