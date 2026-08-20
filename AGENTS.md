# Project guidance

- `src/` is the source of truth and mirrors the bundle's `Contents/` directory.
- Edit `src/Resources/Russian US Punctuation.keylayout`; never edit files under
  `build/`.
- After a layout change run `./tools/check-keylayout.py` to validate it, then
  `./tools/preview-layout.py` to refresh the committed `docs/preview.svg` that
  the README embeds. Commit that refresh; CI fails when the preview is stale.
- Develop and check here; do not build here. `./build.sh` assembles, validates
  and packages the bundle, and GitHub Actions runs it on every push. A local
  build is not useful on Linux, where the result cannot be installed or typed on.

## Project goal

Russian – U.S. Punctuation is a macOS keyboard layout for typing Russian. Keep
most punctuation on the same positions as the standard U.S. layout while
placing Russian letters where they are convenient to type.

This should preserve punctuation muscle memory and make the layout practical on
programmable keyboards such as the Moonlander, including boards with shorter
rows or punctuation keys moved to different physical locations. Keep layout
decisions independent of row length and of where punctuation keys sit.

## References

- Run `./tools/fetch-reference.sh` to populate ignored `reference/vendor/` files.
- URLs and hashes are pinned in `reference/sources.env`.
- Builds must remain offline; do not fetch references from `build.sh`.

## Releases

- Cut a release by pushing an annotated `v*` tag. GitHub Actions builds the
  tagged commit and uploads the assets; never upload them by hand.
- The tag message becomes the release notes, so write them there:
  `git tag -a v1.2.0 -F notes.md`. A bare version string yields empty notes.
- Bump `CFBundleShortVersionString`, `CFBundleVersion` and `SourceVersion` under
  `src/` when the layout changes, so macOS sees a new bundle version.

## Layout invariants

- Keep XML 1.1: control-character references used by special keys require it.
- XML `ID` values must be valid names and all `IDREF`s must resolve.
- Dead-key actions need a `state="none"` branch, a terminator, and an accurate
  `maxout` value.
- Preserve Apple ABC punctuation on the base/Shift layers and reachability of all
  33 Russian letters. Option+E is the acute dead key for Russian stress marks.
- The `<keyboard name>`, the `.keylayout` file stem and the `KLInfo_` key in
  `Info.plist` must be one identical string. When they disagree macOS silently
  ignores the whole `KLInfo_` dict and synthesizes its own input source ID from
  the bundle identifier. The user-visible name is the value in
  `InfoPlist.strings` keyed on that string, never the `name` attribute itself.
