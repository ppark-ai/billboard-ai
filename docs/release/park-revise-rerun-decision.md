# Park / Revise / Rerun Decision

**Status:** provisional advance
**Date:** 2026-05-17

## Current decision

**ADVANCE TOP TWO / HOLD FINAL GREENLIGHT FOR METRICS**

This cycle should not force a final formal release yet, but it should advance the rerendered winners instead of staying in revise-only mode.

## Why

- Internal ranking produced a strong top three.
- Promoted short-form cuts exist and have been logged with fixed technical inventory.
- A provisional internal similarity / rights-risk review is complete, but the final signoff must target a single winning candidate.
- The AI gate is now calibrated against a reference profile built from past Billboard year-end songs.
- After rerender optimization, `Name on Neon` and `Back in Color` both reached `release_watchlist`, while `Leave the Light` improved to `competitive_demo`.

## Most likely next branch

1. Advance `Name on Neon` first.
2. Keep `Back in Color` active as the backup.
3. Keep `Leave the Light` available but not in the lead slot.
4. Re-open the final gate after real response data exists.

## Recommended 7-10 day micro-cycle

1. Put `Name on Neon` and `Back in Color` into a focused public or private audience test.
2. Log results in `docs/shortform/sprint1-hook-test-metrics.csv`.
3. Keep `Leave the Light` as the reserve alternate unless its lift curve gets another pass.
4. Name a single final winner only if completion, recall, and replay/save intent point in the same direction.
5. Run one winner-specific final risk pass.
6. Either GREENLIGHT that winner or keep the lane and revise the framing/production.

## Trigger to change this decision

Move from HOLD to GREENLIGHT only when one candidate shows:
- strongest Billboard-reference AI score plus surviving public evidence
- strongest first-scroll hook retention
- clear quote-back recall
- convincing replay/save intent
- clean visual framing
- acceptable rights/similarity risk

## If no candidate wins clearly

Default outcome should be **BACKUP SWAP OR REVISE**, not force-release:
- keep the strongest lane
- switch to `Back in Color` if the audience rejects `Name on Neon`
- rerun a shorter comparison cycle only if both top cuts fail outside the lab
