#!/usr/bin/env python3
"""Score investigation + report quality and cross-run consistency.

usage: score_reports.py <project dir> [<project dir> …]
Per run:  tier accuracy vs expected.json, report lint (errors + warnings), field
          lengths, report shape (title, intro, sections, fix section iff fix-ready,
          no internal ids). Across runs (2+ dirs): tier agreement per expected group.
"""
import json
import os
import re
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import ft  # noqa: E402


def load(project):
    os.environ["FT_PROJECT_DIR"] = project
    st = ft.Store(project)
    return st, {t["id"]: t for t in st.all()}


def group_map(st, tickets, exp):
    idx = st.index()
    out = {}
    for g, spec in exp["groups"].items():
        tid = idx["refs"].get(spec["refs"][0])
        while tid and tickets[tid]["status"] == "duplicate":
            tid = tickets[tid]["duplicate_of"]
        out[g] = tickets.get(tid)
    return out


SECTIONS = ("## What's happening", "## What we found", "## Sources")


def shape_problems(text, fix_ready):
    """What a tracker-ready report must look like (and must never contain)."""
    probs = []
    if not text.startswith("# "):
        probs.append("no title line")
    if "👋" not in text.split("\n\n")[1]:
        probs.append("no intro")
    if "**Type:**" not in text or "**Status:**" not in text:
        probs.append("no status line")
    for sec in SECTIONS:
        if sec not in text:
            probs.append(f"missing {sec}")
    if ("## Proposed fix" in text) != bool(fix_ready):
        probs.append("fix section does not match fix readiness")
    if re.search(r"\bFT-\d+", text):
        probs.append("internal id leaked")
    if "{{" in text or "<http" in text or "🌶" in text:
        probs.append("template residue")
    return probs


def read_manifest(d):
    p = os.path.join(d, "manifest.json")
    return json.load(open(p)) if os.path.exists(p) else None


def score_run(project, exp):
    st, tickets = load(project)
    groups = group_map(st, tickets, exp)
    res = {"tier_ok": 0, "tier_total": 0,
           "lint_errors": 0, "lint_warnings": 0, "reports": 0, "fix_ready": 0, "shape_bad": [], "tiers": {},
           "fixed_on_base": {"hit": [], "missed": [], "wrong": []},
           "words": {"headline": [], "what": [], "finding": [], "fix": []}}
    for g, t in groups.items():
        spec = exp["groups"][g]
        # fixed_on_base: true = must be found fixed on the base branch; "maybe" = either is fine
        fixed = bool(t and (t.get("verification") or {}).get("fixed_by"))
        want = spec.get("fixed_on_base", False)
        if want is True:
            res["fixed_on_base"]["hit" if fixed else "missed"].append(g)
        elif fixed and want is False:
            res["fixed_on_base"]["wrong"].append(g)
        if not t or not t.get("complexity"):
            continue
        tier = t["complexity"]["tier"]
        res["tiers"][g] = tier
        res["tier_total"] += 1
        res["tier_ok"] += tier in spec["tiers"]
        rep = t.get("report")
        if rep:
            res["reports"] += 1
            e, w = ft.lint_report({k: v for k, v in rep.items() if not k.startswith("_")},
                                  bool(ft.fix_kind(t)), ft.fix_pr_numbers(t))
            res["fix_ready"] += bool(ft.fix_kind(t))
            res["lint_errors"] += len(e)
            res["lint_warnings"] += len(w)
            res["words"]["headline"].append(len(ft.words(rep["headline"])))
            res["words"]["what"].append(len(ft.words(rep["what"])))
            res["words"]["finding"] += [len(ft.words(f)) for f in rep["findings"]]
            if rep.get("fix"):
                res["words"]["fix"].append(len(ft.words(rep["fix"])))
    by_id = {}
    runs = sorted((os.path.basename(dp), dp) for dp, _, _ in os.walk(os.path.join(st.dir, "reports"))
                  if "superseded" not in dp and read_manifest(dp))
    for _, dp in runs[-1:]:  # the newest run is what a human would paste
        for f in read_manifest(dp).get("files", []):
            if f.get("kind") == "ticket":
                by_id[f["id"]] = (os.path.join(dp, os.path.basename(f["file"])), f.get("fix"))
    for tid, (path, fix) in by_id.items():
        probs = shape_problems(open(path).read(), fix)
        if probs:
            res["shape_bad"].append((os.path.basename(path), probs))
    res["words"] = {k: (round(statistics.mean(v), 1), round(statistics.pstdev(v), 1)) if v else None
                    for k, v in res["words"].items()}
    return res


def main(dirs):
    exp = json.load(open(os.path.join(HERE, os.environ.get("SCENARIO", "fixtures"), "expected.json")))
    runs = [score_run(d, exp) for d in dirs]
    for d, r in zip(dirs, runs):
        print(f"== {os.path.basename(d)}")
        print(json.dumps(r, indent=1, ensure_ascii=False))
    if len(runs) > 1:
        agree_t = n = 0
        for g in exp["groups"]:
            ts = [r["tiers"].get(g) for r in runs]
            if None in ts:
                continue
            n += 1
            agree_t += len(set(ts)) == 1
            print(f"  {g:<24} tiers={ts}")
        print(f"cross-run tier agreement: {agree_t}/{n}")


if __name__ == "__main__":
    main(sys.argv[1:])
