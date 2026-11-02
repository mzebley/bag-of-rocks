#!/usr/bin/env bash
# Commit the plugin-only tree for the current checkout onto the release branch and push it.
# Anthropic's directory follows that branch. Run from the repository root at a release commit.
set -euo pipefail

remote="${1:-origin}"
version=$(python3 -c 'import json; print(json.load(open("package.json"))["version"])')
source_commit=$(git rev-parse --short HEAD)
tree=$(mktemp -d)
work=$(mktemp -d)
trap 'git worktree remove --force "$work" >/dev/null 2>&1 || true; rm -rf "$tree"' EXIT

python3 tools/release.py plugin-tree "$tree/plugin"

if git ls-remote --exit-code --heads "$remote" release >/dev/null 2>&1; then
  git fetch -q "$remote" release
  git worktree add -q --detach "$work" FETCH_HEAD
else
  git worktree add -q --detach "$work" HEAD
  git -C "$work" checkout -q --orphan release-new
fi

git -C "$work" rm -rq --ignore-unmatch .
cp -R "$tree/plugin/." "$work/"
git -C "$work" add -A

if git -C "$work" diff --cached --quiet; then
  echo "release branch already matches $version; nothing to push."
  exit 0
fi

git -C "$work" commit -q -m "Bag of Rocks $version" -m "Plugin files for Anthropic's directory, built from $source_commit."
git -C "$work" push -q "$remote" HEAD:refs/heads/release
echo "release branch updated to Bag of Rocks $version (from $source_commit)."
