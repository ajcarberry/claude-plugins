# Design v3: Launchpad, leveled up and right-sized

**Status:** approved direction; supersedes v2 (2026-07-02 review round).
**Goal:** one universal, space-themed plugin system — launchpad as the complete flight
sequence *and* flight rules, thin domain packs, a lean global `~/.claude/CLAUDE.md` —
stealing what's proven from [obra/superpowers](https://github.com/obra/superpowers) and
Karpathy's guidelines, sized for how Sonnet/Opus-class models actually behave and for
real workloads (web SaaS, homelab, website/blog).

**Decision log:**

1. **Architecture** — mega-launchpad (commands + discipline skills in one plugin) +
   thin domain packs. No separate `mission-control`.
2. **Eval rigor** — usage-driven iteration now; automated eval harness deferred.
3. **Quick path** — `/hop` express command; full sequence for real features.
4. **SDD front door** — `/mission`: approaches → approved spec → hard gate.
5. **Full mission arc** (resequenced — you orbit *before* you land) —
   `/launch` (implement) → `/orbit` (push, PR, CI, review iteration) → `/land`
   (merge, deploy, observe, validate) → `/debrief` (deferred).
6. **v3 review round** — token efficiency as a first-class constraint; risk-tiered
   ceremony; observable-check-first as root law; EARS and multi-agent pipelines
   demoted to opt-in; browser verification and data safety promoted to core;
   `/status` added; `/debrief` deferred.

---

## Design principles

1. **Token efficiency is a feature.** Lean defaults, heavyweight opt-in. No fixed-size
   agent pipelines — ceremony scales with stakes, not habit. Budgets: command specs
   ≤ ~200 lines; SKILL.md ≤ ~150 lines with references loaded on demand; model tiering
   per dispatch (cheap models for mechanical work, strongest only for architecture and
   final review).

2. **Risk-tiering (the stakes rubric).** A shared launchpad reference
   (`skills/stakes-rubric` or equivalent) consulted by `/flight-plan`, `/commit`,
   `/launch`, and `/land`:

   | Tier | Examples | Review | Gates | Plan format |
   |---|---|---|---|---|
   | **Low** | content, docs, cosmetic UI, comments | none or one lightweight pass | auto-proceed | small (changes + checks) |
   | **Standard** | typical feature work | single strong reviewer | confirm | plain plan |
   | **High** | auth, payments, schema/data migrations, prod infra, destructive ops, large diffs | full panel | hard gates, typed confirmations | plain plan + optional EARS |

