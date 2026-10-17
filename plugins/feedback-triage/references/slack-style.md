# Slack Style — ASD-STE100 Simplified Technical English, ELI18

Reports are read on a phone between meetings. Write for a smart 18-year-old who
does not know our codebase: plain words, short sentences, the user impact first.
The rules below adapt ASD-STE100 for Slack. `ft.py lint` enforces the countable
ones; the rest are on you.

## The rules

1. **One idea per sentence.** Max 20 words per sentence; headlines max 12.
2. **Active voice, subject first.** "The refresh call fails", not "A failure is
   observed in the refresh call".
3. **Simple tenses.** Present for how things are; past for what happened.
4. **Plain verbs, one word per meaning.** Use *use*, *fail*, *show*, *add*, *fix*,
   *stop*. Pick one word for a thing and keep it ("error" — not error, then
   failure, then crash).
5. **Instructions are commands.** "Merge the PR." "Pick option B." Not "It might be
   worth considering merging."
6. **No hedges, no filler.** State confidence once, as a fact: "Not confirmed."
   "We reproduced it." Lint bans: *just, simply, basically, very, really, actually,
   obviously, clearly, leverage, utilize, facilitate, robust, seamless, in order
   to, please note, going forward, etc.*
7. **Numbers as digits**, with units: "3 users", "2.4.1", "after 60 minutes".
8. **ELI18 jargon test.** Internal names go in `backticks` and appear only when an
   engineer needs them to act. Explain any other term in ≤ 4 words, or drop it.
9. **No formatting in prose.** No emoji, bold, headers, or links inside fields —
   the template adds all styling, so every report looks the same. Links come from
   the ticket's sources and PR.

## Field contracts

| Field | Max | Content |
|---|---|---|
| `headline` | 12 words, no end punctuation | the user-visible problem or want, not the fix |
| `what` | 2 sentences | who hits it, when, what they see (feature: what they want to do and why) |
| `findings` | 1–3 items × 20 words | one verified fact each: repro result, root cause, scope, prior art |
| `recommendation` | 2 sentences | a command for the eng team (required for medium/low) |
| `ask` | 1 sentence | optional; the one decision you need from a human |

Tier shapes the recommendation: **high** → what an engineer should look at first;
**medium** → the recommended option and why, by name ("Option A: retry on the
client."); **low** → "Review and merge the PR." plus the one thing to check.

## Examples

Bad:
> *what:* We've basically been seeing a number of reports where users are
> experiencing issues that might possibly be related to the SSO integration.

Good:
> *what:* Users who stay idle for 60 minutes cannot log in again. They see a 500
> error.

Bad finding: "The code is very fragile and should be refactored going forward."
Good finding: "`refreshToken()` throws when the refresh token has expired."

Bad recommendation: "Consider looking into potential improvements to retries."
Good recommendation: "Pick option A: retry once on the client. It needs no server
change."
