#!/usr/bin/env python3
"""Static context footprint of each phase: what the orchestrator and each subagent
load before doing any work. Tokens ≈ chars / 4 (relative comparisons only).

usage: context_cost.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASES = {  # who: files loaded (command/agent body + skills it loads + refs it is told to read)
    "intake/orchestrator": ["commands/intake.md"],
    "intake/source-reader": ["agents/source-reader.md", "skills/feedback-intake/SKILL.md"],
    "recheck/orchestrator": ["commands/recheck.md"],
    "recheck/ticket-verifier": ["agents/ticket-verifier.md", "skills/ticket-verification/SKILL.md"],
    "investigate/orchestrator": ["commands/investigate.md"],
    "investigate/bug-investigator": ["agents/bug-investigator.md", "skills/issue-investigation/SKILL.md",
                                     "skills/issue-investigation/references/bug-playbook.md", "references/complexity.md",
                                     "references/spiciness.md", "templates/investigation-bug.md"],
    "investigate/feature-analyst": ["agents/feature-analyst.md", "skills/issue-investigation/SKILL.md",
                                    "skills/issue-investigation/references/feature-playbook.md", "references/complexity.md",
                                    "references/spiciness.md", "templates/investigation-feature.md"],
    "investigate/change-reviewer": ["agents/change-reviewer.md"],
    "report/orchestrator": ["commands/report.md"],
    "report/report-writer": ["agents/report-writer.md", "skills/slack-reporting/SKILL.md"],
}


def tok(path):
    p = os.path.join(ROOT, path)
    return len(open(p).read()) // 4 if os.path.exists(p) else 0


total = 0
for who, files in PHASES.items():
    n = sum(tok(f) for f in files)
    total += n
    print(f"{who:<32} {n:>6}  " + " ".join(f"{os.path.basename(os.path.dirname(f)) if f.endswith('SKILL.md') else os.path.basename(f)}:{tok(f)}" for f in files))
print(f"{'sum of load sets':<32} {total:>6}")
