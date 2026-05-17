from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from billboard_ai_hit.cycle_analysis import build_cycle_report
from billboard_ai_hit.pipeline import (
    compute_confidence_assessment,
    compute_popularity_score,
    process_year_file,
    run_from_config,
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_process_year_file_normalizes_fields_and_attaches_genre_and_raw_scores(tmp_path: Path) -> None:
    raw_path = tmp_path / "1965.csv"
    write_csv(
        raw_path,
        [
            {
                "Rank": 1,
                "Song Title": "(I Can't Get No) Satisfaction",
                "Artist(s)": "The Rolling Stones feat. Brian Jones",
                "Weeks on Chart": 14,
                "Peak Position": 1,
            },
            {
                "Rank": 2,
                "Song Title": "Help!",
                "Artist(s)": "The Beatles",
                "Weeks on Chart": 13,
                "Peak Position": 1,
            },
        ],
    )

    genre_lookup = {
        ("i cant get no satisfaction", "the rolling stones"): "rock",
        ("help", "the beatles"): "rock",
    }

    rows = process_year_file(raw_path, year=1965, genre_lookup=genre_lookup)

    assert rows[0]["title"] == "(I Can't Get No) Satisfaction"
    assert rows[0]["title_norm"] == "i cant get no satisfaction"
    assert rows[0]["artist"] == "The Rolling Stones feat. Brian Jones"
    assert rows[0]["artist_norm"] == "the rolling stones"
    assert rows[0]["genre"] == "rock"
    assert rows[0]["chart_rank"] == 1
    assert rows[0]["weeks_on_chart"] == 14
    assert rows[0]["peak_position"] == 1
    assert rows[0]["year"] == 1965
    assert rows[0]["era_bucket"] == "1958-1990"
    assert rows[0]["year_end_score"] > rows[1]["year_end_score"]
    assert rows[0]["popularity_score_raw_100"] > rows[1]["popularity_score_raw_100"]
    assert rows[0]["confidence_label"] == "high"


def test_process_year_file_requires_genre_metadata_when_lookup_cannot_fill_it(tmp_path: Path) -> None:
    raw_path = tmp_path / "1965.csv"
    write_csv(
        raw_path,
        [
            {
                "Rank": 1,
                "Song": "Help!",
                "Artist": "The Beatles",
                "Weeks": 13,
                "Peak": 1,
            }
        ],
    )

    with pytest.raises(ValueError, match="Missing genre metadata"):
        process_year_file(raw_path, year=1965, genre_lookup={})


def test_compute_popularity_score_rewards_rank_peak_and_longevity() -> None:
    top_song = compute_popularity_score(chart_rank=1, weeks_on_chart=20, peak_position=1, p95_weeks_in_year=20)
    mid_song = compute_popularity_score(chart_rank=45, weeks_on_chart=8, peak_position=12, p95_weeks_in_year=20)
    lower_song = compute_popularity_score(chart_rank=90, weeks_on_chart=3, peak_position=45, p95_weeks_in_year=20)

    assert top_song.score > mid_song.score > lower_song.score
    assert top_song.year_end_score > mid_song.year_end_score > lower_song.year_end_score
    assert top_song.peak_score > mid_song.peak_score > lower_song.peak_score
    assert top_song.weeks_score > lower_song.weeks_score


def test_compute_confidence_assessment_labels_transition_and_imputed_rows() -> None:
    high = compute_confidence_assessment(year=1965, genre="rock")
    medium = compute_confidence_assessment(year=1991, genre="unknown")
    low = compute_confidence_assessment(year=1991, genre="unknown", weeks_imputed=True, peak_imputed=True)

    assert high.label == "high"
    assert medium.label == "medium"
    assert low.label == "low"
    assert high.score > medium.score > low.score


def test_run_from_config_writes_dataset_summary_and_framework_scoring_fields(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    output_dir = tmp_path / "processed"
    lookup_path = tmp_path / "genre_lookup.csv"

    write_csv(
        raw_dir / "1965.csv",
        [
            {
                "Rank": 1,
                "Song": "Help!",
                "Artist": "The Beatles",
                "Weeks": 13,
                "Peak": 1,
            },
            {
                "Rank": 27,
                "Song": "California Girls",
                "Artist": "The Beach Boys",
                "Weeks": 9,
                "Peak": 3,
            },
        ],
    )
    write_csv(
        raw_dir / "2005.csv",
        [
            {
                "Rank": 1,
                "Song": "We Belong Together",
                "Artist": "Mariah Carey",
                "Weeks": 31,
                "Peak": 1,
            },
            {
                "Rank": 48,
                "Song": "Boulevard of Broken Dreams",
                "Artist": "Green Day",
                "Weeks": 16,
                "Peak": 2,
            },
        ],
    )
    write_csv(
        lookup_path,
        [
            {"title": "Help!", "artist": "The Beatles", "genre": "rock"},
            {"title": "California Girls", "artist": "The Beach Boys", "genre": "pop"},
            {"title": "We Belong Together", "artist": "Mariah Carey", "genre": "r&b"},
            {"title": "Boulevard of Broken Dreams", "artist": "Green Day", "genre": "rock"},
        ],
    )

    config_path = tmp_path / "settings.toml"
    config_path.write_text(
        "\n".join(
            [
                "[input]",
                f'yearly_glob = "{raw_dir / "*.csv"}"',
                "",
                "[output]",
                f'dataset_path = "{output_dir / "billboard_yearly.csv"}"',
                f'summary_path = "{output_dir / "summary.json"}"',
                "",
                "[genres]",
                f'lookup_csv = "{lookup_path}"',
            ]
        ),
        encoding="utf-8",
    )

    result = run_from_config(config_path)
    rows = read_csv(output_dir / "billboard_yearly.csv")
    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))

    assert result.dataset_path == output_dir / "billboard_yearly.csv"
    assert len(rows) == 4
    assert rows[0]["genre"] == "rock"
    assert rows[1]["genre"] == "pop"
    assert rows[0]["era_bucket"] == "1958-1990"
    assert rows[2]["era_bucket"] == "2005-2012"
    assert rows[0]["popularity_label"] == "canonical_hit"
    assert rows[1]["popularity_label"] == "lower_impact_year_end_entry"
    for row in rows:
        assert row["popularity_score_raw_100"]
        assert row["raw_year_percentile"]
        assert row["raw_era_percentile"]
        assert row["popularity_score_era_adj_100"]
        assert row["confidence_label"] in {"high", "medium", "low"}

    assert summary == {
        "rows": 4,
        "years": [1965, 2005],
        "genres": {"pop": 1, "r&b": 1, "rock": 2},
    }


