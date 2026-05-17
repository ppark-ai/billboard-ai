from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import struct
import tomllib
import wave
from dataclasses import asdict, dataclass
from pathlib import Path

SAMPLE_WIDTH_BYTES = 2
MAX_INT16 = 32767
DEFAULT_SAMPLE_RATE = 16_000
DEFAULT_SWING = 0.08
DEFAULT_MASTER_GAIN = 0.85
DEFAULT_STEREO_WIDTH = 0.28
DEFAULT_ARRANGEMENT_LIFT = 1.15
DEFAULT_DRUM_BUS_GAIN = 1.0
DEFAULT_GUIDE_VOCAL_GAIN = 1.0
DEFAULT_DURATION_SECONDS = 16.0
DEFAULT_DEMO_COUNT = 2
DEFAULT_REFERENCE_PROFILE_RELATIVE_PATH = Path("data/reference/billboard_preview_reference_profile.json")
MODE_INTERVALS = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
}
NOTE_TO_SEMITONE = {
    "c": 0,
    "c#": 1,
    "db": 1,
    "d": 2,
    "d#": 3,
    "eb": 3,
    "e": 4,
    "f": 5,
    "f#": 6,
    "gb": 6,
    "g": 7,
    "g#": 8,
    "ab": 8,
    "a": 9,
    "a#": 10,
    "bb": 10,
    "b": 11,
}
ROMAN_TO_DEGREE = {
    "i": 0,
    "ii": 1,
    "iii": 2,
    "iv": 3,
    "v": 4,
    "vi": 5,
    "vii": 6,
}


@dataclass(frozen=True)
class HookDemoLane:
    name: str
    render_label: str | None
    lane_label: str | None
    demo_id: str | None
    output_slug: str | None
    title_options: tuple[str, ...]
    lyrics_lines: tuple[str, ...]
    clip_reference_scope: str | None
    intended_clip_sections: tuple[str, ...]
    provenance_notes: tuple[str, ...]
    key: str
    mode: str
    tempo_bpm: int
    duration_seconds: float
    demo_count: int
    include_guide_vocal: bool
    chord_loop: tuple[str, ...]
    energy_arc: tuple[float, ...]
    motif_steps: tuple[int, ...]
    motif_rhythm: tuple[float, ...]


@dataclass(frozen=True)
class HookDemoConfig:
    sample_rate: int
    swing: float
    master_gain: float
    stereo_width: float
    arrangement_lift: float
    drum_bus_gain: float
    guide_vocal_gain: float
    demo_dir: Path
    manifest_path: Path
    lanes: tuple[HookDemoLane, ...]


@dataclass(frozen=True)
class HookDemoResult:
    lane: str
    slug: str
    audio_path: Path
    tempo_bpm: int
    duration_seconds: float
    chord_loop: tuple[str, ...]
    energy_arc: tuple[float, ...]
    motif_steps: tuple[int, ...]
    motif_rhythm: tuple[float, ...]
    include_guide_vocal: bool
    sample_rate: int
    seed: int
    render_label: str | None
    lane_label: str | None
    demo_id: str | None
    title_options: tuple[str, ...]
    lyrics_lines: tuple[str, ...]
    clip_reference_scope: str | None
    intended_clip_sections: tuple[str, ...]
    provenance_notes: tuple[str, ...]


@dataclass(frozen=True)
class HookDemoBatchResult:
    demo_dir: Path
    manifest_path: Path
    demos: tuple[HookDemoResult, ...]


@dataclass(frozen=True)
class HookDemoQualityAssessment:
    slug: str
    audio_path: Path
    title: str | None
    overall_score: float
    release_readiness: str
    component_scores: dict[str, float]
    feature_values: dict[str, float]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class HookDemoQualityBatchReport:
    manifest_path: Path
    report_json_path: Path
    report_csv_path: Path
    assessments: tuple[HookDemoQualityAssessment, ...]
    winner_slug: str | None
    reference_profile_path: Path | None = None
    reference_profile_name: str | None = None


@dataclass(frozen=True)
class DemoVariant:
    tempo_bpm: int
    duration_seconds: float
    chord_loop: tuple[str, ...]
    motif_steps: tuple[int, ...]
    motif_rhythm: tuple[float, ...]
    guide_vocal: bool
    seed: int


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def default_lanes() -> tuple[HookDemoLane, ...]:
    return (
        HookDemoLane(
            name="heartbreak-rnb-pop",
            render_label=None,
            lane_label=None,
            demo_id=None,
            output_slug=None,
            title_options=(),
            lyrics_lines=(),
            clip_reference_scope=None,
            intended_clip_sections=(),
            provenance_notes=(),
            key="A",
            mode="minor",
            tempo_bpm=102,
            duration_seconds=16.0,
            demo_count=2,
            include_guide_vocal=True,
            chord_loop=("i", "VI", "III", "VII"),
            energy_arc=(0.32, 0.6, 0.95),
            motif_steps=(0, 2, 4, 2),
            motif_rhythm=(1.0, 0.5, 0.5, 1.0),
        ),
        HookDemoLane(
            name="festival-pop-anthem",
            render_label=None,
            lane_label=None,
            demo_id=None,
            output_slug=None,
            title_options=(),
            lyrics_lines=(),
            clip_reference_scope=None,
            intended_clip_sections=(),
            provenance_notes=(),
            key="C",
            mode="major",
            tempo_bpm=124,
            duration_seconds=18.0,
            demo_count=2,
            include_guide_vocal=False,
            chord_loop=("I", "V", "vi", "IV"),
            energy_arc=(0.42, 0.78, 1.0),
            motif_steps=(0, 4, 5, 4),
            motif_rhythm=(0.5, 0.5, 1.0, 1.0),
        ),
        HookDemoLane(
            name="alt-dance-nocturne",
            render_label=None,
            lane_label=None,
            demo_id=None,
            output_slug=None,
            title_options=(),
            lyrics_lines=(),
            clip_reference_scope=None,
            intended_clip_sections=(),
            provenance_notes=(),
            key="D",
            mode="dorian",
            tempo_bpm=118,
            duration_seconds=20.0,
            demo_count=2,
            include_guide_vocal=True,
            chord_loop=("i", "IV", "VII", "III"),
            energy_arc=(0.38, 0.7, 0.92),
            motif_steps=(0, 3, 5, 7),
            motif_rhythm=(1.0, 1.0, 0.5, 0.5),
        ),
    )


