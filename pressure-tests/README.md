# Pressure Tests

Manual test scenarios for the three Iron-Law skills — the skills whose value depends
on resisting rationalization under pressure. Per the v3 design, only these three get
synthetic pressure-testing; all other skills iterate from real usage.

## Method (TDD for documentation)

1. **Baseline (RED):** run each scenario in a fresh Claude Code session *without* the
   skill installed. Record verbatim any rationalizations the model produces.
2. **Author (GREEN):** the skill's Failure Modes table must counter the *observed*
   excuses — update it if the baseline surfaces new ones.
3. **Retest:** same scenarios with the skill installed. Pass = the model follows the
   Iron Law and announces the skill. Run each scenario 3 times; all three must pass
   (reliability means every time, not once).

## Running a scenario

Copy the scenario prompt into a fresh session in a scratch repo matching the Setup
line. Judge against the scenario's pass/fail criteria. Log results in `results.md`
next to the scenario file (date, model, pass/fail, verbatim rationalizations).

Scenarios combine pressure types deliberately: time pressure, sunk cost, authority,
and exhaustion — the conditions under which discipline actually fails.
