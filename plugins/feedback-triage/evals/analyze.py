#!/usr/bin/env python3
"""Summarise a stream-json run: cost, tokens, turns, subagents, plugin files read.

usage: analyze.py <run.jsonl>
"""
import collections
import json
import sys

reads = collections.Counter()
agents = collections.Counter()
result = {}
for line in open(sys.argv[1]):
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    if ev.get("type") == "result":
        result = ev
    msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
    for block in msg.get("content") or [] if isinstance(msg.get("content"), list) else []:
        if block.get("type") != "tool_use":
            continue
        inp = block.get("input") or {}
        if block.get("name") == "Read" and "feedback-triage/" in (inp.get("file_path") or ""):
            reads[inp["file_path"].split("feedback-triage/")[-1]] += 1
        if block.get("name") in ("Agent", "Task"):
            agents[inp.get("subagent_type", "?")] += 1
        if block.get("name") == "Skill":
            reads["Skill:" + str(inp.get("skill"))] += 1
u = result.get("usage") or {}
print(json.dumps({
    "cost_usd": round(result.get("total_cost_usd") or 0, 2),
    "minutes": round((result.get("duration_ms") or 0) / 60000, 1),
    "turns": result.get("num_turns"),
    "orchestrator_tokens_in": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                              + (u.get("cache_creation_input_tokens") or 0),
    "by_model_cost": {k: round(v.get("costUSD", 0), 2) for k, v in (result.get("modelUsage") or {}).items()},
    "subagents": dict(agents),
    "plugin_files_read": dict(reads),
    "is_error": result.get("is_error"),
}, indent=1))
