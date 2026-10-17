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

ensure_branch_worktree() {
  if [ -e "$DIR/.git" ]; then return 0; fi
  # keep the worktree out of the product branch's status
  local exclude
  exclude="$(git -C "$ROOT" rev-parse --git-common-dir)/info/exclude"
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
    if git -C "$ROOT" ls-remote --exit-code --heads "$REMOTE" "$BRANCH" >/dev/null 2>&1; then
      retry git -C "$DIR" pull --rebase -q "$REMOTE" "$BRANCH"
    fi
    echo "{\"persist\":\"branch\",\"branch\":\"$BRANCH\",\"dir\":\"$DIR\"}" ;;
  branch:save)
    ensure_branch_worktree
    git -C "$DIR" add -A
    git -C "$DIR" diff --cached --quiet || git -C "$DIR" commit -qm "$MSG"
    pushed=false
    for _ in 1 2 3; do
      if retry git -C "$DIR" push -q -u "$REMOTE" "$BRANCH"; then pushed=true; break; fi
      # someone else saved first: replay ours on top (ft.py writes whole files per ticket)
      git -C "$DIR" pull --rebase -q "$REMOTE" "$BRANCH" || { git -C "$DIR" rebase --abort; break; }
    done
    python3 "$FT" validate >/dev/null || echo "WARNING: queue validation failed after save — run ft.py validate" >&2
    echo "{\"persist\":\"branch\",\"saved\":true,\"pushed\":$pushed}" ;;
  *)
    echo "usage: state.sh pull | save \"<message>\"" >&2; exit 1 ;;
esac
