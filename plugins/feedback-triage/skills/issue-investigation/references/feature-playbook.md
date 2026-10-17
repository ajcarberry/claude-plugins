# Feature Playbook — From Request to Requirements

Requests arrive as solutions ("add a --json flag"). The job is to find the
problem under the solution, then specify it well enough that an engineer could
build it — or decide not to — without asking the reporter anything.

## 1. The job behind the request

- **Who** is asking (role, plan, how they use the product) and **what they are
  trying to get done** when they hit the gap.
- **Today's workaround** and what it costs them (time, errors, a competitor).
- Restate as a problem: *"CI users can't parse the output reliably"* — not *"users
  want --json"*. Keep the requested solution as one candidate, not the answer.
- Count the evidence: reporters, linked duplicates, plus-ones, accounts named.

## 2. What already exists

Search before specifying:

- The codebase: is it partly built, behind a flag, or one option away?
- Docs: is it possible today and the user didn't find it? (Then the finding is a
  docs/discoverability gap — often low complexity.)
- Roadmap/spec files (`docs/roadmap.md`, `specs/`, `ROADMAP.md`) and open
  issues/PRs: already planned, already declined, or in flight? Link them.

## 3. Requirements

Write requirements a reviewer can check, in this shape:

- **Must** (the smallest version that solves the job): numbered, testable.
- **Acceptance criteria**: Given / When / Then, one per must.
- **Edge cases**: empty input, large input, permissions, errors, concurrency,
  backward compatibility, other platforms.
- **Non-goals**: what this will not do, so scope can't creep.
- **Open questions**: anything only a product owner can answer. Any open question
  that changes the must-list makes the ticket at least **medium**.

Think hard here — this section is the feature investigation's main value. A
missing edge case found now saves a review cycle later.

## 4. Options (medium and low)

At least two real approaches, each: what it is, where it lives, effort (S/M/L),
risks, migration/compat impact, and which requirements it leaves out. Typical
axes: config flag vs. new command; client vs. server; extend an existing feature
vs. a new surface; build vs. document a workaround.

## Impact for features

Unblocks a workflow that users have no workaround for → 2. Blocks adoption, a
deal, or a strategic goal named in the roadmap → 3. Quality-of-life → 1. Nice to
have → 0.
