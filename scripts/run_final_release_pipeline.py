from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def load_env_value(repo: Path, key: str) -> str | None:
    env_path = repo / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        current_key, value = line.split("=", 1)
        if current_key.strip() == key:
            return value.strip()
    return None


def run(command: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None) -> None:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the final Billboard-calibrated render/evaluate/publish pipeline.")
    parser.add_argument("--config", default="config/sprint2_promoted_hook_demo.toml")
    parser.add_argument("--manifest", default="audio/shortform_hook_tests/manifest.json")
    parser.add_argument("--reference-profile", default="data/reference/billboard_preview_reference_profile.json")
    parser.add_argument("--deploy-vercel", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    config = repo / args.config
    manifest = repo / args.manifest
    reference_profile = repo / args.reference_profile

    run(["python3", "scripts/run_hook_demo_batch.py", str(config.relative_to(repo))], cwd=repo, extra_env={"PYTHONPATH": "src"})
    run(
        [
            "python3",
            "scripts/evaluate_hook_demo_batch.py",
            str(manifest.relative_to(repo)),
            "--reference-profile",
            str(reference_profile.relative_to(repo)),
        ],
        cwd=repo,
        extra_env={"PYTHONPATH": "src"},
    )
    run(["python3", "scripts/publish_top_web_demo.py"], cwd=repo)
    run(["python3", "scripts/stage_vercel_static_output.py"], cwd=repo)

    deployment_url = None
    if args.deploy_vercel:
        token = os.environ.get("VERCEL_TOKEN") or load_env_value(repo, "VERCEL_TOKEN")
        if not token:
            raise SystemExit("VERCEL_TOKEN not found in environment or .env")
        project = json.loads((repo / ".vercel" / "project.json").read_text(encoding="utf-8"))
        deploy_cmd = [
            "npx",
            "vercel",
            "deploy",
            "--prebuilt",
            "--prod",
            "--yes",
            "--token",
            token,
            "--scope",
            project["orgId"],
        ]
        result = subprocess.run(deploy_cmd, cwd=repo, text=True, capture_output=True, check=True)
        output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        deployment_url = output_lines[-1] if output_lines else None

    summary = {
        "config": str(config.relative_to(repo)),
        "manifest": str(manifest.relative_to(repo)),
        "reference_profile": str(reference_profile.relative_to(repo)),
        "published_release_metadata": "audio/published/current_release.json",
        "deployed": bool(deployment_url),
        "deployment_url": deployment_url,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
