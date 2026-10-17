#!/usr/bin/env python3
"""Score investigation + report quality and cross-run consistency.

usage: score_reports.py <project dir> [<project dir> …]
Per run:  tier accuracy vs fixtures/expected.json, spiciness floors, report lint
          (errors + warnings), field lengths, rendered-message shape.
Across runs (2+ dirs): tier and spice agreement per expected group.
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


def shape(text):
    """Line-kind signature of a rendered message: which template lines appear."""
    kinds = []
    for line in text.strip().splitlines():
        if re.match(r"^\S+ \*FT-\d{4} · ", line): kinds.append("title")
        elif "·" in line and re.search(r"(Bug|Feature) · ", line): kinds.append("badges")
        elif line.startswith("*What:*"): kinds.append("what")
        elif line.startswith("*Found:*"): kinds.append("found")
        elif line.startswith("• "): kinds.append("finding")
        elif line.startswith("*Do:*"): kinds.append("do")
        elif line.startswith("*Ask:*"): kinds.append("ask")
        elif line.startswith("<") and "|" in line and ("👉" in line): kinds.append("pr")
        elif line.startswith("🌿 `"): kinds.append("branch")
        elif line.startswith("<"): kinds.append("sources")
        else: kinds.append("OTHER:" + line[:30])
    return kinds


def score_run(project, exp):
    st, tickets = load(project)
    groups = group_map(st, tickets, exp)
    res = {"tier_ok": 0, "tier_total": 0, "spice_floor_ok": 0, "spice_floor_total": 0,
           "lint_errors": 0, "lint_warnings": 0, "reports": 0, "shape_bad": [], "tiers": {}, "spice": {},
           "words": {"headline": [], "what": [], "finding": [], "recommendation": []}}
    for g, t in groups.items():
        spec = exp["groups"][g]
        if not t or not t.get("complexity"):
            continue
        tier = t["complexity"]["tier"]
        res["tiers"][g] = tier
        res["spice"][g] = t["spiciness"]["level"]
        res["tier_total"] += 1
        res["tier_ok"] += tier in spec["tiers"]
        if "min_spice" in spec:
            res["spice_floor_total"] += 1
            res["spice_floor_ok"] += t["spiciness"]["level"] >= spec["min_spice"]
        rep = t.get("report")
        if rep:
            res["reports"] += 1
            e, w = ft.lint_report({k: v for k, v in rep.items() if not k.startswith("_")}, tier)
            res["lint_errors"] += len(e)
            res["lint_warnings"] += len(w)
            res["words"]["headline"].append(len(ft.words(rep["headline"])))
            res["words"]["what"].append(len(ft.words(rep["what"])))
            res["words"]["finding"] += [len(ft.words(f)) for f in rep["findings"]]
            if rep.get("recommendation"):
                res["words"]["recommendation"].append(len(ft.words(rep["recommendation"])))
    outbox = os.path.join(st.dir, "reports")
    for dp, _, files in os.walk(outbox):
        for f in files:
            if re.match(r"\d\d-FT-\d{4}\.txt$", f):
                k = shape(open(os.path.join(dp, f)).read())
                if any(x.startswith("OTHER") for x in k) or k[:3] != ["title", "badges", "what"]:
                    res["shape_bad"].append((f, k))
    res["words"] = {k: (round(statistics.mean(v), 1), round(statistics.pstdev(v), 1)) if v else None
                    for k, v in res["words"].items()}
    return res


def main(dirs):
    exp = json.load(open(os.path.join(HERE, "fixtures", "expected.json")))
    runs = [score_run(d, exp) for d in dirs]
    for d, r in zip(dirs, runs):
        print(f"== {os.path.basename(d)}")
        print(json.dumps(r, indent=1, ensure_ascii=False))
    if len(runs) > 1:
        agree_t = agree_s = n = 0
        for g in exp["groups"]:
            ts = [r["tiers"].get(g) for r in runs]
            ss = [r["spice"].get(g) for r in runs]
            if None in ts:
                continue
            n += 1
            agree_t += len(set(ts)) == 1
            agree_s += len(set(ss)) == 1
            print(f"  {g:<24} tiers={ts} spice={ss}")
        print(f"cross-run agreement: tier {agree_t}/{n} · spice {agree_s}/{n}")


if __name__ == "__main__":
    main(sys.argv[1:])
