# Russian – U.S. Punctuation

Russian – U.S. Punctuation is a macOS keyboard layout for typing Russian. It
places all 33 Russian letters within easy reach and leaves punctuation on the
base and Shift layers where the standard U.S. layout puts it.

The layout suits conventional keyboards and programmable boards such as the
Moonlander equally, including boards with shorter rows or punctuation keys in
different physical positions.

[![Russian – U.S. Punctuation keyboard layout preview](docs/preview.svg)](https://github.com/kaberc/russian-p/releases/latest)

## Features

- U.S./ABC punctuation on the base and Shift layers.
- All 33 Russian letters.
- Latin letters on the `Command` layer, so `⌘C` and `⌘V` keep their U.S. keys.
- `Option`+`E` acute dead key for Russian stress marks.
- Localized English and Russian display names.
- No static icon, allowing macOS to use its generic keyboard-layout icon.

## Install

1. Download `Russian.US.Punctuation.bundle.zip` from the
   [latest release](https://github.com/kaberc/russian-p/releases/latest).
2. Extract the archive.
3. Copy `Russian US Punctuation.bundle` to `~/Library/Keyboard Layouts/`.
4. Clear the quarantine flag the browser set on the download. macOS refuses to
   register a quarantined layout:

   ```sh
   xattr -dr com.apple.quarantine "$HOME/Library/Keyboard Layouts/Russian US Punctuation.bundle"
   ```

5. Log out of macOS and log back in.
6. Open **System Settings → Keyboard → Text Input → Input Sources**, then add
   **Russian – U.S. Punctuation**.

To install from Terminal after extracting the archive:

```sh
mkdir -p "$HOME/Library/Keyboard Layouts"
cp -R "Russian US Punctuation.bundle" "$HOME/Library/Keyboard Layouts/"
xattr -dr com.apple.quarantine "$HOME/Library/Keyboard Layouts/Russian US Punctuation.bundle"
```

## Build

The editable bundle contents live under `src/`. Build the installable bundle
and ZIP archive with:

```sh
./build.sh
```

Outputs are written to `build/`:

- `Russian US Punctuation.bundle`
- `Russian US Punctuation.bundle.zip`

The build validates the keyboard layout before packaging it. For full
validation against Apple's pinned `KeyboardLayout.dtd`, fetch the reference
files first:

```sh
./tools/fetch-reference.sh
./build.sh
```

Reference downloads are hash-verified and are never fetched by `build.sh`, so
ordinary builds remain offline.

Released archives are not built locally. Pushing a `v*` tag runs the same
`build.sh` on GitHub Actions, and the assets on the releases page come from
that build of the tagged commit.

## Preview

The SVG overview at the top of this page is generated. Refresh it after a
layout change with:

```sh
./tools/preview-layout.py
```

It rewrites `docs/preview.svg`; commit that with the layout change, as the
build workflow fails on a stale copy. Validate a layout on its own with:

```sh
./tools/check-keylayout.py
```

GitHub Actions also publishes the bundle ZIP and preview as artifacts for every
push and pull request.
