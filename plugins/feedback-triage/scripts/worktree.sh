#!/bin/bash
# Ticket worktrees: isolated checkouts for repro and low-tier changes, so parallel
# investigators never share a working tree and the main checkout stays clean.
#
#   worktree.sh create FT-0007 <slug>   # → prints the worktree path; branch <prefix><slug> (no ticket id:
#                                       #   branch names can reach PRs and reports)
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
# inside the project (headless permission modes allow edits there), excluded from git
WT="$ROOT/.ft-worktrees/$LOWER"
SETUP=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["investigate"].get("setup") or "")')

case "$CMD" in
  create)
    SLUG=$(echo "${3:-change}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
    if [ ${#SLUG} -gt 40 ]; then SLUG=$(echo "$SLUG" | cut -c1-41 | sed -E 's/-[^-]*$//'); fi
    if [ -d "$WT" ]; then echo "$WT"; exit 0; fi
    BRANCH="${PREFIX}${SLUG}"; n=2
    while git -C "$ROOT" show-ref --verify --quiet "refs/heads/$BRANCH"; do BRANCH="${PREFIX}${SLUG}-$n"; n=$((n + 1)); done
    EXCLUDE="$(cd "$ROOT" && cd "$(git rev-parse --git-common-dir)" && pwd)/info/exclude"
    mkdir -p "$(dirname "$EXCLUDE")"; grep -qxF '.ft-worktrees/' "$EXCLUDE" 2>/dev/null || echo '.ft-worktrees/' >> "$EXCLUDE"
    git -C "$ROOT" fetch -q "$REMOTE" "$BASE" 2>/dev/null || true
    START="$BASE"
    git -C "$ROOT" show-ref --verify --quiet "refs/remotes/$REMOTE/$BASE" && START="$REMOTE/$BASE"
    git -C "$ROOT" worktree add -q -b "$BRANCH" "$WT" "$START"
    # project-defined environment setup (deps, codegen) so repros run like CI
    if [ -n "$SETUP" ]; then (cd "$WT" && bash -c "$SETUP") >"$WT/.ft-setup.log" 2>&1 || echo "setup failed — see $WT/.ft-setup.log" >&2; fi
    echo "$WT" ;;
  remove)
    [ -d "$WT" ] && git -C "$ROOT" worktree remove --force "$WT"
    echo "removed $WT" ;;
  discard)
    [ -d "$WT" ] || { echo "nothing to discard: $WT"; exit 0; }
    B=$(git -C "$WT" branch --show-current 2>/dev/null || true)
    git -C "$ROOT" worktree remove --force "$WT"
    # keep a branch that failed review: it is one of the ticket's options now
    KEEP=$(FT_PROJECT_DIR="$ROOT" python3 "$FT" get "$ID" 2>/dev/null | python3 -c 'import json,sys; print((json.load(sys.stdin).get("investigation") or {}).get("prior_attempt") or "")' 2>/dev/null || true)
    if [ -n "$B" ] && [ "$B" != "$KEEP" ]; then git -C "$ROOT" branch -q -D "$B"; fi
    echo "discarded $WT" ;;
  path)
    [ -d "$WT" ] && echo "$WT" || exit 1 ;;
  *)
    echo "usage: worktree.sh create|remove|discard|path FT-NNNN [slug]" >&2; exit 1 ;;
esac
