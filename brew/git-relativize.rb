require "formula"

class Git_Relativize < Formula
  version "0.0.1"
  desc "Fix git subrepositories with absolute paths"
  url "https://gitlab.xcade.net/avature/git-relativize.git", :using => :git
  homepage "https://gitlab.xcade.net/avature/git-relativize"
  depends_on :python, :git

  include Language::Python::Virtualenv

  def install
     virtualenv_install_with_resources
  end
end
