# Metrics Update Playbook

**Status:** ready
**Date:** 2026-05-17

## Purpose

This file exists so that once public-test numbers arrive, the repo can be updated quickly and consistently without re-deciding the workflow.

## Update order

1. Fill `docs/shortform/public-test-log-template.csv`
2. Collapse each candidate's best evidence into `docs/shortform/sprint1-hook-test-metrics.csv`
3. Rewrite `docs/shortform/sprint1-hook-test-results.md` from provisional to evidence-backed
4. Update `docs/release/release-candidate-one-pager.md`
5. If a clear winner exists, patch `docs/release/release-gate-checklist.md` and `docs/release/park-revise-rerun-decision.md`
6. If no clear winner exists, keep the release gate blocked and mark the cycle `REVISE`

## Minimum evidence needed per candidate

- posting context recorded
- completion signal recorded
- replay / rewatch signal recorded
- save / revisit intent recorded
- at least one qualitative note on lyric recall or visual fit
- explicit decision: `advance`, `rerun`, or `kill`

## Minimum evidence needed to declare a winner

A winner should have:
- best or tied-best quote-back recall
- strongest replay / rewatch behavior
- convincing save or revisit intent
- clear visual framing that matches the lyric/title
- no major risk note that overrides the public response

## Default fallback

If performance is mixed and ambiguous, do **not** force a winner. Keep:
- `winner_status = no_clear_winner`
- release decision = `REVISE / HOLD FOR METRICS`
- next branch = strengthen the top lane and rerun a micro-cycle
