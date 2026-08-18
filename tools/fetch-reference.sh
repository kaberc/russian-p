#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
. "$root/reference/sources.env"
vendor="$root/reference/vendor"

digest() {
	if command -v sha256sum >/dev/null; then
		sha256sum "$1" | cut -d ' ' -f 1
	else
		shasum -a 256 "$1" | cut -d ' ' -f 1
	fi
}

verify() {
	local path=$1 expected=$2 actual
	actual=$(digest "$path")
	if [[ $actual != "$expected" ]]; then
		printf 'hash mismatch for %s\n  expected %s\n  actual   %s\n' \
			"$path" "$expected" "$actual" >&2
		return 1
	fi
}

if [[ ${1:-} == --verify-only ]]; then
	verify "$vendor/$DTD_FILENAME" "$DTD_SHA256"
	verify "$vendor/$US_FILENAME" "$US_SHA256"
	printf 'reference files verified\n'
	exit 0
fi
if [[ $# -ne 0 ]]; then
	printf 'usage: %s [--verify-only]\n' "$0" >&2
	exit 2
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if [[ -f $DTD_SYSTEM_PATH ]]; then
	cp "$DTD_SYSTEM_PATH" "$tmp/$DTD_FILENAME"
else
	curl --fail --location --silent --show-error --retry 2 \
		-o "$tmp/TN2056.html" "$DTD_URL"
	python3 - "$tmp/TN2056.html" "$tmp/$DTD_FILENAME" <<'PY'
import html
import pathlib
import re
import sys

source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
_, marker, section = source.partition("DTS10003085-CH1-SOURCECODE6")
if not marker:
    raise SystemExit("Apple TN2056 no longer contains the KeyboardLayout DTD")
sample = re.search(r"<pre>(.*?)</pre>", section, flags=re.DOTALL)
if sample is None:
    raise SystemExit("Apple TN2056 no longer contains the KeyboardLayout DTD")
dtd = re.sub(r"<[^>]+>", "", sample.group(1))
pathlib.Path(sys.argv[2]).write_text(html.unescape(dtd).strip(), encoding="utf-8")
PY
fi

curl --fail --location --silent --show-error --retry 2 \
	-o "$tmp/$US_FILENAME" "$US_URL"

verify "$tmp/$DTD_FILENAME" "$DTD_SHA256"
verify "$tmp/$US_FILENAME" "$US_SHA256"
mkdir -p "$vendor"
mv "$tmp/$DTD_FILENAME" "$tmp/$US_FILENAME" "$vendor/"
printf 'downloaded and verified:\n  %s\n  %s\n' \
	"$vendor/$DTD_FILENAME" "$vendor/$US_FILENAME"
