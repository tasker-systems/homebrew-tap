# template/ — the formula shape's only home

`temper@MINOR.rb.template` is the ONLY source of formula shape.
`script/render-formula.sh` fills its substitution tokens from a release's own
artifacts — the archive sha256 sidecars (caller-computed from the downloaded
bytes) and the per-triple manifest asset inlined verbatim — and writes
`Formula/temper@<minor>.rb`. No hand-maintained copy of the shape exists
anywhere: a shape change is a change here plus a re-render; a new minor is a
render with new variables; never an edit of a rendered file.

## Tokens

- `@FORMULA_CLASS@` — derived (`TemperAT05` for minor 0.5)
- `@FORMULA_NAME@` — derived (`temper@0.5`)
- `@DESC@` — fixed text
- `@VERSION@` — the released version (`0.5.1`)
- `@MAC_URL@` `@MAC_SHA@` — darwin-arm64 archive URL + caller-computed sha256
- `@LINUX_URL@` `@LINUX_SHA@` — linux-x64 archive URL + caller-computed sha256
- `@MANIFEST_CONTENTS@` — the darwin-arm64 manifest asset's bytes, inlined
  verbatim (parse-checked, never re-formatted). This is what the brew install
  writes as `.temper-manifest.json`, so `temper version --verify` reads the
  release's own digests on both channels.

## Why the install list is explicit

The binary self-locates ONNX Runtime and the embedding model beside a
symlink-resolved exe (`embed.rs` `canonicalized_exe`), and `temper version
--verify` checks every entry of `.temper-manifest.json` against the install
tree — so the install must be the WHOLE manifest set, exactly as install.sh
extracts it. The explicit `libexec.install` list mirrors today's archive
contents; if a release archive grows a file, verify fails loudly until this
template's install list follows. Silent omission would be drift.
