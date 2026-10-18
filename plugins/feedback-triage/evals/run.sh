#!/bin/bash
# Behavioral eval: run a feedback-triage phase headless against a scenario project.
#
#   SCENARIO=fixtures|realworld evals/run.sh setup <workdir>
#   evals/run.sh intake|investigate|report|recheck <workdir> [args]
#
# fixtures  — synthetic tasklite app with planted bugs (fast, fully known truth)
# realworld — python-humanize/humanize at HEAD + a snapshot of its real issues
#             (needs a clone at $HUMANIZE, default /home/user/python-humanize/humanize)
# lore      — epicgames/lore (Rust) at HEAD + a snapshot of its real issues
#             (needs a clone at $LORE, default /home/user/epicgames/lore; a built
#             target/ there is shared with ticket worktrees so repros build incrementally)
#
# Each run writes <workdir>-<phase>-<ts>.jsonl (stream-json) and prints the score;
# analyze.py summarises tokens, cost, and which plugin files were read.
# Requires an authenticated `claude` CLI. Spends real tokens.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(dirname "$HERE")"
CMD="$1"; WD="$2"; shift 2
MODEL="${EVAL_MODEL:-opus}"
SCEN="$(cat "$WD/.scenario" 2>/dev/null || echo "${SCENARIO:-fixtures}")"
export SCENARIO="$SCEN"

run_claude() {
  local out="$WD/../$(basename "$WD")-$CMD-$(date +%s).jsonl"
  (cd "$WD" && FT_PROJECT_DIR="$WD" timeout "${EVAL_TIMEOUT:-3500}" claude -p "$1" \
     --model "$MODEL" --plugin-dir "$PLUGIN" --permission-mode bypassPermissions \
     --output-format stream-json --verbose < /dev/null > "$out" 2>&1) || true
  python3 "$HERE/analyze.py" "$out"
}

case "$CMD" in
  setup)
    rm -rf "$WD"; mkdir -p "$WD"
    SETUP_CMD=""
    if [ "$SCEN" = realworld ]; then
      SRC="${HUMANIZE:-/home/user/python-humanize/humanize}"
      cp -R "$SRC/." "$WD/"
      REPO=python-humanize/humanize; CH=C0APPDEV; CHN=app-feedback
    elif [ "$SCEN" = lore ]; then
      SRC="${LORE:-/home/user/epicgames/lore}"
      (cd "$SRC" && tar --exclude=./target -cf - .) | (cd "$WD" && tar -xf -)
      # one shared build cache: worktrees symlink it (ignored by **/target/ … as a link too)
      [ -d "$SRC/target" ] && ln -sfn "$SRC/target" "$WD/target"
      REPO=epicgames/lore; CH=C0LOREFB; CHN=lore-feedback
      SETUP_CMD="ln -sfn $SRC/target target"
    else
      cp -R "$HERE/fixtures/app/." "$WD/"
      REPO=acme/tasklite; CH=C0FEEDBK; CHN=product-feedback
    fi
    mkdir -p "$WD/.claude" "$WD/feedback-exports"
    cp "$HERE/$SCEN/github-issues.json" "$HERE/$SCEN/slack-export.json" "$WD/feedback-exports/"
    cat > "$WD/.claude/feedback-triage.json" <<JSON
{
  "state": {"persist": "none"},
  "sources": {
    "github": [{"repo": "$REPO", "export": "feedback-exports/github-issues.json"}],
    "slack": [{"channel": "$CHN", "id": "$CH", "export": "feedback-exports/slack-export.json"}]
  },
  "investigate": {"base_branch": "main", "open_prs": false, "setup": "$SETUP_CMD"}
}
JSON
    echo "$SCEN" > "$WD/.scenario"
    (cd "$WD" && { [ -d .git ] || git init -q -b main; } && git checkout -q -B main && \
      printf '.scenario\nfeedback-exports/\n.claude/\n.feedback-triage/\n/target\n' >> .git/info/exclude && \
      { git add -A && git -c user.name=eval -c user.email=eval@local commit -qm "fixture" || true; } && \
      FT_PROJECT_DIR="$WD" python3 "$PLUGIN/scripts/ft.py" init >/dev/null)
    echo "$SCEN project ready: $WD" ;;
  intake)
    run_claude "/feedback-triage:intake feedback-exports/github-issues.json feedback-exports/slack-export.json --since 2024-01-01"
    python3 "$HERE/score_intake.py" "$WD" ;;
  investigate)
    run_claude "/feedback-triage:investigate ${*:-} --no-pr"
    FT_PROJECT_DIR="$WD" python3 "$PLUGIN/scripts/ft.py" list ;;
  report)
    run_claude "/feedback-triage:report"
    python3 "$HERE/score_reports.py" "$WD" ;;
  recheck)
    run_claude "/feedback-triage:recheck --all"
    FT_PROJECT_DIR="$WD" python3 "$PLUGIN/scripts/ft.py" list ;;
  *) echo "usage: run.sh setup|intake|investigate|report|recheck <workdir>" >&2; exit 1 ;;
esac
