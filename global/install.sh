#!/bin/bash
# Install the global CLAUDE.md to ~/.claude/CLAUDE.md.
# Backs up any existing file first. Safe to re-run.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/CLAUDE.md"
DEST_DIR="$HOME/.claude"
DEST="$DEST_DIR/CLAUDE.md"

mkdir -p "$DEST_DIR"

if [ -f "$DEST" ]; then
  if cmp -s "$SRC" "$DEST"; then
    echo "Already up to date: $DEST"
    exit 0
  fi
  BACKUP="$DEST.backup.$(date +%Y%m%d%H%M%S)"
  cp "$DEST" "$BACKUP"
  echo "Backed up existing file to $BACKUP"
fi

cp "$SRC" "$DEST"
echo "Installed $SRC -> $DEST"
