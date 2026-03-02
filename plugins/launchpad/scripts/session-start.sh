#!/bin/bash
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
MISSION_BRIEF="$CWD/.claude/mission-brief.md"
FLIGHT_PLAN="$CWD/.claude/flight-plan.md"

if [ ! -f "$MISSION_BRIEF" ]; then
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

# --- Fresh worktree detection: background env init ---
NEEDS_BUILD=""
NEEDS_SYNC=""
BG_MSG=""

if [ ! -f "$CWD/cluster" ]; then
  NEEDS_BUILD=true
fi

if [ ! -d "$CWD/.venv" ]; then
  NEEDS_SYNC=true
fi

if [ -n "$NEEDS_BUILD" ] || [ -n "$NEEDS_SYNC" ]; then
  TASKS=""
  if [ -n "$NEEDS_BUILD" ]; then
    TASKS="CLI build"
  fi
  if [ -n "$NEEDS_SYNC" ]; then
    [ -n "$TASKS" ] && TASKS="$TASKS + "
    TASKS="${TASKS}Python sync"
  fi
  BG_MSG="Fresh worktree detected — ${TASKS} running in background."

  # Run env init in background
  (
    if [ -n "$NEEDS_BUILD" ]; then
      cd "$CWD/tools/cluster" && go build -o ../../cluster ./cmd/cluster 2>/dev/null
    fi
    if [ -n "$NEEDS_SYNC" ]; then
      cd "$CWD" && uv sync 2>/dev/null
    fi
  ) &
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

# Tailor closing instructions based on whether a flight plan exists
if [ -f "$FLIGHT_PLAN" ]; then
  PREAMBLE="${PREAMBLE}
A flight plan is loaded below. Orient to it and start implementing — no need to re-explore the codebase."
else
  PREAMBLE="${PREAMBLE}
Then proceed to explore the codebase and present your plan of attack."
fi

# --- Assemble context from both documents ---
CONTEXT="${PREAMBLE}

# Mission Brief

${BRIEF_CONTENT}"

if [ -f "$FLIGHT_PLAN" ]; then
  PLAN_CONTENT=$(cat "$FLIGHT_PLAN")
  CONTEXT="${CONTEXT}

# Flight Plan

${PLAN_CONTENT}"
fi

jq -n --arg content "$CONTEXT" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $content
  }
}'
