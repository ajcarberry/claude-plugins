#!/usr/bin/env python3
"""PreToolUse gate for feedback-triage. Deterministic file checks only — no judgment.

1. Queue files (queue/*.json, index.json) are written only by ft.py.
2. A feedback-triage branch (<branch_prefix>*, default triage/) is pushed or opened as a PR only when the
   ticket is low complexity AND its change passed the independent change-reviewer.

This is a guardrail against honest mistakes, not a security boundary: an agent with a
shell can always reach git another way. It therefore fails closed — a push or PR it
cannot positively parse is blocked while triage branches exist. The real boundary is
server-side: draft PRs, branch protection, and human review before merge.

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

PUSH_OR_PR = re.compile(r"\bgh\b.*\bpr\b.*\bcreate\b|\bgh\b.*\bapi\b.*\b(?:pulls|graphql)\b|\bgit\b.*\bpush\b")
GIT_OR_GH = re.compile(r"\b(?:git|gh)\b")


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


CONTROL = {"&&", "||", ";", "|", "&", "|&", ";;", "\n"}
REDIRECT = re.compile(r"^[<>&]*[<>][<>&|]*$")  # >, >>, 2>&1 pieces, &>, <, <<, …


def segments(cmd):
    """Split a command line into simple commands with a real shell tokenizer:
    [(tokens, raw_text, piped_in)]. Redirections stay inside their command."""
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        toks = list(lex)
    except ValueError:
        return None  # unbalanced quotes: unparseable
    out, cur, piped, nxt = [], [], False, False
    for t in toks + [";"]:
        if t and all(c in "();<>&|" for c in t) and t not in CONTROL and not REDIRECT.match(t):
            return None  # an operator run we don't understand ((, ), ;&, )|, …): fail closed
        if t in CONTROL:
            if cur:
                out.append((cur, " ".join(cur), piped))
            cur, piped = [], t in ("|", "|&")
            continue
        cur.append(t)
    cleaned = []
    for words, raw, piped_in in out:
        w, skip = [], False
        for i, t in enumerate(words):
            if skip:
                skip = False
                continue
            if REDIRECT.match(t):
                if w and w[-1].isdigit():
                    w.pop()  # fd number before the operator
                skip = not t.endswith("&") or True
                continue
            w.append(t)
        env = []
        while w and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w[0]):
            env.append(w.pop(0))  # leading VAR=value assignments
        cleaned.append((w, raw, piped_in, env))
    return cleaned


def flag_value(toks, k, short, longs):
    """Value of the flag at toks[k] in any form: -H v, -Hv, --head v, --head=v; else None."""
    t = toks[k]
    for name in longs:
        if t == name and k + 1 < len(toks):
            return toks[k + 1]
        if t.startswith(name + "="):
            return t.split("=", 1)[1]
    for name in short:
        if t == name and k + 1 < len(toks):
            return toks[k + 1]
        if t.startswith(name) and len(t) > len(name) and not t.startswith("--"):
            return t[len(name):].lstrip("=")
    return None


def is_triage(st, name):
    return name.casefold().startswith(st.cfg["investigate"]["branch_prefix"].casefold())


def strip_ref(name):
    return re.sub(r"^refs/heads/", "", name, flags=re.I)


def triage_branches_exist(st, where):
    local = git(where, "for-each-ref", "--format=%(refname:short)", "refs/heads/").split()
    return any(is_triage(st, b) for b in local)


def remote_owner(st, where):
    url = git(where, "remote", "get-url", st.cfg["state"]["remote"])
    m = re.search(r"github\.com[:/]([^/]+)/", url)
    return m.group(1).lower() if m else ""


def check_head(st, head, where, text=""):
    """PR head: 'branch' or 'owner:branch'. Fork heads cannot be verified → blocked.
    text: the PR's title and body, which must not carry internal ticket ids."""
    owner, _, branch = head.rpartition(":")
    if not is_triage(st, branch):
        return
    if ft.INTERNAL_ID.search(text):
        block("internal ticket ids (FT-…) never go in a PR title or body — use the upstream issue.")
    if owner and owner.lower() != remote_owner(st, where):
        block(f"PR head {head} is not on the configured remote — triage PRs come from our own branch.")
    gate_branch(st, branch, remote=True)


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
    if not pos[1:] and is_triage(st, current):
        block(f"name the destination when pushing triage branch {current} "
              f"(git push <remote> {current}) — the implicit target depends on config.")
    refspecs = pos[1:] or [current]
    for r in refspecs:
        if any(c in r for c in "*?[") and triage_branches_exist(st, where):
            block(f"wildcard refspec {r} could include triage branches — push branches by name.")
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


