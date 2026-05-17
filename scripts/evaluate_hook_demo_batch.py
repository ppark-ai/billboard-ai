from pathlib import Path

from billboard_ai_hit.hook_demo import evaluate_hook_demo_manifest


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Evaluate hook-demo batch audio against an automated Billboard-like quality rubric.")
    parser.add_argument("manifest", nargs="?", default="audio/shortform_hook_tests/manifest.json", help="Path to hook-demo manifest JSON")
    parser.add_argument("--reference-profile", dest="reference_profile", default=None, help="Optional path to a Billboard reference-profile JSON used to calibrate quality bands")
    args = parser.parse_args()

    report = evaluate_hook_demo_manifest(Path(args.manifest), Path(args.reference_profile) if args.reference_profile else None)
    print(
        json.dumps(
            {
                "manifest_path": str(report.manifest_path),
                "report_json_path": str(report.report_json_path),
                "report_csv_path": str(report.report_csv_path),
                "winner_slug": report.winner_slug,
                "reference_profile_path": str(report.reference_profile_path) if report.reference_profile_path else None,
                "reference_profile_name": report.reference_profile_name,
                "assessment_count": len(report.assessments),
            },
            indent=2,
        )
    )
