# Rendered by script/render_formula.py from template/temper@MINOR.rb.template — do not edit by hand.
class TemperAT05 < Formula
  desc "Knowledge base for AI-assisted development (temper CLI)"
  homepage "https://github.com/tasker-systems/temper"
  license "MIT"

  # Release CI builds darwin-arm64 only (build-cli-binaries.yml); Intel macs
  # and Windows stay on the script installers.
  if OS.mac?
    depends_on arch: :arm64
    url "https://github.com/tasker-systems/temper/releases/download/v0.5.4/temper-v0.5.4-aarch64-apple-darwin.tar.gz"
    sha256 "db0fe626dab895b653565f55f7eefe47d47165e9fc723803caa91997b34c22f2"
  else
    url "https://github.com/tasker-systems/temper/releases/download/v0.5.4/temper-v0.5.4-x86_64-unknown-linux-gnu.tar.gz"
    sha256 "57fc5d35d14d45d504db73fd8d52f46c299ac27820d511b9fa300b9dea576f6c"
  end

  def install
    # The tree root is `libexec` — deliberately NOT the keg root: brew links
    # keg-root `lib/` into the prefix, and a bundled dylib there collides with
    # any onnxruntime formula. Only `temper` is symlinked into bin; the binary
    # self-locates its dylib and model beside a symlink-resolved exe.
    libexec.install "temper", "lib", "models", "LICENSE", "README-INSTALL.txt"
    (libexec/"BREW-MANAGED").write <<~MARKER
      This temper install is managed by Homebrew.
      Update with: brew upgrade tasker-systems/tap/temper@0.5
      `temper update` refuses here on purpose: this binary is not authoritative for its own update.
    MARKER
    bin.install_symlink libexec/"temper"
  end

  def post_install
    require "digest"
    require "fileutils"
    require "json"

    # Homebrew relocates recognized metadata (LICENSE) to the keg root and
    # finalizes Mach-O files (dynamic-linkage fixups + ad-hoc re-signing with
    # per-install random identifiers) BEFORE this hook runs. The release
    # manifest describes pre-install bytes and would mismatch forever; this
    # manifest is computed from the tree AS INSTALLED, which is exactly what
    # offline `temper version --verify` should prove: nothing has drifted
    # since brew installed it. Artifact provenance stays with brew's own
    # chain — the formula pins the release's archive digest, verified at
    # download. `temper version --verify --online` on a brew install reports
    # that boundary rather than comparing transformed bytes against published
    # ones.
    FileUtils.cp(prefix/"LICENSE", libexec/"LICENSE")

    files = Dir.glob("#{libexec}/**/*")
               .select { |p| File.file?(p) }
               .sort
               .filter_map do |p|
                 rel = Pathname.new(p).relative_path_from(libexec).to_s
                 next if [".temper-manifest.json", "BREW-MANAGED"].include?(rel)

                 {
                   "path"    => rel,
                   "sha256"  => Digest::SHA256.file(p).hexdigest,
                   "size"    => File.size(p),
                 }
               end

    (libexec/".temper-manifest.json").write(
      JSON.pretty_generate({
        "version" => version.to_s,
        "target"  => OS.mac? ? "aarch64-apple-darwin" : "x86_64-unknown-linux-gnu",
        "files"   => files,
      }) + "\n",
    )
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/temper version")
  end
end
