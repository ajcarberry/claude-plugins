# Design v4: Four plugins, right-sized

**Status:** iterating; supersedes v3 (2026-07-12).
**Goal:** four independent plugins — **Launchpad** (dev lifecycle), **TPM** (product lifecycle),
**Document** (docs), **Commit** (commit quality) — plus the **global CLAUDE.md** baseline,
each lean, each useful alone, with Launchpad as the only plugin that calls the others.
Domain packs, R/S/V machinery, and fixed review pipelines are gone. What remains is the
efficiency machinery agentic workflows actually need.

**Decision log (v4):**

1. Strip all four domain packs (`launchpad-web/-electron/-infra/-tpm` in their old form).
2. Five-phase lifecycle: `/stage` → `/mission-plan` (optional) → `/launch` → `/orbit` →
   `/land`. Express lane = skip `/mission-plan`. `/hop` deleted.
3. Kill the mission-brief + flight-plan split and the EARS/R-S-V apparatus; one spec artifact.
4. `/status` returns as the human catch-up command; the SessionStart hook serves Claude's
   context, `/status` serves the human. Different audiences, both kept.
5. TPM becomes a full product-lifecycle plugin grounded in real maintainer scenarios
   (OSS project: GitHub + Discord community + dev team in Slack): inbound
   signals → themes → roadmap/specs, outbound alignment feedback + audience-tailored
   comms (`/feedback`, `/triage`, `/roadmap`, `/spec`, `/comms`).
6. Enforcement moves to hooks built on a dirty/clean validation stamp; skills teach,
   hooks enforce.
7. Specialized workflows (browser verification, infra plan-before-apply, …) cut from
   core — the Iron Laws double as routers that pull specialist skills in when the
   surface demands them (see Flight rules).
8. Global CLAUDE.md stays: the ≤ ~40-line Karpathy-grounded behavioral baseline,
   versioned here, installed to `~/.claude/CLAUDE.md`.
9. Risk and self-review re-added minimally (v4.1): stakes as a one-line mission-state
   field consumed downstream (same trick as the stamp), and self-review as a
   fresh-context step in `/orbit` before the PR opens. The rubric table and the
   independent-reviewer filter survive from v3; the pipeline machinery does not.

---

## Design principles

1. **Context quality determines agent quality.** The repo's thesis. Every component
   exists to hand each model — Opus orchestrator or Haiku drone — exactly the context
   it needs and nothing else.

2. **Efficiency machinery is the product.** Not just "be token-efficient" as a style
   rule, but concrete mechanisms: on-demand reference loading, work-packet dispatch,
   model tiering, structured subagent returns, mission state as shared memory, a
   dirty/clean stamp so enforcement costs a file check instead of a judgment call.
   Budgets: command specs ≤ ~200 lines; SKILL.md ≤ ~150 lines with references loaded
   on demand.

3. **The override convention.** Every skill that ships a default first checks for a
   project-specific definition — (1) a project skill of the same name, (2) a documented
   project file at a known path — and defers to it entirely if found. Applies to:
   validation (Launchpad), spec template (TPM), doc style (Document), commit convention
   (Commit). Each plugin README documents the path it checks. Mirrors how the built-in
   `/verify` bootstraps a project skill.

4. **Skills teach; hooks enforce.** Anything requiring judgment lives in a skill.
   Anything a script can check deterministically (file exists, stamp fresh, exit code)
   lives in a hook. Hooks that make judgment calls produce false blocks, and false
   blocks get the enforcement layer disabled. Every hook: fast (<100ms), dumb, with a
   documented escape hatch.

