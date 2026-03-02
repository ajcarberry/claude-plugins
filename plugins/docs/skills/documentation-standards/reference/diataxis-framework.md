# Diataxis Framework Reference

This project's documentation follows the [Diataxis framework](https://diataxis.fr/) with ADRs replacing the "Explanation" category. See [ADR-0005](../../../../../docs/decisions/0005-diataxis-documentation.md) for why.

## Document Types

Every document serves exactly ONE purpose. Mixing purposes creates docs that serve no one well.

| User Need | Doc Type | Location |
|-----------|----------|----------|
| Learn from scratch | Tutorial | `docs/tutorials/` |
| Accomplish a task | How-To Guide | `docs/guides/` |
| Look something up | Reference | `docs/reference/` |
| Understand why | ADR | `docs/decisions/` |

## Decision Tree

To determine the correct type:
1. Is the reader learning something new? → **Tutorial** (`docs/tutorials/`)
2. Is the reader trying to accomplish a specific task? → **How-To Guide** (`docs/guides/`)
3. Is the reader looking up specific details? → **Reference** (`docs/reference/`)
4. Does it record a significant decision and its reasoning? → **ADR** (`docs/decisions/`)

## Type Characteristics

| Aspect | Tutorial | How-To | Reference | ADR |
|--------|----------|--------|-----------|-----|
| **Reader** | Beginner, learning | Practitioner, doing | Anyone, looking up | Future reader, understanding |
| **Tone** | Encouraging, guided | Direct, practical | Factual, structured | Neutral, comprehensive |
| **Structure** | Steps with outcomes | Problem → Solution | Tables, definitions | Context → Decision → Consequences |
| **Verb mood** | Imperative + explanation | Imperative | Declarative | Past tense narrative |
| **Examples** | Every step verified | Key steps shown | Complete specifications | Alternatives compared |

## Why No "Explanation" Type

ADRs capture the "why" through their Context and Consequences sections. Every significant "why" question traces to a decision. This eliminates a category of docs that often become orphaned opinion pieces.

## Templates

Use the templates in `${CLAUDE_PLUGIN_ROOT}/skills/documentation-standards/templates/` for each type:
- `tutorial.md` — Learning-oriented with verification at each step
- `how-to.md` — Task-oriented with prerequisites and troubleshooting
- `reference.md` — Information-oriented with tables and specifications
- `adr.md` — Decision record with alternatives and consequences
