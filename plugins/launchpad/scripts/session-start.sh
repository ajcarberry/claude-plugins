#!/bin/bash
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
MISSION_BRIEF="$CWD/.claude/mission-brief.md"
FLIGHT_PLAN="$CWD/.claude/flight-plan.md"
FLIGHT_LOG="$CWD/.claude/flight-log.md"
SPECS_DIR="$CWD/.claude/specs"

# --- Flight-rules bootstrap: always injected (survives /clear and compaction) ---
BOOTSTRAP="# Flight Rules

Launchpad flight rules are in effect. Before any implementation work — writing code,
fixing a bug, changing config — check whether a launchpad skill applies and use it,
announcing which one (\"Using test-driven-development: ...\"). Non-negotiable rules:
no completion claim without fresh verification evidence; no production change without
a check that fails first; no bug fix without a stated root cause; web changes are
verified in a browser. Process rules take priority over implementation momentum.
Priority order: explicit user instructions > flight rules > default behavior. Size
ceremony with the stakes-rubric skill — low-stakes work gets a light touch."

emit_context() {
  jq -n --arg content "$1" '{
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $content
    }
  }'
}

# No mission in progress — inject the bootstrap alone.
if [ ! -f "$MISSION_BRIEF" ]; then
  emit_context "$BOOTSTRAP"
  exit 0
fi

BRIEF_CONTENT=$(cat "$MISSION_BRIEF")

# --- Extract runtime context ---
ACTUAL_BRANCH=$(cd "$CWD" && git branch --show-current 2>/dev/null || echo "unknown")
WORKTREE_NAME=$(basename "$CWD")

# --- Extract expected context from mission brief (YAML frontmatter) ---
EXPECTED_BRANCH=$(echo "$BRIEF_CONTENT" | sed -n '/^---$/,/^---$/p' | grep -m1 '^branch:' | sed 's/^branch: *//' | xargs)
BRIEF_DATE=$(echo "$BRIEF_CONTENT" | sed -n '/^---$/,/^---$/p' | grep -m1 '^date:' | sed 's/^date: *//' | xargs)

# --- Detect mismatches ---
WARNINGS=""

# Branch mismatch
if [ -n "$EXPECTED_BRANCH" ] && [ "$ACTUAL_BRANCH" != "$EXPECTED_BRANCH" ]; then
  WARNINGS="${WARNINGS}WARNING: Actual branch \"${ACTUAL_BRANCH}\" does not match brief's expected branch \"${EXPECTED_BRANCH}\". You may be in the wrong worktree — verify before proceeding.\n"
fi

# Stale brief (> 3 days old)
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

# Dirty working tree
DIRTY=$(cd "$CWD" && git status --porcelain 2>/dev/null)
if [ -n "$DIRTY" ]; then
  WARNINGS="${WARNINGS}WARNING: There are uncommitted changes in this worktree. Review them before making new changes.\n"
fi

# --- Project-defined environment init (background) ---
# Projects opt in by providing an executable .claude/session-init.sh — worktree
# builds, dependency syncs, whatever the project needs. Output is discarded.
BG_MSG=""
INIT_SCRIPT="$CWD/.claude/session-init.sh"

if [ -x "$INIT_SCRIPT" ]; then
  BG_MSG="Project session-init.sh running in background."
  ( cd "$CWD" && "$INIT_SCRIPT" >/dev/null 2>&1 ) &
fi

# --- Build additionalContext ---
PREAMBLE="Mission brief found. Respond to the user's first message with the following format, then proactively explore the relevant codebase areas and present a concise plan of attack. Do not ask what to work on — you already know.

When greeting the user, start your response with:

## Session Initialized

**Objective:** <restate the task objective from the brief in your own words>

**Context:**
  Working directory: ${CWD}
  Worktree: ${WORKTREE_NAME}
  Branch: ${ACTUAL_BRANCH}
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

# Tailor closing instructions based on mission state
if [ -f "$FLIGHT_LOG" ]; then
  PREAMBLE="${PREAMBLE}
A flight log is loaded below — resume from its last entry rather than re-planning or re-exploring."
elif [ -f "$FLIGHT_PLAN" ]; then
  PREAMBLE="${PREAMBLE}
A flight plan is loaded below. Orient to it and start implementing — no need to re-explore the codebase."
else
  PREAMBLE="${PREAMBLE}
Then proceed to explore the codebase and present your plan of attack."
fi

# --- Assemble context ---
CONTEXT="${BOOTSTRAP}

${PREAMBLE}

# Mission Brief

${BRIEF_CONTENT}"

# Latest approved spec, if any (mission brief's parent design doc)
if [ -d "$SPECS_DIR" ]; then
  LATEST_SPEC=$(ls -1 "$SPECS_DIR"/*.md 2>/dev/null | sort | tail -1)
  if [ -n "$LATEST_SPEC" ]; then
    CONTEXT="${CONTEXT}

# Approved Spec ($(basename "$LATEST_SPEC"))

$(cat "$LATEST_SPEC")"
  fi
fi

if [ -f "$FLIGHT_PLAN" ]; then
  CONTEXT="${CONTEXT}

# Flight Plan

$(cat "$FLIGHT_PLAN")"
fi

if [ -f "$FLIGHT_LOG" ]; then
  CONTEXT="${CONTEXT}

# Flight Log

$(cat "$FLIGHT_LOG")"
fi

emit_context "$CONTEXT"
