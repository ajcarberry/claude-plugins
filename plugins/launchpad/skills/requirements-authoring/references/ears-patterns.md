# EARS Patterns — Detailed Examples

Reference examples for each EARS pattern. Includes domain-specific (homelab) and general-purpose examples.

## Event-Driven Requirements

Triggered by a specific, identifiable event. Most requirements fall into this category — nearly every behavior has a trigger.

**Homelab:**
```
REQ-1: When a new worktree is created, the session-start hook SHALL detect
       the missing CLI binary and run `go build` in the background.
REQ-2: When the user invokes /land, the workflow SHALL check for uncommitted
       changes before pushing.
REQ-3: When CI completes with failure, the landing workflow SHALL present
       the user with options to proceed or abort.
```

**General:**
```
REQ-1: When a user submits a form with invalid email, the system SHALL display
       "Please enter a valid email address" below the email field.
REQ-2: When a webhook payload is received, the service SHALL validate the
       HMAC signature before processing.
REQ-3: When a file exceeds 10MB, the upload handler SHALL reject it with
       HTTP 413 and a message indicating the size limit.
```

**When to use:** Reactive behavior, user interactions, webhook/event handlers, state transitions.

## State-Driven Requirements

Apply while a condition holds true.

**Homelab:**
```
REQ-1: While the CI run is in progress, the landing workflow SHALL poll
       for completion at 15-second intervals (max 3 attempts).
REQ-2: While operating in a worktree (not the main repo), the /land
       command SHALL offer worktree cleanup after PR creation.
REQ-3: While the cluster has nodes in maintenance mode, the deploy
       command SHALL skip those nodes.
```

**General:**
```
REQ-1: While the database is in read-only mode, the API SHALL reject
       all write operations with HTTP 503 and a retry-after header.
REQ-2: While a background migration is running, the dashboard SHALL
       display a progress banner with estimated completion time.
```

**When to use:** Conditional behavior based on system state, mode-dependent logic.

## Unwanted Behavior Requirements

Handle failure modes and edge cases.

**Homelab:**
```
REQ-1: If git push fails, then the landing workflow SHALL offer retry or abort.
REQ-2: If the branch already exists, then the staging workflow SHALL ask
       the user to reuse it or pick a different name.
REQ-3: If the explore agent returns no results, then the flight plan
       workflow SHALL widen the search scope and retry with alternative terms.
```

**General:**
```
REQ-1: If the external payment API returns a 5xx error, then the checkout
       service SHALL retry up to 3 times with exponential backoff, then
       display "Payment temporarily unavailable" to the user.
REQ-2: If the database connection pool is exhausted, then the service SHALL
       queue incoming requests for up to 5 seconds before returning HTTP 503.
```

**When to use:** Error handling, fallback behavior, edge case mitigation.

## Ubiquitous Requirements

Always true, no trigger or precondition. These are the minority — typically architectural invariants and naming conventions. If you find yourself writing mostly ubiquitous requirements, reconsider whether each one really has no trigger or condition.

**Homelab:**
```
REQ-1: The CLI SHALL validate all job specifications before deployment.
REQ-2: The plugin SHALL use kebab-case for all file and directory names.
REQ-3: The deployment pipeline SHALL target ARM64 architecture exclusively.
```

**General:**
```
REQ-1: The API SHALL authenticate all requests using JWT bearer tokens.
REQ-2: The application SHALL log all database mutations to an audit trail.
REQ-3: All user-facing error messages SHALL avoid exposing internal stack traces.
```

**When to use:** System-wide invariants, naming conventions, architectural constraints, security policies.

## Full Requirement Example (with Rationale + Acceptance Criteria)

```markdown
### REQ-4: Consul Service Registration

When the Prometheus task is running, the job SHALL register a `prometheus`
service in Consul with an HTTP health check against the `/-/healthy` endpoint.

**Rationale:** All cluster services use Consul for discovery. Grafana references
Prometheus via `prometheus.service.consul:9090`. A health check ensures unhealthy
instances are removed from DNS resolution.

**Acceptance Criteria:**
- Service block in job spec has `name = "prometheus"` and `port = 9090`
- HTTP health check configured against `/-/healthy` with 30s interval
- After deployment, `consul catalog services` lists `prometheus`
- `consul health checks prometheus` reports check as `passing`

| ID | Sub-Requirement | Priority |
|----|----------------|----------|
| REQ-4.1 | The service SHALL register with `address_mode = "driver"` and port 9090. | SHALL |
| REQ-4.2 | The service SHALL include an HTTP health check at `/-/healthy`. | SHALL |
| REQ-4.3 | The service SHOULD include `caddy = "true"` metadata for reverse proxy. | SHOULD |
```

