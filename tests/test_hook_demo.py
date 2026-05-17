from __future__ import annotations

import hashlib
import json
import textwrap
import wave
from pathlib import Path

from billboard_ai_hit.hook_demo import evaluate_hook_demo_manifest, load_hook_demo_config, run_hook_demo_batch


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_config(tmp_path: Path, *, include_lanes: bool = True) -> Path:
    demo_dir = tmp_path / "demo_out"
    manifest_path = demo_dir / "manifest.json"
    lane_blocks = ""
    if include_lanes:
        lane_blocks = textwrap.dedent(
            """
            [[lanes]]
            name = "late-night-rnb-pop"
            key = "A"
            mode = "minor"
            tempo_bpm = 104
            duration_seconds = 12
            demo_count = 2
            include_guide_vocal = true
            chord_loop = ["i", "VI", "III", "VII"]
            energy_arc = [0.35, 0.65, 0.95]
            motif_steps = [0, 2, 4, 2]
            motif_rhythm = [1.0, 0.5, 0.5, 1.0]

            [[lanes]]
            name = "festival-pop-lift"
            key = "C"
            mode = "major"
            tempo_bpm = 124
            duration_seconds = 14
            demo_count = 1
            include_guide_vocal = false
            chord_loop = ["I", "V", "vi", "IV"]
            energy_arc = [0.45, 0.8, 1.0]
            motif_steps = [0, 4, 5, 4]
            motif_rhythm = [0.5, 0.5, 1.0, 1.0]

            [[lanes]]
            name = "alt-dance-brood"
            key = "D"
            mode = "dorian"
            tempo_bpm = 118
            duration_seconds = 16
            demo_count = 1
            include_guide_vocal = true
            chord_loop = ["i", "IV", "VII", "III"]
            energy_arc = [0.4, 0.7, 0.9]
            motif_steps = [0, 3, 5, 7]
            motif_rhythm = [1.0, 1.0, 0.5, 0.5]
            """
        ).strip()
    config_text = textwrap.dedent(
        f"""
        [render]
        sample_rate = 16000
        swing = 0.08
        master_gain = 0.8

        [output]
        demo_dir = "{demo_dir}"
        manifest_path = "{manifest_path}"

        {lane_blocks}
        """
    ).strip()
    config_path = tmp_path / "hook_demo.toml"
    config_path.write_text(config_text + "\n", encoding="utf-8")
    return config_path


def test_load_hook_demo_config_uses_three_default_lanes_when_unspecified(tmp_path: Path) -> None:
    config = load_hook_demo_config(build_config(tmp_path, include_lanes=False))

    assert len(config.lanes) == 3
    assert [lane.name for lane in config.lanes] == [
        "heartbreak-rnb-pop",
        "festival-pop-anthem",
        "alt-dance-nocturne",
    ]
    assert all(10 <= lane.duration_seconds <= 30 for lane in config.lanes)


def test_run_hook_demo_batch_writes_manifest_and_lane_outputs(tmp_path: Path) -> None:
    config_path = build_config(tmp_path)

    result = run_hook_demo_batch(config_path)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert len(manifest["lanes"]) == 3
    assert len(manifest["demos"]) == 4
    assert result.demo_dir.exists()
    assert manifest["render"] == {
        "sample_rate": 16000,
        "swing": 0.08,
        "master_gain": 0.8,
        "stereo_width": 0.28,
        "arrangement_lift": 1.15,
        "drum_bus_gain": 1.0,
        "guide_vocal_gain": 1.0,
    }

    for demo in manifest["demos"]:
        audio_path = Path(demo["audio_path"])
        assert audio_path.exists()
        with wave.open(str(audio_path), "rb") as handle:
            duration = handle.getnframes() / handle.getframerate()
            assert 10 <= duration <= 30.1
            assert handle.getsampwidth() == 2
            assert handle.getnchannels() == 2
            assert handle.getframerate() == 16000
        assert demo["tempo_bpm"] > 0
        assert demo["chord_loop"]
        assert demo["motif_steps"]

    assert any(demo["include_guide_vocal"] for demo in manifest["demos"])
    assert any(not demo["include_guide_vocal"] for demo in manifest["demos"])


def test_run_hook_demo_batch_is_repeatable_for_same_config(tmp_path: Path) -> None:
    config_path = build_config(tmp_path)

    first = run_hook_demo_batch(config_path)
    first_manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    first_hashes = {
        demo["slug"]: sha256_file(Path(demo["audio_path"]))
        for demo in first_manifest["demos"]
    }

    second = run_hook_demo_batch(config_path)
    second_manifest = json.loads(second.manifest_path.read_text(encoding="utf-8"))
    second_hashes = {
        demo["slug"]: sha256_file(Path(demo["audio_path"]))
        for demo in second_manifest["demos"]
    }

    assert first_hashes == second_hashes


