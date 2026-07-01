#!/usr/bin/env bash
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
# docs-current: fail a PR that changes a command, skill, or config without
# updating docs/ in the same change. Docs ship with the code.
# Usage: tools/docs-current.sh [base-sha]   (defaults to the merge-base with origin/main)
set -uo pipefail

BASE="${1:-}"
if [ -z "$BASE" ]; then
  BASE="$(git merge-base HEAD origin/main 2>/dev/null || echo "")"
fi
if [ -z "$BASE" ] || ! git rev-parse --verify "$BASE" >/dev/null 2>&1; then
  echo "docs-current: no base ref to diff against; skipping."
  exit 0
fi

changed="$(git diff --name-only "$BASE"...HEAD 2>/dev/null || git diff --name-only "$BASE" HEAD)"

needs=0; hasdocs=0
echo "$changed" | grep -qE '(/commands/|plugins/[^/]+/skills/|openadlc\.example\.yaml)' && needs=1
echo "$changed" | grep -qE '(^|/)docs/' && hasdocs=1

if [ "$needs" = 1 ] && [ "$hasdocs" = 0 ]; then
  echo "docs-current: a command, skill, or config changed but docs/ did not."
  echo "Update the docs in the same PR. Stale docs are a bug."
  exit 1
fi
echo "docs-current: OK"
