require "formula"

class GitRelativize < Formula
  version "0.0.1"
  desc "Fix git subrepositories with absolute paths"
  url "https://github.com/Avature/git-relativize.git", :using => :git
  homepage "https://github.com/Avature/git-relativize"
  depends_on :python
  depends_on "git"

  include Language::Python::Virtualenv

  def install
     virtualenv_install_with_resources
  end
end