## Verification Examples

### Happy-Path Checks

```
V1 (REQ-1): When `./cluster validate` is run, the CLI SHALL exit with
            code 0 and print "All validations passed".
V2 (REQ-4): When the Prometheus task passes its health check,
            `consul health checks prometheus` SHALL report status `passing`.
V3 (REQ-2): When /flight-plan is run on a mission brief, the output
            SHALL contain a Requirements section with REQ-prefixed IDs.
```

### Negative/Failure Checks

Negative checks must verify behavior that **your implementation specifically defines**. The litmus test: "If I introduced a bug in my code, would this check catch it?" If the platform enforces the same outcome regardless, the check isn't testing your work.

**Good** — each check verifies a specific decision you made:
```
V4 (REQ-4): When the Prometheus container is killed, `consul health checks
            prometheus` SHALL report the check as `critical` within 60 seconds.
            (Verifies your configured 30s health check interval catches failures.)
V5 (REQ-3): When /land pushes and CI fails, the workflow SHALL display
            an AskUserQuestion with "Proceed anyway" and "Stop and fix".
            (Verifies your error handling UX, not that CI can fail.)
V6 (REQ-1): When a PR is opened targeting `feat/experiment` instead of `main`,
            the CI pipeline SHALL NOT trigger.
            (Verifies your trigger scoping, not GitHub Actions' event system.)
V7 (REQ-2): When a malformed YAML mission brief is provided, the parser
            SHALL exit with a clear error indicating the malformed line.
            (Verifies your parser's error messages, not that YAML parsing can fail.)
```

**Bad** — these test the platform, not your implementation:
```
AVOID: "When deployed without the CSI volume, Nomad fails placement."
       (Nomad always rejects missing volumes — nothing to do with your code.)
AVOID: "When an invalid job spec is submitted, validation exits with code 1."
       (Nomad validates all specs — this passes even with an empty file.)
AVOID: "When the constraint is removed, macOS scheduling fails."
       (The cluster's driver config enforces this, not your job spec.)
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| "The system shall be reliable" | Not observable or testable | Specify measurable behavior: "SHALL recover within 30s" |
| "When error, handle gracefully" | Vague trigger and action | Name the specific error and the specific handling |
| "REQ-1: Do X and Y and Z" | Multiple concerns in one | Split into REQ-1, REQ-2, REQ-3 — one concern per requirement |
| Missing unwanted-behavior patterns | No error handling defined | Add at least one "If [failure]" requirement per plan |
| Missing rationale | Implementer doesn't know *why* | Add **Rationale:** explaining the problem or constraint |
| Missing acceptance criteria | No way to verify completion | Add **Acceptance Criteria:** with observable conditions |
| Only happy-path verification | Failure modes untested | Add negative V-checks for every unwanted-behavior REQ |
| Verification without trigger | "The output shall be correct" | Add "When [command/action]" prefix |
| No priority differentiation | Everything looks equally critical | Use SHALL/SHOULD/MAY to distinguish must-have from nice-to-have |
| Requirements describe structure only | "Job spec includes constraint block" | Describe functional behavior: "SHALL constrain scheduling to Linux nodes" |

## Small Task Example

For tasks with 1-3 requirements, use the lightweight checklist format instead of full REQ/S/V structure:

```markdown
## Task: Rename `session-start.sh` to `init.sh` across all references

### Changes
| File | Change |
|------|--------|
| `scripts/init.sh` | Rename from `scripts/session-start.sh` |
| `plugin.json` | Update `sessionStart` hook path from `scripts/session-start.sh` to `scripts/init.sh` |
| `README.md` | Update reference in setup instructions |

### Verification
1. `cat plugin.json | grep init.sh` — expected: hook path points to `scripts/init.sh`
2. `test -f scripts/init.sh && echo "exists"` — expected: "exists"
3. `test ! -f scripts/session-start.sh && echo "removed"` — expected: "removed"
4. `grep -r session-start.sh .` — expected: no matches (all references updated)
```

This format is appropriate when the task is a straightforward change with no architectural decisions, error handling concerns, or phased delivery. If the task grows beyond 3 changes or requires tradeoff analysis, upgrade to the full requirements structure.
