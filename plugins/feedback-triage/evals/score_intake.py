#!/usr/bin/env python3
"""Score an intake run against fixtures/expected.json.

usage: score_intake.py <project dir> [--json]
Measures: coverage (every source item tracked or ignored), noise handling,
pairwise dedup precision/recall, the split message, type accuracy, reporter count.
"""
import itertools
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FT = os.path.join(os.path.dirname(HERE), "scripts", "ft.py")


def ft(project, *args):
    out = subprocess.run([sys.executable, FT, *args], capture_output=True, text=True,
                         env={**os.environ, "FT_PROJECT_DIR": project}, check=True).stdout
    return json.loads(out)


def score(project):
    exp = json.load(open(os.path.join(HERE, "fixtures", "expected.json")))
    tickets = {t["id"]: t for t in ft(project, "list", "--format", "json")}
    paths = ft(project, "paths")
    idx = json.load(open(paths["index"]))
    refs, ignored = idx["refs"], idx["ignored"]

    def ticket_of(ref):
        tid = refs.get(ref)
        while tid and tickets[tid]["status"] == "duplicate":
            tid = tickets[tid]["duplicate_of"]
        return tid

    split = exp["split"]
    all_expected = [r for g in exp["groups"].values() for r in g["refs"]] + exp["ignored"]
    missing = [r for r in all_expected if r not in refs and r not in ignored and r != split + "~2"]
    split_tickets = {ticket_of(split), ticket_of(split + "~2")} - {None}
    f1_ticket = ticket_of("github:acme/tasklite#2")
    split_ok = len(split_tickets) == 2 and f1_ticket in split_tickets
    noise_ok = [r for r in exp["ignored"] if r in ignored]
    noise_tracked = [r for r in exp["ignored"] if r in refs]

    # pairwise clustering over non-split tracked refs
    member = {}
    for g, spec in exp["groups"].items():
        for r in spec["refs"]:
            if not r.startswith(split):
                member[r] = g
    tp = fp = fn = 0
    for a, b in itertools.combinations(sorted(member), 2):
        same_exp = member[a] == member[b]
        ta, tb = ticket_of(a), ticket_of(b)
        same_act = ta is not None and ta == tb
        tp += same_exp and same_act
        fp += (not same_exp) and same_act
        fn += same_exp and not same_act
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0

    open_tickets = [t for t in tickets.values() if t["status"] != "duplicate"]
    type_hits, groups = 0, {}
    for g, spec in exp["groups"].items():
        tid = ticket_of(spec["refs"][0]) or ticket_of((spec.get("alt_refs") or [""])[0])
        groups[g] = tid
        if tid and (spec["type"] == "any" or tickets[tid]["type"] == spec["type"]):
            type_hits += 1
    b1 = tickets.get(groups.get("B1-export-drops-last") or "", {})
    reporters = 0
    if b1:
        names = set()
        for s in b1["sources"]:
            names.add(s.get("author", "").lower())
            names.update(p.lower() for p in s.get("plus_ones") or [])
        reporters = len(names - {""})
    valid = subprocess.run([sys.executable, FT, "validate"], capture_output=True, text=True,
                           env={**os.environ, "FT_PROJECT_DIR": project}).returncode == 0
    return {
        "tickets": len(open_tickets), "expected_tickets": len(exp["groups"]),
        "coverage": round(1 - len(missing) / len(all_expected), 3), "missing": missing,
        "noise_ignored": f"{len(noise_ok)}/{len(exp['ignored'])}", "noise_tracked": noise_tracked,
        "dedup_precision": round(precision, 3), "dedup_recall": round(recall, 3),
        "split_ok": split_ok, "type_accuracy": f"{type_hits}/{len(exp['groups'])}",
        "b1_reporters": reporters, "queue_valid": valid, "group_tickets": groups,
    }


if __name__ == "__main__":
    print(json.dumps(score(sys.argv[1]), indent=2))
