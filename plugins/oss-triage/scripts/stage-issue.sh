#!/usr/bin/env bash
# Write <work dir>/repro/<n>/issue.md with the issue body and every comment, live from GitHub.
# Usage: stage-issue.sh <owner/repo> <work dir> <issue number>
set -euo pipefail
REPO="$1"; WORK="$2"; N="$3"
D="$WORK/repro/$N"; mkdir -p "$D"
{
  gh api "repos/$REPO/issues/$N" --jq '"TITLE: \(.title)\nBY: \(.user.login) (\(.author_association)) \(.created_at)\nSTATE: \(.state) labels=\([.labels[].name]|join(","))\n\n\(.body // "")\n\n## Comments\n"'
  gh api "repos/$REPO/issues/$N/comments?per_page=100" --jq '.[] | "[\(.user.login) \(.author_association) \(.created_at[:16])]\n\(.body)\n"'
} > "$D/issue.md"
echo "$D/issue.md"
