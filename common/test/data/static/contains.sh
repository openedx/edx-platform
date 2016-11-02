#!/usr/bin/env zsh
git log --all ^opaque-keys-merge-base --format=%H $1 | while read f; do git branch --contains $f; done | sort -u
