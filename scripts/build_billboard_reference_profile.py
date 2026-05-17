from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path
from typing import Any

from billboard_ai_hit.hook_demo import _analyze_audio_features

DEFAULT_YEARS = (1965, 1975, 1985, 1995, 2005, 2015, 2024)
DEFAULT_TOP_N = 3
USER_AGENT = "Mozilla/5.0 (Hermes Billboard Reference Builder)"
REFERENCE_TRACKS_CSV = Path("data/reference/billboard_preview_reference_tracks.csv")
REFERENCE_PROFILE_JSON = Path("data/reference/billboard_preview_reference_profile.json")
PREVIEW_M4A_DIR = Path("data/reference/audio_previews/m4a")
PREVIEW_WAV_DIR = Path("data/reference/audio_previews/wav")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a Billboard preview-based reference profile for AI music quality gating."
    )
    parser.add_argument(
        "--years",
        default=",".join(str(year) for year in DEFAULT_YEARS),
        help="Comma-separated Billboard year-end years to sample",
    )
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="How many top year-end songs to sample per year")
    parser.add_argument(
        "--tracks-csv",
        default=str(REFERENCE_TRACKS_CSV),
        help="Where to write the per-track preview analysis CSV",
    )
    parser.add_argument(
        "--profile-json",
        default=str(REFERENCE_PROFILE_JSON),
        help="Where to write the aggregated reference-profile JSON",
    )
    parser.add_argument(
        "--preview-m4a-dir",
        default=str(PREVIEW_M4A_DIR),
        help="Directory for downloaded preview AAC/M4A files",
    )
    parser.add_argument(
        "--preview-wav-dir",
        default=str(PREVIEW_WAV_DIR),
        help="Directory for normalized preview WAV files",
    )
    args = parser.parse_args()

    years = tuple(int(part.strip()) for part in args.years.split(",") if part.strip())
    tracks_csv_path = Path(args.tracks_csv)
    profile_json_path = Path(args.profile_json)
    preview_m4a_dir = Path(args.preview_m4a_dir)
    preview_wav_dir = Path(args.preview_wav_dir)

    preview_m4a_dir.mkdir(parents=True, exist_ok=True)
    preview_wav_dir.mkdir(parents=True, exist_ok=True)
    tracks_csv_path.parent.mkdir(parents=True, exist_ok=True)
    profile_json_path.parent.mkdir(parents=True, exist_ok=True)

    track_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []

    for year in years:
        for entry in fetch_billboard_year_end_rows(year, args.top_n):
            try:
                preview = resolve_itunes_preview(entry["title"], entry["artist"])
            except Exception as exc:  # pragma: no cover - operational branch
                skipped_rows.append({**entry, "reason": f"preview lookup failed: {exc}"})
                continue
            if preview is None:
                skipped_rows.append({**entry, "reason": "no matching iTunes preview with previewUrl"})
                continue

            slug = slugify(f"{year}-{entry['rank']}-{entry['title']}-{entry['artist']}")
            m4a_path = preview_m4a_dir / f"{slug}.m4a"
            wav_path = preview_wav_dir / f"{slug}.wav"
            download_file(preview["preview_url"], m4a_path)
            transcode_to_wav(m4a_path, wav_path)
            features = _analyze_audio_features(wav_path)
            track_rows.append(
                {
                    **entry,
                    **preview,
                    "preview_m4a_path": str(m4a_path),
                    "preview_wav_path": str(wav_path),
                    **{key: round(float(value), 6) for key, value in features.items()},
                }
            )

    write_track_rows_csv(tracks_csv_path, track_rows)
    profile = build_reference_profile(years, args.top_n, track_rows, skipped_rows)
    profile_json_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "years": years,
                "top_n": args.top_n,
                "track_count": len(track_rows),
                "skipped_count": len(skipped_rows),
                "tracks_csv_path": str(tracks_csv_path),
                "profile_json_path": str(profile_json_path),
            },
            indent=2,
        )
    )


