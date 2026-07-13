#!/bin/bash
# PostToolUse (Edit|Write|NotebookEdit): an edit since the last validation pass
# marks the mission's validation stamp dirty. Pure file check downstream — the
# merge gate and /land trust this stamp.
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
MISSION="$CWD/.claude/mission"

# No active mission → nothing to track.
[ -d "$MISSION" ] || exit 0

FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')

# Edits to mission state / .claude files don't invalidate validation.
case "$FILE" in
  ""|*/.claude/*) exit 0 ;;
esac

echo "dirty" > "$MISSION/validation-stamp"
exit 0
