from __future__ import annotations

import json
import shutil
from pathlib import Path


CONFIG_JSON = {
    "version": 3,
    "routes": [
        {
            "src": "/audio/(.*)",
            "headers": {"cache-control": "public, max-age=3600"},
            "continue": True,
        },
        {"handle": "filesystem"},
        {"src": "/", "dest": "/index.html"},
    ],
}


def copy_if_exists(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    output_root = repo / ".vercel" / "output"
    static_root = output_root / "static"
    if static_root.exists():
        shutil.rmtree(static_root)
    static_root.mkdir(parents=True, exist_ok=True)

    copy_if_exists(repo / "index.html", static_root / "index.html")
    copy_if_exists(repo / "audio" / "published", static_root / "audio" / "published")
    copy_if_exists(repo / "audio" / "shortform_hook_tests" / "quality_report.json", static_root / "audio" / "shortform_hook_tests" / "quality_report.json")
    copy_if_exists(repo / "audio" / "shortform_hook_tests" / "manifest.json", static_root / "audio" / "shortform_hook_tests" / "manifest.json")
    copy_if_exists(repo / "docs" / "reviews" / "ai-billboard-quality-gate.md", static_root / "docs" / "reviews" / "ai-billboard-quality-gate.md")
    copy_if_exists(repo / "docs" / "final-release-pipeline.md", static_root / "docs" / "final-release-pipeline.md")
    copy_if_exists(repo / "data" / "reference" / "billboard_preview_reference_tracks.csv", static_root / "data" / "reference" / "billboard_preview_reference_tracks.csv")

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "config.json").write_text(json.dumps(CONFIG_JSON, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "static_root": str(static_root),
                "index": str((static_root / 'index.html').relative_to(repo)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