5. **Observable-check-first is the root law** (Karpathy's goal-driven execution):
   every change defines a check that fails before and passes after — a failing test
   where a harness exists; a curl, screenshot, or job-status query where it doesn't.
   TDD is the code specialization of this rule, not the universal law.

---

## System shape

| Component | What it owns | Depends on |
|---|---|---|
| **launchpad** | Dev lifecycle: phases, state, enforcement, orchestration | calls TPM/Document/Commit *optionally* |
| **tpm** | Product lifecycle: feedback → roadmap → spec | nothing |
| **document** | Doc writing: types, style, templates | nothing |
| **commit** | Commit quality: staging, messages, conventions | nothing |
| **global CLAUDE.md** | ≤ ~40-line behavioral baseline, installed to `~/.claude/CLAUDE.md`, versioned in `global/` | nothing |

Launchpad is the only caller; every call site has a stated fallback so it works alone.

---

## Global CLAUDE.md

The Karpathy-grounded baseline every project inherits; project CLAUDE.md files extend
and override it. Its four sections survive v4 intact in spirit:

- **Surgical changes** — every changed line traces to the request; no drive-by refactors.
- **Think before coding** — surface competing interpretations; push back once on
  overcomplication, then defer; no speculative abstraction.
- **Goal-driven execution** — transform tasks into verifiable goals before starting;
  no completion claims without fresh command evidence. This is the root law's
  global-scope statement.
- **Workflow** — check whether a plugin command/skill applies before implementing;
  high-stakes surfaces (auth, payments, secrets, migrations, prod infra, destructive
  ops) mean slow down, gate, back up first.

**v4 change required:** the Workflow section references `/mission` and `/hop`; update
to the v4 command names once they land. Installer (`global/install.sh`) unchanged.

---

## 1. Launchpad

### Commands (6)

- **`/stage`** — create clean worktree + branch from an idea. Writes `.claude/mission/`
  (idea, branch, date, and a `stakes: low|standard|high` call from `references/stakes.md`;
  `/mission-plan` may revise it).
- **`/mission-plan`** — optional, for complex work. Produces the spec via TPM's
  `spec-authoring` skill (fallback: minimal inline format). Decomposes the spec into
  **work packets** (see Efficiency machinery). Output: `.claude/mission/spec.md`.
- **`/launch`** — implementation. With a spec: dispatch packets to subagents per the
  orchestration reference. Without: express lane, implement directly under flight
  rules. Invokes Document's skill for doc updates near the end; uses Commit for
  checkpoints.
- **`/orbit`** — two modes by PR state. No PR: validate → **self-review** → open PR.
  PR open: fetch review comments, respond/fix, re-validate. Re-run on feedback; no
  pretend continuous monitoring.
- **`/land`** — merge PR, delete branch, remove worktree, archive `.claude/mission/`.
  When `stakes: high`, merge requires explicit human confirmation.
- **`/status`** — human catch-up. Walks the workflow state: which phase, what the spec
  says, what's done, validation state, what's next. Narrative, not a file dump.

### Skills (6)

- **`validation`** — default definition of validated (build, tests, lint, change
  exercised end-to-end), scaled by the mission's stakes field. Subject to the
  override convention (project `validation` skill or `.claude/validation.md`).
- **`self-review`** — whole-change review before the PR opens, depth scaled by
  stakes: low → quick inline pass; standard → one fresh-context subagent reviews the
  full diff against the spec; high → add a second reviewer with a specialist lens
  (security / data safety). Carries v3's two good ideas: the independent-reviewer
  filter (only raise what an independent reviewer would flag) and the blocking-vs-nit
  split (blocking fixed before PR; nits noted in the PR description).
- **`mission-status`** — how to reconstruct and narrate mission state (backs `/status`
  and re-entry after compaction).
- **`verification-before-completion`**, **`test-driven-development`**,
  **`systematic-debugging`** — the Iron-Law flight rules. See Flight rules below.

### Flight rules: focused, and doubling as routers

The three Iron Laws stay in the full house style (Iron Law, Go/No-Go gate,
failure-modes table, red flags, pressure-tested). Focus test for each: one law, one
gate, no workflow content — if a rule can't be stated in a sentence, it's a skill
trying to be a pipeline.

They also carry the routing duty that lets core stay lean: **the law names the
obligation; the surface picks the tool.** `verification-before-completion` requires
evidence *matched to the surface touched* — a web change means loading the page, an
infra change means a plan/status read, a CLI change means running the command. That
requirement is what pulls specialized skills (browser verification, plan-before-apply,
future domain skills) into play when they're installed, without hardcoding any of them
in core. Cutting `browser-verified-web-work` from core is safe *because* the Iron Law
still forces the question "what evidence fits this surface?" — a specialist skill just
answers it better when present.

### Hooks (4) — the dirty/clean stamp mechanism

State: `.claude/mission/validation-stamp` — `dirty` or `clean` + timestamp.

1. **`SessionStart`** — inject mission state (spec, phase, branch drift) on startup,
   `/clear`, compaction. Exists today; keep.
2. **`PostToolUse`** (Edit|Write|NotebookEdit, during a mission) — mark stamp dirty.
   One line of shell.
3. **`PreToolUse`** (Bash matching `git push` / `gh pr create` / `gh pr merge`) —
   block if stamp is dirty: "validation hasn't run since the last edit."
   Escape hatch: `LAUNCHPAD_SKIP_GATE=1`.
4. **`Stop`** — ralph backstop: during `/launch` with the autonomous flag set in
   mission state, if the spec checklist has unchecked items or the stamp is dirty,
   block the stop with "continue: X, Y remain." Off by default; opt-in per mission.

The validation skill marks the stamp clean only after checks pass. Gates are then pure
file checks — no judgment in hooks.

### Agents

None in v1. `/launch` orchestrates general-purpose subagents with briefs from the
orchestration reference. Custom agent definitions only when repeated shapes emerge.

### Stakes: assess once, store as state, consume cheaply

v3 made risk a skill driving a pipeline; v4 makes it a one-line mission property —
the same trick as the dirty/clean stamp. `/stage` sets `stakes` from a ~20-line
rubric (`references/stakes.md`: low = content/docs/cosmetic; standard = typical
feature work; high = auth, payments, schema/data migrations, prod infra, destructive
ops, large diffs). Downstream consumers just read the field: validation scales its
checks, self-review scales its depth, `/land` gates the merge behind human
confirmation on high. Non-mission work keeps the global CLAUDE.md catch-all
("high-stakes surfaces: slow down, gate, back up first"). Possible hardening later:
the PreToolUse merge gate also reads the field — still a pure file check — but that
waits for real usage.

### References

- **`references/mission-state.md`** — `.claude/mission/` schema (spec.md, log.md,
  validation-stamp, stakes, flags) so all commands + hooks agree.
- **`references/stakes.md`** — the risk rubric table (v3's, minus plan formats and
  review-panel columns) + what each tier changes.
- **`references/orchestration.md`** — work-packet brief template, model-tiering table,
  return-format schemas (see Efficiency machinery).

### Cut from v3

`/mission`, `/flight-plan`, `/hop`, `/commit` (moved out), EARS + R/S/V,
`stakes-rubric` (shrunk to the stakes field + `references/stakes.md`), `peer-review`
(shrunk to the `self-review` skill — filter and blocking/nit split kept, panel
machinery dropped), `data-safety` (its surfaces are the high tier of the stakes
rubric), `subagent-driven-development` (superseded by the orchestration reference),
`receiving-code-review` (folded into orbit), `browser-verified-web-work` (re-enters
as an optional specialist skill routed by the Iron Laws), all domain packs,
`librarian`/`historian` agents.

---

## 2. TPM

The product lifecycle, grounded in real maintainer scenarios: a TPM who is also a
core maintainer of an OSS project — GitHub repo, active Discord community, dev team
in Slack. Two directions of flow: **inbound** (signals → themes → roadmap/specs) and
**outbound** (alignment feedback → audience-tailored comms). Every command stands
alone; launchpad's `/mission-plan` is just one caller of `spec-authoring`.

### The scenarios it must serve

1. Aggregate the conversation/feedback happening in Discord; identify what needs
   digging into, then dig into it.
2. Incorporate findings into existing specs, the roadmap, and new specs.
3. Review community-raised issues, bugs, and PRs on GitHub; keep them aligned with
   roadmap and specs; provide the feedback that keeps them aligned.
4. Author specs that move the roadmap forward; author new roadmaps for the future.
5. Communicate feedback, decisions, and roadmap to the community *and* to executive
   sponsors — same facts, different altitude.

### Commands (5)

- **`/feedback`** — aggregate raw signal (Discord, Slack, GitHub discussions, ticket
  exports, CSVs — source-agnostic, uses connected MCP tools when present) into themes
  with evidence counts, flagging themes that need investigation. Output:
  `feedback-themes.md`. **Dig mode** (`/feedback dig <theme>`): pull the thread on a
  flagged theme — search history, related issues, the code — and produce a findings
  note that feeds `/roadmap` or `/spec`.
- **`/triage`** — review community-raised issues/bugs/PRs against the project's
  roadmap and specs (its source of truth); classify each as aligned / misaligned /
  needs-decision; draft the alignment feedback for posting.
- **`/roadmap`** — two modes:
  - *Proactive*: brainstorm from themes + strategy; generate stakeholder question
    lists; structure prioritization (effort/impact or RICE).
  - *Reactive* (new spec, dig finding, or request arrives): slot it into the existing
    roadmap; surface displacement tradeoffs explicitly ("this pushes X to Q3").
- **`/spec`** — idea → spec via `spec-authoring`. The handoff point to launchpad.
- **`/comms`** — render one set of facts (themes, decisions, roadmap changes) for a
  named audience: community post (Discord / GitHub discussion) vs. executive sponsor
  update. Never invents facts; only re-altitudes them.

### Skills (5)

- **`spec-authoring`** — questions to ask, what a done spec contains, when "TBD" is
  allowed. Override convention: project spec template supersedes the default.
  *Skeleton this round; real content next iteration.*
- **`feedback-synthesis`** — clustering raw signal into themes, evidence discipline
  (every theme cites its sources and counts), separating frequency from severity,
  and the judgment call of when a theme warrants a dig.
- **`triage-alignment`** — judging an issue/PR against roadmap + specs; writing
  feedback that redirects without demoralizing contributors (OSS tone is part of the
  skill, not decoration).
- **`roadmap-planning`** — proactive + reactive modes as above; tradeoffs kept
  explicit rather than absorbed.
- **`stakeholder-comms`** — the audience model: what the community needs (openness,
  reasoning behind decisions, what's next) vs. what sponsors need (progress against
  commitments, risks, asks); decisions always communicated with their why.

### Source-of-truth convention

`/triage`, `/roadmap`, and `/comms` need to find the project's canonical roadmap and
specs. Override convention again: default locations (`docs/roadmap.md`, `specs/`),
superseded by whatever the project declares.

### References/templates

`templates/spec.md`, `templates/roadmap.md`, `templates/feedback-themes.md`,
`templates/community-update.md`, `templates/exec-update.md` — skeletons now,
standardized in the next iteration.

### Agents / hooks

None. Sources connect via MCP (Discord, Slack) or the `gh` CLI; the skills stay
source-agnostic and use whatever is connected.

---

## 3. Document

### Commands (1)

- **`/docs`** — audit and update docs for the current change, or the whole repo
  standalone.

### Skills (1)

- **`writing-docs`** — Diataxis doc types + default style. Override convention:
  project `docs/STYLE.md` or project `writing-docs` skill supersedes.
  This is the skill `/launch` invokes.

### References/templates

`templates/` — ADR, how-to, reference, tutorial (carried from the current docs plugin).

### Agents / hooks

None. (v3's `librarian`/`historian` dropped — the command spawns general-purpose
readers when it needs a doc survey.)

---

## 4. Commit

### Commands (1)

- **`/commit`** — stage intelligently (related together, unrelated split), write the
  message, commit. Never pushes unless asked.

### Skills (1)

- **`commit-conventions`** — message format + atomicity. Override order: documented
  project convention (CONTRIBUTING.md, commitlint) → inferred from recent `git log` →
  plugin default.

### Agents / hooks / references

None. If it needs more, it's overcomplicated again.

---

## Efficiency machinery (how models succeed)

The mechanisms that put an Opus orchestrator and Sonnet/Haiku subagents in the best
position to succeed. Encoded in `/mission-plan` (packet creation), `/launch`
(dispatch), and `launchpad/references/orchestration.md` (templates).

1. **Work packets, not vibes.** Every subagent dispatch is a self-contained brief:
   goal, files in scope, interface contracts, the check that proves done, required
   return format. A subagent with a complete packet can't wander.

2. **Model tiering by packet type.**

   | Tier | Work |
   |---|---|
   | Opus (orchestrator) | spec decomposition, architecture, cross-packet integration, final review |
   | Sonnet | scoped implementation packets |
   | Haiku | mechanical packets: renames, fixtures, log parsing, boilerplate |

3. **Verification asymmetry.** Work from a cheaper model is checked by a stronger one.
   Nothing self-certifies. Pairs with the dirty/clean stamp. Self-review is this same
   principle applied to the whole change: the implementer's context is polluted with
   its own intentions, so a fresh-context subagent that never saw the implementation
   conversation approximates an independent reviewer.

4. **Context hygiene.** Subagents receive the relevant spec slice + contracts, never
   conversation history. They return structured results. `.claude/mission/log.md` is
   the shared memory so the orchestrator's context stays lean across a long mission.

5. **Targets before creativity.** Interfaces and failing checks written before
   implementation packets dispatch (the TDD flight rule doing double duty) —
   subagents converge faster with something to make pass.

6. **Two ralph flavors.** Outer loop (preferred): fresh subagent per packet, clean
   context each time, orchestrator persists. Inner loop (backstop): the Stop-hook
   keepalive against premature "done." Quality comes from the outer loop.

7. **Cheap enforcement.** The dirty/clean stamp turns "did we validate?" into a file
   check. Hooks never spend tokens; skills never repeat what hooks already guarantee.

---

## Open questions

- `/stage` naming: confirmed as worktree-setup, with `/status` as the human catch-up?
  (v4 assumes yes.)
- Spec template contents — deferred to the next iteration (TPM skill definition round).
- Does `/orbit` also own deploy/observe (v3's `/land` scope), or is that out of scope
  for the lean core?
- Which optional specialist skills to keep in-repo (browser verification,
  plan-before-apply) vs. delete and rebuild on demand.
- Source connectivity for TPM inbound work: which Discord/Slack MCP servers to rely
  on vs. export-file workflows as the fallback.

## Build order

Strip first, then build the two tracks that get used immediately, then let the rest
earn its way in:

1. **Dev spine (Launchpad + Commit + Document):** `/stage`, `/launch`, `/orbit`
   (validate → self-review → PR), `/land`, the stamp hooks, stakes field, the three
   Iron Laws, `/commit`, `/docs`.
2. **TPM track:** `/spec` + the spec template first (it's also the dev spine's
   planning input), then `/feedback` and `/triage` (the daily inbound work), then
   `/roadmap` and `/comms`.
3. **Run real work through both** — a real mission and a real Discord/GitHub triage
   week. Friction found here beats design debate.
4. **Earned tail:** `/status` + `mission-status`, the Stop-hook ralph loop, optional
   specialist skills — added when their absence actually hurts, not before.

## Totals

**13 commands, 13 skills, 4 hooks, 0 agents** across four plugins + the global
baseline — versus v3's 10 commands + ~14 skills + 4 domain packs + 2 agents, with
the growth all in TPM (scenario-driven), and launchpad itself down to 6 commands.
