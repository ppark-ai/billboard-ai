# Promoted Short-Form Hook Tests

This directory contains the first promoted short-form hook-test renders from `config/sprint2_promoted_hook_demo.toml`.

Run from `/home/patrick/billboard-ai-hit`:

`PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint2_promoted_hook_demo.toml`

Render profile:
- sample rate: 22050 Hz
- channels: stereo (2-channel WAV)
- stereo width: 0.42
- arrangement lift: 1.32
- drum bus gain: 1.2
- guide vocal gain: 0.9

Produced files:
1. `promo-name-on-neon-direct-chorus.wav` — 12.00s — sha256 prefix `98ad1ad638db5ebb`
2. `promo-leave-the-light-silence-drop.wav` — 13.00s — sha256 prefix `494ae798c2c97438`
3. `promo-back-in-color-payoff-open.wav` — 11.00s — sha256 prefix `477dcc9cf08780be`

Notes:
- These are focused short-form test cuts promoted from the Tier A sprint-1 concepts.
- Output inventory and render settings are recorded in `audio/shortform_hook_tests/manifest.json`.
- Public completion/rewatch/save metrics are still pending; this directory only captures the internal preflight assets.
