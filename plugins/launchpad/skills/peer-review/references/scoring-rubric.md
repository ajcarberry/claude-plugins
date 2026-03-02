# Confidence Scoring Rubric

Give this rubric to each scoring agent verbatim.

Score each concern 0-100 using this scale:

| Score | Meaning |
|-------|---------|
| 0 | False positive — doesn't stand up to light scrutiny, or is a pre-existing issue |
| 25 | Might be real, plausible, but unverified; even after reviewing against source |
| 50 | Real but minor — nitpick, won't impact outcome. Relative to the rest of the change, not important |
| 60 | Verified against source but low practical impact — confirmed by reading surrounding code, yet unlikely to cause issues |
| 75 | Verified concern — reviewer double checked against source and verified it will likely impact correctness |
| 100 | Certain — reviewer double checked against source and confirmed a gap, conflict, or error that will cause issues in practice |

## Threshold

Scores are continuous (0-100). The table above defines anchor points, not discrete levels. A concern at 75 means "verified against source, but borderline confidence." A concern at 85 means "verified with strong confidence."

**Filter at 80.** This sits above the 75 verification floor intentionally — a score of 75 indicates the reviewer checked the source but isn't confident the concern will matter in practice. Concerns must clear 80 to demonstrate both verification and practical impact. Concerns below the threshold fall into three categories that are correctly filtered: verified false positives (0), concerns that remain unverifiable even after checking source (25), and concerns verified as real but low-impact (50-60).

## Classification

Concerns that survive filtering are classified as:

- **Blocking** — must be resolved before proceeding (gaps, incorrect ordering, constraint violations, security issues)
- **Non-blocking (nit)** — optional improvement, style preference, minor suggestion. Prefix with "Nit:"
