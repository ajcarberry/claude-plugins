#!/bin/bash
# Behavioral eval: run a feedback-triage phase headless against the fixture project.
#
#   evals/run.sh setup <workdir>                 # fresh fixture project + config + empty queue
#   evals/run.sh intake <workdir>                # /intake over the fixture exports
#   evals/run.sh investigate <workdir> [ids]     # /investigate
#   evals/run.sh report <workdir>                # /report --dry-run (renders, never sends)
#   evals/run.sh recheck <workdir>               # /recheck --all
#
# Requires an authenticated `claude` CLI. Spends real tokens.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(dirname "$HERE")"
CMD="$1"; WD="$2"; shift 2
MODEL="${EVAL_MODEL:-opus}"

run_claude() {
  (cd "$WD" && FT_PROJECT_DIR="$WD" timeout "${EVAL_TIMEOUT:-1800}" claude -p "$1" \
     --model "$MODEL" --plugin-dir "$PLUGIN" --permission-mode bypassPermissions \
     --output-format json < /dev/null > "$WD/../$(basename "$WD")-$CMD-$(date +%s).json" 2>&1) || true
}

case "$CMD" in
  setup)
    rm -rf "$WD"; mkdir -p "$WD"
    cp -R "$HERE/fixtures/app/." "$WD/"
    mkdir -p "$WD/.claude" "$WD/feedback-exports"
    cp "$HERE/fixtures/github-issues.json" "$HERE/fixtures/slack-export.json" "$WD/feedback-exports/"
    cat > "$WD/.claude/feedback-triage.json" <<JSON
{
  "state": {"persist": "none"},
  "sources": {
    "github": [{"repo": "acme/tasklite", "export": "feedback-exports/github-issues.json"}],
    "slack": [{"channel": "product-feedback", "id": "C0FEEDBK", "export": "feedback-exports/slack-export.json"}]
  },
  "investigate": {"base_branch": "main", "open_prs": false},
  "report": {"channel": "#eng-triage", "auto_send": false}
}
JSON
    (cd "$WD" && git init -q -b main && git add -A && git commit -qm "tasklite 2.4.1" && \
      FT_PROJECT_DIR="$WD" python3 "$PLUGIN/scripts/ft.py" init >/dev/null)
    echo "fixture project ready: $WD" ;;
  intake)
    run_claude "/feedback-triage:intake feedback-exports/github-issues.json feedback-exports/slack-export.json --since 2026-09-01"
    python3 "$HERE/score_intake.py" "$WD" ;;
  investigate)
    run_claude "/feedback-triage:investigate ${*:-} --no-pr"
    FT_PROJECT_DIR="$WD" python3 "$PLUGIN/scripts/ft.py" list ;;
  report)
    run_claude "/feedback-triage:report --dry-run"
    python3 "$HERE/score_reports.py" "$WD" ;;
  recheck)
    run_claude "/feedback-triage:recheck --all"
    FT_PROJECT_DIR="$WD" python3 "$PLUGIN/scripts/ft.py" list ;;
  *) echo "usage: run.sh setup|intake|investigate|report|recheck <workdir>" >&2; exit 1 ;;
esac
