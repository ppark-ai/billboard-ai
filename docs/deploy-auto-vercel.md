# Auto deploy notes

This repo includes `.github/workflows/vercel-prod.yml`.

## Trigger
- every push to `main`
- manual run via `workflow_dispatch`

## Requirement
Add the GitHub Actions repository secret:
- `VERCEL_TOKEN`

`VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` are already baked into the workflow from `.vercel/project.json`.

## Deploy path
The workflow now uses the repo's own static publication pipeline:
1. `PYTHONPATH=src python3 scripts/run_final_release_pipeline.py`
   - rerender promoted candidates
   - rescore them against the Billboard reference profile
   - publish the real top scorer to the web page
   - stage `.vercel/output/static`
2. `vercel deploy --prebuilt --prod`

This avoids the old Python-framework build failure and deploys the prebuilt static winner site directly.

## Important limitation
I added the workflow file, but the repo secret still has to exist inside GitHub for the workflow to succeed. Local `.env` is **not** visible to GitHub Actions.
