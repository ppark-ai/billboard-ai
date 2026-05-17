from __future__ import annotations

import csv
import json
import math
import re
import tomllib
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .cycle_analysis import build_cycle_report

TITLE_ALIASES = {
    "song",
    "song_title",
    "songtitle",
    "title",
}
ARTIST_ALIASES = {
    "artist",
    "artists",
    "artist_s",
    "artist_name",
}
RANK_ALIASES = {
    "rank",
    "chart_rank",
    "position",
}
WEEKS_ALIASES = {
    "weeks",
    "weeks_on_chart",
    "weeksonchart",
}
PEAK_ALIASES = {
    "peak",
    "peak_position",
    "peak_pos",
    "peakposition",
}
GENRE_ALIASES = {
    "genre",
    "primary_genre",
}
TRANSITION_YEARS = {1991, 1992, 2005, 2006, 2012, 2013, 2020, 2021}


@dataclass(frozen=True)
class PopularityScore:
    score: float
    year_end_score: float
    peak_score: float
    weeks_score: float
    p95_weeks_in_year: float


@dataclass(frozen=True)
class ConfidenceAssessment:
    score: float
    label: str


@dataclass(frozen=True)
class PipelineResult:
    dataset_path: Path
    summary_path: Path
    rows: int
    cycle_analysis_path: Path | None = None


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = value.replace("&", " and ")
    value = re.sub(r"['’]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_artist(value: str) -> str:
    primary_artist = re.split(r"\b(?:feat\.?|featuring|with)\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    return normalize_text(primary_artist)


def detect_field(fieldnames: Iterable[str], aliases: set[str], label: str) -> str:
    normalized = {_normalize_field_name(name): name for name in fieldnames}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    raise ValueError(f"Missing required column for {label}: expected one of {sorted(aliases)}")


def _normalize_field_name(value: str) -> str:
    return normalize_text(value).replace(" ", "_")


def _round(value: float) -> float:
    return round(value, 4)


def _parse_int(value: str | int | None, label: str) -> int:
    if value is None or value == "":
        raise ValueError(f"Missing integer value for {label}")
    return int(str(value).strip())


def _infer_year(path: Path) -> int:
    match = re.search(r"(19\d{2}|20\d{2})", path.stem)
    if not match:
        raise ValueError(f"Could not infer year from filename: {path}")
    return int(match.group(1))


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _compute_quantile(values: list[int], quantile: float) -> float:
    if not values:
        return 1.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    index = (len(ordered) - 1) * quantile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(ordered[lower])
    fraction = index - lower
    return float(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction)


def load_genre_lookup(path: Path | None) -> dict[tuple[str, str], str]:
    if path is None:
        return {}
    rows = _load_rows(path)
    lookup: dict[tuple[str, str], str] = {}
    for row in rows:
        title = row.get("title") or row.get("song")
        artist = row.get("artist")
        genre = row.get("genre")
        if not title or not artist or not genre:
            continue
        lookup[(normalize_text(title), normalize_artist(artist))] = genre.strip().lower()
    return lookup


def get_era_bucket(year: int) -> str:
    if 1958 <= year <= 1990:
        return "1958-1990"
    if 1991 <= year <= 2004:
        return "1991-2004"
    if 2005 <= year <= 2012:
        return "2005-2012"
    if 2013 <= year <= 2019:
        return "2013-2019"
    return "2020+"


def compute_popularity_score(
    chart_rank: int,
    weeks_on_chart: int,
    peak_position: int,
    *,
    p95_weeks_in_year: float | None = None,
) -> PopularityScore:
    normalized_p95 = float(p95_weeks_in_year if p95_weeks_in_year and p95_weeks_in_year > 0 else max(weeks_on_chart, 1))
    year_end_score = 1 - math.pow((chart_rank - 1) / 99, 0.65)
    peak_score = 1 - math.pow((peak_position - 1) / 99, 0.55)
    weeks_score = min(1.0, math.log1p(weeks_on_chart) / math.log1p(normalized_p95))
    score = 100 * (0.60 * year_end_score + 0.15 * peak_score + 0.25 * weeks_score)
    return PopularityScore(
        score=_round(score),
        year_end_score=_round(year_end_score),
        peak_score=_round(peak_score),
        weeks_score=_round(weeks_score),
        p95_weeks_in_year=_round(normalized_p95),
    )


def compute_confidence_assessment(
    *,
    year: int,
    genre: str | None,
    weeks_imputed: bool = False,
    peak_imputed: bool = False,
    weak_genre_source: bool = False,
    proxies_used: bool = False,
    proxy_coverage_ok: bool = True,
) -> ConfidenceAssessment:
    score = 1.0
    normalized_genre = (genre or "unknown").strip().lower()
    if weeks_imputed:
        score -= 0.20
    if peak_imputed:
        score -= 0.15
    if weak_genre_source or normalized_genre == "unknown":
        score -= 0.10
    if year in TRANSITION_YEARS:
        score -= 0.10
    if proxies_used and not proxy_coverage_ok:
        score -= 0.10

    score = max(0.0, _round(score))
    if score >= 0.85:
        label = "high"
    elif score >= 0.70:
        label = "medium"
    else:
        label = "low"
    return ConfidenceAssessment(score=score, label=label)


def _compute_percentile_map(values: list[float]) -> dict[float, float]:
    if not values:
        return {}
    if len(values) == 1:
        return {values[0]: 1.0}

    counts = Counter(values)
    mapping: dict[float, float] = {}
    seen = 0
    total = len(values)
    for value in sorted(counts):
        start_rank = seen + 1
        seen += counts[value]
        end_rank = seen
        average_rank = (start_rank + end_rank) / 2
        mapping[value] = _round((average_rank - 1) / (total - 1))
    return mapping


def _assign_percentiles(rows: list[dict[str, int | float | str]]) -> list[dict[str, int | float | str]]:
    rows_by_year: dict[int, list[dict[str, int | float | str]]] = {}
    rows_by_era: dict[str, list[dict[str, int | float | str]]] = {}
    for row in rows:
        rows_by_year.setdefault(int(row["year"]), []).append(row)
        rows_by_era.setdefault(str(row["era_bucket"]), []).append(row)

    year_maps = {
        year: _compute_percentile_map([float(row["popularity_score_raw_100"]) for row in group])
        for year, group in rows_by_year.items()
    }
    era_maps = {
        era: _compute_percentile_map([float(row["popularity_score_raw_100"]) for row in group])
        for era, group in rows_by_era.items()
    }

    for row in rows:
        raw_score = float(row["popularity_score_raw_100"])
        raw_year_percentile = year_maps[int(row["year"])] [raw_score]
        raw_era_percentile = era_maps[str(row["era_bucket"])] [raw_score]
        era_adjusted = _round(100 * (0.65 * raw_year_percentile + 0.35 * raw_era_percentile))
        row["raw_year_percentile"] = raw_year_percentile
        row["raw_era_percentile"] = raw_era_percentile
        row["popularity_score_era_adj_100"] = era_adjusted
        row["popularity_score"] = era_adjusted
        row["popularity_label"] = assign_popularity_label(era_adjusted)
    return rows


def assign_popularity_label(score: float) -> str:
    if score >= 90:
        return "canonical_hit"
    if score >= 75:
        return "major_hit"
    if score >= 60:
        return "solid_hit"
    if score >= 45:
        return "moderate_hit"
    if score >= 30:
        return "minor_hit"
    return "lower_impact_year_end_entry"


def process_year_file(
    path: Path,
    *,
    year: int | None = None,
    genre_lookup: dict[tuple[str, str], str] | None = None,
) -> list[dict[str, int | float | str]]:
    rows = _load_rows(path)
    if not rows:
        return []
    fieldnames = list(rows[0].keys())
    rank_field = detect_field(fieldnames, RANK_ALIASES, "chart rank")
    title_field = detect_field(fieldnames, TITLE_ALIASES, "title")
    artist_field = detect_field(fieldnames, ARTIST_ALIASES, "artist")
    weeks_field = detect_field(fieldnames, WEEKS_ALIASES, "weeks on chart")
    peak_field = detect_field(fieldnames, PEAK_ALIASES, "peak position")
    try:
        genre_field = detect_field(fieldnames, GENRE_ALIASES, "genre")
    except ValueError:
        genre_field = None

    year_value = year if year is not None else _infer_year(path)
    lookup = genre_lookup or {}

    parsed_rows: list[dict[str, int | str]] = []
    weeks_values: list[int] = []
    for raw_row in rows:
        title = str(raw_row[title_field]).strip()
        artist = str(raw_row[artist_field]).strip()
        title_norm = normalize_text(title)
        artist_norm = normalize_artist(artist)
        if genre_field and raw_row.get(genre_field):
            genre = str(raw_row[genre_field]).strip().lower()
        else:
            genre = lookup.get((title_norm, artist_norm), "unknown")
        if genre == "unknown":
            raise ValueError(
                f"Missing genre metadata for {title!r} by {artist!r}; provide a genre column or lookup entry"
            )

        weeks_on_chart = _parse_int(raw_row.get(weeks_field), "weeks on chart")
        parsed_row = {
            "year": year_value,
            "chart_rank": _parse_int(raw_row.get(rank_field), "chart rank"),
            "title": title,
            "artist": artist,
            "title_norm": title_norm,
            "artist_norm": artist_norm,
            "weeks_on_chart": weeks_on_chart,
            "peak_position": _parse_int(raw_row.get(peak_field), "peak position"),
            "genre": genre,
            "era_bucket": get_era_bucket(year_value),
        }
        weeks_values.append(weeks_on_chart)
        parsed_rows.append(parsed_row)

    p95_weeks_in_year = _compute_quantile(weeks_values, 0.95)
    normalized_rows: list[dict[str, int | float | str]] = []
    for parsed_row in parsed_rows:
        popularity = compute_popularity_score(
            chart_rank=int(parsed_row["chart_rank"]),
            weeks_on_chart=int(parsed_row["weeks_on_chart"]),
            peak_position=int(parsed_row["peak_position"]),
            p95_weeks_in_year=p95_weeks_in_year,
        )
        confidence = compute_confidence_assessment(year=year_value, genre=str(parsed_row["genre"]))
        normalized_rows.append(
            {
                **parsed_row,
                "weeks_p95_in_year": popularity.p95_weeks_in_year,
                "year_end_score": popularity.year_end_score,
                "peak_score": popularity.peak_score,
                "weeks_score": popularity.weeks_score,
                "popularity_score_raw_100": popularity.score,
                "raw_year_percentile": 0.0,
                "raw_era_percentile": 0.0,
                "popularity_score_era_adj_100": 0.0,
                "popularity_score": 0.0,
                "popularity_label": "pending_era_adjustment",
                "confidence_score": confidence.score,
                "confidence_label": confidence.label,
            }
        )
    return normalized_rows


def write_csv(path: Path, rows: list[dict[str, int | float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else [
        "year",
        "era_bucket",
        "chart_rank",
        "title",
        "artist",
        "title_norm",
        "artist_norm",
        "weeks_on_chart",
        "peak_position",
        "genre",
        "weeks_p95_in_year",
        "year_end_score",
        "peak_score",
        "weeks_score",
        "popularity_score_raw_100",
        "raw_year_percentile",
        "raw_era_percentile",
        "popularity_score_era_adj_100",
        "popularity_score",
        "popularity_label",
        "confidence_score",
        "confidence_label",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_from_config(config_path: Path) -> PipelineResult:
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)

    input_glob = config["input"]["yearly_glob"]
    dataset_path = Path(config["output"]["dataset_path"]).expanduser()
    summary_path = Path(config["output"]["summary_path"]).expanduser()
    cycle_analysis_path = Path(config["output"].get("cycle_analysis_path", dataset_path.with_name("cycle_analysis.json"))).expanduser()
    genre_lookup_path = Path(config["genres"]["lookup_csv"]).expanduser() if config.get("genres", {}).get("lookup_csv") else None
    rolling_window = int(config.get("analysis", {}).get("rolling_window", 3))

    genre_lookup = load_genre_lookup(genre_lookup_path)
    all_rows: list[dict[str, int | float | str]] = []
    glob_iterable = sorted(Path().glob(input_glob)) if not Path(input_glob).is_absolute() else sorted(Path("/").glob(input_glob.lstrip("/")))
    for file_path in glob_iterable:
        all_rows.extend(process_year_file(file_path, genre_lookup=genre_lookup))

    all_rows.sort(key=lambda row: (int(row["year"]), int(row["chart_rank"])))
    _assign_percentiles(all_rows)
    write_csv(dataset_path, all_rows)

    genre_counts = Counter(str(row["genre"]) for row in all_rows)
    summary = {
        "rows": len(all_rows),
        "years": sorted({int(row["year"]) for row in all_rows}),
        "genres": dict(sorted(genre_counts.items())),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    cycle_report = build_cycle_report(all_rows, rolling_window=rolling_window)
    cycle_analysis_path.parent.mkdir(parents=True, exist_ok=True)
    cycle_analysis_path.write_text(json.dumps(cycle_report, indent=2), encoding="utf-8")
    return PipelineResult(
        dataset_path=dataset_path,
        summary_path=summary_path,
        rows=len(all_rows),
        cycle_analysis_path=cycle_analysis_path,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build a normalized Billboard yearly analysis dataset.")
    parser.add_argument("config", nargs="?", default="config/settings.toml", help="Path to pipeline config TOML")
    args = parser.parse_args(argv)

    result = run_from_config(Path(args.config))
    print(json.dumps({
        "dataset_path": str(result.dataset_path),
        "summary_path": str(result.summary_path),
        "rows": result.rows,
        "cycle_analysis_path": str(result.cycle_analysis_path) if result.cycle_analysis_path else None,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
