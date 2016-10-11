#!/bin/bash -eu

if test $# -ne 1; then
    echo "Missing version number"
    exit 1
fi

VERSION=$1

echo "Running tests"
tox --recreate > /dev/null
dch -v $VERSION
git commit -am "Bumps version $VERSION"
git tag $VERSION -am "Version $VERSION"
