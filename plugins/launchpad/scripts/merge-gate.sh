#!/bin/bash
# PreToolUse (Bash): during a mission, block push / PR-create / merge while the
# validation stamp is dirty. Deterministic file check only — no judgment here.
# Escape hatch: LAUNCHPAD_SKIP_GATE=1 (env, or prefixed on the command itself).
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
MISSION="$CWD/.claude/mission"

[ -d "$MISSION" ] || exit 0
[ "$LAUNCHPAD_SKIP_GATE" = "1" ] && exit 0

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
echo "$CMD" | grep -qE 'git push|gh pr create|gh pr merge' || exit 0
echo "$CMD" | grep -q 'LAUNCHPAD_SKIP_GATE=1' && exit 0

STAMP="$MISSION/validation-stamp"
if [ -f "$STAMP" ] && head -1 "$STAMP" | grep -q '^clean'; then
  exit 0
fi

echo "Launchpad gate: validation hasn't run since the last edit (stamp is dirty or missing). Run the launchpad:validation skill to completion before pushing or merging. Override (rare, deliberate): prefix the command with LAUNCHPAD_SKIP_GATE=1." >&2
exit 2