def test_run_hook_demo_batch_preserves_explicit_demo_metadata_in_manifest(tmp_path: Path) -> None:
    demo_dir = tmp_path / "sprint1_demo_out"
    manifest_path = demo_dir / "manifest.json"
    config_path = tmp_path / "sprint1_hook_demo.toml"
    config_path.write_text(
        textwrap.dedent(
            f"""
            [render]
            sample_rate = 16000
            swing = 0.08
            master_gain = 0.8

            [output]
            demo_dir = "{demo_dir}"
            manifest_path = "{manifest_path}"

            [[lanes]]
            name = "lane-1-euphoric-recovery"
            render_label = "Lane 1 Demo 1A"
            lane_label = "Lane 1"
            demo_id = "1A"
            output_slug = "lane1-demo1a-back-in-color"
            title_options = ["Back in Color", "Out Your Frame"]
            clip_reference_scope = "Writing-pack target timestamps, not measured offsets in the short local WAV render"
            intended_clip_sections = [
              "0:11-0:19: Now I'm back in color / Back where the bright lights are",
              "1:37-1:45: final chorus entry with bigger drums and vocal stack",
            ]
            provenance_notes = [
              "Source brief: sprint1_writing_pack.md",
              "Prototype engine: local no-Suno hook demo renderer",
            ]
            key = "G"
            mode = "major"
            tempo_bpm = 122
            duration_seconds = 16
            demo_count = 1
            include_guide_vocal = true
            chord_loop = ["I", "V", "vi", "IV"]
            energy_arc = [0.42, 0.76, 1.0]
            motif_steps = [0, 2, 4, 2]
            motif_rhythm = [0.5, 0.5, 1.0, 1.0]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    run_hook_demo_batch(config_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["demos"] == [
        {
            "lane": "lane-1-euphoric-recovery",
            "slug": "lane1-demo1a-back-in-color",
            "audio_path": str(demo_dir / "lane1-demo1a-back-in-color.wav"),
            "tempo_bpm": 124,
            "duration_seconds": 16.0,
            "chord_loop": ["vi", "IV", "I", "V"],
            "energy_arc": [0.42, 0.76, 1.0],
            "motif_steps": [4, 2, 0, 2],
            "motif_rhythm": [1.0, 0.5, 0.5, 1.0],
            "include_guide_vocal": True,
            "sample_rate": 16000,
            "seed": 2055678089202135814,
            "render_label": "Lane 1 Demo 1A",
            "lane_label": "Lane 1",
            "demo_id": "1A",
            "title_options": ["Back in Color", "Out Your Frame"],
            "clip_reference_scope": "Writing-pack target timestamps, not measured offsets in the short local WAV render",
            "intended_clip_sections": [
                "0:11-0:19: Now I'm back in color / Back where the bright lights are",
                "1:37-1:45: final chorus entry with bigger drums and vocal stack",
            ],
            "provenance_notes": [
                "Source brief: sprint1_writing_pack.md",
                "Prototype engine: local no-Suno hook demo renderer",
            ],
        }
    ]


def test_run_hook_demo_batch_makes_output_slug_unique_when_demo_count_exceeds_one(tmp_path: Path) -> None:
    demo_dir = tmp_path / "slug_collision_demo_out"
    manifest_path = demo_dir / "manifest.json"
    config_path = tmp_path / "slug_collision_hook_demo.toml"
    config_path.write_text(
        textwrap.dedent(
            f"""
            [output]
            demo_dir = "{demo_dir}"
            manifest_path = "{manifest_path}"

            [[lanes]]
            name = "collision-check"
            output_slug = "same-slug"
            key = "C"
            mode = "major"
            tempo_bpm = 120
            duration_seconds = 12
            demo_count = 2
            include_guide_vocal = false
            chord_loop = ["I", "V", "vi", "IV"]
            energy_arc = [0.4, 0.7, 1.0]
            motif_steps = [0, 2, 4, 2]
            motif_rhythm = [1.0, 0.5, 0.5, 1.0]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    run_hook_demo_batch(config_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert [demo["slug"] for demo in manifest["demos"]] == ["same-slug-01", "same-slug-02"]
    assert [Path(demo["audio_path"]).name for demo in manifest["demos"]] == ["same-slug-01.wav", "same-slug-02.wav"]
    assert len({demo["audio_path"] for demo in manifest["demos"]}) == 2


def test_load_hook_demo_config_supports_review_grade_render_controls(tmp_path: Path) -> None:
    demo_dir = tmp_path / "review_grade_demo_out"
    manifest_path = demo_dir / "manifest.json"
    config_path = tmp_path / "review_grade_hook_demo.toml"
    config_path.write_text(
        textwrap.dedent(
            f"""
            [render]
            sample_rate = 22050
            swing = 0.12
            master_gain = 0.72
            stereo_width = 0.45
            arrangement_lift = 1.3
            drum_bus_gain = 1.2
            guide_vocal_gain = 0.78

            [output]
            demo_dir = "{demo_dir}"
            manifest_path = "{manifest_path}"

            [[lanes]]
            name = "review-grade-check"
            key = "C"
            mode = "major"
            tempo_bpm = 120
            duration_seconds = 12
            demo_count = 1
            include_guide_vocal = true
            chord_loop = ["I", "V", "vi", "IV"]
            energy_arc = [0.4, 0.75, 1.0]
            motif_steps = [0, 2, 4, 2]
            motif_rhythm = [1.0, 0.5, 0.5, 1.0]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    config = load_hook_demo_config(config_path)

    assert config.sample_rate == 22050
    assert config.swing == 0.12
    assert config.master_gain == 0.72
    assert config.stereo_width == 0.45
    assert config.arrangement_lift == 1.3
    assert config.drum_bus_gain == 1.2
    assert config.guide_vocal_gain == 0.78


def test_evaluate_hook_demo_manifest_writes_repeatable_quality_reports(tmp_path: Path) -> None:
    config_path = build_config(tmp_path)
    batch = run_hook_demo_batch(config_path)

    first = evaluate_hook_demo_manifest(batch.manifest_path)
    second = evaluate_hook_demo_manifest(batch.manifest_path)

    assert first.report_json_path.exists()
    assert first.report_csv_path.exists()
    assert first.winner_slug is not None
    assert first.winner_slug == second.winner_slug
    assert len(first.assessments) == len(second.assessments) == 4

    first_scores = {assessment.slug: assessment.overall_score for assessment in first.assessments}
    second_scores = {assessment.slug: assessment.overall_score for assessment in second.assessments}
    assert first_scores == second_scores

    for assessment in first.assessments:
        assert 0.0 <= assessment.overall_score <= 100.0
        assert assessment.release_readiness in {"release_watchlist", "competitive_demo", "revise", "not_ready"}
        assert assessment.component_scores["hook_clarity"] >= 55.0
        assert "duration_seconds" in assessment.feature_values
        assert assessment.notes


def test_evaluate_hook_demo_manifest_uses_reference_profile_when_provided(tmp_path: Path) -> None:
    config_path = build_config(tmp_path)
    batch = run_hook_demo_batch(config_path)

    baseline = evaluate_hook_demo_manifest(batch.manifest_path)
    reference_profile_path = tmp_path / "reference_profile.json"
    reference_profile_path.write_text(
        json.dumps(
            {
                "profile_name": "test-reference-profile",
                "feature_bands": {
                    "rms_level": {"minimum": 0.2, "target_low": 0.25, "target_high": 0.3, "maximum": 0.35},
                    "peak_level": {"minimum": 0.9, "target_low": 0.95, "target_high": 1.0, "maximum": 1.01},
                    "dynamic_lift_ratio": {"minimum": 0.95, "target_low": 1.0, "target_high": 1.1, "maximum": 1.25},
                    "stereo_width_ratio": {"minimum": 0.12, "target_low": 0.18, "target_high": 0.28, "maximum": 0.42},
                    "window_motion": {"minimum": 0.02, "target_low": 0.03, "target_high": 0.05, "maximum": 0.08},
                },
                "feature_caps": {"silence_ratio": {"maximum": 0.18}},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    calibrated = evaluate_hook_demo_manifest(batch.manifest_path, reference_profile_path)

    assert calibrated.reference_profile_path == reference_profile_path
    assert calibrated.reference_profile_name == "test-reference-profile"
    assert calibrated.assessments[0].component_scores["mix_headroom"] <= baseline.assessments[0].component_scores["mix_headroom"]
    calibrated_json = json.loads(calibrated.report_json_path.read_text(encoding="utf-8"))
    assert calibrated_json["reference_profile_path"] == str(reference_profile_path)
    assert calibrated_json["reference_profile_name"] == "test-reference-profile"
