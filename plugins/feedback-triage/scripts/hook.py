#!/usr/bin/env python3
"""PreToolUse gate for feedback-triage. Deterministic file checks only — no judgment.

1. Queue files (queue/*.json, index.json) are written only by ft.py.
2. A feedback-triage branch (<branch_prefix>*, default triage/) is pushed or opened as a PR only when the
   ticket is low complexity AND its change passed the independent change-reviewer.

Exit 0 = allow, exit 2 = block (stderr goes to Claude).
Escape hatch (rare, deliberate): FT_SKIP_GATE=1 in the environment.
"""
import json
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft  # noqa: E402

PUSH_OR_PR = re.compile(r"gh\s+pr\s+create|gh\s+api\b.*\bpulls\b|\bgit\b.*\bpush\b")


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


def gate_branch(st, branch, commit=None, remote=False):
    """commit: the exact commit being sent; remote: verify the branch head on the remote."""
    args = ["--branch", branch] + (["--commit", commit] if commit else []) + (["--remote"] if remote else [])
    try:
        ft.cmd_gate_pr(args, st)
    except ft.Blocked as e:
        block(f"{e}.")
    except ft.BadInput:
        return


def git(where, *args):
    try:
        return subprocess.run(["git", "-C", where, *args], capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def segments(cmd):
    """Split a shell command line into simple commands (good enough for gating; quotes respected)."""
    parts, buf, quote = [], "", None
    i = 0
    while i < len(cmd):
        c = cmd[i]
        if quote:
            buf += c
            if c == quote:
                quote = None
        elif c in "'\"":
            quote, buf = c, buf + c
        elif cmd.startswith(("&&", "||"), i):
            parts.append(buf); buf = ""; i += 1
        elif c in ";|\n":
            parts.append(buf); buf = ""
        else:
            buf += c
        i += 1
    parts.append(buf)
    out = []
    for p in parts:
        try:
            toks = shlex.split(p)
        except ValueError:
            toks = p.split()
        while toks and "=" in toks[0] and not toks[0].startswith("-"):
            toks = toks[1:]  # leading VAR=value assignments
        if toks:
            out.append(toks)
    return out


def is_triage(st, name):
    return name.casefold().startswith(st.cfg["investigate"]["branch_prefix"].casefold())


def strip_ref(name):
    return re.sub(r"^refs/heads/", "", name, flags=re.I)


def check_push(st, args, where):
    """args: everything after `git … push`."""
    force, everything, pos = False, False, []
    takes_value = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--all", "--mirror", "--branches"):
            everything = True
        elif a in ("-f", "--force") or a.startswith(("--force-with-lease", "--force-if-includes")):
            force = True
        elif a in takes_value:
            i += 1
        elif not a.startswith("-"):
            pos.append(a)
        i += 1
    if everything:
        local = git(where, "for-each-ref", "--format=%(refname:short)", "refs/heads/").split()
        if any(is_triage(st, b) for b in local):
            block("--all/--mirror would push triage branches without the per-branch review check.")
        return
    current = git(where, "branch", "--show-current")
    refspecs = pos[1:] or [current]
    for r in refspecs:
        plus = r.startswith("+")
        r = r.lstrip("+")
        src, dst = r.split(":", 1) if ":" in r else (r, r)
        src = src or ""
        if src == "HEAD":
            src_name = current
        else:
            src_name = strip_ref(src)
        dst = strip_ref(dst if dst != "HEAD" else current)
        if is_triage(st, src_name) and not is_triage(st, dst):
            block(f"pushing triage branch {src_name} to {dst} skips the change request — push it to itself and open a PR.")
        if not is_triage(st, dst):
            continue
        if force or plus:
            block(f"force-pushing triage branch {dst} is not allowed — the reviewed commit must stay what ships.")
        sha = git(where, "rev-parse", "--verify", "-q", f"{src}^{{commit}}") if src else ""
        if not sha:
            block(f"cannot resolve what is being pushed to {dst} ({src or 'delete'}) — not allowed for triage branches.")
        gate_branch(st, dst, commit=sha)


def check_bash(st, cmd, cwd):
    if not PUSH_OR_PR.search(cmd):
        return
    where = cwd
    for toks in segments(cmd):
        if toks[0] in ("cd", "pushd") and len(toks) > 1:
            where = os.path.join(where, toks[1]) if not os.path.isabs(toks[1]) else toks[1]
            continue
        if toks[0] == "git":
            j, here = 1, where
            while j < len(toks) and toks[j].startswith("-"):
                if toks[j] in ("-C", "-c"):
                    if toks[j] == "-C" and j + 1 < len(toks):
                        here = os.path.join(here, toks[j + 1]) if not os.path.isabs(toks[j + 1]) else toks[j + 1]
                    j += 2
                else:
                    j += 1
            if j < len(toks) and toks[j] == "push":
                check_push(st, toks[j + 1:], here)
        elif toks[0] == "gh" and toks[1:3] == ["pr", "create"]:
            head = None
            for k, t in enumerate(toks):
                if t in ("--head", "-H") and k + 1 < len(toks):
                    head = toks[k + 1]
                elif t.startswith("--head="):
                    head = t.split("=", 1)[1]
            head = (head or git(where, "branch", "--show-current")).split(":")[-1]
            if is_triage(st, head):
                gate_branch(st, head, remote=True)
        elif toks[0] == "gh" and len(toks) > 1 and toks[1] == "api":
            for t in toks:
                m = re.match(r"head=(.+)", t)
                if m and is_triage(st, m.group(1).split(":")[-1]):
                    gate_branch(st, m.group(1).split(":")[-1], remote=True)


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
        head = (ti.get("head") or "").split(":")[-1]
        if is_triage(st, head):
            gate_branch(st, head, remote=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
