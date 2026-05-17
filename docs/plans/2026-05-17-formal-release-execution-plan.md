# Billboard AI Hit Formal Release Execution Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Convert the current scaffold + prototype-hook project into a release-ready candidate pipeline over a 30-day cycle, with clear gates for data quality, demo quality, short-form testing, and final release readiness.

**Architecture:** Run four parallel-but-gated tracks: (1) data enrichment for stronger lane guidance, (2) demo rendering upgrades so candidate hooks are worth human review, (3) human review plus short-form hook testing to identify a winner, and (4) release gating so no song ships without memorability, risk, and packaging checks. Use the existing Python pipeline and TOML config surface as the control plane; add review and release artifacts under `docs/` so the repo itself becomes the operating system for the next month.

**Tech Stack:** Python (`src/billboard_ai_hit/*.py`), TOML configs in `config/`, generated WAV assets in `audio/`, processed JSON/CSV outputs in `data/processed/`, static hosting via Vercel, and markdown operating docs under `docs/`.

---

## Current baseline

Existing production-shaped assets already in repo:
- Dataset pipeline: `src/billboard_ai_hit/pipeline.py`
- Cycle-analysis scaffold: `src/billboard_ai_hit/cycle_analysis.py`
- Local hook renderer: `src/billboard_ai_hit/hook_demo.py`
- Dataset config: `config/settings.toml`
- Sprint-1 demo config: `config/sprint1_local_hook_demo.toml`
- Sprint-1 demo artifacts: `audio/sprint1_local_demo_batch/`
- Strategy doc and release logic: `docs/strategy/billboard_ai_hit_strategy_v1.md`

Critical constraints from the current state:
- `data/processed/summary.json` is still tiny-sample scaffold output.
- `data/processed/cycle_analysis.json` still exposes placeholder recurrence notes.
- `audio/sprint1_local_demo_batch/README.md` explicitly labels the current WAVs as prototype-grade sketches, not final productions.
- Therefore the immediate mission is **not** “ship the current demos”; it is “upgrade the system until at least one candidate deserves release testing.”

---

## Success criteria for the 30-day cycle

Ship a release candidate only if all of the following are true:
1. At least one lane produces a hook that earns Tier A internally.
2. That hook survives upgraded re-rendering and still scores well.
3. A short-form test cut beats the lane baseline on completion/rewatch/save-intent proxies.
4. The candidate has a clear audience lane, title, and visual framing.
5. Rights/similarity review does not raise elevated concerns.
6. The repo contains enough docs/config/artifacts that the run is reproducible.

If those conditions are not met by Day 30, the cycle ends with a documented **park / revise / rerun** decision rather than a weak release.

---

## Track map

### Track A — Data enrichment
Purpose: make lane decisions and writing prompts less guessy.

Primary files:
- Modify: `config/settings.toml`
- Modify: `README.md`
- Modify: `src/billboard_ai_hit/pipeline.py`
- Modify: `src/billboard_ai_hit/cycle_analysis.py`
- Refresh outputs: `data/processed/billboard_yearly.csv`
- Refresh outputs: `data/processed/summary.json`
- Refresh outputs: `data/processed/cycle_analysis.json`

### Track B — Demo quality upgrade
Purpose: replace primitive “good enough to sketch” audio with “good enough to judge.”

Primary files:
- Modify: `src/billboard_ai_hit/hook_demo.py`
- Modify: `config/hook_demo.toml`
- Modify: `config/sprint1_local_hook_demo.toml`
- Refresh outputs: `audio/sprint1_local_demo_batch/manifest.json`
- Refresh outputs: `audio/sprint1_local_demo_batch/*.wav`
- Update notes: `audio/sprint1_local_demo_batch/README.md`

### Track C — Review + short-form testing
Purpose: pick winners based on evidence, not intuition.