def load_hook_demo_config(config_path: Path) -> HookDemoConfig:
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    render = raw.get("render", {})
    output = raw.get("output", {})
    demo_dir = Path(output.get("demo_dir", config_path.parent / "audio" / "hook_demo_batches")).expanduser()
    manifest_path = Path(output.get("manifest_path", demo_dir / "manifest.json")).expanduser()
    raw_lanes = raw.get("lanes") or []
    lanes = tuple(_load_lane(item) for item in raw_lanes) if raw_lanes else default_lanes()
    return HookDemoConfig(
        sample_rate=int(render.get("sample_rate", DEFAULT_SAMPLE_RATE)),
        swing=float(render.get("swing", DEFAULT_SWING)),
        master_gain=float(render.get("master_gain", DEFAULT_MASTER_GAIN)),
        stereo_width=float(render.get("stereo_width", DEFAULT_STEREO_WIDTH)),
        arrangement_lift=float(render.get("arrangement_lift", DEFAULT_ARRANGEMENT_LIFT)),
        drum_bus_gain=float(render.get("drum_bus_gain", DEFAULT_DRUM_BUS_GAIN)),
        guide_vocal_gain=float(render.get("guide_vocal_gain", DEFAULT_GUIDE_VOCAL_GAIN)),
        demo_dir=demo_dir,
        manifest_path=manifest_path,
        lanes=lanes,
    )


def _load_lane(raw_lane: dict[str, object]) -> HookDemoLane:
    return HookDemoLane(
        name=str(raw_lane.get("name", "unnamed-lane")),
        render_label=_optional_string(raw_lane.get("render_label")),
        lane_label=_optional_string(raw_lane.get("lane_label")),
        demo_id=_optional_string(raw_lane.get("demo_id")),
        output_slug=_optional_string(raw_lane.get("output_slug")),
        title_options=_load_string_tuple(raw_lane.get("title_options")),
        lyrics_lines=_load_string_tuple(raw_lane.get("lyrics_lines")),
        clip_reference_scope=_optional_string(raw_lane.get("clip_reference_scope")),
        intended_clip_sections=_load_string_tuple(raw_lane.get("intended_clip_sections")),
        provenance_notes=_load_string_tuple(raw_lane.get("provenance_notes")),
        key=str(raw_lane.get("key", "C")),
        mode=str(raw_lane.get("mode", "major")).lower(),
        tempo_bpm=int(raw_lane.get("tempo_bpm", 120)),
        duration_seconds=float(raw_lane.get("duration_seconds", DEFAULT_DURATION_SECONDS)),
        demo_count=int(raw_lane.get("demo_count", DEFAULT_DEMO_COUNT)),
        include_guide_vocal=bool(raw_lane.get("include_guide_vocal", False)),
        chord_loop=tuple(str(item) for item in raw_lane.get("chord_loop", ("I", "V", "vi", "IV"))),
        energy_arc=tuple(float(item) for item in raw_lane.get("energy_arc", (0.4, 0.7, 1.0))),
        motif_steps=tuple(int(item) for item in raw_lane.get("motif_steps", (0, 2, 4, 2))),
        motif_rhythm=tuple(float(item) for item in raw_lane.get("motif_rhythm", (1.0, 0.5, 0.5, 1.0))),
    )


def run_hook_demo_batch(config_path: Path) -> HookDemoBatchResult:
    config = load_hook_demo_config(config_path)
    config.demo_dir.mkdir(parents=True, exist_ok=True)
    config.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    demos: list[HookDemoResult] = []
    for lane in config.lanes:
        for index in range(lane.demo_count):
            variant = build_variant(lane, index)
            slug = build_demo_slug(lane, index)
            audio_path = config.demo_dir / f"{slug}.wav"
            render_hook_demo(
                audio_path,
                lane=lane,
                variant=variant,
                sample_rate=config.sample_rate,
                swing=config.swing,
                master_gain=config.master_gain,
                stereo_width=config.stereo_width,
                arrangement_lift=config.arrangement_lift,
                drum_bus_gain=config.drum_bus_gain,
                guide_vocal_gain=config.guide_vocal_gain,
            )
            demos.append(
                HookDemoResult(
                    lane=lane.name,
                    slug=slug,
                    audio_path=audio_path,
                    tempo_bpm=variant.tempo_bpm,
                    duration_seconds=variant.duration_seconds,
                    chord_loop=variant.chord_loop,
                    energy_arc=lane.energy_arc,
                    motif_steps=variant.motif_steps,
                    motif_rhythm=variant.motif_rhythm,
                    include_guide_vocal=variant.guide_vocal,
                    sample_rate=config.sample_rate,
                    seed=variant.seed,
                    render_label=lane.render_label,
                    lane_label=lane.lane_label,
                    demo_id=lane.demo_id,
                    title_options=lane.title_options,
                    lyrics_lines=lane.lyrics_lines,
                    clip_reference_scope=lane.clip_reference_scope,
                    intended_clip_sections=lane.intended_clip_sections,
                    provenance_notes=lane.provenance_notes,
                )
            )

    manifest = {
        "config_path": str(config_path),
        "demo_dir": str(config.demo_dir),
        "run_command": f"PYTHONPATH=src python3 scripts/run_hook_demo_batch.py {config_path}",
        "render": {
            "sample_rate": config.sample_rate,
            "swing": config.swing,
            "master_gain": config.master_gain,
            "stereo_width": config.stereo_width,
            "arrangement_lift": config.arrangement_lift,
            "drum_bus_gain": config.drum_bus_gain,
            "guide_vocal_gain": config.guide_vocal_gain,
        },
        "lanes": [asdict(lane) for lane in config.lanes],
        "demos": [
            {
                **asdict(demo),
                "audio_path": str(demo.audio_path),
            }
            for demo in demos
        ],
    }
    config.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return HookDemoBatchResult(demo_dir=config.demo_dir, manifest_path=config.manifest_path, demos=tuple(demos))


