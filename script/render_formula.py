#!/usr/bin/env python3
"""Render Formula/temper@<minor>.rb from template/temper@MINOR.rb.template.

The template is the only source of formula shape; this script is the only way
a formula comes into existence. Everything variable is either derived from
--version or handed in as a digest computed from the release's OWN bytes (the
caller downloads and hashes; this script never guesses).

Usage:
  script/render_formula.py --version 0.5.1 \
      --mac-sha <sha256 of darwin-arm64 archive> \
      --linux-sha <sha256 of linux-x64 archive> \
      --mac-manifest <path to darwin manifest.json> \
      --linux-manifest <path to linux manifest.json> \
      [--out Formula/temper@0.5.rb]

The URLs are derived from the version: release assets are named
temper-v<VERSION>-<triple>.<ext> under the v<VERSION> tag — one fact, one
source. The per-triple manifest is inlined verbatim (parse-checked, never
re-formatted) into the formula as OS-selected constants; its digest is echoed
so the caller's PR record carries it.
"""

import argparse
import hashlib
import json
import pathlib
import re
import sys

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "template" / "temper@MINOR.rb.template"
MAC_TRIPLE = "aarch64-apple-darwin"
LINUX_TRIPLE = "x86_64-unknown-linux-gnu"


def render(
    version: str,
    mac_sha: str,
    linux_sha: str,
    mac_manifest_text: str,
    linux_manifest_text: str,
    minor: str | None = None,
) -> str:
    """Produce the formula text for one release — the single render path.
    apply_release.py calls this too, so no second copy of the shape logic
    exists anywhere."""
    if minor is None:
        minor = version.rsplit(".", 1)[0]
    base = f"https://github.com/tasker-systems/temper/releases/download/v{version}"
    mac_url = f"{base}/temper-v{version}-{MAC_TRIPLE}.tar.gz"
    linux_url = f"{base}/temper-v{version}-{LINUX_TRIPLE}.tar.gz"

    # The manifest content must be the release asset's own bytes, written
    # verbatim: parse only to prove it is valid JSON, never re-format.
    json.loads(mac_manifest_text)
    json.loads(linux_manifest_text)

    # The cop requires 4-space heredoc indentation; `<<~` strips exactly that
    # common prefix at runtime, so what the formula WRITES stays byte-identical
    # to the release asset. Assert the round-trip rather than assume it.
    def indent2(asset_text: str) -> str:
        had_final_newline = asset_text.endswith("\n")
        lines = [f"    {line}" if line else line for line in asset_text.splitlines()]
        round_trip = "\n".join(line[4:] for line in lines) + ("\n" if had_final_newline else "")
        if round_trip != asset_text:
            sys.exit("error: 4-space indent round-trip is not byte-identical")
        return "\n".join(lines)

    text = TEMPLATE.read_text()
    repl = {
        "@FORMULA_CLASS@": f"TemperAT{minor.replace('.', '')}",
        "@FORMULA_NAME@": f"temper@{minor}",
        "@DESC@": "Knowledge base for AI-assisted development (temper CLI)",
        "@MAC_URL@": mac_url,
        "@MAC_SHA@": mac_sha,
        "@LINUX_URL@": linux_url,
        "@LINUX_SHA@": linux_sha,
        "@MAC_MANIFEST_CONTENTS@": indent2(mac_manifest_text),
        "@LINUX_MANIFEST_CONTENTS@": indent2(linux_manifest_text),
    }
    for token, value in repl.items():
        text = text.replace(token, value)
    leftover = re.findall(r"@[A-Z_]+@", text)
    if leftover:
        sys.exit(f"error: unsubstituted tokens remain: {sorted(set(leftover))}")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)  # M.m.p
    ap.add_argument("--mac-sha", required=True)
    ap.add_argument("--linux-sha", required=True)
    ap.add_argument("--mac-manifest", required=True, type=pathlib.Path)
    ap.add_argument("--linux-manifest", required=True, type=pathlib.Path)
    ap.add_argument("--out")
    args = ap.parse_args()

    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        sys.exit("error: --version must be M.m.p")
    minor = args.version.rsplit(".", 1)[0]
    for name, sha in (("--mac-sha", args.mac_sha), ("--linux-sha", args.linux_sha)):
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            sys.exit(f"error: {name} must be a 64-hex sha256")
    for flag, p in (("--mac-manifest", args.mac_manifest), ("--linux-manifest", args.linux_manifest)):
        if not p.is_file():
            sys.exit(f"error: {flag} must be an existing file")

    mac_manifest_text = args.mac_manifest.read_text()
    linux_manifest_text = args.linux_manifest.read_text()
    mac_manifest_sha = hashlib.sha256(mac_manifest_text.encode()).hexdigest()
    linux_manifest_sha = hashlib.sha256(linux_manifest_text.encode()).hexdigest()

    text = render(args.version, args.mac_sha, args.linux_sha, mac_manifest_text, linux_manifest_text)
    out = pathlib.Path(args.out) if args.out else pathlib.Path(f"Formula/temper@{minor}.rb")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"rendered {out}")
    print("  archive shas (caller-supplied):")
    print(f"    {MAC_TRIPLE}  {args.mac_sha}")
    print(f"    {LINUX_TRIPLE}  {args.linux_sha}")
    print("  manifest shas (computed here from the provided files):")
    print(f"    {MAC_TRIPLE}  {mac_manifest_sha}")
    print(f"    {LINUX_TRIPLE}  {linux_manifest_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
