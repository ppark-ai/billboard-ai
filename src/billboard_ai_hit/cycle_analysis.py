from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable, Mapping

TRAIT_FIELDS = ("chart_rank", "weeks_on_chart", "peak_position")
TRAIT_SCALES = {
    "chart_rank": 100.0,
    "weeks_on_chart": 52.0,
    "peak_position": 100.0,
}
PLACEHOLDER_NOTE = (
    "placeholder cycle-detection hooks emitted; replace recurrence scoring with spectral/autocorrelation analysis once richer feature coverage is available"
)
RECURRENCE_NOTE = "placeholder recurrence score blends genre-share overlap and weighted-trait similarity"


Row = Mapping[str, object]


def _round(value: float) -> float:
    return round(value, 4)


def _as_int(row: Row, field: str) -> int:
    return int(row[field])


def _as_float(row: Row, field: str) -> float:
    return float(row[field])


def _group_rows_by_year(rows: Iterable[Row]) -> dict[int, list[Row]]:
    grouped: dict[int, list[Row]] = defaultdict(list)
    for row in rows:
        grouped[_as_int(row, "year")].append(row)
    return dict(sorted(grouped.items()))


def _compute_genre_share(rows: list[Row]) -> dict[str, float]:
    if not rows:
        return {}
    counts = Counter(str(row.get("genre", "unknown")) for row in rows)
    total = len(rows)
    return {genre: _round(count / total) for genre, count in sorted(counts.items())}


def _compute_weighted_traits(rows: list[Row]) -> dict[str, float]:
    if not rows:
        return {field: 0.0 for field in TRAIT_FIELDS}
    total_weight = sum(max(_as_float(row, "popularity_score"), 1.0) for row in rows)
    if total_weight == 0:
        total_weight = float(len(rows))
    weighted: dict[str, float] = {}
    for field in TRAIT_FIELDS:
        weighted[field] = _round(
            sum(_as_float(row, field) * max(_as_float(row, "popularity_score"), 1.0) for row in rows) / total_weight
        )
    return weighted


def _summarize_year(year: int, rows: list[Row]) -> dict[str, object]:
    return {
        "year": year,
        "track_count": len(rows),
        "average_popularity_score": _round(sum(_as_float(row, "popularity_score") for row in rows) / len(rows)) if rows else 0.0,
        "genre_share": _compute_genre_share(rows),
        "popularity_weighted_traits": _compute_weighted_traits(rows),
    }


def _window_rows(grouped_rows: dict[int, list[Row]], start_index: int, rolling_window: int) -> tuple[list[int], list[Row]]:
    years = list(grouped_rows.keys())[start_index : start_index + rolling_window]
    rows: list[Row] = []
    for year in years:
        rows.extend(grouped_rows[year])
    return years, rows


def _build_rolling_windows(grouped_rows: dict[int, list[Row]], rolling_window: int) -> list[dict[str, object]]:
    years = list(grouped_rows.keys())
    if rolling_window <= 1 or len(years) < rolling_window:
        return []

    windows: list[dict[str, object]] = []
    for index in range(len(years) - rolling_window + 1):
        window_years, rows = _window_rows(grouped_rows, index, rolling_window)
        windows.append(
            {
                "window_start": window_years[0],
                "window_end": window_years[-1],
                "years": window_years,
                "genre_share": _compute_genre_share(rows),
                "popularity_weighted_traits": _compute_weighted_traits(rows),
            }
        )
    return windows


def _genre_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    genres = set(left) | set(right)
    if not genres:
        return 0.0
    distance = sum(abs(left.get(genre, 0.0) - right.get(genre, 0.0)) for genre in genres) / 2.0
    return max(0.0, 1.0 - distance)


def _trait_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    similarities: list[float] = []
    for field in TRAIT_FIELDS:
        scale = TRAIT_SCALES[field]
        difference = abs(left[field] - right[field])
        similarities.append(max(0.0, 1.0 - (difference / scale)))
    return sum(similarities) / len(similarities)


def _build_recurrence_candidates(yearly_metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for index, base in enumerate(yearly_metrics):
        for comparison in yearly_metrics[index + 1 :]:
            base_genre_share = dict(base["genre_share"])
            comparison_genre_share = dict(comparison["genre_share"])
            genre_similarity = _genre_similarity(base_genre_share, comparison_genre_share)
            trait_similarity = _trait_similarity(
                dict(base["popularity_weighted_traits"]),
                dict(comparison["popularity_weighted_traits"]),
            )
            score = _round(genre_similarity * 0.4 + trait_similarity * 0.6)
            if score < 0.9:
                continue
            shared_genres = sorted(set(base_genre_share) & set(comparison_genre_share))
            candidates.append(
                {
                    "base_year": int(base["year"]),
                    "comparison_year": int(comparison["year"]),
                    "score": score,
                    "shared_genres": shared_genres,
                    "notes": [RECURRENCE_NOTE],
                }
            )
    candidates.sort(key=lambda candidate: (-float(candidate["score"]), int(candidate["base_year"]), int(candidate["comparison_year"])))
    return candidates


def build_cycle_report(rows: Iterable[Row], *, rolling_window: int = 3) -> dict[str, object]:
    grouped_rows = _group_rows_by_year(rows)
    yearly_metrics = [_summarize_year(year, year_rows) for year, year_rows in grouped_rows.items()]
    return {
        "years": list(grouped_rows.keys()),
        "yearly_metrics": yearly_metrics,
        "rolling_windows": _build_rolling_windows(grouped_rows, rolling_window),
        "recurrence_candidates": _build_recurrence_candidates(yearly_metrics),
        "cycle_detection_notes": [PLACEHOLDER_NOTE],
    }