GIT_RE = re.compile(r"(?:^|/)git$")
GH_RE = re.compile(r"(?:^|/)gh$")
WRAPPERS = {"env", "command", "builtin", "nice", "nohup", "time", "exec", "sudo"}
OPAQUE = re.compile(r"\$\(|\$\{|`|\beval\b|\bxargs\b|\b(?:ba|z|da|k)?sh\s+-c\b|\bsource\b|(?:^|[;&|]\s*)\.\s|"
                    r"\balias\.|\bGIT_CONFIG|\bparallel\b|\bfind\b.*-exec")
# git subcommands the gate understands; anything else (aliases, git-foo extensions) fails closed
GIT_KNOWN = set("""add am annotate apply archive bisect blame branch bundle cat-file check-attr check-ignore
check-mailmap check-ref-format checkout cherry cherry-pick clean clone commit commit-graph commit-tree config
count-objects describe diff diff-files diff-index diff-tree difftool fetch for-each-ref format-patch fsck gc
grep hash-object help init log ls-files ls-remote ls-tree merge merge-base merge-file merge-tree mergetool mv
name-rev notes pull push range-diff read-tree rebase reflog remote repack replace rerere reset restore rev-list
rev-parse revert rm shortlog show show-branch show-ref sparse-checkout stash status submodule switch symbolic-ref
tag update-index update-ref var verify-commit verify-tag version whatchanged worktree write-tree""".split())
GH_FLAGS_WITH_VALUE = {"-R", "--repo", "--hostname"}
GIT_SAFE_GLOBALS = {"--no-pager", "-P", "-p", "--paginate", "--no-optional-locks", "--literal-pathspecs",
                    "--no-replace-objects"}


