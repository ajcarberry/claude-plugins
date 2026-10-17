#!/bin/bash
# Ticket worktrees: isolated checkouts for repro and low-tier changes, so parallel
# investigators never share a working tree and the main checkout stays clean.
#
#   worktree.sh create FT-0007 <slug>   # → prints the worktree path; branch ft/FT-0007-<slug>
#   worktree.sh remove FT-0007          # removes the worktree, keeps the branch
#   worktree.sh discard FT-0007         # removes the worktree AND its ft/ branch (non-low tiers)
#   worktree.sh path FT-0007            # prints the path if it exists
set -euo pipefail

FT="$(dirname "$0")/ft.py"
ROOT="${FT_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}}"
CFG=$(FT_PROJECT_DIR="$ROOT" python3 "$FT" config)
BASE=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["investigate"]["base_branch"])')
PREFIX=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["investigate"]["branch_prefix"])')
REMOTE=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"]["remote"])')

CMD="${1:-}"
ID=$(echo "${2:-}" | tr '[:lower:]' '[:upper:]')
[[ "$ID" =~ ^FT-[0-9]{4,}$ ]] || { echo "usage: worktree.sh create|remove|discard|path FT-NNNN [slug]" >&2; exit 1; }
LOWER=$(echo "$ID" | tr '[:upper:]' '[:lower:]')
WT="$(dirname "$ROOT")/$(basename "$ROOT")--$LOWER"

case "$CMD" in
  create)
    SLUG=$(echo "${3:-change}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g' | cut -c1-41 | sed -E 's/-[^-]*$//; s/-+$//')
    BRANCH="${PREFIX}${ID}-${SLUG}"
    if [ -d "$WT" ]; then echo "$WT"; exit 0; fi
    git -C "$ROOT" fetch -q "$REMOTE" "$BASE" 2>/dev/null || true
    START="$BASE"
    git -C "$ROOT" show-ref --verify --quiet "refs/remotes/$REMOTE/$BASE" && START="$REMOTE/$BASE"
    if git -C "$ROOT" show-ref --verify --quiet "refs/heads/$BRANCH"; then
      git -C "$ROOT" worktree add -q "$WT" "$BRANCH"
    else
      git -C "$ROOT" worktree add -q -b "$BRANCH" "$WT" "$START"
    fi
    echo "$WT" ;;
  remove)
    [ -d "$WT" ] && git -C "$ROOT" worktree remove --force "$WT"
    echo "removed $WT" ;;
  discard)
    [ -d "$WT" ] && git -C "$ROOT" worktree remove --force "$WT"
    for b in $(git -C "$ROOT" for-each-ref --format='%(refname:short)' "refs/heads/${PREFIX}${ID}-*"); do
      git -C "$ROOT" branch -q -D "$b"
    done
    echo "discarded $WT" ;;
  path)
    [ -d "$WT" ] && echo "$WT" || exit 1 ;;
  *)
    echo "usage: worktree.sh create|remove|discard|path FT-NNNN [slug]" >&2; exit 1 ;;
esac