Primary files to create:
- Create: `docs/reviews/sprint1-demo-scorecard.md`
- Create: `docs/reviews/sprint1-tier-ranking.md`
- Create: `docs/shortform/sprint1-hook-test-plan.md`
- Create: `docs/shortform/sprint1-hook-test-results.md`
- Create: `docs/creative/top-candidate-briefs.md`

### Track D — Release gate
Purpose: prevent premature shipping.

Primary files to create:
- Create: `docs/release/release-gate-checklist.md`
- Create: `docs/release/release-candidate-one-pager.md`
- Create: `docs/release/park-revise-rerun-decision.md`

---

## 30-day calendar

### Week 1 — Stabilize inputs and upgrade the renderer
Target outcome: a believable second-pass demo batch exists.

### Week 2 — Internal ranking and promotion
Target outcome: top 1-3 hooks are selected and rewritten into stronger short-form cuts.

### Week 3 — Short-form testing and iteration
Target outcome: one lead candidate clearly outperforms the others.

### Week 4 — Release gate and candidate packaging
Target outcome: either a release candidate is approved or a documented no-go decision is made.

---

## Task-by-task plan

### Task 1: Create the release operating docs skeleton

**Objective:** Establish repo-native files for review, testing, and release decisions so the execution cycle has a durable paper trail.

**Files:**
- Create: `docs/reviews/sprint1-demo-scorecard.md`
- Create: `docs/reviews/sprint1-tier-ranking.md`
- Create: `docs/shortform/sprint1-hook-test-plan.md`
- Create: `docs/shortform/sprint1-hook-test-results.md`
- Create: `docs/creative/top-candidate-briefs.md`
- Create: `docs/release/release-gate-checklist.md`
- Create: `docs/release/release-candidate-one-pager.md`
- Create: `docs/release/park-revise-rerun-decision.md`

**Step 1: Create empty-but-usable markdown templates**
Include headings for owner, date, status, inputs, pass/fail criteria, and next action.

**Step 2: Link them from `README.md`**
Add a short “Operating docs” section under the sprint/demo material.

**Step 3: Verify file discovery**
Run: `find docs -maxdepth 2 -type f | sort`
Expected: new review/shortform/release docs appear.

**Step 4: Commit**
```bash
git add docs README.md
git commit -m "docs: add release execution operating templates"
```

### Task 2: Expand the legal-safe enrichment schema

**Objective:** Decide exactly which additional metadata fields can be added without drifting into risky imitation logic.

**Files:**
- Modify: `config/settings.toml`
- Modify: `README.md`
- Modify: `docs/strategy/billboard_ai_hit_strategy_v1.md`

**Step 1: Document the first enrichment batch**
Add fields such as lane tags, emotional polarity, tempo bucket, energy bucket, intro speed, chorus-entry timing bucket, and instrumentation tags.

**Step 2: Keep the policy explicit**
State that enrichment remains abstract, pattern-level, and non-imitative.

**Step 3: Verify the docs are aligned**
Run: `python3 - <<'PY'
from pathlib import Path
for p in ['README.md','docs/strategy/billboard_ai_hit_strategy_v1.md','config/settings.toml']:
    print(p, Path(p).exists())
PY`
Expected: all files print `True`.

**Step 4: Commit**
```bash
git add README.md docs/strategy/billboard_ai_hit_strategy_v1.md config/settings.toml
git commit -m "docs: define first legal-safe enrichment batch"
```

### Task 3: Upgrade the dataset pipeline to ingest the first enrichment batch

**Objective:** Turn the enrichment schema into actual processed outputs.

**Files:**
- Modify: `src/billboard_ai_hit/pipeline.py`
- Modify: `tests/test_pipeline.py`
- Optionally create/update: `data/reference/*.csv`

**Step 1: Write failing tests for the new enrichment columns**
Add assertions for required output fields and fallback behavior.

**Step 2: Run failing test**
Run: `PYTHONPATH=src pytest tests/test_pipeline.py -q`
Expected: FAIL on missing enrichment behavior.

**Step 3: Implement the minimal pipeline changes**
Add parsing, normalization, defaults, and output serialization for the new batch.