def test_build_cycle_report_tracks_genre_share_weighted_traits_and_recurrence() -> None:
    rows = [
        {
            "year": 1965,
            "chart_rank": 1,
            "weeks_on_chart": 12,
            "peak_position": 1,
            "genre": "rock",
            "popularity_score": 100,
        },
        {
            "year": 1965,
            "chart_rank": 25,
            "weeks_on_chart": 8,
            "peak_position": 5,
            "genre": "pop",
            "popularity_score": 50,
        },
        {
            "year": 1966,
            "chart_rank": 2,
            "weeks_on_chart": 11,
            "peak_position": 1,
            "genre": "soul",
            "popularity_score": 90,
        },
        {
            "year": 1966,
            "chart_rank": 12,
            "weeks_on_chart": 9,
            "peak_position": 4,
            "genre": "rock",
            "popularity_score": 60,
        },
        {
            "year": 1967,
            "chart_rank": 3,
            "weeks_on_chart": 12,
            "peak_position": 1,
            "genre": "rock",
            "popularity_score": 95,
        },
        {
            "year": 1967,
            "chart_rank": 22,
            "weeks_on_chart": 7,
            "peak_position": 6,
            "genre": "pop",
            "popularity_score": 55,
        },
    ]

    report = build_cycle_report(rows, rolling_window=2)

    assert [entry["year"] for entry in report["yearly_metrics"]] == [1965, 1966, 1967]
    assert report["yearly_metrics"][0]["genre_share"] == {"pop": 0.5, "rock": 0.5}
    assert report["yearly_metrics"][0]["popularity_weighted_traits"] == {
        "chart_rank": 9.0,
        "weeks_on_chart": 10.6667,
        "peak_position": 2.3333,
    }
    assert report["rolling_windows"] == [
        {
            "window_start": 1965,
            "window_end": 1966,
            "years": [1965, 1966],
            "genre_share": {"pop": 0.25, "rock": 0.5, "soul": 0.25},
            "popularity_weighted_traits": {
                "chart_rank": 7.5,
                "weeks_on_chart": 10.4333,
                "peak_position": 2.2667,
            },
        },
        {
            "window_start": 1966,
            "window_end": 1967,
            "years": [1966, 1967],
            "genre_share": {"pop": 0.25, "rock": 0.5, "soul": 0.25},
            "popularity_weighted_traits": {
                "chart_rank": 7.9833,
                "weeks_on_chart": 10.1833,
                "peak_position": 2.5167,
            },
        },
    ]
    assert report["recurrence_candidates"][0] == {
        "base_year": 1965,
        "comparison_year": 1967,
        "score": 0.9951,
        "shared_genres": ["pop", "rock"],
        "notes": [
            "placeholder recurrence score blends genre-share overlap and weighted-trait similarity"
        ],
    }
    assert "placeholder" in report["cycle_detection_notes"][0]