def fetch_billboard_year_end_rows(year: int, top_n: int) -> list[dict[str, Any]]:
    page_title = f"Billboard_Year-End_Hot_100_singles_of_{year}"
    url = f"https://en.wikipedia.org/wiki/{page_title}"
    html = fetch_text(url)
    table_match = re.search(r'<table class="wikitable[^>]*>(.*?)</table>', html, re.S)
    if not table_match:
        raise ValueError(f"Could not find wikitable on {url}")
    rows = re.findall(r"<tr>(.*?)</tr>", table_match.group(1), re.S)
    parsed: list[dict[str, Any]] = []
    for row in rows[1:]:
        cols = [clean_html(cell) for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if len(cols) < 3:
            continue
        rank_text, title, artist = cols[:3]
        rank_match = re.search(r"\d+", rank_text)
        if not rank_match:
            continue
        parsed.append(
            {
                "year": year,
                "rank": int(rank_match.group()),
                "title": title.strip('" '),
                "artist": artist,
                "source_url": url,
            }
        )
        if len(parsed) >= top_n:
            break
    if len(parsed) < top_n:
        raise ValueError(f"Expected {top_n} rows on {url}, found {len(parsed)}")
    return parsed


def resolve_itunes_preview(title: str, artist: str) -> dict[str, Any] | None:
    query = urllib.parse.urlencode({"term": f"{title} {artist}", "entity": "song", "limit": 10})
    payload = fetch_json(f"https://itunes.apple.com/search?{query}")
    results = payload.get("results", [])
    best_score = -1
    best: dict[str, Any] | None = None
    target_title = normalize_lookup(title)
    target_artist = normalize_lookup(artist)
    for item in results:
        preview_url = item.get("previewUrl")
        if not preview_url:
            continue
        score = 0
        track_name = normalize_lookup(str(item.get("trackName", "")))
        artist_name = normalize_lookup(str(item.get("artistName", "")))
        if track_name == target_title:
            score += 3
        elif target_title and target_title in track_name:
            score += 1
        if artist_name == target_artist:
            score += 3
        elif target_artist and target_artist in artist_name:
            score += 1
        if score > best_score:
            best_score = score
            best = {
                "matched_track_name": item.get("trackName"),
                "matched_artist_name": item.get("artistName"),
                "collection_name": item.get("collectionName"),
                "preview_url": preview_url,
                "itunes_track_view_url": item.get("trackViewUrl"),
                "itunes_track_id": item.get("trackId"),
            }
    return best


def build_reference_profile(
    years: tuple[int, ...],
    top_n: int,
    track_rows: list[dict[str, Any]],
    skipped_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    feature_fields = [
        "rms_level",
        "peak_level",
        "stereo_width_ratio",
        "dynamic_lift_ratio",
        "window_motion",
    ]
    feature_bands = {
        field: quantile_band([float(row[field]) for row in track_rows]) for field in feature_fields
    }
    feature_bands["tempo_bpm"] = {
        "minimum": 88.0,
        "target_low": 96.0,
        "target_high": 132.0,
        "maximum": 148.0,
        "source": "fallback_shortform_target_band",
    }
    feature_bands["duration_seconds"] = {
        "minimum": 8.0,
        "target_low": 10.0,
        "target_high": 16.0,
        "maximum": 22.0,
        "source": "fallback_shortform_target_band",
    }
    silence_values = [float(row["silence_ratio"]) for row in track_rows]
    silence_cap = max(0.18, quantile(silence_values, 0.9) * 2 if silence_values else 0.18)

    return {
        "profile_name": "billboard-year-end-preview-reference-v1",
        "profile_description": (
            "Preview-audio reference profile aggregated from public iTunes 30-second previews for selected "
            "Billboard year-end Hot 100 songs across eras. Audio feature bands are calibrated from the preview set; "
            "tempo and duration bands remain short-form-target fallbacks."
        ),
        "source_type": "itunes_preview_of_billboard_year_end_songs",
        "sample_years": list(years),
        "top_n_per_year": top_n,
        "reference_track_count": len(track_rows),
        "skipped_track_count": len(skipped_rows),
        "feature_bands": feature_bands,
        "feature_caps": {
            "silence_ratio": {
                "maximum": round(silence_cap, 6),
                "source": "preview_quantile_with_floor",
            }
        },
        "reference_tracks": track_rows,
        "skipped_tracks": skipped_rows,
    }


def quantile_band(values: list[float]) -> dict[str, Any]:
    if not values:
        raise ValueError("Cannot build quantile band from empty values")
    minimum = quantile(values, 0.10)
    target_low = quantile(values, 0.35)
    target_high = quantile(values, 0.65)
    maximum = quantile(values, 0.90)
    if minimum == target_low:
        target_low += 1e-6
    if target_high == maximum:
        maximum += 1e-6
    return {
        "minimum": round(minimum, 6),
        "target_low": round(target_low, 6),
        "target_high": round(target_high, 6),
        "maximum": round(maximum, 6),
        "source": "preview_quantiles_p10_p35_p65_p90",
    }


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def write_track_rows_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "year",
        "rank",
        "title",
        "artist",
        "matched_track_name",
        "matched_artist_name",
        "collection_name",
        "preview_url",
        "itunes_track_view_url",
        "itunes_track_id",
        "preview_m4a_path",
        "preview_wav_path",
        "duration_seconds",
        "sample_rate",
        "rms_level",
        "peak_level",
        "stereo_width_ratio",
        "dynamic_lift_ratio",
        "window_motion",
        "silence_ratio",
        "source_url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def transcode_to_wav(source_path: Path, target_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-ac",
            "2",
            "-ar",
            "22050",
            str(target_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def download_file(url: str, target_path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        target_path.write_bytes(response.read())


def fetch_json(url: str) -> dict[str, Any]:
    return json.loads(fetch_text(url))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def clean_html(value: str) -> str:
    value = re.sub(r"<sup.*?</sup>", " ", value, flags=re.S)
    value = re.sub(r"<.*?>", " ", value)
    return unescape(re.sub(r"\s+", " ", value)).strip()


def normalize_lookup(value: str) -> str:
    value = value.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", value)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


if __name__ == "__main__":
    main()