def check_bash(st, cmd, cwd):
    if not GIT_OR_GH.search(cmd):
        return
    triage = None  # computed lazily: fail-closed blocks only matter while triage branches exist

    def fail(msg):
        nonlocal triage
        if triage is None:
            triage = triage_branches_exist(st, cwd)
        if triage:
            block(msg)

    if OPAQUE.search(cmd):
        fail("this command hides what it runs (subshell, eval, sh -c, xargs, aliases, GIT_CONFIG) "
             "next to git/gh — run git/gh directly so the gate can check it.")
    segs = segments(cmd)
    if segs is None:
        fail("could not tokenize this git/gh command — run it plainly so the gate can check it.")
        return
    where = cwd
    for toks, raw, piped_in, env in segs:
        while toks and toks[0] in WRAPPERS:
            toks = toks[1:]
            while toks and (toks[0].startswith("-") or "=" in toks[0]):
                if toks[0].startswith("GIT_"):
                    fail("GIT_* settings through a wrapper can't be checked.")
                toks = toks[1:]
        if any(e.startswith("GIT_") for e in env):
            fail("GIT_* environment settings on a git command can't be checked.")
        if not toks:
            continue
        if toks[0] in ("cd", "pushd") and len(toks) > 1:
            where = os.path.join(where, toks[1]) if not os.path.isabs(toks[1]) else toks[1]
            continue
        if GIT_RE.search(toks[0]):
            j, here = 1, where
            while j < len(toks) and toks[j].startswith("-"):
                if toks[j] == "-C" and j + 1 < len(toks):
                    here = os.path.join(here, toks[j + 1]) if not os.path.isabs(toks[j + 1]) else toks[j + 1]
                    j += 2
                elif toks[j] in GIT_SAFE_GLOBALS:
                    j += 1
                else:  # -c, --config-env, --git-dir, --exec-path, …: config can change what push does
                    fail(f"git {toks[j]} can't be checked — run git without global overrides.")
                    j += 2 if toks[j] in ("-c", "--config-env", "--git-dir", "--work-tree",
                                          "--namespace", "--exec-path", "--super-prefix") else 1
            sub = toks[j] if j < len(toks) else ""
            if sub == "push":
                if piped_in:
                    fail("git push reading from a pipe can't be checked — run it directly.")
                check_push(st, toks[j + 1:], here)
            elif sub != "stash" and any(t == "push" and not toks[j + i].startswith("-")
                                        for i, t in enumerate(toks[j + 1:])):
                fail(f"git {sub} … push can't be checked — run git push directly.")
            elif sub and sub not in GIT_KNOWN:
                fail(f"git '{sub}' is not a built-in command the gate knows (alias or extension) — "
                     "run the real git command.")
            continue
        if not GH_RE.search(toks[0]):
            if PUSH_OR_PR.search(raw):
                fail("could not parse this push/PR command — run git push / gh pr create directly.")
            continue
        args = toks[1:]
        k = 0
        while k < len(args) and args[k].startswith("-"):  # global flags before the command
            k += 2 if args[k] in GH_FLAGS_WITH_VALUE else 1
        group = args[k] if k < len(args) else ""
        rest = args[k + 1:]
        m = 0
        while m < len(rest) and rest[m].startswith("-"):
            m += 2 if rest[m] in GH_FLAGS_WITH_VALUE else 1
        sub = rest[m] if m < len(rest) else ""
        if group == "pr" and (sub == "create" or "create" in rest):
            if piped_in:
                fail("gh pr create reading from a pipe can't be checked — run it directly.")
            head = None
            for q in range(len(toks)):
                head = flag_value(toks, q, ("-H",), ("--head",)) or head
            if head and head.startswith("@"):
                fail("a PR head read from a file can't be checked.")
            text = " ".join(toks)
            for q in range(len(toks)):
                bf = flag_value(toks, q, ("-F",), ("--body-file",))
                if bf and bf != "-" and os.path.isfile(os.path.join(where, bf)):
                    text += " " + open(os.path.join(where, bf), errors="replace").read()
            check_head(st, head or git(where, "branch", "--show-current"), where, text)
        elif group == "api":
            text = " ".join(toks)
            if not re.search(r"\bpulls\b|graphql", text):
                continue
            if re.search(r"--input\b|graphql", text):
                fail("gh api --input / graphql PR calls can't be checked — use gh pr create.")
                continue
            heads = []
            for q in range(len(toks)):
                val = flag_value(toks, q, ("-f", "-F"), ("--field", "--raw-field"))
                if val and val.startswith("head="):
                    heads.append(val[5:])
            if any(h.startswith("@") for h in heads):
                fail("a PR head read from a file can't be checked.")
            if not heads and re.search(re.escape(st.cfg["investigate"]["branch_prefix"]), text, re.I):
                fail("this gh api call names a triage branch but no head could be parsed.")
            for h in heads:
                check_head(st, h, where)
        elif group == "alias" or (group and group not in {"pr", "api", "issue", "repo", "run", "workflow",
                                                           "auth", "browse", "release", "search", "status",
                                                           "gist", "label", "cache", "variable", "secret"}):
            fail(f"gh '{group}' is not a command the gate knows (alias or extension) — use gh pr create.")


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
    if tool == "Bash" and not GIT_OR_GH.search(ti.get("command") or ""):
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
        check_head(st, ti.get("head") or "", cwd, f"{ti.get('title') or ''} {ti.get('body') or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
