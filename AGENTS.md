# Project guidance

- `src/` is the source of truth and mirrors the bundle's `Contents/` directory.
- Edit `src/Resources/Russian US Punctuation.keylayout`; never edit files under
  `build/`.
- Run `./build.sh` after changes. It validates the layout and produces
  `build/Russian US Punctuation.bundle` plus
  `build/Russian US Punctuation.bundle.zip`.
- Generate a visual check with `./tools/preview-layout.py`.

## Project goal

Russian (U.S. Punctuation) is a Russian-English bi-layout built around standard
U.S. key positions rather than conventional full-size keyboard geometry. Keep
most punctuation on the same positions as the standard U.S. layout while
placing Russian letters where they are convenient to type.

This should preserve punctuation muscle memory and make the layout practical on
programmable, non-standard keyboards such as the Moonlander, including boards
with shorter rows or punctuation keys moved to different physical locations.
Do not make layout decisions that depend unnecessarily on standard row lengths
or fixed punctuation-key placement.

## References

- Run `./tools/fetch-reference.sh` to populate ignored `reference/vendor/` files.
- URLs and hashes are pinned in `reference/sources.env`.
- Builds must remain offline; do not fetch references from `build.sh`.

## Layout invariants

- Keep XML 1.1: control-character references used by special keys require it.
- XML `ID` values must be valid names and all `IDREF`s must resolve.
- Dead-key actions need a `state="none"` branch, a terminator, and an accurate
  `maxout` value.
- Preserve Apple ABC punctuation on the base/Shift layers and reachability of all
  33 Russian letters. Option+E is the acute dead key for Russian stress marks.
- If macOS is unavailable, report that installation and live typing were not
  tested; validators and previews are not substitutes for that final check.
