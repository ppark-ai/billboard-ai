# Billboard yearly analysis scaffold

Local-first Python project for building a normalized Billboard Hot 100 yearly dataset from 1958 onward.

What it does:
- ingests per-year CSV exports
- normalizes song and artist fields for join-friendly matching
- preserves yearly chart rank, weeks on chart, peak position, and genre
- computes framework-aligned popularity sub-scores plus raw and era-adjusted labels
- writes a processed dataset CSV, summary JSON, and cycle-analysis scaffold JSON

## Layout

- `src/billboard_ai_hit/pipeline.py` — core ingestion, normalization, scoring, and CLI entrypoint
- `src/billboard_ai_hit/cycle_analysis.py` — yearly aggregation, genre-share windows, and recurrence-scoring scaffold
- `src/billboard_ai_hit/hook_demo.py` — local-first hook-demo batch generator and WAV renderer
- `scripts/run_pipeline.py` — thin dataset runner script
- `scripts/run_hook_demo_batch.py` — thin hook-demo runner script
- `config/settings.toml` — local dataset pipeline config
- `config/hook_demo.toml` — three-lane hook-demo batch config
- `data/raw/` — yearly source CSV files
- `data/reference/genre_lookup.csv` — optional genre enrichment table
- `data/processed/` — generated dataset outputs
- `audio/hook_demo_batches/` — generated hook-demo WAV batches plus manifest
- `tests/` — focused pytest coverage

## Expected yearly CSV columns

The pipeline accepts common aliases for the required fields:
- rank: `Rank`, `chart_rank`, `position`
- title: `Song`, `Song Title`, `title`
- artist: `Artist`, `Artist(s)`, `artist_name`
- weeks: `Weeks`, `Weeks on Chart`, `weeks_on_chart`
- peak: `Peak`, `Peak Position`, `peak_pos`
- genre must be present either in the source file or via the lookup table; the pipeline raises if neither source provides it

## Run it

From `/home/patrick/billboard-ai-hit`:

`PYTHONPATH=src python3 scripts/run_pipeline.py config/settings.toml`

The command writes:
- `/home/patrick/billboard-ai-hit/data/processed/billboard_yearly.csv`
- `/home/patrick/billboard-ai-hit/data/processed/summary.json`
- `/home/patrick/billboard-ai-hit/data/processed/cycle_analysis.json`

## Generate local hook-demo batches

Repeatable run command from `/home/patrick/billboard-ai-hit`:

`PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/hook_demo.toml`

What it does:
- renders short 10-30 second `.wav` hook demos locally with no Suno dependency
- batches across three default Billboard-oriented lanes: `heartbreak-rnb-pop`, `festival-pop-anthem`, and `alt-dance-nocturne`
- lets each lane specify tempo, chord loop, energy arc, motif steps/rhythm, demo count, and whether to add a synthetic guide-vocal lead
- supports per-demo metadata fields such as `render_label`, `lane_label`, `demo_id`, `output_slug`, `title_options`, `clip_reference_scope`, `intended_clip_sections`, and `provenance_notes`
- writes per-demo audio files plus `/home/patrick/billboard-ai-hit/audio/hook_demo_batches/manifest.json`

Config knobs in `config/hook_demo.toml`:
- `[render]` — sample rate, swing, master gain, stereo width, arrangement lift, drum-bus gain, and guide-vocal gain
- `[output]` — destination directory and manifest path
- `[[lanes]]` — `tempo_bpm`, `duration_seconds`, `demo_count`, `chord_loop`, `energy_arc`, `motif_steps`, `motif_rhythm`, `include_guide_vocal`, `key`, and `mode`
- optional `[[lanes]]` metadata fields — `render_label`, `lane_label`, `demo_id`, `output_slug`, `title_options`, `clip_reference_scope`, `intended_clip_sections`, `provenance_notes`

Sprint-1 local six-demo batch:
- run `PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint1_local_hook_demo.toml`
- outputs land in `/home/patrick/billboard-ai-hit/audio/sprint1_local_demo_batch/`
- the sprint-1 manifest includes ordered mappings for Lane 1 Demo 1A, 1B, 3A, 1C, 3B, and 2A plus title, clip, and provenance metadata
- `clip_reference_scope` marks the clip timestamps as writing-pack targets rather than measured offsets in the short local WAVs
- see `/home/patrick/billboard-ai-hit/audio/sprint1_local_demo_batch/README.md` after a run for exact reproduction notes

Prototype note:
- the guide-vocal path is a synthetic placeholder lead line for melody sketching, not a full singing model
- the generator is intended for fast hook exploration and A/B testing, not polished final production

## Scoring framework

The scaffold now follows the finalized popularity framework instead of the older one-line heuristic.

Per-song raw scoring components:
- `year_end_score` = concave transform of year-end rank
- `peak_score` = concave transform of peak rank
- `weeks_score` = log-scaled longevity score normalized by that year's `weeks_p95_in_year`

Raw score formula:
- `popularity_score_raw_100 = 100 * (0.60 * year_end_score + 0.15 * peak_score + 0.25 * weeks_score)`

Era buckets:
- `1958-1990`
- `1991-2004`
- `2005-2012`
- `2013-2019`
- `2020+`

Cross-era adjustment fields:
- `raw_year_percentile`
- `raw_era_percentile`
- `popularity_score_era_adj_100 = 100 * (0.65 * raw_year_percentile + 0.35 * raw_era_percentile)`

Compatibility note:
- `popularity_score` is retained as an alias of `popularity_score_era_adj_100` so the cycle-analysis scaffold can keep using a single weight field.

Popularity labels come from the era-adjusted score:
- `canonical_hit` >= 90
- `major_hit` >= 75
- `solid_hit` >= 60
- `moderate_hit` >= 45
- `minor_hit` >= 30
- `lower_impact_year_end_entry` < 30

Confidence outputs:
- `confidence_score`
- `confidence_label`

Current confidence penalties follow the framework's starter rules:
- missing or imputed weeks
- missing or imputed peak rank
- weak or unknown genre metadata
- transition-era years (`1991-1992`, `2005-2006`, `2012-2013`, `2020-2021`)
- low-coverage proxy use if optional proxies are ever added later

## Tiny-sample scaffold caveat

This repo's fixtures are intentionally tiny, so the percentile and `weeks_p95_in_year` calculations are only a scaffold-level stand-in for full Top 100 yearly cohorts.

That means:
- local tests still verify the scoring flow end to end
- the output field names and formulas are production-shaped
- but percentile behavior is only fully representative when you run the pipeline on real year-level datasets instead of the miniature test fixtures

## Cycle-analysis scaffold

`cycle_analysis.json` currently includes:
- `yearly_metrics` with per-year track counts, genre share, and popularity-weighted averages for `chart_rank`, `weeks_on_chart`, and `peak_position`
- `rolling_windows` for multi-year comparisons; configure the window size with `[analysis].rolling_window`
- `recurrence_candidates` using a placeholder similarity score that compares genre-share overlap plus weighted trait similarity across years
- `cycle_detection_notes` calling out where to swap in spectral, autocorrelation, or other stronger cycle-detection methods once more audio/metadata features exist

This keeps the project usable today while leaving a clear seam for more rigorous cyclical-trend models later.

## Tests

Run:

`PYTHONPATH=src pytest tests/test_pipeline.py -q`
