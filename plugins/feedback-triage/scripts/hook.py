#!/usr/bin/env python3
"""PreToolUse gate for feedback-triage. Deterministic file checks only — no judgment.

1. Queue files (queue/*.json, index.json) are written only by ft.py.
2. A feedback-triage branch (ft/FT-NNNN-*) is pushed or opened as a PR only when the
   ticket is low complexity AND its change passed the independent change-reviewer.
3. A Slack message that carries a ticket id must be byte-identical to a rendered
   outbox file — reports are never hand-written.

Exit 0 = allow, exit 2 = block (stderr goes to Claude).
Escape hatch (rare, deliberate): FT_SKIP_GATE=1 in the environment.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft  # noqa: E402

TICKET_ID = re.compile(r"\bFT-\d{4,}\b")
PUSH_OR_PR = re.compile(r"gh\s+pr\s+create|\bgit\b(?:\s+-C\s+\S+)?\s+push\b")
TEXT_KEYS = ("text", "message", "markdown_text", "content", "body")


def block(msg):
    print(f"feedback-triage gate: {msg} Override (rare, deliberate): FT_SKIP_GATE=1.", file=sys.stderr)
    sys.exit(2)


def store_for(cwd):
    if cwd and not (os.environ.get("FT_PROJECT_DIR") or os.environ.get("CLAUDE_PROJECT_DIR")):
        os.chdir(cwd)
    return ft.Store()


def check_queue_edit(st, path):
    if not path:
        return
    path = os.path.realpath(path if os.path.isabs(path) else os.path.join(os.getcwd(), path))
    sdir = os.path.realpath(st.dir)
    if path == os.path.join(sdir, "index.json") or path.startswith(os.path.join(sdir, "queue") + os.sep):
        block("queue files are written only through ft.py (upsert/link/investigated/recheck-apply/…), "
              "so the ledger and schema stay consistent.")


def gate_branch(st, branch):
    try:
        ft.cmd_gate_pr(["--branch", branch], st)
    except ft.Blocked as e:
        block(f"{e}.")
    except ft.BadInput:
        return


def current_branch(cwd):
    try:
        return subprocess.run(["git", "-C", cwd or ".", "branch", "--show-current"],
                              capture_output=True, text=True, timeout=2).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def check_bash(st, cmd, cwd):
    if not PUSH_OR_PR.search(cmd):
        return
    prefix = re.escape(st.cfg["investigate"]["branch_prefix"])
    named = re.findall(rf"(?:^|[\s:=])({prefix}FT-\d{{4,}}[\w./-]*)", cmd, re.I)
    where = re.search(r"git\s+-C\s+(\S+)\s+push", cmd) or re.search(r"\bcd\s+(\S+)\s*(?:&&|;)", cmd)
    branches = named or [current_branch(where.group(1).strip("'\"") if where else cwd)]
    for b in branches:
        gate_branch(st, b)


def check_slack(st, tool_input):
    text = next((tool_input[k] for k in TEXT_KEYS if isinstance(tool_input.get(k), str)), "")
    if not TICKET_ID.search(text):
        return
    outbox = os.path.join(st.dir, "reports", "outbox")
    for dirpath, _, files in os.walk(outbox):
        for name in files:
            if name.endswith(".txt"):
                with open(os.path.join(dirpath, name)) as f:
                    if f.read().strip() == text.strip():
                        return
    block("this Slack message names a ticket but is not a rendered report. Render it with "
          "`ft.py render` and send the outbox file's text verbatim.")


def main():
    if os.environ.get("FT_SKIP_GATE") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool = payload.get("tool_name") or ""
    ti = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    # fast path: most tool calls are none of our business
    if tool == "Bash" and not PUSH_OR_PR.search(ti.get("command") or ""):
        return 0
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit") and not re.search(
            r"index\.json$|[/\\]queue[/\\]", ti.get("file_path") or ti.get("notebook_path") or ""):
        return 0
    if re.search(r"slack", tool, re.I) and not TICKET_ID.search(json.dumps(ti, ensure_ascii=False)):
        return 0
    st = store_for(cwd)
    if not os.path.exists(st.index_path):
        return 0  # feedback-triage not in use in this project
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        check_queue_edit(st, ti.get("file_path") or ti.get("notebook_path"))
    elif tool == "Bash":
        cmd = ti.get("command") or ""
        if "FT_SKIP_GATE=1" not in cmd:
            check_bash(st, cmd, cwd)
    elif re.search(r"create_pull_request", tool):
        gate_branch(st, ti.get("head") or "")
    elif re.search(r"slack", tool, re.I):
        check_slack(st, ti)
    return 0


if __name__ == "__main__":
    sys.exit(main())
