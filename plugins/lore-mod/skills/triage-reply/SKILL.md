---
name: triage-reply
description: How to draft, review, and post a maintainer reply on a public issue: layouts by disposition, the maintainer's voice, the HITL marker review loop, adversarial review, and posting mechanics. Load when drafting or posting any comment.
---

# Triage reply

Drafts live at `repro/<n>/reply-draft.md`. Always give the maintainer the absolute path with `:1` so it is clickable. Fill the matching template from `templates/`; never post an unfilled template.

## Voice

Written as the maintainer, for humans. Short sentences, active voice, plain words. US spelling. No em dashes; space-hyphen-space if a dash is needed. No exclamation marks unless the maintainer adds them. Explicitly supportive of community contributions: name the person, say why it matters, invite the next step. The close is never the last word; the invitation is. Never name a file from a reporter's kit without saying what it is and does. Write "PR #n" and "commit <sha>", never bare numbers.

## Layouts

- **Resolved** (`templates/reply-resolved.md`, `reply-resolved-untagged.md`): one line "confirmed <symptom> is gone on <version>"; `## Fix` with commit, PR when there is one, one or two sentences on what changed, and for untagged "Not in a tagged release yet; it will ship with the next release after vX"; `## Verified on <version>` with Platform and Repository bullets only, the reporter's commands and output in blocks (for long runs, `### What was run` and `### Result`); one sentence on what the output shows; "Closing as fixed." and nothing after it. Never "upgrade to vX and this goes away"; the release is already named.
- **Question** (`reply-question.md`): answer each part in the reporter's order; link the doc passage rather than quoting at length; what exists, what is planned per the docs, what does not exist; invite the next step; community pointer; close or keep-open line.
- **Roll-up close** (`reply-rollup-close.md`): thanks to anyone with work in flight, policy sentence with the exception, why these children do not qualify, facts per child, close line.
- **Exists, undocumented** (`reply-exists-undocumented.md`): "we have it, and you could not find it because...", the doc links, a demonstration on the current release, what does not exist, the retitle and relabel announced.
- **Roadmap keep** (`reply-roadmap-keep.md`): answer each component of the request, name the theme and quote its status word as the roadmap uses it (In progress, Committed, Exploring), what exists today, the retitle announced, an ask for real-world numbers.
- **Junk or misfiled**: one line on why, and the corrective action: where it should have gone (the canonical issue, the template, the community channel).

## Review loop

1. Draft.
2. Dispatch `oss-triage:adversarial-reviewer` with the draft, the thread, the evidence, and the proposed mechanics. Apply its fixes. Verdicts of REWRITE mean the claim changed; say so to the maintainer.
3. Hand the path to the maintainer. They review in the file with `<!-- HITL-<NAME>-CHANGE: note -->text<!-- /HITL-<NAME>-CHANGE -->` and `<!-- HITL-<NAME>-DELETE -->text<!-- /HITL-<NAME>-DELETE -->`. Answer each note in chat, apply, strip markers, show the changed lines. When asked for more warmth or vision in a paragraph, add one or two sentences inside their structure; do not rewrite the paragraph. Do not rewrite a file wholesale while they have it open.
4. Post only on an explicit go for that draft.

## Posting

```
gh issue comment <n> -R <repo> --body-file "repro/<n>/reply-draft.md"
gh issue edit <n> -R <repo> --remove-label needs-triage [--add-label ...] [--title "..."]
gh issue close <n> -R <repo> --reason completed|"not planned"        # only if told to close
```

Comment first, then labels and title, then close. Confirm live state afterwards and report the comment URL. Closing as duplicate is done in the UI (it asks for the canonical issue).
