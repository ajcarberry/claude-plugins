#!/bin/bash
# SessionStart (startup|clear|compact): always inject the flight-rules bootstrap;
# when a mission is active, also inject brief + spec + log, detect drift, and run
# project env init in the background.
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
MISSION="$CWD/.claude/mission"
BRIEF="$MISSION/brief.md"
SPEC="$MISSION/spec.md"
LOG="$MISSION/log.md"

# --- Flight-rules bootstrap: always injected (survives /clear and compaction) ---
BOOTSTRAP="# Flight Rules

Launchpad flight rules are in effect. Before any implementation work — writing code,
fixing a bug, changing config — check whether a launchpad skill applies and use it,
announcing which one (\"Using test-driven-development: ...\"). Non-negotiable rules:
no completion claim without fresh verification evidence, matched to the surface
touched (a web change means loading the page, an infra change means reading live
state); no production change without a check that fails first; no bug fix without a
stated root cause. Process rules take priority over implementation momentum.
Priority order: explicit user instructions > flight rules > default behavior.
During a mission, the stakes tier in the brief sizes the ceremony — low-stakes work
gets a light touch."

emit_context() {
  jq -n --arg content "$1" '{
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $content
    }
  }'
}

# No mission in progress — inject the bootstrap alone.
if [ ! -f "$BRIEF" ]; then
  emit_context "$BOOTSTRAP"
  exit 0
fi

BRIEF_CONTENT=$(cat "$BRIEF")

# --- Runtime vs expected context ---
ACTUAL_BRANCH=$(cd "$CWD" && git branch --show-current 2>/dev/null || echo "unknown")
WORKTREE_NAME=$(basename "$CWD")
EXPECTED_BRANCH=$(echo "$BRIEF_CONTENT" | sed -n '/^---$/,/^---$/p' | grep -m1 '^branch:' | sed 's/^branch: *//' | xargs)
BRIEF_DATE=$(echo "$BRIEF_CONTENT" | sed -n '/^---$/,/^---$/p' | grep -m1 '^date:' | sed 's/^date: *//' | xargs)
STAKES=$(echo "$BRIEF_CONTENT" | sed -n '/^---$/,/^---$/p' | grep -m1 '^stakes:' | sed 's/^stakes: *//' | xargs)

WARNINGS=""

if [ -n "$EXPECTED_BRANCH" ] && [ "$ACTUAL_BRANCH" != "$EXPECTED_BRANCH" ]; then
  WARNINGS="${WARNINGS}WARNING: Actual branch \"${ACTUAL_BRANCH}\" does not match brief's expected branch \"${EXPECTED_BRANCH}\". You may be in the wrong worktree — verify before proceeding.\n"
fi

if [ -n "$BRIEF_DATE" ]; then
  BRIEF_EPOCH=$(date -j -f "%Y-%m-%d" "$BRIEF_DATE" "+%s" 2>/dev/null || date -d "$BRIEF_DATE" "+%s" 2>/dev/null)
  NOW_EPOCH=$(date "+%s")
  if [ -n "$BRIEF_EPOCH" ]; then
    AGE_DAYS=$(( (NOW_EPOCH - BRIEF_EPOCH) / 86400 ))
    if [ "$AGE_DAYS" -gt 3 ]; then
      WARNINGS="${WARNINGS}WARNING: Mission brief is from ${BRIEF_DATE} (${AGE_DAYS} days ago). The task may already be completed — check git log before starting work.\n"
    fi
  fi
fi

DIRTY=$(cd "$CWD" && git status --porcelain 2>/dev/null)
if [ -n "$DIRTY" ]; then
  WARNINGS="${WARNINGS}WARNING: There are uncommitted changes in this worktree. Review them before making new changes.\n"
fi

# --- Project-defined environment init (background, opt-in via executable script) ---
BG_MSG=""
INIT_SCRIPT="$CWD/.claude/session-init.sh"
if [ -x "$INIT_SCRIPT" ]; then
  BG_MSG="Project session-init.sh running in background."
  ( cd "$CWD" && "$INIT_SCRIPT" >/dev/null 2>&1 ) &
fi

# --- Assemble ---
PREAMBLE="Mission in progress (stakes: ${STAKES:-unset}). Respond to the user's first message with the following format, then continue the mission — do not ask what to work on; you already know.

When greeting the user, start your response with:

## Session Initialized

**Objective:** <restate the task objective from the brief in your own words>

**Context:**
  Working directory: ${CWD}
  Worktree: ${WORKTREE_NAME}
  Branch: ${ACTUAL_BRANCH}
  Stakes: ${STAKES:-unset}
"

if [ -n "$WARNINGS" ]; then
  PREAMBLE="${PREAMBLE}
$(echo -e "$WARNINGS")"
fi

if [ -n "$BG_MSG" ]; then
  PREAMBLE="${PREAMBLE}
${BG_MSG}
"
fi

if [ -f "$LOG" ]; then
  PREAMBLE="${PREAMBLE}
The mission log is loaded below — resume from its last entry rather than re-planning or re-exploring."
elif [ -f "$SPEC" ]; then
  PREAMBLE="${PREAMBLE}
The spec is loaded below. Orient to it and continue — /launch implements it; no need to re-explore from scratch."
else
  PREAMBLE="${PREAMBLE}
No spec yet. For complex work suggest /mission-plan; otherwise explore and proceed under the flight rules."
fi

CONTEXT="${BOOTSTRAP}

${PREAMBLE}

# Mission Brief

${BRIEF_CONTENT}"

if [ -f "$SPEC" ]; then
  CONTEXT="${CONTEXT}

# Spec

$(cat "$SPEC")"
fi

if [ -f "$LOG" ]; then
  CONTEXT="${CONTEXT}

# Mission Log

$(cat "$LOG")"
fi

emit_context "$CONTEXT"
