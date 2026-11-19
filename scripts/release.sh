#!/usr/bin/env bash
# Build a release tarball + sha256 for the current commit. Does not tag or publish.
set -euo pipefail

VERSION="${1:-}"
[ -n "$VERSION" ] || { echo "usage: scripts/release.sh <version>  (e.g. 0.1.0)"; exit 1; }
NAME="video-explainer-kit"
PREFIX="${NAME}-${VERSION}"
GIT_SHA="$(git rev-parse --short HEAD)"
OUT="dist/${PREFIX}.tar.gz"

git diff --quiet || { echo "release.sh: uncommitted changes; commit first"; exit 1; }
git diff --cached --quiet || { echo "release.sh: staged changes; commit first"; exit 1; }

mkdir -p dist
git archive --format=tar.gz --prefix="${PREFIX}/" -o "$OUT" HEAD

printf '%s  %s\n' "$(shasum -a 256 "$OUT" | cut -d' ' -f1)" "$(basename "$OUT")" > "${OUT}.sha256"

echo "built $OUT ($(du -h "$OUT" | cut -f1)) from ${GIT_SHA}"
echo "verify: shasum -a 256 -c ${PREFIX}.tar.gz.sha256"
echo "next (maintainer):"
echo "  git tag v${VERSION} && git push origin v${VERSION}"
echo "  gh release create v${VERSION} $OUT ${OUT}.sha256 --title '${NAME} v${VERSION}'"