def test_run_from_config_writes_cycle_analysis_scaffold(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    output_dir = tmp_path / "processed"
    lookup_path = tmp_path / "genre_lookup.csv"

    write_csv(
        raw_dir / "1965.csv",
        [
            {"Rank": 1, "Song": "Help!", "Artist": "The Beatles", "Weeks": 13, "Peak": 1},
            {"Rank": 20, "Song": "My Girl", "Artist": "The Temptations", "Weeks": 9, "Peak": 1},
        ],
    )
    write_csv(
        raw_dir / "1966.csv",
        [
            {"Rank": 2, "Song": "Good Vibrations", "Artist": "The Beach Boys", "Weeks": 12, "Peak": 1},
            {"Rank": 25, "Song": "Reach Out I'll Be There", "Artist": "Four Tops", "Weeks": 10, "Peak": 1},
        ],
    )
    write_csv(
        raw_dir / "1967.csv",
        [
            {"Rank": 3, "Song": "All You Need Is Love", "Artist": "The Beatles", "Weeks": 11, "Peak": 1},
            {"Rank": 24, "Song": "Respect", "Artist": "Aretha Franklin", "Weeks": 12, "Peak": 1},
        ],
    )
    write_csv(
        lookup_path,
        [
            {"title": "Help!", "artist": "The Beatles", "genre": "rock"},
            {"title": "My Girl", "artist": "The Temptations", "genre": "soul"},
            {"title": "Good Vibrations", "artist": "The Beach Boys", "genre": "rock"},
            {"title": "Reach Out I'll Be There", "artist": "Four Tops", "genre": "soul"},
            {"title": "All You Need Is Love", "artist": "The Beatles", "genre": "rock"},
            {"title": "Respect", "artist": "Aretha Franklin", "genre": "soul"},
        ],
    )

    config_path = tmp_path / "settings.toml"
    config_path.write_text(
        "\n".join(
            [
                "[input]",
                f'yearly_glob = "{raw_dir / "*.csv"}"',
                "",
                "[output]",
                f'dataset_path = "{output_dir / "billboard_yearly.csv"}"',
                f'summary_path = "{output_dir / "summary.json"}"',
                f'cycle_analysis_path = "{output_dir / "cycle_analysis.json"}"',
                "",
                "[genres]",
                f'lookup_csv = "{lookup_path}"',
                "",
                "[analysis]",
                "rolling_window = 2",
            ]
        ),
        encoding="utf-8",
    )

    result = run_from_config(config_path)
    cycle_analysis = json.loads((output_dir / "cycle_analysis.json").read_text(encoding="utf-8"))

    assert result.cycle_analysis_path == output_dir / "cycle_analysis.json"
    assert cycle_analysis["years"] == [1965, 1966, 1967]
    assert len(cycle_analysis["yearly_metrics"]) == 3
    assert len(cycle_analysis["rolling_windows"]) == 2
    assert cycle_analysis["recurrence_candidates"]
    assert cycle_analysis["cycle_detection_notes"] == [
        "placeholder cycle-detection hooks emitted; replace recurrence scoring with spectral/autocorrelation analysis once richer feature coverage is available"
    ]
