# Release Candidate One-Pager

**Status:** AI-first leader locked for the next external validation pass
**Date:** 2026-05-17
**Supporting docs:**
- `docs/shortform/sprint1-hook-test-results.md`
- `docs/reviews/ai-billboard-quality-gate.md`
- `docs/release/similarity-risk-review.md`
- `docs/strategy/billboard_ai_hit_strategy_v1.md`

## Current state

The project has completed:
- renderer upgrade + sprint-1 re-render
- Tier A/B/C internal ranking
- promotion of top three candidates
- short-form test-cut generation
- automated Billboard-like AI quality evaluation
- Billboard reference-profile calibration from past year-end songs
- rerender optimization pass against the calibrated AI gate
- provisional internal similarity / rights-risk review

The project has **not** completed:
- public hook-test measurement
- final winner selection confirmed by audience response
- winner-specific final release signoff

## AI-first leaderboard

1. `Name on Neon` — 94.32 (`release_watchlist`)
2. `Back in Color` — 90.17 (`release_watchlist`)
3. `Leave the Light` — 77.28 (`competitive_demo`)

## Why `Name on Neon` currently leads

- highest automated overall score in the batch
- strongest release-watchlist score after Billboard-reference-calibrated rerender
- no weak component left below the concern threshold
- best path to public test lead without pretending public evidence already exists

## Why `Back in Color` remains important

- also cleared `release_watchlist`
- close enough to remain a serious backup if public metrics reject the leader
- keeps the lane flexible without reverting to human-first guessing

## Why no song is fully greenlit yet

The current AI gate says the best cuts are now **release-watchlist grade**, which is a major upgrade, but the strategy still requires:
- public-response evidence that the same lead candidate actually wins with listeners
- final winner-specific rights/similarity signoff

## Current machine diagnosis

Across the batch, the rerender fixed the earlier bottlenecks in:
- mix/headroom profile
- energy motion inside the hook window

The one remaining notable weakness is mainly on `Leave the Light`:
- section-lift / payoff shape is still less controlled than the top two

## Provisional recommendation

Use `Name on Neon` as the AI-first lead release candidate.

Operationally:
1. lead public testing with `Name on Neon`
2. keep `Back in Color` as the active backup
3. keep `Leave the Light` as a competitive-demo alternate, not the lead
4. only convert this memo into a final release approval after the public evidence agrees

## Immediate next step

Run the next pass under an AI-first workflow:
1. push the rerendered artifacts and updated docs
2. use `Name on Neon` as the primary public-test cut
3. track public metrics in the repo templates
4. if `Name on Neon` still leads, finalize the release package around it
5. if not, promote `Back in Color` without redoing the whole selection logic
