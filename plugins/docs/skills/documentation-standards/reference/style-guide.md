# Documentation Style Guide

Guidelines for writing consistent documentation.

## General Principles

### Active Voice

Write in active voice. The subject performs the action.

```markdown
<!-- Good -->
Run the command to start the server.
The role installs Docker on Linux nodes.

<!-- Bad -->
The command should be run to start the server.
Docker is installed on Linux nodes by the role.
```

### Concise Sentences

One idea per sentence. Avoid run-on sentences.

```markdown
<!-- Good -->
Install Docker first. Then configure the network.

<!-- Bad -->
Install Docker first and then configure the network settings to ensure proper communication between containers.
```

### No Marketing Language

Avoid superlatives and promotional language.

```markdown
<!-- Good -->
This approach reduces deployment time.

<!-- Bad -->
This amazing approach dramatically reduces deployment time!
```

### Define Technical Terms

Either define terms inline or link to definitions.

```markdown
<!-- Good -->
Use CSI (Container Storage Interface) volumes for persistent storage.

<!-- Or link -->
Use [CSI volumes](../reference/csi.md) for persistent storage.
```

## Formatting

### Headers

Use title case for headers (capitalize major words).

```markdown
<!-- Good -->
## How to Deploy a Service

<!-- Bad -->
## How to deploy a service
```

### Code Blocks

Always specify the language for syntax highlighting.

````markdown
```bash
./cluster config deploy
```

```hcl
job "my-app" {
  datacenters = ["home"]
}
```

```yaml
- name: Install package
  ansible.builtin.apt:
    name: curl
```
````

### Lists

Use bullet lists for unordered items, numbered lists for sequential steps.

```markdown
<!-- Unordered - no sequence -->
Available drivers:
- docker
- raw_exec
- exec

<!-- Ordered - sequential steps -->
1. Validate configuration
2. Preview changes
3. Deploy to canary
4. Deploy to all nodes
```

### Tables

Use tables for structured data with multiple attributes.

```markdown
| Variable | Default | Description |
|----------|---------|-------------|
| `version` | `1.0.0` | Software version |
| `enabled` | `true` | Enable feature |
```

## Code Examples

### Make Examples Runnable

Include complete commands that can be copy-pasted.

```markdown
<!-- Good -->
nomad job run nomad/jobs/my-app.nomad.hcl

<!-- Bad -->
nomad job run <job-file>
```

### Show Expected Output

When helpful, show what the user should see.

```markdown
```bash
consul members
```

Output:
```
Node       Address          Status  Type    Build
watchtower 10.1.0.200:8301  alive   server  1.20.1
```
```

### Use Placeholders Sparingly

When placeholders are necessary, use descriptive names.

```markdown
<!-- Good -->
ssh alex@<node-ip>
nomad alloc logs <allocation-id>

<!-- Bad -->
ssh <user>@<host>
nomad alloc logs <id>
```

## File Naming

- Use lowercase letters
- Use hyphens to separate words
- Be descriptive but concise
- ADRs use number prefix: `0001-decision-name.md`

```
getting-started.md      # Good
GettingStarted.md       # Bad
getting_started.md      # Bad
gs.md                   # Bad - not descriptive
```

## Single Source of Truth

Every piece of data must live in exactly one place. Other docs cross-reference it — they never duplicate it.

```markdown
<!-- Good: reference the authoritative source -->
For Homebrew packages installed on macOS, see [base_system role reference](../reference/roles/base_system.md).

<!-- Bad: repeating a list that already exists in another doc -->
The macOS node installs: curl, git, vim, htop, gnu-tar, awscli, terraform, node, forgejo-cli.
```

When deciding where data belongs:
- **Reference docs** own factual data (ports, packages, config values, architecture)
- **Guides** own procedures (step-by-step workflows)
- **ADRs** own rationale (why decisions were made)
- If you need the same data in two places, put it in one and link from the other

## Cross-References

Link to related documentation to help readers navigate. Prefer cross-references over duplicating content.

```markdown
## Related Documentation

- [Getting Started](../tutorials/getting-started.md)
- [CLI Reference](../reference/cli.md)
- [ADR-0001](../decisions/0001-nomad-over-kubernetes.md)
```

## Checklist

Before submitting documentation:

- [ ] Spell-checked
- [ ] Code examples tested
- [ ] Links verified
- [ ] Headers in title case
- [ ] Active voice used
- [ ] No marketing language
- [ ] Related docs linked
- [ ] No data duplicated — single source of truth per fact
