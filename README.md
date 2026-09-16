# tasker-systems homebrew tap

Versioned formulae for tasker-systems CLIs — **one formula per minor**, mirroring
the wire-contract pins ([`schemas/versions/<M.m>/`](https://github.com/tasker-systems/temper/tree/main/schemas/versions)
in the temper repo): a fleet Brewfile pins a minor the same way a client pins a
contract.

## Install

```sh
brew install tasker-systems/tap/temper@0.5   # pinned to the 0.5 wire contract
brew install tasker-systems/tap/temper       # alias — the current minor only
```

Fleet pinning is a Brewfile line:

```ruby
brew "tasker-systems/tap/temper@0.5"
```

The `temper` alias moves only when a new minor's formula lands, so the alias
floats per-minor, never per-patch.

## Upgrade discipline

- **Patches** (`0.5.1 → 0.5.2`): `brew upgrade tasker-systems/tap/temper@0.5` — safe by
  construction; within a minor the wire contract is additive-only (both skew directions),
  and the formula updates in place with the release's own digests.
- **Minors** (`0.5 → 0.6`): a NEW formula appears (`temper@0.6`). Moving your Brewfile to
  it is a deliberate edit — the same deliberate, signaled act the M bump is on the wire.

## `temper update` on a brew install

It refuses, on purpose. The install carries a `BREW-MANAGED` marker beside the binary:
this binary is not authoritative for its own update — `brew upgrade` is the only
updater here. `temper update --check` still reports what's newer.

## Verification

- **Offline** — `temper version --verify` proves the installed tree matches what brew
  installed: the formula computes `.temper-manifest.json` from the ACTUAL installed files
  at post-install (Homebrew re-signs Mach-O and relocates metadata at keg finalization,
  so the release's own pre-install manifest cannot describe the keg byte-for-byte).
- **Online** — `temper version --verify --online` on a brew install reports the boundary
  honestly (`unverifiable`): artifact provenance here is brew's own chain — the formula
  pins the release's archive digest, verified by brew at download — and temper's
  attestation check describes the script-installer path.

## How releases feed this tap

The temper release chain renders each formula from the release's own artifacts —
`script/render_formula.py` fills `template/temper@MINOR.rb.template` with URLs and the
digests of the release's own bytes. No formula is ever hand-edited; a rendered formula
says so in its first line. The `update-homebrew-tap` job in the temper repo's release
workflow applies every release automatically; a new minor also moves the `temper` alias.

## Formula inventory

| Formula | Wire contract | Since |
|---|---|---|
| `temper@0.5` | pin `schemas/versions/0.5/` | v0.5.1 (seeded) |
