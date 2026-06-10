class R105 < Formula
  include Language::Python::Virtualenv

  desc "r105 — Beyond the prompt. Rich terminal AI assistant for any OpenAI-compatible backend."
  homepage "https://github.com/bnelabs/r105"
  url "https://files.pythonhosted.org/packages/source/r/r105/r105-0.3.0.tar.gz"
  sha256 "4550b963b6479fa4b7d50c42c57bdb7b0948a5a48db6fc4f0403be1b56b78290"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "r105 #{version}", shell_output("#{bin}/r105 --version")
  end
end
