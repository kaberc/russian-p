# Reference material

Reference payloads are downloaded explicitly and are not committed:

```sh
./tools/fetch-reference.sh
```

The script writes to the ignored `reference/vendor/` directory. It never runs
from `build.sh`, so ordinary builds stay offline. URLs and SHA-256 hashes are
locked in `sources.env`; a changed upstream file is rejected rather than
silently accepted.

## KeyboardLayout.dtd

**Authoritative.** Apple's DTD for the `.keylayout` format.

On macOS the fetcher prefers Apple's installed copy at
`/System/Library/DTDs/KeyboardLayout.dtd`. Elsewhere it extracts the DTD from
Apple Technote TN2056:

<https://developer.apple.com/library/archive/technotes/tn2056/_index.html>

The public DTD URL named by old layouts now returns 404. The pinned hash is:

```text
86587806c28bdf8ee7c5c596fa690fde786208b65d6e33d273787e7125a5f639
```

`tools/check-keylayout.py` uses this file for full DTD validation when both the
file and either `xmllint` or Python `lxml` are available. `xmllint` ships with
macOS. Without the file, the checker prints the exact fetch command and still
runs its standard-library structural checks.

## US-extracted.keylayout

**Useful, not authoritative.** A community extraction of a macOS system U.S.
layout, pinned to gist revision
`6e07fe693157d05de9cfe1ef0c23a4797e56e3ee`:

<https://gist.github.com/paiv/a396403b890647e0faa22b03d7d5f573>

It is named **U.S.** (id 0), not **ABC** (id 252), is undated, and cannot be
treated as Apple's latest XML source. Apple has shipped stock layouts as
compiled data since macOS 10.5, so no official readable XML is available.

The file is retained as a behavioral reference because it establishes Apple's
dead-key idiom:

- Five dead keys in the plain-Option map: acute, grave, circumflex, diaeresis,
  and tilde.
- Spacing terminators U+00B4, U+0060, U+02C6, U+00A8, and U+02DC.
- `maxout="2"`, with decomposed `J`/`j` + U+0301 where Unicode has no
  precomposed acute character. Russian (U.S. Punctuation) follows that
  precedent for stressed Russian vowels.

The extraction itself fails DTD validation because several generated XML IDs
begin with digits. Use it to compare behavior, not as a validity model. Its
pinned hash is:

```text
9c1a8b3e9a42e37df2a6773fe49ead7afd3a15c4eead843d2938a02889e00b71
```
