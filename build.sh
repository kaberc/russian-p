#!/usr/bin/env bash
# Assemble Russian US Punctuation.bundle from the editable sources in src/.
#
# src/ mirrors the bundle's Contents/ directory, so most files copy straight
# across. The one transformation is InfoPlist.strings: it lives as UTF-8 in
# src/ so git can diff it, and is re-encoded to UTF-16LE with a BOM on the way
# into the bundle, which is the form macOS ships.
set -euo pipefail
cd "$(dirname "$0")"

name='Russian US Punctuation'
out="build/${name}.bundle"

rm -rf build
mkdir -p "${out}/Contents/Resources"

cp src/Info.plist src/version.plist "${out}/Contents/"
cp "src/Resources/${name}.keylayout" "${out}/Contents/Resources/"

for dir in src/Resources/*.lproj; do
	target="${out}/Contents/Resources/$(basename "$dir")"
	mkdir -p "$target"
	printf '\xff\xfe' >"${target}/InfoPlist.strings"
	iconv -f UTF-8 -t UTF-16LE <"${dir}/InfoPlist.strings" >>"${target}/InfoPlist.strings"
done

# macOS installs malformed layouts without complaint; fail here instead
python3 tools/check-keylayout.py "${out}/Contents/Resources/${name}.keylayout"

# archive for transfer to a Mac; zip(1) is absent on some Linux boxes
if command -v zip >/dev/null; then
	(cd build && zip -qr "${name}.bundle.zip" "${name}.bundle")
else
	python3 - "$name" <<'PY'
import pathlib, sys, zipfile
name = sys.argv[1]
root = pathlib.Path('build')
with zipfile.ZipFile(root / f'{name}.bundle.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for path in sorted((root / f'{name}.bundle').rglob('*')):
        z.write(path, path.relative_to(root))
PY
fi
printf 'built  %s\n       build/%s.bundle.zip\n' "$out" "$name"

cat <<EOF

install on a Mac:
  cp -R "${out}" ~/Library/Keyboard\\ Layouts/
then log out and back in, and enable it under
System Settings > Keyboard > Text Input > Input Sources.
EOF