def evaluate_hook_demo_manifest(manifest_path: Path, reference_profile_path: Path | None = None) -> HookDemoQualityBatchReport:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    demo_dir = Path(manifest["demo_dir"])
    report_json_path = demo_dir / "quality_report.json"
    report_csv_path = demo_dir / "quality_report.csv"
    resolved_reference_profile_path = _resolve_reference_profile_path(manifest_path, reference_profile_path)
    reference_profile = _load_reference_profile(resolved_reference_profile_path)

    assessments: list[HookDemoQualityAssessment] = []
    for demo in manifest.get("demos", []):
        audio_path = Path(demo["audio_path"])
        feature_values = _analyze_audio_features(audio_path)
        component_scores = _score_audio_quality(demo, feature_values, reference_profile)
        overall_score = round(sum(component_scores.values()) / max(len(component_scores), 1), 2)
        release_readiness = _release_readiness(overall_score)
        assessments.append(
            HookDemoQualityAssessment(
                slug=str(demo["slug"]),
                audio_path=audio_path,
                title=(demo.get("title_options") or [None])[0],
                overall_score=overall_score,
                release_readiness=release_readiness,
                component_scores=component_scores,
                feature_values=feature_values,
                notes=_quality_notes(component_scores, feature_values),
            )
        )

    winner = max(assessments, key=lambda item: item.overall_score).slug if assessments else None
    report = {
        "manifest_path": str(manifest_path),
        "reference_profile_path": str(resolved_reference_profile_path) if resolved_reference_profile_path else None,
        "reference_profile_name": reference_profile.get("profile_name") if reference_profile else None,
        "winner_slug": winner,
        "assessments": [
            {
                "slug": item.slug,
                "audio_path": str(item.audio_path),
                "title": item.title,
                "overall_score": item.overall_score,
                "release_readiness": item.release_readiness,
                "component_scores": item.component_scores,
                "feature_values": item.feature_values,
                "notes": list(item.notes),
            }
            for item in assessments
        ],
    }
    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    fieldnames = [
        "slug",
        "title",
        "overall_score",
        "release_readiness",
        "hook_clarity",
        "mix_headroom",
        "dynamic_lift",
        "stereo_spread",
        "energy_motion",
        "tempo_fit",
        "duration_fit",
        "rms_level",
        "peak_level",
        "stereo_width_ratio",
        "dynamic_lift_ratio",
        "window_motion",
        "silence_ratio",
        "notes",
    ]
    with report_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in assessments:
            writer.writerow(
                {
                    "slug": item.slug,
                    "title": item.title or "",
                    "overall_score": f"{item.overall_score:.2f}",
                    "release_readiness": item.release_readiness,
                    "hook_clarity": f"{item.component_scores['hook_clarity']:.2f}",
                    "mix_headroom": f"{item.component_scores['mix_headroom']:.2f}",
                    "dynamic_lift": f"{item.component_scores['dynamic_lift']:.2f}",
                    "stereo_spread": f"{item.component_scores['stereo_spread']:.2f}",
                    "energy_motion": f"{item.component_scores['energy_motion']:.2f}",
                    "tempo_fit": f"{item.component_scores['tempo_fit']:.2f}",
                    "duration_fit": f"{item.component_scores['duration_fit']:.2f}",
                    "rms_level": f"{item.feature_values['rms_level']:.5f}",
                    "peak_level": f"{item.feature_values['peak_level']:.5f}",
                    "stereo_width_ratio": f"{item.feature_values['stereo_width_ratio']:.5f}",
                    "dynamic_lift_ratio": f"{item.feature_values['dynamic_lift_ratio']:.5f}",
                    "window_motion": f"{item.feature_values['window_motion']:.5f}",
                    "silence_ratio": f"{item.feature_values['silence_ratio']:.5f}",
                    "notes": " | ".join(item.notes),
                }
            )

    return HookDemoQualityBatchReport(
        manifest_path=manifest_path,
        report_json_path=report_json_path,
        report_csv_path=report_csv_path,
        assessments=tuple(assessments),
        winner_slug=winner,
        reference_profile_path=resolved_reference_profile_path,
        reference_profile_name=reference_profile.get("profile_name") if reference_profile else None,
    )


def _resolve_reference_profile_path(manifest_path: Path, reference_profile_path: Path | None) -> Path | None:
    if reference_profile_path is not None:
        return reference_profile_path
    for parent in (manifest_path.parent, *manifest_path.parents):
        candidate = parent / DEFAULT_REFERENCE_PROFILE_RELATIVE_PATH
        if candidate.exists():
            return candidate
    return None


def _load_reference_profile(reference_profile_path: Path | None) -> dict[str, object] | None:
    if reference_profile_path is None or not reference_profile_path.exists():
        return None
    return json.loads(reference_profile_path.read_text(encoding="utf-8"))


