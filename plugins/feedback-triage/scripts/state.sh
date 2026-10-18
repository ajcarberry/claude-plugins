#!/bin/bash
# Persist the feedback-triage queue so it survives ephemeral sessions and is shared
# by every run (intake, recheck, investigate, report — local, /loop, or CI).
#
#   state.sh pull             # before a phase: get the latest queue
#   state.sh save "<message>" # after a phase: commit (and push, in branch mode)
#
# Modes (config state.persist):
#   branch  queue lives on its own orphan branch (default feedback-triage/state),
#           checked out as a worktree at state.dir; never touches product branches
#   commit  queue is committed to the current branch (no push)
#   none    local files only
set -euo pipefail

FT="$(dirname "$0")/ft.py"
ROOT="${FT_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}}"
CFG=$(FT_PROJECT_DIR="$ROOT" python3 "$FT" config)
MODE=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"]["persist"])')
DIR=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"]["dir"])')
BRANCH=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"]["branch"])')
REMOTE=$(echo "$CFG" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"]["remote"])')
case "$DIR" in /*) ;; *) DIR="$ROOT/$DIR" ;; esac
CMD="${1:-}"
MSG="${2:-feedback-triage: update queue}"

retry() { # network ops: 4 tries, exponential backoff
  local n=0 delay=2
  until "$@"; do
    n=$((n + 1)); [ "$n" -ge 4 ] && return 1
    sleep "$delay"; delay=$((delay * 2))
  done
}

# never leave the queue mid-rebase (conflict markers in JSON break every ft call)
abort_stale_rebase() {
  local gd
  gd=$(git -C "$DIR" rev-parse --git-dir 2>/dev/null) || return 0
  case "$gd" in /*) ;; *) gd="$DIR/$gd" ;; esac
  if [ -d "$gd/rebase-merge" ] || [ -d "$gd/rebase-apply" ]; then git -C "$DIR" rebase --abort 2>/dev/null || true; fi
}

# another runner saved first and our changes conflict: keep ours on a backup branch,
# take theirs, and ask for the phase to be re-run (phases are idempotent by source ref)
recover_conflict() {
  git -C "$DIR" rebase --abort 2>/dev/null || true
  local backup="$BRANCH-conflict-$(date -u +%Y%m%dT%H%M%SZ)"
  git -C "$DIR" branch -f "$backup" HEAD
  git -C "$DIR" push -q "$REMOTE" "$backup" 2>/dev/null || true  # survive ephemeral runners
  git -C "$DIR" reset -q --hard "$REMOTE/$BRANCH"
  echo "state.sh: another runner saved conflicting queue changes. Took the remote queue; this run's commit is on branch $backup. Re-run intake/recheck/report as-is. For investigate, re-run for the same tickets and first record any PR already opened (see $backup log.jsonl) with ft.py pr. Run one writer at a time per queue." >&2
  echo "{\"persist\":\"branch\",\"pushed\":false,\"conflict\":true,\"backup\":\"$backup\"}"
  exit 3
}

ensure_branch_worktree() {
  if [ -e "$DIR/.git" ]; then return 0; fi
  # keep the worktree out of the product branch's status
  local exclude
  exclude="$(cd "$ROOT" && cd "$(git rev-parse --git-common-dir)" && pwd)/info/exclude"
  mkdir -p "$(dirname "$exclude")"
  local rel="${DIR#"$ROOT"/}/"
  grep -qxF "$rel" "$exclude" 2>/dev/null || echo "$rel" >> "$exclude"
  retry git -C "$ROOT" fetch "$REMOTE" "$BRANCH" >/dev/null 2>&1 || true
  if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
    # existing local state, no worktree yet: move it aside, adopt it after checkout
    mv "$DIR" "$DIR.adopt.$$"
  fi
  if git -C "$ROOT" show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
    git -C "$ROOT" worktree add -B "$BRANCH" "$DIR" "$REMOTE/$BRANCH" >/dev/null
  elif git -C "$ROOT" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git -C "$ROOT" worktree add "$DIR" "$BRANCH" >/dev/null
  else
    git -C "$ROOT" worktree add --detach "$DIR" >/dev/null
    git -C "$DIR" checkout --orphan "$BRANCH" >/dev/null 2>&1
    git -C "$DIR" rm -rf . >/dev/null 2>&1 || true
    printf '# feedback-triage state\n\nManaged by the feedback-triage plugin. Do not edit queue files by hand — use ft.py.\n' > "$DIR/README.md"
    printf '.lock\n*.tmp\nruns/\n' > "$DIR/.gitignore"
    printf 'log.jsonl merge=union\n' > "$DIR/.gitattributes"
    git -C "$DIR" add -A && git -C "$DIR" commit -qm "feedback-triage: initialise state branch"
  fi
  if [ -d "$DIR.adopt.$$" ]; then
    (cd "$DIR.adopt.$$" && find . -type f) | while read -r f; do
      [ -e "$DIR/$f" ] || { mkdir -p "$(dirname "$DIR/$f")"; cp "$DIR.adopt.$$/$f" "$DIR/$f"; }
    done
    rm -rf "$DIR.adopt.$$"
  fi
}

case "$MODE:$CMD" in
  none:*)
    echo '{"persist":"none","note":"local only"}' ;;
  commit:pull)
    echo '{"persist":"commit","note":"queue follows the current branch"}' ;;
  commit:save)
    printf '.lock\n*.tmp\nruns/\n' > "$DIR/.gitignore"
    git -C "$ROOT" add -- "$DIR"
    git -C "$ROOT" diff --cached --quiet -- "$DIR" || git -C "$ROOT" commit -qm "$MSG" -- "$DIR"
    echo '{"persist":"commit","saved":true}' ;;
  branch:pull)
    ensure_branch_worktree
    abort_stale_rebase
    # unsaved changes from a crashed phase: commit them so a conflict is recoverable, never left in the tree
    git -C "$DIR" add -A
    git -C "$DIR" diff --cached --quiet || git -C "$DIR" commit -qm "feedback-triage: unsaved changes from an interrupted run"
    if git -C "$ROOT" ls-remote --exit-code --heads "$REMOTE" "$BRANCH" >/dev/null 2>&1; then
      retry git -C "$DIR" fetch -q "$REMOTE" "$BRANCH"
      git -C "$DIR" rebase -q "$REMOTE/$BRANCH" >/dev/null 2>&1 || recover_conflict
    fi
    echo "{\"persist\":\"branch\",\"branch\":\"$BRANCH\",\"dir\":\"$DIR\"}" ;;
  branch:save)
    ensure_branch_worktree
    abort_stale_rebase
    if [ -n "$(git -C "$DIR" diff --name-only --diff-filter=U)" ] || ! FT_PROJECT_DIR="$ROOT" python3 "$FT" validate >/dev/null; then
      echo "state.sh: the queue is invalid (run ft.py validate) — not saving or pushing it." >&2
      exit 4
    fi
    git -C "$DIR" add -A
    git -C "$DIR" diff --cached --quiet || git -C "$DIR" commit -qm "$MSG"
    pushed=false
    for _ in 1 2 3; do
      if git -C "$DIR" push -q -u "$REMOTE" "$BRANCH" 2>/dev/null; then pushed=true; break; fi
      # rejected (someone saved first) or network: fetch, replay ours on top, try again
      retry git -C "$DIR" fetch -q "$REMOTE" "$BRANCH" || { sleep 2; continue; }
      git -C "$DIR" rebase -q "$REMOTE/$BRANCH" >/dev/null 2>&1 || recover_conflict
      FT_PROJECT_DIR="$ROOT" python3 "$FT" validate >/dev/null || recover_conflict
    done
    echo "{\"persist\":\"branch\",\"saved\":true,\"pushed\":$pushed}" ;;
  *)
    echo "usage: state.sh pull | save \"<message>\"" >&2; exit 1 ;;
esac