**Step 4: Re-run tests**
Run: `PYTHONPATH=src pytest tests/test_pipeline.py -q`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/billboard_ai_hit/pipeline.py tests/test_pipeline.py data/reference || true
git commit -m "feat: add first enrichment trait batch to pipeline"
```

### Task 4: Strengthen cycle-analysis outputs enough to guide creative decisions

**Objective:** Improve `cycle_analysis.json` from placeholder-only notes toward actionable lane guidance.

**Files:**
- Modify: `src/billboard_ai_hit/cycle_analysis.py`
- Modify: `tests/test_pipeline.py`
- Refresh: `data/processed/cycle_analysis.json`

**Step 1: Add failing tests for richer yearly summaries**
Examples: lane-like trait distributions, stronger rolling-window summaries, clearer recurrence annotations.

**Step 2: Run failing tests**
Run: `PYTHONPATH=src pytest tests/test_pipeline.py -q`
Expected: FAIL on the new structure.

**Step 3: Implement the minimal logic**
Prefer robust summary outputs over speculative math. Keep recurrence language conservative.

**Step 4: Rebuild processed outputs**
Run: `PYTHONPATH=src python3 scripts/run_pipeline.py config/settings.toml`
Expected: refreshed CSV/JSON outputs in `data/processed/`.

**Step 5: Commit**
```bash
git add src/billboard_ai_hit/cycle_analysis.py tests/test_pipeline.py data/processed/cycle_analysis.json data/processed/summary.json data/processed/billboard_yearly.csv
git commit -m "feat: strengthen cycle analysis for creative planning"
```

### Task 5: Raise the hook renderer from sketch-grade to review-grade

**Objective:** Make the audio output credible enough that internal ranking reflects song potential rather than renderer weakness.

**Files:**
- Modify: `src/billboard_ai_hit/hook_demo.py`
- Modify: `tests/test_hook_demo.py`
- Modify: `README.md`

**Step 1: Write failing tests for renderer controls**
Candidate controls: stereo rendering, arrangement layers, better envelope handling, drums/bass separation, clearer guide-vocal gain, and output metadata stability.

**Step 2: Run failing tests**
Run: `PYTHONPATH=src pytest tests/test_hook_demo.py -q`
Expected: FAIL.

**Step 3: Implement the smallest review-grade upgrade set**
Prioritize changes that improve comparative judgment: cleaner drums, better dynamic lift, more distinct sections, and less brittle guide-vocal masking.

**Step 4: Re-run tests**
Run: `PYTHONPATH=src pytest tests/test_hook_demo.py -q`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/billboard_ai_hit/hook_demo.py tests/test_hook_demo.py README.md
git commit -m "feat: upgrade hook renderer for internal review"
```

### Task 6: Re-render Sprint 1 with the upgraded engine

**Objective:** Replace the current six-demo batch with the best possible review pass from the local engine.

**Files:**
- Modify: `config/sprint1_local_hook_demo.toml`
- Refresh: `audio/sprint1_local_demo_batch/*.wav`
- Refresh: `audio/sprint1_local_demo_batch/manifest.json`
- Refresh: `audio/sprint1_local_demo_batch/README.md`

**Step 1: Tune lane configs**
Adjust tempo, energy, hook timing, title emphasis, and arrangement settings per lane.

**Step 2: Re-run batch render**
Run: `PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint1_local_hook_demo.toml`
Expected: six refreshed WAVs plus updated manifest.

**Step 3: Verify outputs exist**
Run: `python3 - <<'PY'
from pathlib import Path
p = Path('audio/sprint1_local_demo_batch')
print(sorted(x.name for x in p.glob('*.wav')))
print((p/'manifest.json').exists(), (p/'README.md').exists())
PY`
Expected: six `.wav` names plus `True True`.

**Step 4: Commit**
```bash
git add config/sprint1_local_hook_demo.toml audio/sprint1_local_demo_batch
git commit -m "feat: re-render sprint1 demos with upgraded engine"
```

