from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
import wave
from dataclasses import asdict, dataclass
from pathlib import Path

SAMPLE_WIDTH_BYTES = 2
MAX_INT16 = 32767
DEFAULT_SAMPLE_RATE = 16_000
DEFAULT_SWING = 0.08
DEFAULT_MASTER_GAIN = 0.85
DEFAULT_DURATION_SECONDS = 16.0
DEFAULT_DEMO_COUNT = 2
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
    clip_reference_scope: str | None
    intended_clip_sections: tuple[str, ...]
    provenance_notes: tuple[str, ...]


@dataclass(frozen=True)
class HookDemoBatchResult:
    demo_dir: Path
    manifest_path: Path
    demos: tuple[HookDemoResult, ...]


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
            render_hook_demo(audio_path, lane=lane, variant=variant, sample_rate=config.sample_rate, swing=config.swing, master_gain=config.master_gain)
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
                    clip_reference_scope=lane.clip_reference_scope,
                    intended_clip_sections=lane.intended_clip_sections,
                    provenance_notes=lane.provenance_notes,
                )
            )

    manifest = {
        "config_path": str(config_path),
        "demo_dir": str(config.demo_dir),
        "run_command": f"PYTHONPATH=src python3 scripts/run_hook_demo_batch.py {config_path}",
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
        level = interpolate_energy(energy_points, bar_start / variant.duration_seconds)
        for note in chord_notes:
            add_sine_event(
                buffer,
                start_time=bar_start,
                duration=seconds_per_bar,
                frequency=midi_to_frequency(note),
                amplitude=0.055 * level,
                sample_rate=sample_rate,
                attack=0.02,
                release=0.12,
            )
        add_sine_event(
            buffer,
            start_time=bar_start,
            duration=seconds_per_bar,
            frequency=midi_to_frequency(chord_notes[0] - 12),
            amplitude=0.038 * level,
            sample_rate=sample_rate,
            attack=0.01,
            release=0.08,
            tremolo_hz=0.75,
            tremolo_depth=0.18,
        )

    render_bass(buffer, lane, variant, sample_rate, energy_points)
    render_motif(buffer, lane, variant, sample_rate, energy_points, swing=swing)
    render_drums(buffer, variant, sample_rate, energy_points, swing=swing)
    if variant.guide_vocal:
        render_guide_vocal(buffer, lane, variant, sample_rate, energy_points)

    write_wav(output_path, buffer, sample_rate=sample_rate, master_gain=master_gain)


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
) -> None:
    seconds_per_beat = 60.0 / variant.tempo_bpm
    seconds_per_bar = seconds_per_beat * 4
    total_beats = int(math.ceil(variant.duration_seconds / seconds_per_beat))
    for beat_index in range(total_beats):
        beat_time = beat_index * seconds_per_beat
        chord = variant.chord_loop[int(beat_time / seconds_per_bar) % len(variant.chord_loop)]
        root = chord_to_midi(lane.key, lane.mode, chord)[0] - 24
        amplitude = 0.07 if beat_index % 4 == 0 else 0.045
        level = interpolate_energy(energy_points, beat_time / variant.duration_seconds)
        duration = seconds_per_beat * (0.82 if beat_index % 2 == 0 else 0.62)
        add_sine_event(
            buffer,
            start_time=beat_time,
            duration=duration,
            frequency=midi_to_frequency(root),
            amplitude=amplitude * level,
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
            level = interpolate_energy(energy_points, start_time / variant.duration_seconds)
            add_lead_event(
                buffer,
                start_time=start_time,
                duration=min(beat_duration * 0.95, max(0.12, variant.duration_seconds - start_time)),
                frequency=midi_to_frequency(note),
                amplitude=0.075 * level,
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
) -> None:
    seconds_per_beat = 60.0 / variant.tempo_bpm
    phrase_time = 0.0
    note_index = 0
    syllable_lengths = (1.0, 0.5, 0.5, 1.5)
    while phrase_time < variant.duration_seconds:
        length = syllable_lengths[note_index % len(syllable_lengths)] * seconds_per_beat
        start_time = phrase_time + seconds_per_beat * 0.12
        if start_time >= variant.duration_seconds:
            return
        melodic_note = scale_step_to_midi(
            lane.key,
            lane.mode,
            variant.motif_steps[note_index % len(variant.motif_steps)],
            octave_shift=2,
        )
        level = interpolate_energy(energy_points, start_time / variant.duration_seconds)
        add_lead_event(
            buffer,
            start_time=start_time,
            duration=min(length, max(0.18, variant.duration_seconds - start_time)),
            frequency=midi_to_frequency(melodic_note),
            amplitude=0.048 * level,
            sample_rate=sample_rate,
            vibrato_hz=6.2,
            vibrato_depth=0.012,
            overtone_blend=0.35,
        )
        phrase_time += length + seconds_per_beat * 0.25
        note_index += 1


def render_drums(
    buffer: list[float],
    variant: DemoVariant,
    sample_rate: int,
    energy_points: tuple[float, ...],
    *,
    swing: float,
) -> None:
    seconds_per_beat = 60.0 / variant.tempo_bpm
    half_beat = seconds_per_beat / 2
    total_half_beats = int(math.ceil(variant.duration_seconds / half_beat))
    for index in range(total_half_beats):
        hit_time = index * half_beat
        if hit_time >= variant.duration_seconds:
            return
        level = interpolate_energy(energy_points, hit_time / variant.duration_seconds)
        if index % 4 == 0:
            add_kick(buffer, hit_time, sample_rate, amplitude=0.22 * level)
        if index % 4 == 2:
            add_snare(buffer, hit_time, sample_rate, amplitude=0.11 * level)
        hat_time = hit_time + apply_swing(index, seconds_per_beat, swing) * 0.35
        add_hat(buffer, hat_time, sample_rate, amplitude=0.045 * level if index % 2 else 0.03 * level)


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


def write_wav(path: Path, buffer: list[float], *, sample_rate: int, master_gain: float) -> None:
    peak = max((abs(sample) for sample in buffer), default=1.0)
    scale = master_gain / peak if peak > master_gain and peak > 0 else master_gain
    frames = bytearray()
    for sample in buffer:
        clipped = max(-1.0, min(1.0, sample * scale))
        frames.extend(int(clipped * MAX_INT16).to_bytes(SAMPLE_WIDTH_BYTES, byteorder="little", signed=True))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
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