3. **Observable-check-first is the root law** (Karpathy's goal-driven execution):
   every change defines a check that fails before and passes after — a failing test
   where a harness exists; a curl, screenshot, or `nomad job status` where it doesn't.
   TDD is the code specialization of this rule, not the universal law.

---

## System shape

| Plugin | What it is | Status |
|---|---|---|
| **launchpad** | Flight sequence (commands) + flight rules (discipline skills) + session hooks | exists; major upgrade |
| **docs** | Documentation management | exists; optimize (bounded) |
| **launchpad-web / -electron / -infra / -tpm** | Thin domain packs — skills only | new; usage-driven |
| **global CLAUDE.md** | ≤ ~50-line behavioral baseline installed to `~/.claude/CLAUDE.md`, versioned here | new |

---

## Launchpad: the flight sequence

### Commands (10 — six new)

```
IDEA ─► /mission ─► /stage ─► /flight-plan ─► /launch ─► /orbit ─► /land ─► /debrief
             │                               (implement;  (push, PR,  (merge,    (deferred)
             │                                /commit at   CI, review  deploy,
             │                                checkpoints) iteration)  validate)
             └─ small task? ─► /hop ─────────────────────────► PR
                                        /status = re-entry point, any time
```

`/commit` is a checkpoint, not a sequence stage — `/launch` invokes it at phase
boundaries, and it works ad-hoc anytime. `/hop` is the express lane.

| Command | Role | Change |
|---|---|---|
| **/mission** (new) | SDD front door. Clarifying questions (batched where natural, multiple-choice preferred), 2-3 approaches with trade-offs + recommendation, spec written to `.claude/specs/YYYY-MM-DD-<topic>.md`. **Hard gate:** no implementation until the spec is approved. Section-by-section approval only for high-stakes or large designs. Skippable for small/obvious work. | new |
| **/stage** | Fast workspace setup (worktree + mission brief; links `/mission` spec as `spec:` parent). Verifies a clean test baseline in the background — a failing baseline is surfaced before work begins. Keeps its ~15-second identity. | minor |
| **/flight-plan** | Research → **plain-language plan**: objective, verified starting points (`path:line`), phases with checkpoints, V-check list tagged **orbit** (branch-verifiable) or **landing** (live-system). Steps sized for a fresh-context implementer (exact paths, real signatures, no "similar to S3"). EARS/RFC 2119/R-S-V traceability is **opt-in** — high-stakes tier or explicit request. Small Task Format is the floor. Review scaled by stakes rubric. | upgrade |
| **/launch** (new) | Executes the flight plan. **Default: main-session execution** — work phase by phase, update `.claude/flight-log.md` after every step, review at phase checkpoints via `/commit`. **Heavyweight mode** (~10+ steps or multi-hour builds, or on request): fresh implementer subagent per step, two-stage per-step review, file-based handoffs, DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT protocol (on BLOCKED, change something before retrying), per-dispatch model tiering, final whole-branch review on the strongest model. Resumable from the flight log. Solo mode (sequential, no subagents) for constrained environments. | new |
| **/commit** | Validation gate + **single strong reviewer by default**, covering spec/plan compliance and code quality as prompt dimensions. Full panel only on high-stakes tier. Concern filter: the independent-reviewer test ("would another qualified reviewer, given this diff and these rules, flag this?") — no per-concern scoring agents. A checkpoint, not a sequence stage. | rework |
| **/hop** (new) | Express lane for small tasks (1-3 changes): inline mini-brief, no worktree by default, observable-check-first (a failing test where a harness exists), single lightweight review, commit, optional straight-to-PR. Escalates to the full sequence if scope grows past ~3 changes. | new |
| **/orbit** (new — absorbs the old `/land`) | Ascent complete, now circling. Docs drift check, push, CI watch, PR creation, run the **orbit** V-checks. Review iteration: process PR feedback via `receiving-code-review`, dispatch fixes, keep the worktree alive. Publishes **landing** V-checks in the PR body as `/land`'s work queue. Ends with **Go/No-Go for landing**: CI green, review threads resolved, approval in. | new |
| **/land** (reworked) | Reentry and touchdown — only after go-for-landing. Confirm rollback path → **backup-before-destructive** (snapshot volume / dump DB before any destructive apply) → merge → deploy → observe telemetry until stable → execute **landing** V-checks against the live system (including negative checks — kill the container, watch the alert). Unstable? **Abort-to-orbit**: roll back, reopen iteration. Then environment-aware worktree cleanup (git-dir vs common-dir), typed "discard" confirmation for destructive paths. Touchdown = verified in reality; the mission closes here. Domain packs supply deploy/observe mechanics. | reworked |
| **/status** (new) | Re-entry point for missions spanning days. Reads mission brief, flight plan, flight log, CI/PR state; reports where the mission is, what's next, what's blocked. Read-only, cheap. | new |
| **/debrief** | **Deferred.** Build only when it can meet two criteria: output is *applied diffs* (to skills, CLAUDE.md, pressure scenarios), and a run takes ~2 minutes. Until then, feed lessons back manually. | deferred |

### Discipline skills ("Flight Rules")

Skill `name`/`description` stay functionally precise — descriptions are pure trigger
conditions, never workflow summaries (superpowers' empirical finding: summarize the
workflow and the agent executes the summary instead of reading the body). Theme lives
in the body voice.

**Full Iron-Law house style** (Iron Law + Go/No-Go gate + failure-modes table built
from observed excuses + red-flags STOP list) is reserved for the **three skills where
models actually rationalize**. Everything else uses a **lean format**: trigger
description + process + when-NOT-to-use.

**Iron-Law skills (3):**

1. **verification-before-completion** — the highest-leverage gate. No "done / passing /
   fixed" claim without fresh command evidence in the same message. IDENTIFY → RUN →
   READ → VERIFY → claim. Red-green-red regression proof for bug fixes.
2. **test-driven-development** — Iron Law restated under the root law: *no change
   without a check that fails before and passes after; when a test harness exists for
   the code you're changing, that check is a failing test* (RED → GREEN → REFACTOR;
   code written before its test is deleted). When-NOT-to-use: config, content,
   no-harness work — where the observable check is a command/screenshot instead.
   Absorbs `write-tests` content as references.
3. **systematic-debugging** — Iron Law: *no fix without root cause*. References:
   root-cause-tracing, condition-based-waiting, defense-in-depth. 3-strikes rule:
   three failed fixes → question the architecture.

**Lean skills:**

