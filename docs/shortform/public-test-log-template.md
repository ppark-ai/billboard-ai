# Public Test Log Template

**Status:** ready
**Date:** 2026-05-17
**CSV companion:** `docs/shortform/public-test-log-template.csv`
**Metrics sink:** `docs/shortform/sprint1-hook-test-metrics.csv`

## How to use

1. Create one row per uploaded post in `public-test-log-template.csv`.
2. Keep one candidate per row.
3. After 24-72 hours, copy the winning summary signals into `sprint1-hook-test-metrics.csv`.
4. Then update:
   - `docs/shortform/sprint1-hook-test-results.md`
   - `docs/release/release-candidate-one-pager.md`
   - `docs/release/park-revise-rerun-decision.md` if a clear winner exists

## Fast interpretation rules

- `first_24h_completion_signal`: use a number, percentile, or plain-language note
- `first_24h_rewatch_signal`: note replay behavior, loop comments, or retention clues
- `first_24h_save_intent`: save/share/profile-click/revisit intent
- `quote_back_recall_examples`: paste exact comments quoting the lyric if any
- `creator_reuse_signal`: duet/remix/reuse or creator-interest evidence
- `advance_rerun_kill_decision`: choose `advance`, `rerun`, or `kill`
- `winner_status`: choose `winner`, `runner_up`, `no_clear_winner`, or `provisional`

## Recommended first-pass schedule

| Day | Candidate | Preferred window | Default caption |
|---|---|---|---|
| Day 1 | `promo-name-on-neon-direct-chorus` | Window B | `got my name on neon / burning where the doubt was` |
| Day 2 | `promo-leave-the-light-silence-drop` | Window C | `say don't come over / i'm already outside` |
| Day 3 | `promo-back-in-color-payoff-open` | Window B | `now i'm back in color` |

## Winner handoff rule

Only promote a candidate to final release consideration if the same row set shows:
- strongest quote-back recall
- strong replay/rewatch signal
- clear visual fit
- no obvious kill-signal comments

If the rows split across those dimensions, keep `winner_status=no_clear_winner` and stay in REVISE mode.
