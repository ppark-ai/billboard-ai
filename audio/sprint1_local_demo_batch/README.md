# Sprint 1 local demo batch

This directory contains the first six sprint-1 prototype demo renders produced with the local no-Suno hook-demo engine.

Run from `/home/patrick/billboard-ai-hit`:

`PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint1_local_hook_demo.toml`

Config and source brief:
- Config: `config/sprint1_local_hook_demo.toml`
- Writing pack: `sprint1_writing_pack.md` from kanban task `t_1d66dedc`
- Manifest: `audio/sprint1_local_demo_batch/manifest.json`

Produced files in render order:
1. Lane 1 Demo 1A — `lane1-demo1a-back-in-color.wav` — 17.00s — sha256 prefix `f349d7350c9444f7`
2. Lane 1 Demo 1B — `lane1-demo1b-fits-me-now.wav` — 16.00s — sha256 prefix `2cd89badd3323707`
3. Lane 3 Demo 3A — `lane3-demo3a-county-line-light.wav` — 18.00s — sha256 prefix `37a46c765534e23b`
4. Lane 1 Demo 1C — `lane1-demo1c-name-on-neon.wav` — 15.00s — sha256 prefix `5531bf4cf2d8f628`
5. Lane 3 Demo 3B — `lane3-demo3b-rearview-gold.wav` — 19.00s — sha256 prefix `a291bef608ac4303`
6. Lane 2 Demo 2A — `lane2-demo2a-leave-the-light.wav` — 17.00s — sha256 prefix `8ce8e744c538d04d`

Notes:
- The manifest now carries `render_label`, `lane_label`, `demo_id`, `title_options`, `clip_reference_scope`, `intended_clip_sections`, and `provenance_notes` per demo.
- `clip_reference_scope` explicitly marks the clip timestamps as writing-pack targets rather than measured offsets in these short local WAV renders.
- Durations may vary slightly from lane defaults because the renderer deterministically offsets timing per seed.
- These are prototype-grade WAV sketches with synthetic guide vocals where enabled, not final productions.
