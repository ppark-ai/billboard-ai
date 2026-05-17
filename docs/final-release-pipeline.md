# Final release pipeline

This repo now has an end-to-end final release pipeline for the Billboard-calibrated short-form demo flow.

## Components

### 1. Renderer / demo generator
- `src/billboard_ai_hit/hook_demo.py`
- CLI wrapper: `scripts/run_hook_demo_batch.py`
- Config: `config/sprint2_promoted_hook_demo.toml`

This generates the promoted short-form candidate WAV files and `audio/shortform_hook_tests/manifest.json`.

### 2. Billboard reference profile builder
- `scripts/build_billboard_reference_profile.py`
- Reference artifacts:
  - `data/reference/billboard_preview_reference_profile.json`
  - `data/reference/billboard_preview_reference_tracks.csv`

This defines the Billboard preview-based calibration space used by the evaluator.

### 3. Automated quality judge
- `scripts/evaluate_hook_demo_batch.py`

This scores all promoted candidates against the Billboard calibration profile and writes:
- `audio/shortform_hook_tests/quality_report.json`
- `audio/shortform_hook_tests/quality_report.csv`

### 4. Winner-to-web publisher
- `scripts/publish_top_web_demo.py`

This picks the true highest-scoring winner from the quality report, computes the nearest Billboard reference-calibration neighbors, creates a softened web listening export, and rewrites the website around the actual winner.

### 5. One-command orchestration
- `scripts/run_final_release_pipeline.py`

Runs render -> evaluate -> publish. Optional production deployment is available with `--deploy-vercel` when `VERCEL_TOKEN` is present.

## Recommended commands

### Local full pipeline
`PYTHONPATH=src python3 scripts/run_final_release_pipeline.py`

### Local full pipeline + production deploy
`PYTHONPATH=src python3 scripts/run_final_release_pipeline.py --deploy-vercel`

## Output of record
- Winner page: `index.html`
- Published web audio metadata: `audio/published/current_release.json`
- Full machine report: `audio/shortform_hook_tests/quality_report.json`

## Current publishing policy
- The website should display only the actual top-scoring song.
- Billboard songs shown next to it must be labeled as reference-calibration matches, not source-song claims.
- If synthetic guide-vocal harshness remains, the page should say so explicitly.
