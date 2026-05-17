# Release Gate Checklist

**Status:** AI gate passed; blocked only on public hook-test metrics and final winner-specific signoff
**Date:** 2026-05-17
**Candidate pool:** `docs/creative/top-candidate-briefs.md`
**Internal risk review:** `docs/release/similarity-risk-review.md`
**AI quality gate:** `docs/reviews/ai-billboard-quality-gate.md`

## Gate items

| Check | Status | Notes |
|---|---|---|
| Tier A internal hook exists | PASS | `Name on Neon`, `Leave the Light`, and `Back in Color` were promoted. |
| Focused short-form test cuts exist | PASS | See `audio/shortform_hook_tests/` and `docs/shortform/sprint1-hook-test-metrics.csv`. |
| AI Billboard-like quality gate run | PASS | Automated scores written to `audio/shortform_hook_tests/quality_report.json` and summarized in `docs/reviews/ai-billboard-quality-gate.md`. |
| AI gate calibrated against past Billboard reference tracks | PASS | Reference profile built at `data/reference/billboard_preview_reference_profile.json` from public previews of past Billboard year-end songs. |
| At least one candidate clears automated competitive-demo band | PASS | All three now clear `competitive_demo`; top two clear `release_watchlist`. |
| Public hook-test winner identified | BLOCKED | External metrics not collected yet. |
| Clear audience lane + visual framing | PASS | Defined in `docs/creative/top-candidate-briefs.md`. |
| Similarity / rights-risk review complete | PARTIAL | Internal provisional review completed in `docs/release/similarity-risk-review.md`; final signoff must target the eventual winner. |
| Final release candidate one-pager complete | PASS | One-pager updated with AI lead and backup rationale. |

## Current gate reading

- The project is **ready for AI-led release-candidate narrowing**.
- The project is **ready for focused public short-form testing led by the machine winner**.
- The project is **not fully release-approved until public evidence and final winner-specific signoff land**.

## Blockers

1. No real completion / rewatch / save-intent metrics yet.
2. Final similarity / rights-risk signoff should target the eventual winner, not the whole pool generically.
3. `Leave the Light` still needs a cleaner lift shape if it is meant to compete with the top two.

## Required evidence to unlock the final gate

The next pass should add:
- public evidence that `Name on Neon` or `Back in Color` really wins with listeners
- quote-back recall
- creator reuse / visual-fit notes
- explicit winner/runner-up status
- winner-specific final risk signoff

## Next action

Advance `Name on Neon` as the AI-first lead. Use `Back in Color` as the immediate backup. Collect public metrics next, then finalize the release candidate only if the same ordering survives external response.