4. **browser-verified-web-work** (new, core — the workloads are web-heavy) — after any
   UI/web change: load the page (DevTools MCP / claude-in-chrome), check the console,
   screenshot. A web change isn't done until observed rendering. This is
   verification-before-completion's web specialization.
5. **data-safety** (new, core) — migrations written up + down together and tested
   against a copy; backup/snapshot before destructive operations (SaaS DB, homelab
   volumes). Pairs with `/land`'s backup-before-destructive gate.
6. **subagent-driven-development** — the engine of `/launch` heavyweight mode (and
   ad-hoc big multi-step work): fresh implementer per step, two-stage review,
   file-based handoffs, flight-log ledger, status vocabulary, model tiering. Ships
   `implementer-prompt.md` / `step-reviewer-prompt.md` as references.
7. **receiving-code-review** — verify feedback against the codebase before
   implementing; reasoned pushback expected; performative agreement banned; YAGNI
   grep-before-adding.
8. **peer-review** (rewritten) — single-reviewer default; full panel only when the
   stakes rubric triggers it; independent-reviewer test as the concern filter.
   Confidence-scoring pipeline and scoring-rubric reference **removed**.
9. **stakes-rubric** (new reference) — the risk tiers table; consulted by commands,
   kept tiny.
10. **requirements-authoring** — demoted to opt-in reference for high-stakes plans;
    its Small Task Format is promoted into `/flight-plan`'s default. EARS content
    retained for when precision genuinely pays.
11. **authoring-skills** (meta) — usage-driven iteration is the default loop: write
    lean, use for real, fix observed failures. Synthetic pressure-testing reserved for
    the three Iron-Law skills (their failure-modes tables must quote real excuses).

### Hook upgrade

- Matcher `startup|clear|compact` — methodology re-injects after `/clear` and
  compaction.
- Injects a compact flight-rules bootstrap (~150 words): check whether a launchpad
  skill applies before implementation work and announce its use; process skills take
  priority over implementation momentum; user > skills > defaults.
- Loads `.claude/mission-brief.md`, `.claude/flight-plan.md`, `.claude/flight-log.md`,
  latest `.claude/specs/*` when present.

---

## Domain packs (thin, usage-driven)

Skills only — no commands, no hooks. Each pack supplies domain skills plus **landing
mechanics** — the deploy/observe/validate know-how `/land` calls into (core owns the
loop; the pack knows the stack). Build from real friction, not speculation.

| Pack | Seed skills | Landing mechanics |
|---|---|---|
| **launchpad-web** | Web perf/a11y check patterns (browser verification lives in core now) | Preview/prod deploy, browser-based V-check execution, console + web-vitals observation |
| **launchpad-electron** | Main/renderer process discipline; run-and-verify loop; packaging checks | Package + notarize, install-and-smoke-test, crash-log observation |
| **launchpad-infra** | Plan-before-apply (dry-runs as the RED analog); rollback-path-required | `nomad job run`/`terraform apply`, Consul/Prometheus health observation, live negative checks, rollback execution |
| **launchpad-tpm** | PRD/spec authoring (reuses `/mission` + EARS reference); decision-doc discipline; stakeholder summary style | "Deploy" = publish/share; validation = stakeholder review checklist |

---

## Global `~/.claude/CLAUDE.md`

Versioned here (`global/CLAUDE.md` + install script), **≤ ~50 lines**, behavioral only.
Anything that must be guaranteed becomes a hook or `permissions.deny`, not text. Keep
only rules that still change model behavior:

- **Every changed line traces directly to the request** (the diff-discipline test).
- **Orphan asymmetry** — remove what YOUR change orphaned; mention, don't touch,
  pre-existing dead code.
- **Present competing interpretations** on genuinely ambiguous requests — don't pick
  silently; push back when a simpler approach exists. (Trivial-task escape hatch.)