### Task 7: Execute `next-4a` — formal 3-rater review

**Objective:** Convert subjective impressions into a traceable Tier A/B/C ranking.

**Files:**
- Update: `docs/reviews/sprint1-demo-scorecard.md`
- Update: `docs/reviews/sprint1-tier-ranking.md`
- Reference: `audio/sprint1_local_demo_batch/manifest.json`

**Step 1: Define rating axes**
Use at least: hook memorability, title strength, emotional clarity, clip-worthiness in first 10 seconds, lane fit, and “would you replay this?”

**Step 2: Score all six demos**
Each demo receives three independent ratings or three separate passes by the curator using fixed criteria.

**Step 3: Publish Tier A/B/C ranking**
Write an ordered summary with reasons, not just scores.

**Step 4: Verify ranking completeness**
Check that all six demos appear exactly once in the final ranking document.

**Step 5: Commit**
```bash
git add docs/reviews/sprint1-demo-scorecard.md docs/reviews/sprint1-tier-ranking.md
git commit -m "docs: rank sprint1 demos into tier list"
```

### Task 8: Execute `next-4b` — promote the top 1-3 hooks

**Objective:** Turn the best demos into concrete short-form candidates with stronger framing.

**Files:**
- Update: `docs/creative/top-candidate-briefs.md`
- Update: `config/sprint1_local_hook_demo.toml` or create `config/sprint2_promoted_hook_demo.toml`

**Step 1: Choose the promotion set**
Pick 1-3 demos only. If no demo earns Tier A, promote at most one “best available” candidate and mark it risky.

**Step 2: Write per-candidate creative briefs**
For each promoted demo include: core line, audience lane, emotional thesis, visual angle, title lock, and clip openings.

**Step 3: Create focused re-render config**
Either repurpose `config/sprint1_local_hook_demo.toml` or create `config/sprint2_promoted_hook_demo.toml` for stronger targeted iterations.

**Step 4: Verify references are consistent**
Ensure every promoted brief maps cleanly to a demo ID and output slug.

**Step 5: Commit**
```bash
git add docs/creative/top-candidate-briefs.md config/sprint1_local_hook_demo.toml config/sprint2_promoted_hook_demo.toml 2>/dev/null || true
git commit -m "docs: promote top sprint1 hooks into shortform briefs"
```

### Task 9: Generate short-form hook-test cuts

**Objective:** Produce testable clips built around the promoted candidates rather than the broad initial sprint.

**Files:**
- Update: `src/billboard_ai_hit/hook_demo.py`
- Update/create: `config/sprint2_promoted_hook_demo.toml`
- Create outputs under: `audio/shortform_hook_tests/`
- Update: `docs/shortform/sprint1-hook-test-plan.md`

**Step 1: Define test cut shapes**
Create 2-3 formats per promoted hook: direct-chorus open, lyric-first open, and beat-drop open.

**Step 2: Render the clips**
Run: `PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint2_promoted_hook_demo.toml`
Expected: focused short-form assets for promoted songs.

**Step 3: Verify output inventory**
Run: `find audio/shortform_hook_tests -maxdepth 2 -type f | sort`
Expected: clip outputs plus manifest/readme if configured.

**Step 4: Commit**
```bash
git add src/billboard_ai_hit/hook_demo.py config/sprint2_promoted_hook_demo.toml audio/shortform_hook_tests docs/shortform/sprint1-hook-test-plan.md
git commit -m "feat: generate promoted hook shortform test cuts"
```

### Task 10: Run the short-form test and log the result

**Objective:** Use consistent criteria to decide which candidate actually deserves release packaging.

**Files:**
- Update: `docs/shortform/sprint1-hook-test-results.md`
- Update: `docs/release/release-candidate-one-pager.md`

**Step 1: Define the baseline and winner rule**
Track completion, rewatch intent, save intent, quote-back recall, and strongest visual pairing.

