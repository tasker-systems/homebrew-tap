#!/usr/bin/env python3
"""Apply one temper release to this tap — the feeder's whole tap-side logic.

Called by the temper release chain's `update-homebrew-tap` job (D-H4) after
the GitHub Release is published. Everything variable comes from the release's
own artifacts, whose bytes the caller downloads and hands over; the archive
sha256s are computed HERE from those bytes, never taken from a sidecar on
faith.

Idempotent by ruling (E): applying an already-applied version renders the
committed formula byte-for-byte and commits nothing — the job skips the push.
A NEW minor renders a new formula and re-points the `temper` alias (the alias
moves only at M bumps); the README inventory row is the one deliberate manual
edit, riding the release PR.

Usage:
  script/apply_release.py --version 0.6.0 --tap . \
      --mac-archive <downloaded tar.gz> --linux-archive <downloaded tar.gz> \
      --mac-manifest <downloaded manifest.json> --linux-manifest <downloaded manifest.json>

Prints `changed=true` (commit created) or `changed=false` (no-op) as the last
line, for the calling workflow to branch on.
"""

import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import render_formula  # noqa: E402


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)  # M.m.p
    ap.add_argument("--tap", required=True, type=pathlib.Path)
    ap.add_argument("--mac-archive", required=True, type=pathlib.Path)
    ap.add_argument("--linux-archive", required=True, type=pathlib.Path)
    ap.add_argument("--mac-manifest", required=True, type=pathlib.Path)
    ap.add_argument("--linux-manifest", required=True, type=pathlib.Path)
    args = ap.parse_args()

    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        sys.exit("error: --version must be M.m.p")
    minor = args.version.rsplit(".", 1)[0]
    tap = args.tap.resolve()
    formula = tap / "Formula" / f"temper@{minor}.rb"
    alias = tap / "aliases" / "temper"

    mac_sha = sha256_file(args.mac_archive)
    linux_sha = sha256_file(args.linux_archive)
    mac_manifest_text = args.mac_manifest.read_text()
    linux_manifest_text = args.linux_manifest.read_text()
    mac_manifest_sha = hashlib.sha256(mac_manifest_text.encode()).hexdigest()
    linux_manifest_sha = hashlib.sha256(linux_manifest_text.encode()).hexdigest()

    new_minor = not formula.exists()
    text = render_formula.render(
        args.version, mac_sha, linux_sha, mac_manifest_text, linux_manifest_text
    )

    if new_minor:
        if minor == "0.5":
            # The seed formula was committed by hand-render; a feeder pass must
            # not re-create it as new and move the alias backwards.
            sys.exit(
                "error: Formula/temper@0.5.rb is missing but 0.5 is the seeded "
                "minor — the tap tree is wrong; investigate instead of re-seeding"
            )
        formula.parent.mkdir(parents=True, exist_ok=True)
        print(f"new minor {minor}: creating {formula.name} and moving the alias")
        formula.write_text(text)
        if alias.is_symlink() or alias.exists():
            alias.unlink()
        alias.symlink_to(f"../Formula/{formula.name}")
    else:
        committed = formula.read_text()
        if committed == text:
            print("no changes — the release is already applied (idempotent no-op)")
            print("changed=false")
            return 0
        print(f"updating {formula.name} in place ({args.version})")
        formula.write_text(text)

    subprocess.run(["git", "-C", str(tap), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tap),
            "-c",
            "user.name=temper release feeder",
            "-c",
            "user.email=feeder@tasker-systems.github.io",
            "commit",
            "-m",
            f"temper@{minor}: {args.version} from release v{args.version}",
        ],
        check=True,
        capture_output=True,
    )
    print("  archive shas (computed from the downloaded bytes):")
    print(f"    {render_formula.MAC_TRIPLE}  {mac_sha}")
    print(f"    {render_formula.LINUX_TRIPLE}  {linux_sha}")
    print("  manifest shas:")
    print(f"    {render_formula.MAC_TRIPLE}  {mac_manifest_sha}")
    print(f"    {render_formula.LINUX_TRIPLE}  {linux_manifest_sha}")
    print("changed=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