- **No error handling for impossible scenarios.**
- **Imperative → verifiable transforms** ("fix the bug" → "write a failing check that
  reproduces it, then make it pass"); plan steps as `step → verify:`.
- **Verification backstop** — no completion claims without fresh evidence.
- **One bootstrap line** — "Before implementing, check whether a launchpad skill
  applies, and use it."

Dropped as redundant with Claude Code's current defaults: generic simplicity
headlines, generic ask-when-unsure, blanket style rules.

---

## Docs plugin (bounded optimization)

- De-duplicate: Diataxis decision tree (librarian agent vs documentation-standards
  skill) and the review-filtering guidance → one source each, cross-referenced.
- Least privilege: librarian read-only, scoped Bash. Description quality, token trims.

## Repo fixes

- Root `CLAUDE.md` claims "skills do not auto-load" — false; skills auto-invoke on
  description. Fix the Conventions section.
- Root `CLAUDE.md` references the confidence-scoring threshold (80+) — update when
  peer-review is reworked.
- Bump `plugin.json` versions per phase; update marketplace.json when packs land.

---

## Superpowers ↔ launchpad map

Superpowers ships no commands — everything is an auto-triggering skill. Launchpad makes
each phase transition an explicit command and keeps skills for cross-cutting discipline.

| Launchpad | Superpowers counterpart | Delta |
|---|---|---|
| `/mission` | brainstorming | Ours is a command with spec artifact + hard gate, ceremony scaled to stakes; theirs auto-triggers, always one-question-at-a-time |
| `/stage` | using-git-worktrees | Ours adds the mission brief; both verify a clean test baseline |
| `/flight-plan` | writing-plans | Ours: plain plan + V-checks, risk-scaled review, EARS opt-in; theirs contributed zero-context step rigor |
| `/launch` | subagent-driven-development (+ executing-plans as solo mode) | Command is ours; their orchestration is our *heavyweight mode*, not the default |
| `/commit` | requesting-code-review (per-task) | Ours adds validation gate + risk-scaled review; drops their per-task review-everything default |
| `/orbit` | finishing-a-development-branch (push/PR path) + requesting/receiving-code-review | Ours adds CI watch, orbit V-checks, landing-check queue |
| `/land` | finishing-a-development-branch (merge/cleanup path) | **Deploy–observe–validate is ours alone** — superpowers ends at merge |
| `/status`, `/hop`, `/debrief` | — | Ours alone (superpowers applies full ceremony to everything, has no re-entry or retro) |
| skills: verification-before-completion, test-driven-development, systematic-debugging, receiving-code-review, authoring-skills | same names (authoring-skills = writing-skills) | Adopted with Flight Rules voice; TDD generalized under observable-check-first; house style reserved for the Iron-Law three |
| skills: browser-verified-web-work, data-safety, stakes-rubric | — | Ours alone |
| SessionStart bootstrap hook | using-superpowers + session-start hook | Ours also loads mission state (brief, plan, flight log, spec) |

**Gaps superpowers covers that we didn't — disposition:**

- Clean-test-baseline before work → **absorbed** into `/stage`.
- `executing-plans` sequential fallback → **absorbed** as `/launch` solo mode.
- Mid-flight ad-hoc review ("when stuck, before a refactor") → **covered** by invoking
  peer-review directly; no new command.
- Pressure-testing every skill → **scoped down** to the three Iron-Law skills;
  everything else iterates from real usage.
- `dispatching-parallel-agents` → **deferred**; revisit after Phase 3.
- Multi-harness portability (Cursor/Codex/etc.) → **out of scope**; Claude Code only.

---

## Phased build plan

Each phase lands as its own branch/PR via the existing flight sequence (dogfooding).

- **Phase 1 — Core rules, right-sized review.** The Iron-Law three
  (verification-before-completion, test-driven-development generalized,
  systematic-debugging — full house style, pressure-tested) +
  `browser-verified-web-work` + `stakes-rubric` + peer-review rewrite (single-reviewer
  default, drop scoring pipeline). Hook upgrade (clear/compact re-inject + bootstrap).
  Fix root CLAUDE.md.
- **Phase 2 — Front doors.** `/mission` (lean ceremony, hard gate), `/hop`, `/status`.
- **Phase 3 — Implement + orbit.** `/launch` (lean default + heavyweight mode) +
  flight-log + `subagent-driven-development` + `receiving-code-review` + `data-safety`;
  `/flight-plan` rework (plain default, EARS opt-in, orbit/landing tagging); `/commit`
  rework (risk-scaled review); old `/land` → `/orbit`.
- **Phase 4 — Global CLAUDE.md.** Author ≤ ~50 lines, install script, live with it,
  prune what doesn't change behavior.
- **Phase 5 — Landing.** New `/land` (go-for-landing gate → backup → merge → deploy →
  observe → validate → cleanup, abort-to-orbit rollback). First landing mechanics from
  whichever domain pack ships first.
- **Phase 6 — Domain packs + docs optimization.** Seed the four packs (incl. landing
  mechanics) from real usage; bounded docs plugin fixes.
- **Deferred:** `/debrief` (build criteria: applied diffs, ~2-minute run), eval
  harness (pressure-test corpus + `/debrief` output as seed data),
  `dispatching-parallel-agents`.
