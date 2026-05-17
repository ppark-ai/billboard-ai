# Auto deploy notes

This repo now includes `.github/workflows/vercel-prod.yml`.

## Trigger
- every push to `main`
- manual run via `workflow_dispatch`

## Requirement
Add the GitHub Actions repository secret:
- `VERCEL_TOKEN`

`VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` are already baked into the workflow from `.vercel/project.json`.

## Deploy path
The workflow runs:
1. `vercel pull --environment=production`
2. `vercel build --prod`
3. `vercel deploy --prebuilt --prod`

So future pushes to `main` should deploy automatically once `VERCEL_TOKEN` exists in repo secrets.
