#!/usr/bin/env bash
# Source this from a repro script. Provides isolated env setup and safe server start/stop.
# Requires: BIN (dir with binaries), SERVER (server binary name), PORTS (space-separated), WORK (mktemp dir)
triage_isolate() {
  export HOME="$WORK/home"; export TMPDIR="$WORK/tmp"; mkdir -p "$HOME" "$TMPDIR"
  export PATH="$BIN:$PATH"; export RUST_BACKTRACE=1
}
triage_ports_free() {
  for p in $PORTS; do lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1 && return 1; lsof -nP -iUDP:"$p" >/dev/null 2>&1 && return 1; done; return 0
}
triage_server_start() {  # usage: triage_server_start <health url>
  pkill -f "$BIN/$SERVER" 2>/dev/null || true
  for i in $(seq 1 20); do triage_ports_free && break; sleep 0.5; done
  (cd "$WORK" && exec "$BIN/$SERVER") > "$WORK/server.log" 2>&1 &
  SERVER_PID=$!
  for i in $(seq 1 30); do curl -sf "$1" >/dev/null 2>&1 && break; sleep 0.5; done
  # confirm the PID we hold owns the port
  for p in $PORTS; do lsof -nP -iTCP:"$p" -sTCP:LISTEN -t 2>/dev/null | grep -qx "$SERVER_PID" && return 0; done
  echo "WARNING: server pid $SERVER_PID does not own a listening port; another server may be running" >&2
}
triage_server_stop() {
  kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true
  pkill -f "$BIN/$SERVER" 2>/dev/null || true
  for i in $(seq 1 20); do triage_ports_free && break; sleep 0.5; done
}
triage_say() { echo "$*" | tee -a "$LOG"; }
triage_run() { triage_say "\$ $*"; "$@" 2>&1 | tee -a "$LOG"; return "${PIPESTATUS[0]}"; }