**Step 2: Log every cut outcome**
Even if testing is manual or lightweight, store the observations in a fixed table.

**Step 3: Name one lead candidate**
If no candidate wins clearly, explicitly mark the cycle as not ready for release.

**Step 4: Commit**
```bash
git add docs/shortform/sprint1-hook-test-results.md docs/release/release-candidate-one-pager.md
git commit -m "docs: record hook-test results and lead candidate"
```

### Task 11: Run similarity and rights-risk review

**Objective:** Block accidental imitation before release packaging starts.

**Files:**
- Update: `docs/release/release-gate-checklist.md`
- Update: `docs/release/release-candidate-one-pager.md`

**Step 1: Create a rights-risk checklist**
Cover title uniqueness, topline similarity concerns, lane-overfit notes, and any lyrical red flags.

**Step 2: Review the lead candidate**
Mark pass / concern / blocked for every line item.

**Step 3: Verify a final status exists**
No blank checklist entries are allowed.

**Step 4: Commit**
```bash
git add docs/release/release-gate-checklist.md docs/release/release-candidate-one-pager.md
git commit -m "docs: add rights and similarity release gate"
```

### Task 12: Make the release decision

**Objective:** End the cycle with a clear yes/no outcome and next action.

**Files:**
- Update: `docs/release/release-candidate-one-pager.md`
- Update: `docs/release/park-revise-rerun-decision.md`

**Step 1: Apply the gate**
Check the candidate against the strategy rules in `docs/strategy/billboard_ai_hit_strategy_v1.md`.

**Step 2: Record the decision**
Allowed outputs: `GREENLIGHT`, `REVISE`, `PARK`, or `RERUN_LANE`.

**Step 3: Verify the repo tells a coherent story**
A new collaborator should be able to answer: what was tested, what won, why it did or did not advance, and what to do next.

**Step 4: Commit**
```bash
git add docs/release/release-candidate-one-pager.md docs/release/park-revise-rerun-decision.md
git commit -m "docs: finalize release-cycle decision"
```

---

## Mapping to current todo IDs

- `next-4` → entire 30-day cycle in this document
- `next-4a` → Task 7
- `next-4b` → Task 8
- recommended new sub-phases to add:
  - `next-4d` renderer upgrade + sprint1 re-render (Tasks 5-6)
  - `next-4e` short-form test cut generation and results (Tasks 9-10)
  - `next-4f` release-gate and final decision (Tasks 11-12)

---

## Day-30 exit states

### Exit A: Release candidate approved
Conditions:
- Tier A hook exists
- short-form winner exists
- rights gate passes
- packaging is clear

Next action:
- prepare external release assets and distribution timeline

### Exit B: Revise and rerun
Conditions:
- one promising hook exists but render, topline, or framing still underperforms

Next action:
- keep the winning lane, revise production and clip framing, run another 7-10 day micro-cycle

### Exit C: Park the batch
Conditions:
- no hook proves sticky enough even after upgrade

Next action:
- document learnings, retire the lane set, start a fresh monthly batch

---

## Minimum command set for this cycle

From `/home/patrick/billboard-ai-hit`:

```bash
PYTHONPATH=src pytest tests/test_pipeline.py -q
PYTHONPATH=src pytest tests/test_hook_demo.py -q
PYTHONPATH=src python3 scripts/run_pipeline.py config/settings.toml
PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint1_local_hook_demo.toml
PYTHONPATH=src python3 scripts/run_hook_demo_batch.py config/sprint2_promoted_hook_demo.toml
```

---

## Definition of done

This execution plan is complete when the repo contains:
- refreshed data outputs that are more useful than the current scaffold-only summaries
- a second-pass review-grade sprint demo batch
- a documented Tier A/B/C ranking for all sprint-1 demos
- promoted creative briefs for the top 1-3 candidates
- short-form test plan + results
- a release gate checklist and final cycle decision

If any one of those is missing, the release cycle is incomplete.
