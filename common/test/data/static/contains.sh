#!/usr/bin/env zsh
# shellcheck disable=all
# ^ This is zsh, which shellcheck doesn't support.
git log --all ^opaque-keys-merge-base --format=%H $1 | while read f; do git branch --contains $f; done | sort -u
