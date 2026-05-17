# Public Hook-Test Execution Checklist

**Status:** ready
**Date:** 2026-05-17
**Inputs:**
- `docs/shortform/sprint1-hook-test-plan.md`
- `docs/shortform/sprint1-hook-test-results.md`
- `docs/shortform/sprint1-hook-test-metrics.csv`
- `docs/release/release-candidate-one-pager.md`

## Test order

1. `promo-name-on-neon-direct-chorus`
2. `promo-leave-the-light-silence-drop`
3. `promo-back-in-color-payoff-open`

## Before posting

- confirm final exported clip file and slug match the metrics CSV row
- confirm title/caption angle matches the intended emotional thesis
- confirm first frame communicates the visual hook immediately
- confirm no candidate is posted with conflicting title language
- confirm all three candidates use comparable posting conditions if the goal is A/B judgment

## Minimum fields to log after each post

- platform / account used
- post timestamp
- candidate slug
- framing angle used
- completion signal
- rewatch signal
- save or revisit intent
- quote-back recall in comments/messages
- strongest visual reaction note
- whether the cut should be rerun, advanced, or killed

## Decision rules

Mark a candidate `winner` only if:
- first-scroll hook retention is strongest
- quote-back recall is visible
- save/revisit intent is convincing
- visual framing feels native rather than forced

Mark `runner_up` if it is competitive but not clearly first.

Mark `no_clear_winner` if results split across metrics without a coherent leader.

Mark `killed` if the opening fails to hold attention or no lyric/image lock appears.

## After the first 24-72 hours

1. update `docs/shortform/sprint1-hook-test-metrics.csv`
2. update `docs/shortform/sprint1-hook-test-results.md`
3. update `docs/release/release-candidate-one-pager.md`
4. rerun final winner-specific similarity/risk pass
5. change `docs/release/park-revise-rerun-decision.md` only if the winner is clear