def _analyze_audio_features(audio_path: Path) -> dict[str, float]:
    with wave.open(str(audio_path), "rb") as handle:
        frame_rate = handle.getframerate()
        channel_count = handle.getnchannels()
        frame_count = handle.getnframes()
        if channel_count != 2:
            raise ValueError(f"Expected stereo WAV for quality analysis: {audio_path}")
        raw = handle.readframes(frame_count)

    pairs = struct.iter_unpack("<hh", raw)
    mono: list[float] = []
    peak_level = 0.0
    sum_squares = 0.0
    side_squares = 0.0
    for left_sample, right_sample in pairs:
        left_value = left_sample / MAX_INT16
        right_value = right_sample / MAX_INT16
        mono_value = (left_value + right_value) * 0.5
        side_value = (left_value - right_value) * 0.5
        peak_level = max(peak_level, abs(left_value), abs(right_value))
        sum_squares += (left_value * left_value + right_value * right_value) * 0.5
        side_squares += side_value * side_value
        mono.append(mono_value)

    total_frames = max(len(mono), 1)
    rms_level = math.sqrt(sum_squares / total_frames)
    stereo_width_ratio = math.sqrt(side_squares / total_frames) / max(rms_level, 1e-6)

    window_size = max(1, int(frame_rate * 0.5))
    window_rms: list[float] = []
    for start in range(0, len(mono), window_size):
        chunk = mono[start : start + window_size]
        if not chunk:
            continue
        rms = math.sqrt(sum(sample * sample for sample in chunk) / len(chunk))
        window_rms.append(rms)

    first_len = max(1, len(window_rms) // 3)
    first_third = window_rms[:first_len]
    last_third = window_rms[-first_len:]
    first_mean = sum(first_third) / max(len(first_third), 1)
    last_mean = sum(last_third) / max(len(last_third), 1)
    dynamic_lift_ratio = last_mean / max(first_mean, 1e-6)
    window_motion = 0.0
    if len(window_rms) > 1:
        window_motion = sum(abs(window_rms[index] - window_rms[index - 1]) for index in range(1, len(window_rms))) / (len(window_rms) - 1)
    silence_ratio = sum(1 for value in window_rms if value < 0.025) / max(len(window_rms), 1)

    return {
        "duration_seconds": frame_count / max(frame_rate, 1),
        "sample_rate": float(frame_rate),
        "rms_level": rms_level,
        "peak_level": peak_level,
        "stereo_width_ratio": stereo_width_ratio,
        "dynamic_lift_ratio": dynamic_lift_ratio,
        "window_motion": window_motion,
        "silence_ratio": silence_ratio,
    }


def _score_audio_quality(
    demo: dict[str, object],
    feature_values: dict[str, float],
    reference_profile: dict[str, object] | None = None,
) -> dict[str, float]:
    title_options = demo.get("title_options") or []
    intended_sections = demo.get("intended_clip_sections") or []
    tempo_value = float(str(demo.get("tempo_bpm", 0)))
    hook_metadata = 0.55
    if title_options:
        hook_metadata += 0.2
    if intended_sections:
        hook_metadata += 0.15
    if demo.get("include_guide_vocal"):
        hook_metadata += 0.1

    mix_rms_band = _feature_band(reference_profile, "rms_level", (0.05, 0.11, 0.24, 0.33))
    mix_peak_band = _feature_band(reference_profile, "peak_level", (0.55, 0.75, 0.96, 1.0))
    dynamic_lift_band = _feature_band(reference_profile, "dynamic_lift_ratio", (0.9, 1.05, 1.45, 1.9))
    stereo_spread_band = _feature_band(reference_profile, "stereo_width_ratio", (0.03, 0.08, 0.35, 0.65))
    motion_band = _feature_band(reference_profile, "window_motion", (0.01, 0.025, 0.14, 0.26))
    silence_cap = _feature_cap(reference_profile, "silence_ratio", 0.45)
    tempo_band = _feature_band(reference_profile, "tempo_bpm", (88.0, 96.0, 132.0, 148.0))
    duration_band = _feature_band(reference_profile, "duration_seconds", (8.0, 10.0, 16.0, 22.0))

    return {
        "hook_clarity": round(100 * max(0.0, min(1.0, hook_metadata)), 2),
        "mix_headroom": round(100 * ((_band_score(feature_values["rms_level"], *mix_rms_band) * 0.55) + (_band_score(feature_values["peak_level"], *mix_peak_band) * 0.45)), 2),
        "dynamic_lift": round(100 * _band_score(feature_values["dynamic_lift_ratio"], *dynamic_lift_band), 2),
        "stereo_spread": round(100 * _band_score(feature_values["stereo_width_ratio"], *stereo_spread_band), 2),
        "energy_motion": round(100 * ((_band_score(feature_values["window_motion"], *motion_band) * 0.7) + ((1.0 - min(feature_values["silence_ratio"], silence_cap) / silence_cap) * 0.3)), 2),
        "tempo_fit": round(100 * _band_score(tempo_value, *tempo_band), 2),
        "duration_fit": round(100 * _band_score(feature_values["duration_seconds"], *duration_band), 2),
    }


def _feature_band(
    reference_profile: dict[str, object] | None,
    feature_name: str,
    fallback: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    if not reference_profile:
        return fallback
    feature_bands = reference_profile.get("feature_bands")
    if not isinstance(feature_bands, dict):
        return fallback
    feature_band = feature_bands.get(feature_name)
    if not isinstance(feature_band, dict):
        return fallback
    keys = ("minimum", "target_low", "target_high", "maximum")
    values: list[float] = []
    for key in keys:
        try:
            values.append(float(str(feature_band[key])))
        except (KeyError, TypeError, ValueError):
            return fallback
    minimum, target_low, target_high, maximum = values
    if not minimum < target_low <= target_high < maximum:
        return fallback
    return minimum, target_low, target_high, maximum


def _feature_cap(reference_profile: dict[str, object] | None, feature_name: str, fallback: float) -> float:
    if not reference_profile:
        return fallback
    feature_caps = reference_profile.get("feature_caps")
    if not isinstance(feature_caps, dict):
        return fallback
    feature_cap = feature_caps.get(feature_name)
    if not isinstance(feature_cap, dict):
        return fallback
    try:
        value = float(str(feature_cap["maximum"]))
    except (KeyError, TypeError, ValueError):
        return fallback
    return value if value > 0 else fallback


def _band_score(value: float, minimum: float, target_low: float, target_high: float, maximum: float) -> float:
    if value <= minimum or value >= maximum:
        return 0.0
    if target_low <= value <= target_high:
        return 1.0
    if value < target_low:
        return (value - minimum) / max(target_low - minimum, 1e-6)
    return (maximum - value) / max(maximum - target_high, 1e-6)


def _release_readiness(score: float) -> str:
    if score >= 85.0:
        return "release_watchlist"
    if score >= 72.0:
        return "competitive_demo"
    if score >= 58.0:
        return "revise"
    return "not_ready"


def _quality_notes(component_scores: dict[str, float], feature_values: dict[str, float]) -> tuple[str, ...]:
    notes: list[str] = []
    if component_scores["hook_clarity"] >= 85:
        notes.append("hook metadata is strong enough for an AI-first preflight")
    if component_scores["mix_headroom"] < 65:
        notes.append("mix/headroom profile still sits below a Billboard-like reference band")
    if component_scores["dynamic_lift"] < 65:
        notes.append("section lift is too flat or too exaggerated for a release-ready hook cut")
    if component_scores["stereo_spread"] < 65:
        notes.append("stereo field needs refinement to feel commercially wide without smearing")
    if component_scores["energy_motion"] < 65:
        notes.append("energy motion is weak relative to a competitive short-form payoff curve")
    if feature_values["silence_ratio"] > 0.18:
        notes.append("silence ratio is high enough to require manual verification of the drop/intro logic")
    if not notes:
        notes.append("overall profile lands inside the current automated competitive-demo band")
    return tuple(notes)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _load_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)


def build_demo_slug(lane: HookDemoLane, demo_index: int) -> str:
    if lane.output_slug:
        base = slugify(lane.output_slug)
        if lane.demo_count > 1:
            return f"{base}-{demo_index + 1:02d}"
        return base
    return f"{slugify(lane.name)}-{demo_index + 1:02d}"


def build_variant(lane: HookDemoLane, demo_index: int) -> DemoVariant:
    seed_input = f"{lane.name}|{demo_index}|{lane.key}|{lane.mode}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_input).digest()[:8], "big")
    offset = (seed % 5) - 2
    tempo_bpm = max(88, lane.tempo_bpm + offset)
    duration_offset = ((seed // 7) % 3) - 1
    duration_seconds = max(10.0, min(30.0, lane.duration_seconds + float(duration_offset)))
    motif_rotation = seed % max(len(lane.motif_steps), 1)
    rhythm_rotation = (seed // 11) % max(len(lane.motif_rhythm), 1)
    chord_rotation = (seed // 17) % max(len(lane.chord_loop), 1)
    guide_vocal = lane.include_guide_vocal and demo_index % 2 == 0 or (lane.include_guide_vocal and lane.demo_count == 1)
    return DemoVariant(
        tempo_bpm=tempo_bpm,
        duration_seconds=duration_seconds,
        chord_loop=_rotate_tuple(lane.chord_loop, chord_rotation),
        motif_steps=_rotate_tuple(lane.motif_steps, motif_rotation),
        motif_rhythm=_rotate_tuple(lane.motif_rhythm, rhythm_rotation),
        guide_vocal=guide_vocal,
        seed=seed,
    )


def _rotate_tuple(values: tuple[object, ...], amount: int) -> tuple[object, ...]:
    if not values:
        return values
    amount = amount % len(values)
    return values[amount:] + values[:amount]


def render_hook_demo(
    output_path: Path,
    *,
    lane: HookDemoLane,
    variant: DemoVariant,
    sample_rate: int,
    swing: float,
    master_gain: float,
    stereo_width: float,
    arrangement_lift: float,
    drum_bus_gain: float,
    guide_vocal_gain: float,
) -> None:
    total_frames = int(sample_rate * variant.duration_seconds)
    buffer = [0.0] * total_frames
    seconds_per_beat = 60.0 / variant.tempo_bpm
    seconds_per_bar = seconds_per_beat * 4
    total_bars = max(1, math.ceil(variant.duration_seconds / seconds_per_bar))
    energy_points = normalize_energy_arc(lane.energy_arc)

    for bar_index in range(total_bars):
        bar_start = bar_index * seconds_per_bar
        chord = variant.chord_loop[bar_index % len(variant.chord_loop)]
        chord_notes = chord_to_midi(lane.key, lane.mode, chord)
        progress = bar_start / variant.duration_seconds if variant.duration_seconds else 0.0
        level = interpolate_energy(energy_points, progress)
        lift = section_lift(progress, arrangement_lift)
        for note in chord_notes:
            add_sine_event(
                buffer,
                start_time=bar_start,
                duration=seconds_per_bar,
                frequency=midi_to_frequency(note),
                amplitude=0.055 * level * lift,
                sample_rate=sample_rate,
                attack=0.02,
                release=0.12,
            )
        add_sine_event(
            buffer,
            start_time=bar_start,
            duration=seconds_per_bar,
            frequency=midi_to_frequency(chord_notes[0] - 12),
            amplitude=0.038 * level * max(1.0, lift * 0.92),
            sample_rate=sample_rate,
            attack=0.01,
            release=0.08,
            tremolo_hz=0.75,
            tremolo_depth=0.18,
        )

    render_bass(buffer, lane, variant, sample_rate, energy_points, arrangement_lift=arrangement_lift)
    render_motif(buffer, lane, variant, sample_rate, energy_points, swing=swing, arrangement_lift=arrangement_lift)
    render_drums(buffer, variant, sample_rate, energy_points, swing=swing, drum_bus_gain=drum_bus_gain, arrangement_lift=arrangement_lift)
    if variant.guide_vocal:
        render_guide_vocal(
            buffer,
            lane,
            variant,
            sample_rate,
            energy_points,
            guide_vocal_gain=guide_vocal_gain,
            arrangement_lift=arrangement_lift,
        )

    write_wav(output_path, buffer, sample_rate=sample_rate, master_gain=master_gain, stereo_width=stereo_width)


def normalize_energy_arc(values: tuple[float, ...]) -> tuple[float, ...]:
    if not values:
        return (0.6, 0.85, 1.0)
    return tuple(max(0.15, min(1.1, float(value))) for value in values)


def interpolate_energy(arc: tuple[float, ...], progress: float) -> float:
    if len(arc) == 1:
        return arc[0]
    clamped = max(0.0, min(1.0, progress))
    position = clamped * (len(arc) - 1)
    lower = math.floor(position)
    upper = min(len(arc) - 1, lower + 1)
    if lower == upper:
        return arc[lower]
    fraction = position - lower
    return arc[lower] + (arc[upper] - arc[lower]) * fraction


def render_bass(
    buffer: list[float],
    lane: HookDemoLane,
    variant: DemoVariant,
    sample_rate: int,
    energy_points: tuple[float, ...],
    *,
    arrangement_lift: float,
) -> None:
    seconds_per_beat = 60.0 / variant.tempo_bpm
    seconds_per_bar = seconds_per_beat * 4
    total_beats = int(math.ceil(variant.duration_seconds / seconds_per_beat))
    for beat_index in range(total_beats):
        beat_time = beat_index * seconds_per_beat
        chord = variant.chord_loop[int(beat_time / seconds_per_bar) % len(variant.chord_loop)]
        root = chord_to_midi(lane.key, lane.mode, chord)[0] - 24
        amplitude = 0.07 if beat_index % 4 == 0 else 0.045
        progress = beat_time / variant.duration_seconds if variant.duration_seconds else 0.0
        level = interpolate_energy(energy_points, progress)
        lift = section_lift(progress, arrangement_lift)
        duration = seconds_per_beat * (0.82 if beat_index % 2 == 0 else 0.62)
        add_sine_event(
            buffer,
            start_time=beat_time,
            duration=duration,
            frequency=midi_to_frequency(root),
            amplitude=amplitude * level * max(1.0, lift * 0.9),
            sample_rate=sample_rate,
            attack=0.004,
            release=0.08,
            tremolo_hz=2.0,
            tremolo_depth=0.06,
        )


def render_motif(
    buffer: list[float],
    lane: HookDemoLane,
    variant: DemoVariant,
    sample_rate: int,
    energy_points: tuple[float, ...],
    *,
    swing: float,
    arrangement_lift: float,
) -> None:
    seconds_per_beat = 60.0 / variant.tempo_bpm
    total_bars = max(1, math.ceil(variant.duration_seconds / (seconds_per_beat * 4)))
    motif_time = 0.0
    rhythm_index = 0
    note_index = 0
    for bar_index in range(total_bars):
        chord = variant.chord_loop[bar_index % len(variant.chord_loop)]
        chord_notes = chord_to_midi(lane.key, lane.mode, chord)
        for _ in range(4):
            beat_duration = variant.motif_rhythm[rhythm_index % len(variant.motif_rhythm)] * seconds_per_beat
            beat_duration = max(seconds_per_beat * 0.25, beat_duration)
            start_time = motif_time + apply_swing(note_index, seconds_per_beat, swing)
            if start_time >= variant.duration_seconds:
                return
            scale_note = scale_step_to_midi(lane.key, lane.mode, variant.motif_steps[note_index % len(variant.motif_steps)], octave_shift=1)
            note = nearest_chord_tone(scale_note, chord_notes)
            progress = start_time / variant.duration_seconds if variant.duration_seconds else 0.0
            level = interpolate_energy(energy_points, progress)
            lift = section_lift(progress, arrangement_lift)
            add_lead_event(
                buffer,
                start_time=start_time,
                duration=min(beat_duration * 0.95, max(0.12, variant.duration_seconds - start_time)),
                frequency=midi_to_frequency(note),
                amplitude=0.075 * level * lift,
                sample_rate=sample_rate,
                vibrato_hz=5.4,
                vibrato_depth=0.006,
            )
            motif_time += beat_duration
            rhythm_index += 1
            note_index += 1
            if motif_time >= variant.duration_seconds:
                return


def render_guide_vocal(
    buffer: list[float],
    lane: HookDemoLane,
    variant: DemoVariant,
    sample_rate: int,
    energy_points: tuple[float, ...],
    *,
    guide_vocal_gain: float,
    arrangement_lift: float,
) -> None:
    seconds_per_beat = 60.0 / variant.tempo_bpm
    lyric_tokens = build_lyric_tokens(lane)
    if not lyric_tokens:
        lyric_tokens = ("oh", "na", "on", "neon")

    total_token_beats = 0.0
    token_beats: list[float] = []
    for index, token in enumerate(lyric_tokens):
        beats = lyric_token_beats(token, emphasis=index % 4 == 0)
        token_beats.append(beats)
        total_token_beats += beats

    if total_token_beats <= 0:
        return

    gap_seconds = seconds_per_beat * 0.08
    available_seconds = max(0.0, variant.duration_seconds - gap_seconds * max(len(lyric_tokens) - 1, 0))
    time_scale = available_seconds / (total_token_beats * seconds_per_beat)
    phrase_time = 0.0

    for note_index, token in enumerate(lyric_tokens):
        length = max(0.12, token_beats[note_index] * seconds_per_beat * time_scale)
        start_time = phrase_time + min(seconds_per_beat * 0.08, gap_seconds)
        if start_time >= variant.duration_seconds:
            return
        melodic_note = scale_step_to_midi(
            lane.key,
            lane.mode,
            variant.motif_steps[note_index % len(variant.motif_steps)],
            octave_shift=2,
        )
        progress = start_time / variant.duration_seconds if variant.duration_seconds else 0.0
        level = interpolate_energy(energy_points, progress)
        lift = section_lift(progress, arrangement_lift)
        render_lyric_token(
            buffer,
            token=token,
            start_time=start_time,
            duration=min(length, max(0.14, variant.duration_seconds - start_time)),
            frequency=midi_to_frequency(melodic_note),
            amplitude=0.05 * level * guide_vocal_gain * max(0.92, lift),
            sample_rate=sample_rate,
        )
        phrase_time += length + gap_seconds


def build_lyric_tokens(lane: HookDemoLane) -> tuple[str, ...]:
    lyric_lines = lane.lyrics_lines or infer_lyrics_lines(lane.intended_clip_sections)
    tokens: list[str] = []
    for line in lyric_lines:
        for token in re.findall(r"[A-Za-z']+", line.lower()):
            normalized = token.strip("'")
            if normalized:
                tokens.append(normalized)
    return tuple(tokens)


def infer_lyrics_lines(intended_sections: tuple[str, ...]) -> tuple[str, ...]:
    lyric_lines: list[str] = []
    for section in intended_sections:
        _, _, payload = section.partition(":")
        if not payload:
            continue
        for fragment in payload.split("/"):
            cleaned = fragment.strip()
            lowered = cleaned.lower()
            if not cleaned:
                continue
            if any(marker in lowered for marker in ("hook repeat", "post-chorus", "silence-drop", "final chorus", "drum", "loop")):
                continue
            lyric_lines.append(cleaned)
    return tuple(lyric_lines)


def lyric_token_beats(token: str, *, emphasis: bool) -> float:
    vowel_groups = re.findall(r"[aeiouy]+", token.lower())
    beats = 0.45 + 0.22 * max(1, len(vowel_groups))
    if len(token) >= 6:
        beats += 0.08
    if emphasis:
        beats += 0.14
    return beats


def render_lyric_token(
    buffer: list[float],
    *,
    token: str,
    start_time: float,
    duration: float,
    frequency: float,
    amplitude: float,
    sample_rate: int,
) -> None:
    consonant_ratio = min(0.18, 0.025 * len(re.findall(r"[^aeiouy]", token.lower())))
    consonant_duration = duration * consonant_ratio
    vowel_start = start_time + consonant_duration * 0.35
    vowel_duration = max(0.08, duration - consonant_duration)
    vowel_profile = infer_vowel_profile(token)
    if consonant_duration > 0.01:
        add_noise_event(
            buffer,
            start_time=start_time,
            duration=consonant_duration,
            frequency=2400.0 + 500.0 * vowel_profile[2],
            amplitude=amplitude * 0.22,
            sample_rate=sample_rate,
            attack=0.001,
            release=min(0.03, consonant_duration * 0.6),
        )
    add_vocal_event(
        buffer,
        start_time=vowel_start,
        duration=vowel_duration,
        frequency=frequency,
        amplitude=amplitude,
        sample_rate=sample_rate,
        vowel_profile=vowel_profile,
        vibrato_hz=6.1,
        vibrato_depth=0.01,
    )


def infer_vowel_profile(token: str) -> tuple[float, float, float]:
    lowered = token.lower()
    if any(vowel in lowered for vowel in ("ee", "ea", "ie", "i", "y")):
        return (1.9, 3.3, 0.42)
    if any(vowel in lowered for vowel in ("oo", "ou", "u")):
        return (1.1, 2.2, 0.24)
    if any(vowel in lowered for vowel in ("o", "oa")):
        return (1.35, 2.5, 0.3)
    if any(vowel in lowered for vowel in ("e", "ae")):
        return (1.6, 2.9, 0.36)
    return (1.45, 2.7, 0.32)


def render_drums(
    buffer: list[float],
    variant: DemoVariant,
    sample_rate: int,
    energy_points: tuple[float, ...],
    *,
    swing: float,
    drum_bus_gain: float,
    arrangement_lift: float,
) -> None:
    seconds_per_beat = 60.0 / variant.tempo_bpm
    half_beat = seconds_per_beat / 2
    total_half_beats = int(math.ceil(variant.duration_seconds / half_beat))
    for index in range(total_half_beats):
        hit_time = index * half_beat
        if hit_time >= variant.duration_seconds:
            return
        progress = hit_time / variant.duration_seconds if variant.duration_seconds else 0.0
        level = interpolate_energy(energy_points, progress)
        lift = section_lift(progress, arrangement_lift)
        if index % 4 == 0:
            add_kick(buffer, hit_time, sample_rate, amplitude=0.22 * level * drum_bus_gain * max(1.0, lift * 0.95))
        if index % 4 == 2:
            add_snare(buffer, hit_time, sample_rate, amplitude=0.11 * level * drum_bus_gain * lift)
        hat_time = hit_time + apply_swing(index, seconds_per_beat, swing) * 0.35
        hat_gain = 0.045 if index % 2 else 0.03
        add_hat(buffer, hat_time, sample_rate, amplitude=hat_gain * level * drum_bus_gain * max(0.9, lift * 0.88))


def section_lift(progress: float, arrangement_lift: float) -> float:
    if progress < 0.18:
        return 0.9
    if progress < 0.55:
        return 1.0
    if progress < 0.82:
        return max(1.0, arrangement_lift * 0.96)
    return max(1.0, arrangement_lift)


def add_kick(buffer: list[float], start_time: float, sample_rate: int, *, amplitude: float) -> None:
    add_sine_event(
        buffer,
        start_time=start_time,
        duration=0.18,
        frequency=58.0,
        amplitude=amplitude,
        sample_rate=sample_rate,
        attack=0.001,
        release=0.12,
        pitch_drop_hz=42.0,
    )


def add_snare(buffer: list[float], start_time: float, sample_rate: int, *, amplitude: float) -> None:
    add_noise_event(
        buffer,
        start_time=start_time,
        duration=0.14,
        frequency=1900.0,
        amplitude=amplitude,
        sample_rate=sample_rate,
        attack=0.001,
        release=0.07,
    )


def add_hat(buffer: list[float], start_time: float, sample_rate: int, *, amplitude: float) -> None:
    add_noise_event(
        buffer,
        start_time=start_time,
        duration=0.05,
        frequency=4200.0,
        amplitude=amplitude,
        sample_rate=sample_rate,
        attack=0.0005,
        release=0.02,
    )


def add_vocal_event(
    buffer: list[float],
    *,
    start_time: float,
    duration: float,
    frequency: float,
    amplitude: float,
    sample_rate: int,
    vowel_profile: tuple[float, float, float],
    vibrato_hz: float,
    vibrato_depth: float,
) -> None:
    start_index, end_index = resolve_frame_window(buffer, start_time, duration, sample_rate)
    if end_index <= start_index:
        return
    length = end_index - start_index
    attack_frames = max(1, int(sample_rate * 0.008))
    release_frames = max(1, int(sample_rate * 0.09))
    formant_one, formant_two, breath = vowel_profile
    for offset in range(length):
        current_time = offset / sample_rate
        env = envelope(offset, length, attack_frames, release_frames)
        vibrato = 1 + vibrato_depth * math.sin(2 * math.pi * vibrato_hz * current_time)
        fundamental = math.sin(2 * math.pi * frequency * vibrato * current_time)
        octave = math.sin(2 * math.pi * frequency * 2.0 * current_time)
        formant_a = math.sin(2 * math.pi * frequency * formant_one * current_time)
        formant_b = math.sin(2 * math.pi * frequency * formant_two * current_time)
        airy = math.sin(2 * math.pi * frequency * 0.5 * current_time)
        composite = (
            0.48 * fundamental
            + 0.18 * octave
            + 0.18 * formant_a
            + 0.1 * formant_b
            + 0.06 * airy * breath
        )
        buffer[start_index + offset] += amplitude * env * composite


def add_lead_event(
    buffer: list[float],
    *,
    start_time: float,
    duration: float,
    frequency: float,
    amplitude: float,
    sample_rate: int,
    vibrato_hz: float,
    vibrato_depth: float,
    overtone_blend: float = 0.18,
) -> None:
    start_index, end_index = resolve_frame_window(buffer, start_time, duration, sample_rate)
    if end_index <= start_index:
        return
    length = end_index - start_index
    attack_frames = max(1, int(sample_rate * 0.01))
    release_frames = max(1, int(sample_rate * 0.08))
    for offset in range(length):
        current_time = offset / sample_rate
        env = envelope(offset, length, attack_frames, release_frames)
        vibrato = 1 + vibrato_depth * math.sin(2 * math.pi * vibrato_hz * current_time)
        fundamental = math.sin(2 * math.pi * frequency * vibrato * current_time)
        overtone = math.sin(2 * math.pi * frequency * 2.0 * current_time)
        buffer[start_index + offset] += amplitude * env * ((1 - overtone_blend) * fundamental + overtone_blend * overtone)


def add_sine_event(
    buffer: list[float],
    *,
    start_time: float,
    duration: float,
    frequency: float,
    amplitude: float,
    sample_rate: int,
    attack: float,
    release: float,
    tremolo_hz: float = 0.0,
    tremolo_depth: float = 0.0,
    pitch_drop_hz: float = 0.0,
) -> None:
    start_index, end_index = resolve_frame_window(buffer, start_time, duration, sample_rate)
    if end_index <= start_index:
        return
    length = end_index - start_index
    attack_frames = max(1, int(sample_rate * attack))
    release_frames = max(1, int(sample_rate * release))
    for offset in range(length):
        current_time = offset / sample_rate
        env = envelope(offset, length, attack_frames, release_frames)
        tremolo = 1.0
        if tremolo_hz and tremolo_depth:
            tremolo = 1 - tremolo_depth + tremolo_depth * (0.5 + 0.5 * math.sin(2 * math.pi * tremolo_hz * current_time))
        current_frequency = max(20.0, frequency - pitch_drop_hz * (offset / max(length - 1, 1)))
        buffer[start_index + offset] += amplitude * env * tremolo * math.sin(2 * math.pi * current_frequency * current_time)


def add_noise_event(
    buffer: list[float],
    *,
    start_time: float,
    duration: float,
    frequency: float,
    amplitude: float,
    sample_rate: int,
    attack: float,
    release: float,
) -> None:
    start_index, end_index = resolve_frame_window(buffer, start_time, duration, sample_rate)
    if end_index <= start_index:
        return
    length = end_index - start_index
    attack_frames = max(1, int(sample_rate * attack))
    release_frames = max(1, int(sample_rate * release))
    for offset in range(length):
        current_time = offset / sample_rate
        env = envelope(offset, length, attack_frames, release_frames)
        metallic = math.sin(2 * math.pi * frequency * current_time)
        air = math.sin(2 * math.pi * frequency * 1.71 * current_time)
        buffer[start_index + offset] += amplitude * env * (0.6 * metallic + 0.4 * air)


def resolve_frame_window(buffer: list[float], start_time: float, duration: float, sample_rate: int) -> tuple[int, int]:
    start_index = max(0, int(start_time * sample_rate))
    end_index = min(len(buffer), int((start_time + duration) * sample_rate))
    return start_index, end_index


def envelope(index: int, total_frames: int, attack_frames: int, release_frames: int) -> float:
    attack = min(1.0, index / attack_frames) if attack_frames else 1.0
    tail_frames = total_frames - index - 1
    release = min(1.0, tail_frames / release_frames) if release_frames else 1.0
    return max(0.0, min(1.0, attack, release))


def chord_to_midi(key: str, mode: str, token: str) -> tuple[int, int, int]:
    scale = MODE_INTERVALS.get(mode.lower())
    if scale is None:
        raise ValueError(f"Unsupported mode: {mode}")
    numeral = re.sub(r"[^ivIV]+", "", token)
    if not numeral:
        raise ValueError(f"Unsupported chord token: {token}")
    degree = ROMAN_TO_DEGREE.get(numeral.lower())
    if degree is None:
        raise ValueError(f"Unsupported chord token: {token}")
    root = scale_step_to_midi(key, mode, degree, octave_shift=0)
    third = scale_step_to_midi(key, mode, degree + 2, octave_shift=0)
    fifth = scale_step_to_midi(key, mode, degree + 4, octave_shift=0)
    return (root, third, fifth)


def nearest_chord_tone(note: int, chord_notes: tuple[int, int, int]) -> int:
    options = [tone + octave for tone in chord_notes for octave in (-12, 0, 12)]
    return min(options, key=lambda candidate: abs(candidate - note))


def scale_step_to_midi(key: str, mode: str, step: int, *, octave_shift: int) -> int:
    scale = MODE_INTERVALS.get(mode.lower())
    if scale is None:
        raise ValueError(f"Unsupported mode: {mode}")
    semitone = NOTE_TO_SEMITONE.get(key.strip().lower())
    if semitone is None:
        raise ValueError(f"Unsupported key: {key}")
    octave_steps, scale_index = divmod(step, len(scale))
    return 60 + semitone + scale[scale_index] + 12 * (octave_shift + octave_steps)


def midi_to_frequency(note: int) -> float:
    return 440.0 * math.pow(2.0, (note - 69) / 12)


def apply_swing(index: int, seconds_per_beat: float, swing: float) -> float:
    if index % 2 == 0:
        return 0.0
    return seconds_per_beat * 0.5 * max(0.0, min(0.24, swing))


def write_wav(path: Path, buffer: list[float], *, sample_rate: int, master_gain: float, stereo_width: float) -> None:
    peak = max((abs(sample) for sample in buffer), default=1.0)
    scale = master_gain / peak if peak > master_gain and peak > 0 else master_gain
    width = max(0.0, min(0.95, stereo_width))
    delay_frames = max(1, int(sample_rate * 0.0035))
    frames = bytearray()
    for index, sample in enumerate(buffer):
        delayed = buffer[index - delay_frames] if index >= delay_frames else 0.0
        mid = sample * scale
        side = (sample - delayed) * scale * width * 0.5
        left = max(-1.0, min(1.0, mid + side))
        right = max(-1.0, min(1.0, mid - side))
        frames.extend(int(left * MAX_INT16).to_bytes(SAMPLE_WIDTH_BYTES, byteorder="little", signed=True))
        frames.extend(int(right * MAX_INT16).to_bytes(SAMPLE_WIDTH_BYTES, byteorder="little", signed=True))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(SAMPLE_WIDTH_BYTES)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate local hook-demo batches across multiple song lanes.")
    parser.add_argument("config", nargs="?", default="config/hook_demo.toml", help="Path to hook-demo TOML config")
    args = parser.parse_args(argv)
    result = run_hook_demo_batch(Path(args.config))
    print(
        json.dumps(
            {
                "demo_dir": str(result.demo_dir),
                "manifest_path": str(result.manifest_path),
                "demo_count": len(result.demos),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
