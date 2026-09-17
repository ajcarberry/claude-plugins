# Anti-patterns seen in practice

From the first Lore OSS triage pass, September 2026. Each cost time or credibility.

- **Batch agents of 20 issues.** Reports blur; roll-up children get miscounted ("three of four landed" was two). One issue per agent.
- **Posting "fixed" before validating.** A comment went up on the strength of a commit trailer; the close was held while a repro ran. Validate first.
- **Trusting an agent's summary of a roll-up.** Check every referenced child live before writing.
- **Compiling per issue.** Build `main` once at the start of the pass.
- **Starting a server with `cd dir && server &`.** The wrapper dies, the server lives, the next run talks to a ghost. `exec` it and check port ownership.
- **Runs sharing the real `HOME`.** A newer client rewrote user-level state an older client then could not read.
- **Expanding a paragraph into vision prose when asked for warmth.** Add a sentence inside the maintainer's structure.
- **Naming a kit file as if the reader had the zip.** Say what it is and does.
- **Stale status.** Reporting an issue open after the maintainer closed it. Query live first.
- **Collapsing a mixed proposal to its worst half.** #110 asked for peer caches and edge caches; only one was a non-goal.
- **Crediting the vehicle PR and missing the origin PR.** The `Imported-PR` trailer is not the whole story.
- **"Upgrade to vX and this goes away" after already naming the release.** Reads as a brush-off. End with "Closing as fixed."
- **Overclaiming from a proxy.** A 4 GB flat-directory run does not validate a 600 GB, 648,000-file report. Say what it covers.
- **Paraphrase presented as a quote.** Quote verbatim or link and paraphrase openly.
- **Using roadmap status words loosely.** "Committed" has a defined meaning on the roadmap page.
- **Adding side findings to the reply or the engineering list.** Pass log only, unless community-reported and confirmed.
