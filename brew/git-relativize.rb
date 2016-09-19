require "formula"

class GitRelativize < Formula
  version "0.0.1"
  desc "Fix git subrepositories with absolute paths"
  url "https://gitlab.xcade.net/javier.santacruz/git-relativize.git", :using => :git
  homepage "https://gitlab.xcade.net/javier.santacruz/git-relativize"
  depends_on :python
  depends_on "git"

  include Language::Python::Virtualenv

  def install
     virtualenv_install_with_resources
  end
end
