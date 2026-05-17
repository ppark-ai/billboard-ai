# AI Billboard-Like Quality Gate

**Status:** automated pass complete with Billboard preview reference calibration
**Date:** 2026-05-17
**Manifest input:** `audio/shortform_hook_tests/manifest.json`
**Machine report outputs:**
- `audio/shortform_hook_tests/quality_report.json`
- `audio/shortform_hook_tests/quality_report.csv`

**Billboard reference artifacts:**
- `data/reference/billboard_preview_reference_tracks.csv`
- `data/reference/billboard_preview_reference_profile.json`
- `scripts/build_billboard_reference_profile.py`

## Why this gate exists

This project should not rely mainly on human taste for first-pass quality screening. Before public testing, the repo now runs an automated audio-quality judge that scores each short-form cut against a **reference profile built from past Billboard year-end songs**.

This gate is not a legal opinion and not a guarantee of commercial success. It is a deterministic preflight that answers a narrower question:

> does this cut's audio profile look competitive enough, relative to a reference band derived from past Billboard hits, to deserve public testing, release-watchlist promotion, or further revision?

## What changed in this pass

The judge loads `data/reference/billboard_preview_reference_profile.json`, built from **21 public iTunes preview clips** taken from the top 3 year-end Billboard Hot 100 songs for these sample years:
- 1965
- 1975
- 1985
- 1995
- 2005
- 2015
- 2024

The profile calibrates these audio bands from the preview set:
- `rms_level`
- `peak_level`
- `stereo_width_ratio`
- `dynamic_lift_ratio`
- `window_motion`

`tempo_fit` and `duration_fit` still use the project’s short-form target band rather than preview-derived values.

## Rerender tuning that unlocked the score jump

The promoted short-form config was rerendered with:
- `master_gain = 2.2`
- `stereo_width = 0.36`
- `arrangement_lift = 1.02`
- `drum_bus_gain = 1.3`
- `guide_vocal_gain = 1.0`
- flatter, denser lane energy arcs to reduce over-lift while raising sustained level and motion

This moved the top cuts much closer to the Billboard preview-derived mix and motion bands.

## Current rubric

The automated judge scores each clip on:
- `hook_clarity`
- `mix_headroom`
- `dynamic_lift`
- `stereo_spread`
- `energy_motion`
- `tempo_fit`
- `duration_fit`

## Release-readiness labels

- `release_watchlist` = 85+
- `competitive_demo` = 72-84.99
- `revise` = 58-71.99
- `not_ready` = below 58

## Current batch result

| Candidate | Clip slug | Overall score | Label | Key issue summary |
|---|---|---:|---|---|
| Name on Neon | `promo-name-on-neon-direct-chorus` | 94.32 | `release_watchlist` | Clear machine winner after rerender; no remaining weak component below the concern threshold. |
| Back in Color | `promo-back-in-color-payoff-open` | 90.17 | `release_watchlist` | Strong backup and now inside release-watchlist territory. |
| Leave the Light | `promo-leave-the-light-silence-drop` | 77.28 | `competitive_demo` | Much stronger than before, but dynamic-lift shape is still outside the preferred reference band. |

## Machine winner

**Current AI leader:** `promo-name-on-neon-direct-chorus`

## What the AI is saying right now

1. The **hook ideas** are strong enough to keep moving.
2. The rerender closed the previous **mix/headroom** and **energy-motion** gap.
3. `Name on Neon` and `Back in Color` now both clear the `release_watchlist` band.
4. `Leave the Light` is usable as a `competitive_demo`, but it still needs a more controlled lift/payoff contour.

## Immediate implication

The batch is no longer in revise-first status.

The repo can now treat:
- `Name on Neon` as the **AI-first lead release candidate**
- `Back in Color` as the **strong secondary release-watchlist backup**
- `Leave the Light` as the **emotional alternate that still needs one more shape pass**

## Limitations of the reference set

- The reference set uses **public 30-second previews**, not full masters.
- It is a **cross-era calibration sample**, not a complete Billboard universe.
- It is designed to make the gate more grounded than a pure hand-tuned heuristic, not to act like a perfect commercial hit predictor.

## Next renderer targets from the AI gate

1. if you want a cleaner full-batch result, smooth `Leave the Light` so its dynamic lift lands closer to the reference band
2. keep rerunning `scripts/evaluate_hook_demo_batch.py` after every promoted rerender
3. rebuild the reference profile periodically as the Billboard dataset and reference pool get richer
4. use public metrics next as secondary validation rather than first-pass selection
