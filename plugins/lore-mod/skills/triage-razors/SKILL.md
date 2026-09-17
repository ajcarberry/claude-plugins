---
name: triage-razors
description: Decision razors for hard triage calls: roll-up and meta issues, mechanism versus need, origin versus vehicle PR, when a merged-PR shortcut is allowed, and docs-gap detection. Load when an issue is a tracker, a mixed proposal, or claims to be fixed by a PR.
---

# Triage razors

**Roll-up razor.** A roll-up earns its place only when one change would close every child. Ask in order: shared root or shared shape (same reason in the same code, or the same kind of mistake in different places)? Would one fix close them all? Does it carry anything the children lack (move that to the child)? Did a maintainer ask for it (then it is exempt)? Shape alone means close it: duplicate of the one open child, or not planned. Comment shape: policy sentence with the exception stated ("We prefer to track individual issues rather than theme roll-ups, unless one change would close several of them"), one sentence on why these children do not qualify, facts per child, close line. Address any contributor with work in flight first, by name. Check every referenced child live before writing; agent summaries of roll-ups have been wrong.

**Mechanism versus need.** Read a request component by component before matching it to a non-goal or a roadmap theme. A title or a reviewer's summary can collapse a mixed proposal into its most objectionable half. Answer each half. If any half is planned, keep the issue open under the theme and retitle to the half that is planned.

**Origin PR versus vehicle PR.** A mirrored commit's `Imported-PR:` trailer names the PR that carried the change, not necessarily the PR that wrote the fix. Check the thread and the author's closed PRs for one a maintainer closed as "included in" the landed one. Credit both: "PR #104, folded into PR #89, landed as commit 929fa91". Always write "PR #n" and "commit <sha>" so the reader knows which is which.

**Merged-PR shortcut, narrow.** Skip the repro only when a PR written to fix this issue carries the `merged` label and the bot's "Closed by mirrored commit <sha>" line. If the fix rode along in another PR, that is a lead; run the repro.

**Community confirmation is signal, not substitute.** A member saying "cannot reproduce on the new version" raises confidence. If the reporter gave a kit, run it on the fixed version anyway.

**Docs-gap detection.** When a feature request asks for something that exists, grep the whole `docs/` tree and the published site's search index. Present only in an explanation doc and a glossary, absent from how-to, reference, and quickstart, means a docs issue, not a feature request. Retitle and relabel; never ask the reporter to re-file.

**Fixed version, not old version.** Reproducing the failure on the reporter's old version is optional context. The verdict rests on the reporter's steps passing on the fixed version.
