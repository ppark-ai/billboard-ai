# Sprint 1 local demo batch

This directory contains the refreshed six-song sprint-1 local demo batch rendered with the upgraded review-grade hook-demo engine.

Run from `/home/patrick/billboard-ai-hit`:

`PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint1_local_hook_demo.toml`

Config and source brief:
- Config: `config/sprint1_local_hook_demo.toml`
- Writing pack: `sprint1_writing_pack.md` from kanban task `t_1d66dedc`
- Manifest: `audio/sprint1_local_demo_batch/manifest.json`

Render profile:
- sample rate: 22050 Hz
- channels: stereo (2-channel WAV)
- swing: 0.09
- arrangement lift: 1.28
- drum bus gain: 1.18
- guide vocal gain: 0.88

Produced files in render order:
1. Lane 1 Demo 1A — `lane1-demo1a-back-in-color.wav` — 17.00s — sha256 prefix `5fdc7ae88b22c925`
2. Lane 1 Demo 1B — `lane1-demo1b-fits-me-now.wav` — 16.00s — sha256 prefix `29073f4d2f81d061`
3. Lane 3 Demo 3A — `lane3-demo3a-county-line-light.wav` — 18.00s — sha256 prefix `22becf2f7a93866a`
4. Lane 1 Demo 1C — `lane1-demo1c-name-on-neon.wav` — 15.00s — sha256 prefix `90ac4d921df88e4d`
5. Lane 3 Demo 3B — `lane3-demo3b-rearview-gold.wav` — 19.00s — sha256 prefix `632b4b5e385a00d6`
6. Lane 2 Demo 2A — `lane2-demo2a-leave-the-light.wav` — 17.00s — sha256 prefix `ec6ad6c9f9d8588f`

Notes:
- The manifest carries `render_label`, `lane_label`, `demo_id`, `title_options`, `clip_reference_scope`, `intended_clip_sections`, and `provenance_notes` per demo.
- `clip_reference_scope` explicitly marks the clip timestamps as writing-pack targets rather than measured offsets in these short local WAV renders.
- Durations may vary slightly from lane defaults because the renderer deterministically offsets timing per seed.
- These are still local synthetic demos, but they now render with stereo widening, stronger late-section lift, and louder drum/vocal buses for internal ranking passes.
