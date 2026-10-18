"""Tests for scripts/ft.py and the hook scripts. Run: python3 -m unittest discover -s tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FT = os.path.join(ROOT, "scripts", "ft.py")
HOOK = os.path.join(ROOT, "scripts", "hook.py")


class Env:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        os.makedirs(os.path.join(self.dir, ".claude"))
        with open(os.path.join(self.dir, ".claude", "feedback-triage.json"), "w") as f:
            json.dump({"state": {"persist": "none"}, "report": {"channel": "#eng"}}, f)

    def close(self):
        self.tmp.cleanup()

    def run(self, *args, stdin=None, ok=True):
        p = subprocess.run([sys.executable, FT, *args], input=stdin, capture_output=True, text=True,
                           env={**os.environ, "FT_PROJECT_DIR": self.dir})
        if ok and p.returncode != 0:
            raise AssertionError(f"ft {' '.join(args)} failed ({p.returncode}): {p.stderr}{p.stdout}")
        return p

    def j(self, *args, **kw):
        return json.loads(self.run(*args, **kw).stdout)

    def hook(self, payload):
        return subprocess.run([sys.executable, HOOK], input=json.dumps({"cwd": self.dir, **payload}),
                              capture_output=True, text=True, env={**os.environ, "FT_PROJECT_DIR": self.dir})


def cand(ref, title="Login fails after SSO timeout", typ="bug", **extra):
    url = f"https://github.com/acme/app/issues/{ref}" if isinstance(ref, int) else ref
    return json.dumps({"type": typ, "title": title, "summary": "Users see a 500 after the SSO session expires.",
                       "source": {"url": url, "author": extra.pop("author", "dana"),
                                  "excerpt": extra.pop("excerpt", "500 on login"), "raised_at": "2026-10-01T10:00:00Z"},
                       **extra})


GOOD_REPORT = {
    "headline": "Login returns 500 after the SSO session expires",
    "what": "Users who stay idle for one hour cannot log in again. They see a server error.",
    "findings": ["The token refresh code does not handle an expired refresh token.",
                 "We reproduced it on version 2.4.1 with a failing test."],
}
FIX = "Catch the expired token and send the user to the SSO login page. Check that the new test covers an empty token."


class Intake(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.e.run("init")

    def test_create_then_idempotent(self):
        a = self.e.j("upsert", "--json", cand(12))
        self.assertEqual(a["action"], "created")
        b = self.e.j("upsert", "--json", cand(12))
        self.assertEqual((b["action"], b["id"]), ("exists", a["id"]))
        # URL and short ref normalise to the same ledger key
        c = self.e.j("upsert", "--json", json.dumps({"type": "bug", "title": "x", "summary": "y",
                                                     "source": {"ref": "ACME/App#12", "url": "u"}}))
        self.assertEqual(c["action"], "exists")

    def test_cross_link_from_excerpt(self):
        a = self.e.j("upsert", "--json", cand(12))
        slack = "https://acme.slack.com/archives/C01ABC/p1700000000000100"
        c = cand(slack, excerpt="same as https://github.com/acme/app/issues/12 for me", author="lee")
        # a link is evidence, not a verdict: dry-run surfaces it, a blind upsert is refused
        self.assertEqual(self.e.j("upsert", "--dry-run", "--json", c)["action"], "links-tracked")
        self.assertEqual(self.e.run("upsert", "--json", c, ok=False).returncode, 2)
        # duplicate_of may name the original's URL — no predicted ticket ids
        b = self.e.j("upsert", "--json", json.dumps(dict(json.loads(c), duplicate_of="https://github.com/acme/app/issues/12")))
        self.assertEqual((b["action"], b["id"]), ("linked", a["id"]))
        t = self.e.j("get", a["id"])
        self.assertEqual([s["relation"] for s in t["sources"]], ["original", "duplicate"])
        self.assertEqual(t["sources"][1]["ref"], "slack:C01ABC/1700000000.000100")

    def test_duplicate_of_and_merge(self):
        a = self.e.j("upsert", "--json", cand(12))
        b = self.e.j("upsert", "--json", cand(13, author="kim"))
        self.assertEqual(b["action"], "created")
        c = self.e.j("upsert", "--json", cand(14, duplicate_of=a["id"], duplicate_reason="same stack trace"))
        self.assertEqual(c["action"], "linked")
        self.e.j("merge", b["id"], a["id"], "--reason", "same root cause")
        t = self.e.j("get", a["id"])
        self.assertEqual(len(t["sources"]), 3)
        self.assertEqual(self.e.j("get", b["id"])["status"], "duplicate")
        # the merged-away source now resolves to the surviving ticket
        self.assertEqual(self.e.j("upsert", "--json", cand(13))["id"], a["id"])
        self.assertTrue(self.e.j("validate")["ok"])

    def test_distinct_despite_link(self):
        a = self.e.j("upsert", "--json", cand(12))
        c = json.loads(cand(30, excerpt="not like https://github.com/acme/app/issues/12, a new crash"))
        c["distinct"] = True
        self.assertEqual(self.e.j("upsert", "--json", json.dumps(c))["action"], "created")
        self.assertNotEqual(self.e.j("get", "FT-0002")["id"], a["id"])

    def test_split_refs(self):
        self.e.j("upsert", "--json", cand(12))
        c = json.loads(cand(12, title="Second issue in the same report"))
        c["source"]["ref"] = "github:acme/app#12~2"
        self.assertEqual(self.e.j("upsert", "--json", json.dumps(c))["action"], "created")

    def test_move_source(self):
        a = self.e.j("upsert", "--json", cand(12))["id"]
        b = self.e.j("upsert", "--json", cand(13, title="Other bug", author="kim"))["id"]
        self.e.j("upsert", "--json", cand(14, duplicate_of=a, author="x"))
        self.e.j("move-source", "acme/app#14", "--to", b, "--reason", "wrong ticket")
        self.assertEqual(len(self.e.j("get", b)["sources"]), 2)
        self.assertTrue(self.e.j("validate")["ok"])

    def test_merge_chain_and_double_merge(self):
        ids = [self.e.j("upsert", "--json", cand(n, author=f"u{n}"))["id"] for n in (1, 2, 3)]
        self.e.j("merge", ids[0], ids[1], "--reason", "same")
        self.e.j("merge", ids[1], ids[2], "--reason", "same")
        self.assertEqual(self.e.run("merge", ids[0], ids[2], "--reason", "again", ok=False).returncode, 2)
        self.assertEqual(self.e.j("get", ids[0])["duplicate_of"], ids[2])  # re-pointed
        r = self.e.j("upsert", "--json", cand(9, duplicate_of=ids[0], author="z"))
        self.assertEqual(r["id"], ids[2])  # whole chain followed
        self.assertTrue(self.e.j("validate")["ok"])

    def test_rereading_updates_momentum(self):
        a = self.e.j("upsert", "--json", cand(12))["id"]
        c = json.loads(cand(12)); c["source"]["plus_ones"] = ["kim", "lee"]
        self.assertTrue(self.e.j("upsert", "--json", json.dumps(c))["refreshed"])
        self.assertEqual(self.e.j("get", a)["sources"][0]["plus_ones"], ["kim", "lee"])

    def test_reopened_issue_is_feedback_again(self):
        self.e.j("ignore", "--ref", "acme/app#40", "--reason", "closed: fixed upstream")
        c = json.loads(cand(40)); c["source"]["state"] = "open"
        self.assertEqual(self.e.j("upsert", "--json", json.dumps(c))["action"], "created")

    def test_search_finds_well_raised_ticket(self):
        a = self.e.j("upsert", "--json", cand(12))["id"]
        for n in range(20, 26):
            self.e.j("upsert", "--json", cand(n, duplicate_of=a, author=f"u{n}",
                                               excerpt="lots of unrelated words about dashboards and widgets"))
        self.assertEqual(self.e.j("search", "login", "sso", "timeout")[0]["id"], a)

    def test_related_ignores_common_words(self):
        mk = lambda n, title, who: self.e.j("upsert", "--json", cand(n, title=title, author=who))["id"]
        a = mk(1, "intword prints huge decillion counts", "a")
        b = mk(2, "More intword names beyond decillion", "b")
        mk(3, "Export fails with an error", "c")
        mk(4, "Login fails with an error", "d")
        mk(5, "Sync fails with an error", "e")
        claimed = {c["id"]: c["related"] for c in self.e.j("claim")["claimed"]}
        self.assertEqual(claimed[a], [b])
        self.assertEqual(claimed["FT-0003"], [])
        self.assertEqual(self.e.j("related", a)[0]["id"], b)

    def test_passive_lint_ignores_adjectives(self):
        r = dict(GOOD_REPORT, what="The issue is open and the build is green. The file is often empty.")
        self.assertEqual(self.e.j("lint", "--json", json.dumps(r))["warnings"], [])
        r = dict(GOOD_REPORT, what="The token is rejected by the server.")
        self.assertTrue(self.e.j("lint", "--json", json.dumps(r))["warnings"])

    def test_ignore_and_reclassify(self):
        self.e.j("ignore", "--ref", "acme/app#99", "--reason", "closed: fixed upstream")
        self.assertEqual(self.e.j("upsert", "--json", cand(99))["action"], "ignored")  # still closed
        self.e.j("ignore", "--ref", "acme/app#98", "--reason", "question: how to export")
        # re-read later and now judged a bug ("it drops a row") → tracked, never missed
        self.assertEqual(self.e.j("upsert", "--json", cand(98))["action"], "created")

    def test_watermark_monotonic(self):
        self.e.j("watermark", "set", "github:acme/app", "2026-10-02T00:00:00Z")
        p = self.e.run("watermark", "set", "github:acme/app", "2026-10-01T00:00:00Z", ok=False)
        self.assertEqual(p.returncode, 2)

    def test_search(self):
        a = self.e.j("upsert", "--json", cand(12))
        hits = self.e.j("search", "sso", "login", "timeout", "error")
        self.assertEqual(hits[0]["id"], a["id"])

    def test_bad_candidate(self):
        p = self.e.run("upsert", "--json", json.dumps({"type": "bug", "title": "", "summary": "s",
                                                       "source": {"url": "https://github.com/a/b/issues/1"}}), ok=False)
        self.assertEqual(p.returncode, 1)


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.e.run("init")
        self.id = self.e.j("upsert", "--json", cand(12))["id"]
        inv = os.path.join(self.e.dir, ".feedback-triage", "investigations", f"{self.id}.md")
        with open(inv, "w") as f:
            f.write("# findings\n")
        self.inv = os.path.relpath(inv, self.e.dir)

    def investigate(self, tier="medium", **extra):
        self.assertEqual(self.e.j("claim")["claimed"][0]["id"], self.id)
        res = {"id": self.id, "status": "DONE", "complexity": {"tier": tier, "rationale": "one module"},
               "repro": "reproduced", "investigation_file": self.inv,
               "options_count": 2, **extra}
        return self.e.j("investigated", "--json", json.dumps(res))

    def test_illegal_transition_blocked(self):
        p = self.e.run("investigated", "--json", json.dumps({"id": self.id}), ok=False)
        self.assertEqual(p.returncode, 2)

    def test_medium_needs_options(self):
        self.e.j("claim")
        res = {"id": self.id, "complexity": {"tier": "medium", "rationale": "r"}, "repro": "reproduced", "investigation_file": self.inv, "options_count": 1}
        self.assertEqual(self.e.run("investigated", "--json", json.dumps(res), ok=False).returncode, 1)

    def render_one(self, *args):
        out = self.e.j("render", *args)
        f = next(f for f in out["files"] if f["kind"] == "ticket")
        return out, open(os.path.join(self.e.dir, f["file"])).read()

    def test_researched_report_shape(self):
        self.investigate()
        bad = dict(GOOD_REPORT, what="We basically just leverage the token. It is very robust 🔥.")
        self.assertEqual(self.e.run("report-set", self.id, "--json", json.dumps(bad), ok=False).returncode, 2)
        # a researched report has no fix section; a fix field is refused
        self.assertEqual(self.e.run("report-set", self.id, "--json", json.dumps(dict(GOOD_REPORT, fix=FIX)),
                                    ok=False).returncode, 2)
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        out, text = self.render_one()
        self.assertTrue(text.startswith("# Login returns 500 after the SSO session expires\n"))
        self.assertIn("👋 Hi team!", text)
        self.assertIn("**Status:** Researched: fix approaches outlined, needs a decision", text)
        self.assertIn("**Reproduced:** Yes", text)
        self.assertIn("## What we found\n\n- The token refresh code", text)
        self.assertIn("## Sources\n\n- GitHub acme/app#12 (dana): https://github.com/acme/app/issues/12", text)
        for gone in ("## Proposed fix", "## Open question", "Do:", "🌶", "FT-0", "{{"):
            self.assertNotIn(gone, text)
        self.assertNotIn("\n\n\n", text)
        self.e.j("sent", out["run"], "--all")
        self.assertEqual(self.e.j("get", self.id)["status"], "reported")
        self.assertEqual(self.e.j("due", "report"), [])  # unchanged → not re-reported

    def test_internal_ids_never_reach_a_report(self):
        self.investigate()
        leaky = dict(GOOD_REPORT, findings=["It is the same root cause as FT-0003."])
        p = self.e.run("report-set", self.id, "--json", json.dumps(leaky), ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("internal ticket id", p.stdout)

    def git_branch(self, name, push=False):
        """Project repo with a local bare 'origin'; returns the branch head."""
        d = self.e.dir
        g = lambda *a: subprocess.run(["git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                      capture_output=True, text=True, check=True).stdout.strip()
        if not os.path.isdir(os.path.join(d, ".git")):
            remote = os.path.join(d + "-remote.git")
            subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
            self.addCleanup(subprocess.run, ["rm", "-rf", remote])
            g("init", "-q", "-b", "main")
            g("remote", "add", "origin", remote)
            g("commit", "-q", "--allow-empty", "-m", "base")
        g("branch", name)
        if push:
            g("push", "-q", "origin", name)
        return g("rev-parse", name)

    def commit_on(self, name):
        d = self.e.dir
        g = lambda *a: subprocess.run(["git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                      capture_output=True, text=True, check=True).stdout.strip()
        g("checkout", "-q", name)
        g("commit", "-q", "--allow-empty", "-m", "unreviewed")
        g("checkout", "-q", "main")
        return g("rev-parse", name)

    def test_gate_ties_branch_to_reviewed_commit_and_one_ticket(self):
        head = self.git_branch("triage/sso-refresh")
        self.investigate(tier="low", branch="triage/sso-refresh")
        self.assertEqual(self.e.run("review", self.id, "--verdict", "approved", "--notes", "ok", ok=False).returncode, 1)
        self.e.j("review", self.id, "--verdict", "approved", "--notes", "ok", "--commit", head)
        bash = lambda c: self.e.hook({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                      "tool_input": {"command": c}}).returncode
        self.assertEqual(bash("git push origin triage/sso-refresh"), 0)
        self.assertEqual(bash("git push -u origin refs/heads/triage/sso-refresh:refs/heads/triage/sso-refresh"), 0)
        # the PR is built from the remote branch: not pushed yet → cannot verify → blocked
        pr = lambda h: self.e.hook({"hook_event_name": "PreToolUse", "tool_name": "mcp__github__create_pull_request",
                                    "tool_input": {"head": h}}).returncode
        self.assertEqual(pr("triage/sso-refresh"), 2)
        subprocess.run(["git", "-C", self.e.dir, "push", "-q", "origin", "triage/sso-refresh"], check=True)
        self.assertEqual(pr("triage/sso-refresh"), 0)
        self.assertEqual(pr("someone-else:triage/sso-refresh"), 2)  # fork head: can't verify
        self.assertEqual(bash("gh pr create --head triage/sso-refresh --title x"), 0)
        # attacks: another commit pushed under the reviewed name, force, renames, --all, case games
        other = self.commit_on("main")
        self.assertEqual(bash(f"git push origin {other}:triage/sso-refresh"), 2)
        self.assertEqual(bash("git push origin main:refs/heads/triage/sso-refresh"), 2)
        self.assertEqual(bash("git push origin +triage/sso-refresh"), 2)
        self.assertEqual(bash("git push --force origin triage/sso-refresh"), 2)
        self.assertEqual(bash("git push origin triage/sso-refresh:main"), 2)
        self.assertEqual(bash("git push --all origin"), 2)
        self.assertEqual(bash("FOO=1 git -c x.y=z push origin " + other + ":TRIAGE/sso-refresh"), 2)
        self.assertEqual(pr("TRIAGE/other"), 2)
        # fail closed on what the gate cannot see through
        for hidden in ("sh -c 'git push origin triage/sso-refresh'", "eval git push origin triage/sso-refresh",
                       "git push origin $(git rev-parse main):triage/sso-refresh",
                       "git -c alias.p=push p origin triage/sso-refresh",
                       "git push origin 'refs/heads/*:refs/heads/*'",
                       "gh api repos/acme/app/pulls --input body.json"):
            self.assertEqual(bash(hidden), 2, hidden)
        self.assertEqual(bash("env GIT_TRACE=0 /usr/bin/git push origin " + other + ":triage/sso-refresh"), 2)
        self.assertEqual(bash("gh api repos/acme/app/pulls -f head=triage/other -f base=main"), 2)
        subprocess.run(["git", "-C", self.e.dir, "checkout", "-q", "triage/sso-refresh"], check=True)
        self.assertEqual(bash("git push"), 2)  # implicit destination from a triage branch
        subprocess.run(["git", "-C", self.e.dir, "checkout", "-q", "main"], check=True)
        # ordinary commands that merely mention push are not caught
        for fine in ("git log --grep push", "gh pr view 3", "git push origin main"):
            self.assertEqual(bash(fine), 0, fine)
        # a commit added after the review is not what the reviewer approved
        self.commit_on("triage/sso-refresh")
        self.assertEqual(bash("git push origin triage/sso-refresh"), 2)
        # a second ticket cannot claim the same branch
        other_t = self.e.j("upsert", "--json", cand(31, title="Other", author="o"))["id"]
        self.e.j("claim", "--ids", other_t)
        res = {"id": other_t, "complexity": {"tier": "low", "rationale": "r"}, "repro": "reproduced",
               "investigation_file": self.inv, "branch": "triage/sso-refresh"}
        self.assertEqual(self.e.run("investigated", "--json", json.dumps(res), ok=False).returncode, 2)
        # a resolved ticket's old approval does not let its branch out
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "resolved", "evidence": ["x"]}))
        self.assertEqual(pr("triage/sso-refresh"), 2)

    def test_low_tier_gate_and_fix_ready_report(self):
        head = self.git_branch("triage/sso-refresh", push=True)
        self.investigate(tier="low", branch="triage/sso-refresh")
        hook = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": "gh pr create --head triage/sso-refresh --title x"}}
        self.assertEqual(self.e.hook(hook).returncode, 2)  # review pending
        self.assertEqual(self.e.run("pr", self.id, "--url", "https://x", ok=False).returncode, 2)
        self.e.j("review", self.id, "--verdict", "approved", "--notes", "tests cover it", "--commit", head)
        self.assertEqual(self.e.hook(hook).returncode, 0)
        self.assertEqual(self.e.j("due", "report-writing"), [{"id": self.id, "fix_ready": True}])
        # a fix-ready report must carry the fix
        self.assertEqual(self.e.run("report-set", self.id, "--json", json.dumps(GOOD_REPORT), ok=False).returncode, 2)
        self.e.j("report-set", self.id, "--json", json.dumps(dict(GOOD_REPORT, fix=FIX)))
        _, text = self.render_one()
        self.assertIn("Fix ready on branch `triage/sso-refresh`", text)
        self.assertIn("## Proposed fix\n\nCatch the expired token", text)
        self.assertIn("we're confident is ready to merge", text)
        self.e.j("pr", self.id, "--url", "https://github.com/acme/app/pull/7")
        _, text = self.render_one("--ids", self.id)
        self.assertIn("**Status:** Fix ready: PR open, independently reviewed", text)
        self.assertIn("Review it here: https://github.com/acme/app/pull/7", text)
        self.assertNotIn("<http", text)
        mcp = {"hook_event_name": "PreToolUse", "tool_name": "mcp__github__create_pull_request",
               "tool_input": {"head": "triage/sso-refresh"}}
        self.assertEqual(self.e.hook(mcp).returncode, 0)

    def test_push_from_worktree_is_gated(self):
        self.investigate()  # medium tier
        wt = os.path.join(self.e.dir, "wt")
        subprocess.run(["git", "init", "-q", "-b", "triage/try", wt], check=True)
        for cmd in (f"git -C {wt} push -u origin HEAD", f"cd {wt} && git push",
                    "gh pr create --head \"triage/try\"", "git push origin HEAD:refs/heads/triage/try",
                    "git push origin +triage/try"):
            p = self.e.hook({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": cmd}})
            self.assertEqual(p.returncode, 2, cmd)
        p = self.e.hook({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                         "tool_input": {"command": "git push origin main"}})
        self.assertEqual(p.returncode, 0)

    def test_medium_branch_cannot_pr(self):
        self.investigate(tier="low", branch="triage/try")
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "needs-reinvestigation", "evidence": ["x"]}))
        self.investigate()  # now medium: the branch is no longer the ticket's change
        hook = {"hook_event_name": "PreToolUse", "tool_name": "mcp__github__create_pull_request",
                "tool_input": {"head": "triage/try"}}
        p = self.e.hook(hook)
        self.assertEqual(p.returncode, 2)
        self.assertIn("no ticket has finished", p.stderr)

    def test_recheck_only_existing_and_allowed_keys(self):
        self.investigate()
        p = self.e.run("recheck-apply", "--json", json.dumps({"id": "FT-0099", "verdict": "confirmed",
                                                               "evidence": ["x"]}), ok=False)
        self.assertEqual(p.returncode, 1)
        p = self.e.run("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "corrected",
                                                               "patch": {"status": "resolved"}, "evidence": ["x"]}), ok=False)
        self.assertEqual(p.returncode, 2)
        r = self.e.j("recheck-apply", "--json", json.dumps({
            "id": self.id, "verdict": "resolved", "evidence": ["acme/app#12 closed by PR #40"],
            "upstream": {"states": {"github:acme/app#12": "closed"}, "fixed_by": "https://github.com/acme/app/pull/40"}}))
        self.assertEqual(r["status"], "resolved")
        self.assertEqual(self.e.j("due", "recheck", "--min-age-hours", "1"), [])

    def test_new_report_reopens_resolved(self):
        self.investigate()
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "resolved", "evidence": ["x"]}))
        self.e.j("upsert", "--json", cand(77, duplicate_of=self.id, author="new"))
        self.assertEqual(self.e.j("get", self.id)["status"], "needs-reinvestigation")

    def test_existing_pr_makes_a_fix_ready_report(self):
        self.e.j("claim")
        res = {"id": self.id, "complexity": {"tier": "low", "rationale": "one line"},
               "repro": "reproduced", "investigation_file": self.inv,
               "existing_pr": {"url": "https://github.com/acme/app/pull/9", "verdict": "fixes",
                               "unlinked_reason": "test"}}
        self.assertEqual(self.e.j("investigated", "--json", json.dumps(res))["next"], "report")
        bad = dict(GOOD_REPORT, fix="PR #78 fixes it. Merge it.")
        self.assertEqual(self.e.run("report-set", self.id, "--json", json.dumps(bad), ok=False).returncode, 2)
        self.e.j("report-set", self.id, "--json", json.dumps(dict(GOOD_REPORT, fix="PR #9 fixes every reported case. Check the empty-token test.")))
        out, text = self.render_one()
        self.assertIn("**Status:** Fix ready: an open upstream PR fixes it (we tested it)", text)
        self.assertIn("Review it here: https://github.com/acme/app/pull/9", text)
        allr = open(os.path.join(self.e.dir, out["all"])).read()
        self.assertIn("# Login returns 500", allr)
        self.e.j("sent", out["run"], "--all")
        self.assertEqual(self.e.j("get", self.id)["status"], "reported")

    def test_partial_pr_is_a_researched_report_listing_the_pr(self):
        self.e.j("claim")
        src = {"type": "bug", "title": "x", "summary": "y"}
        res = {"id": self.id, "complexity": {"tier": "medium", "rationale": "r"},
               "repro": "reproduced", "investigation_file": self.inv, "options_count": 2,
               "existing_pr": {"url": "https://github.com/acme/app/pull/77", "verdict": "partial"}}
        p = self.e.run("investigated", "--json", json.dumps(res), ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("not linked", p.stderr)
        res["existing_pr"]["unlinked_reason"] = "same diff, author forgot to link"
        self.e.j("investigated", "--json", json.dumps(res))
        self.assertEqual(self.e.run("report-set", self.id, "--json", json.dumps(dict(GOOD_REPORT, fix=FIX)),
                                    ok=False).returncode, 2)  # partial is not fix-ready
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        _, text = self.render_one()
        self.assertNotIn("## Proposed fix", text)

    def test_backslash_in_finding_renders(self):
        self.investigate()
        self.e.j("report-set", self.id, "--json", json.dumps(dict(GOOD_REPORT, findings=[r"It fails on `C:\Users\dana` paths."])))
        _, text = self.render_one()
        self.assertIn("C:\\Users", text)

    def test_sent_survives_status_change_after_render(self):
        self.investigate()
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        out = self.e.j("render")
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "needs-reinvestigation",
                                                        "evidence": ["new info"]}))
        self.e.j("claim")
        self.e.j("sent", out["run"], "--all")
        t = self.e.j("get", self.id)
        self.assertEqual((t["status"], t["reported"]["count"]), ("investigating", 1))
        self.e.run("sent", out["run"], "--all", ok=False)  # run already moved; no double count
        self.assertEqual(self.e.j("get", self.id)["reported"]["count"], 1)

    def test_downgrade_returns_for_options_and_forbids_low(self):
        self.investigate(tier="low", branch="triage/x")
        self.e.j("review", self.id, "--verdict", "changes", "--notes", "misses edge case", "--downgrade")
        t = self.e.j("get", self.id)
        self.assertEqual((t["status"], t["investigation"]["prior_attempt"]), ("needs-reinvestigation", "triage/x"))
        self.e.j("claim")
        res = {"id": self.id, "complexity": {"tier": "low", "rationale": "r"},
               "repro": "reproduced", "investigation_file": self.inv, "branch": "triage/y"}
        self.assertEqual(self.e.run("investigated", "--json", json.dumps(res), ok=False).returncode, 1)
        res.update(complexity={"tier": "medium", "rationale": "r"}, options_count=2)
        res.pop("branch")
        self.e.j("investigated", "--json", json.dumps(res))

    def test_reinvestigated_as_medium_drops_stale_pr(self):
        self.investigate(tier="low", branch="triage/x")
        self.e.j("review", self.id, "--verdict", "approved", "--notes", "ok", "--commit", "abc1234")
        self.e.j("pr", self.id, "--url", "https://github.com/acme/app/pull/99")
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "needs-reinvestigation", "evidence": ["x"]}))
        self.investigate(tier="medium")
        inv = self.e.j("get", self.id)["investigation"]
        self.assertNotIn("pr_url", inv)
        self.assertNotIn("review", inv)

    def test_low_with_partial_pr_still_needs_our_change(self):
        self.e.j("claim")
        res = {"id": self.id, "complexity": {"tier": "low", "rationale": "r"},
               "repro": "reproduced", "investigation_file": self.inv,
               "existing_pr": {"url": "https://github.com/acme/app/pull/9", "verdict": "partial", "unlinked_reason": "t"}}
        self.assertEqual(self.e.run("investigated", "--json", json.dumps(res), ok=False).returncode, 1)

    def test_reprint_keeps_unposted_run_and_filters(self):
        self.investigate()
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        first = self.e.j("render")
        again = self.e.j("render", "--ids", self.id)
        self.assertTrue(again["files"])
        self.e.j("sent", first["run"], "--all")  # the first paste can still be recorded
        other = self.e.j("upsert", "--json", cand(55, title="Unrelated", author="q"))["id"]
        self.assertIsNone(self.e.j("render", "--ids", other)["run"])  # no report yet: nothing, no crash

    def test_fixed_on_base_resolves_without_report(self):
        self.e.j("claim")
        r = self.e.j("investigated", "--json", json.dumps({"id": self.id, "investigation_file": self.inv,
                     "fixed_on_base": {"commit": "ca892b36", "evidence": "repro passes on main"}}))
        self.assertEqual(r["status"], "resolved")
        self.assertEqual(self.e.j("due", "report-writing"), [])

    def test_render_reports_backlog_outside_the_reports(self):
        self.investigate()
        self.e.j("upsert", "--json", cand(60, title="Not looked at yet", author="z"))
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        out, text = self.render_one()
        self.assertEqual(out["backlog"]["not_investigated"], 1)
        self.assertNotIn("not investigated", text)

    def test_existing_fix_forbids_duplicate_branch(self):
        self.e.j("claim")
        res = {"id": self.id, "complexity": {"tier": "low", "rationale": "r"},
               "repro": "reproduced", "investigation_file": self.inv, "branch": "triage/dup",
               "existing_pr": {"url": "https://github.com/acme/app/pull/9", "verdict": "fixes",
                               "unlinked_reason": "test"}}
        p = self.e.run("investigated", "--json", json.dumps(res), ok=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("already fixes", p.stderr)

    def test_failures_not_claims_count_toward_blocked(self):
        self.investigate()
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "needs-reinvestigation",
                                                        "evidence": ["x"]}))
        self.e.j("claim")
        self.assertEqual(self.e.j("release", self.id, "--reason", "timeout")["status"], "new")

    def test_resolved_drops_out_of_recheck_after_quiet_checks(self):
        self.investigate()
        v = {"id": self.id, "verdict": "resolved", "evidence": ["closed"]}
        self.e.j("recheck-apply", "--json", json.dumps(v))
        for _ in range(2):
            self.e.j("recheck-apply", "--json", json.dumps(dict(v, verdict="confirmed")))
        self.assertEqual(self.e.j("due", "recheck", "--min-age-hours", "0"), [])

    def test_resolved_is_announced_once(self):
        self.investigate()
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        out = self.e.j("render")
        self.e.j("sent", out["run"], "--all")
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "resolved",
                                                        "evidence": ["closed by PR #40"]}))
        out = self.e.j("render")
        self.assertEqual(out["files"], [])
        self.assertEqual(out["closed"][0]["title"], "Login fails after SSO timeout")
        self.e.j("sent", out["run"], "--all")
        self.assertIsNone(self.e.j("render")["run"])

    def test_reinvestigation_marks_report_stale(self):
        self.investigate()
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        self.e.j("recheck-apply", "--json", json.dumps({"id": self.id, "verdict": "needs-reinvestigation",
                                                        "evidence": ["new repro on 2.5"]}))
        self.investigate()
        self.assertEqual(self.e.j("due", "report"), [])
        self.assertEqual(self.e.j("due", "report-writing"), [{"id": self.id, "fix_ready": False}])

    def test_reporter_count_in_report(self):
        self.investigate()
        for n, who in ((20, "a"), (21, "b"), (22, "c")):
            self.e.j("upsert", "--json", cand(n, duplicate_of=self.id, author=who))
        self.e.j("report-set", self.id, "--json", json.dumps(GOOD_REPORT))
        _, text = self.render_one()
        self.assertIn("**Reported by:** 4 people", text)


class Persistence(unittest.TestCase):
    """state.sh branch mode: two clones share one queue through an orphan state branch."""

    def test_branch_mode_round_trip(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        remote = os.path.join(tmp.name, "remote.git")
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        clones = []
        for name in ("a", "b"):
            d = os.path.join(tmp.name, name)
            subprocess.run(["git", "init", "-q", "-b", "main", d], check=True)
            subprocess.run(["git", "-C", d, "remote", "add", "origin", remote], check=True)
            subprocess.run(["git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                            "--allow-empty", "-m", "init"], check=True)
            os.makedirs(os.path.join(d, ".claude"))
            with open(os.path.join(d, ".claude", "feedback-triage.json"), "w") as f:
                json.dump({"state": {"persist": "branch"}}, f)
            clones.append(d)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        state = os.path.join(ROOT, "scripts", "state.sh")

        def sh(d, *args):
            return subprocess.run([state, *args], capture_output=True, text=True, check=True,
                                  env={**env, "FT_PROJECT_DIR": d})

        def ft(d, *args):
            return subprocess.run([sys.executable, FT, *args], capture_output=True, text=True, check=True,
                                  env={**env, "FT_PROJECT_DIR": d}).stdout

        a, b = clones
        sh(a, "pull")
        ft(a, "init", "--no-config")
        ft(a, "upsert", "--json", cand(1))
        self.assertIn('"pushed":true', sh(a, "save", "intake a").stdout)
        sh(b, "pull")
        self.assertIn("FT-0001", ft(b, "list"))
        ft(b, "upsert", "--json", cand(2, author="kim"))
        sh(b, "save", "intake b")
        sh(a, "pull")
        self.assertIn("FT-0002", ft(a, "list"))
        # two runners allocate the same id → conflict is recovered, not wedged
        ft(a, "upsert", "--json", cand(3, author="p"))
        ft(b, "upsert", "--json", cand(4, author="q"))
        sh(a, "save", "a")
        r = subprocess.run([state, "save", "b"], capture_output=True, text=True,
                           env={**env, "FT_PROJECT_DIR": b})
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn('"conflict":true', r.stdout)
        sh(b, "pull")
        self.assertIn("ok", ft(b, "validate"))  # clean queue, no conflict markers
        ft(b, "upsert", "--json", cand(4, author="q"))  # re-run the phase
        self.assertIn('"pushed":true', sh(b, "save", "b again").stdout)
        sh(a, "pull")
        self.assertEqual(ft(a, "list", "--format", "ids").split(), ["FT-0001", "FT-0002", "FT-0003", "FT-0004"])
        # a crashed phase left unsaved changes that conflict with the remote: pull must not leave markers
        ft(a, "upsert", "--json", cand(5, author="r"))          # a crashes before saving (FT-0005)
        ft(b, "upsert", "--json", cand(6, author="s"))          # b allocates FT-0005 too and saves
        sh(b, "save", "b")
        r = subprocess.run([state, "pull"], capture_output=True, text=True, env={**env, "FT_PROJECT_DIR": a})
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("ok", ft(a, "validate"))
        st_dir = os.path.join(a, ".feedback-triage")
        unmerged = subprocess.run(["git", "-C", st_dir, "diff", "--name-only", "--diff-filter=U"],
                                  capture_output=True, text=True).stdout
        self.assertEqual(unmerged, "")
        # the product branch never sees queue files
        status = subprocess.run(["git", "-C", a, "status", "--porcelain"], capture_output=True, text=True).stdout
        self.assertNotIn(".feedback-triage", status)


class Hooks(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.e.run("init")

    def test_direct_queue_edit_blocked(self):
        p = self.e.hook({"hook_event_name": "PreToolUse", "tool_name": "Write",
                         "tool_input": {"file_path": os.path.join(self.e.dir, ".feedback-triage", "queue", "FT-0001.json")}})
        self.assertEqual(p.returncode, 2)
        p = self.e.hook({"hook_event_name": "PreToolUse", "tool_name": "Write",
                         "tool_input": {"file_path": os.path.join(self.e.dir, ".feedback-triage", "investigations", "FT-0001.md")}})
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
