# Sprint 1 Hook Test Results

**Status:** AI quality gate rerendered and now passing at release-watchlist level for the top two cuts; public metrics still pending
**Date:** 2026-05-17
**Source plan:** `docs/shortform/sprint1-hook-test-plan.md`
**Structured metric file:** `docs/shortform/sprint1-hook-test-metrics.csv`
**AI quality gate:** `docs/reviews/ai-billboard-quality-gate.md`

## AI-first quality table

| Candidate | Clip slug | AI quality score | AI label | Public metrics status | Notes |
|---|---|---:|---|---|---|
| Name on Neon | `promo-name-on-neon-direct-chorus` | 94.32 | `release_watchlist` | pending | Clear machine leader after rerender; best current release candidate. |
| Back in Color | `promo-back-in-color-payoff-open` | 90.17 | `release_watchlist` | pending | Strong runner-up and viable backup release-watchlist candidate. |
| Leave the Light | `promo-leave-the-light-silence-drop` | 77.28 | `competitive_demo` | pending | Significant improvement, but dynamic-lift shape still trails the top two. |

## Current interpretation

- Human taste is not the primary gate for this stage.
- The primary first-pass gate is now the automated Billboard-reference quality judge.
- That judge currently ranks the batch:
  1. `promo-name-on-neon-direct-chorus`
  2. `promo-back-in-color-payoff-open`
  3. `promo-leave-the-light-silence-drop`
- The rerender materially improved the whole batch and moved the top two into `release_watchlist` territory.

## What is already clear without public data

- The **hook packaging** is strong across all three promoted cuts.
- The rerender solved the biggest prior weakness in **mix/headroom** and **energy motion**.
- `Name on Neon` is now the default AI-first lead.
- `Back in Color` is close enough to keep active as a serious backup.

## Remaining blocker to finalization

Actual external outcome metrics are still pending:
- completion
- rewatch
- save intent
- quote-back recall
- creator reuse / visual fit

## Next action

Use the AI score as the default ranking signal for the next pass. Lead with `Name on Neon`, keep `Back in Color` hot as the backup, and use public metrics as secondary validation before any final release lock.
