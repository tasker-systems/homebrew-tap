# Rendered by script/render_formula.py from template/temper@MINOR.rb.template — do not edit by hand.
class TemperAT05 < Formula
  desc "Knowledge base for AI-assisted development (temper CLI)"
  homepage "https://github.com/tasker-systems/temper"
  license "MIT"

  # Release CI builds darwin-arm64 only (build-cli-binaries.yml); Intel macs
  # and Windows stay on the script installers.
  if OS.mac?
    depends_on arch: :arm64
    url "https://github.com/tasker-systems/temper/releases/download/v0.5.1/temper-v0.5.1-aarch64-apple-darwin.tar.gz"
    sha256 "a4870d46b72f5cbce2025dda5b161863567d5e1c6b7fb32012c3dca345dad55c"
  else
    url "https://github.com/tasker-systems/temper/releases/download/v0.5.1/temper-v0.5.1-x86_64-unknown-linux-gnu.tar.gz"
    sha256 "7e1cfad7a47135d9a12ea6ea934f1989af48b75547f76edff48597d694822835"
  end

  # The release's own per-triple manifests, inlined at render time from the
  # release assets (parse-checked, never re-formatted). The one matching this
  # OS is installed as `.temper-manifest.json` beside the tree — the same
  # baseline install.sh writes — so `temper version --verify` reads identical
  # digests on script and brew channels. The contents are the release's own
  # bytes; the render-time digest echo keeps them from ever drifting.
  MAC_MANIFEST = <<~MANIFEST.freeze
    {
      "version": "0.5.1",
      "target": "aarch64-apple-darwin",
      "files": [
        {
          "path": "LICENSE",
          "sha256": "85860ec4384c14c5f0d197c87c8d65dbff74608951bee3b9c10785037a94a97b",
          "size": 1071
        },
        {
          "path": "README-INSTALL.txt",
          "sha256": "2cd8c9a2af047b4a6f5bbc3d765c67bd242bda1cb3ed1df08ca3144e96be39a5",
          "size": 353
        },
        {
          "path": "lib/libonnxruntime.dylib",
          "sha256": "87df6f94dd559ea958748adc80fd4c46d91c52bc025771f513291d155539590a",
          "size": 35361512
        },
        {
          "path": "models/model_quantized.onnx",
          "sha256": "c9729cc84cbd0e9fecc759505d2be65916c9fe05222d7ea26c65fcb3382af38d",
          "size": 110083337
        },
        {
          "path": "temper",
          "sha256": "e8b0d8594974f1a30f876f918f775b3d2c51f8ef4e3210fd50fcefc8ce460ab3",
          "size": 30005344
        }
      ]
    }
  MANIFEST
  LINUX_MANIFEST = <<~MANIFEST.freeze
    {
      "version": "0.5.1",
      "target": "x86_64-unknown-linux-gnu",
      "files": [
        {
          "path": "LICENSE",
          "sha256": "85860ec4384c14c5f0d197c87c8d65dbff74608951bee3b9c10785037a94a97b",
          "size": 1071
        },
        {
          "path": "README-INSTALL.txt",
          "sha256": "8377353e31f3a2dfaa823dd8ddee2180a2e966091c930204098ef81b22c6f32b",
          "size": 357
        },
        {
          "path": "lib/libonnxruntime.so",
          "sha256": "ffc84d48e845cf0b562ba4ea5ca32aaafc0d4069019fef4f63095b307d0270ad",
          "size": 22065056
        },
        {
          "path": "models/model_quantized.onnx",
          "sha256": "c9729cc84cbd0e9fecc759505d2be65916c9fe05222d7ea26c65fcb3382af38d",
          "size": 110083337
        },
        {
          "path": "temper",
          "sha256": "01b6e410fba4a136472c455d770f4d05214bb5c864f16a8240d74db54195600a",
          "size": 37675904
        }
      ]
    }
  MANIFEST

  def install
    # The whole archive tree installs under libexec and only `temper` is
    # symlinked into bin. The binary self-locates ONNX Runtime and the
    # embedding model beside a symlink-resolved exe, and `temper version
    # --verify` checks every entry of `.temper-manifest.json` against the
    # install tree — so the install must be the WHOLE manifest set, exactly
    # as install.sh extracts it. If a release archive grows a file, verify
    # fails loudly until this template's install list follows; silent
    # omission would be drift. Shape rationale: template/README.md.
    libexec.install "temper", "lib", "models", "LICENSE", "README-INSTALL.txt"
    (libexec/".temper-manifest.json").write(OS.mac? ? MAC_MANIFEST : LINUX_MANIFEST)
    (libexec/"BREW-MANAGED").write <<~MARKER
      This temper install is managed by Homebrew.
      Update with: brew upgrade tasker-systems/tap/temper@0.5
      `temper update` refuses here on purpose: this binary is not authoritative for its own update.
    MARKER
    bin.install_symlink libexec/"temper"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/temper version")
  end
end
