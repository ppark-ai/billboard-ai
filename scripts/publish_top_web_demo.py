from __future__ import annotations

import argparse
import csv
import html
import json
import math
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def nearest_references(reference_csv: Path, feature_values: dict[str, float], top_n: int = 3) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = []
    with reference_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            refs.append(
                {
                    "title": row["title"],
                    "artist": row["artist"],
                    "year": int(row["year"]),
                    "rank": int(row["rank"]),
                    "rms_level": float(row["rms_level"]),
                    "stereo_width_ratio": float(row["stereo_width_ratio"]),
                    "dynamic_lift_ratio": float(row["dynamic_lift_ratio"]),
                    "window_motion": float(row["window_motion"]),
                }
            )

    scored: list[tuple[float, dict[str, object]]] = []
    for ref in refs:
        ref_rms = float(str(ref["rms_level"]))
        ref_stereo = float(str(ref["stereo_width_ratio"]))
        ref_lift = float(str(ref["dynamic_lift_ratio"]))
        ref_motion = float(str(ref["window_motion"]))
        distance = math.sqrt(
            (float(feature_values["rms_level"]) - ref_rms) ** 2
            + (float(feature_values["stereo_width_ratio"]) - ref_stereo) ** 2
            + (float(feature_values["dynamic_lift_ratio"]) - ref_lift) ** 2
            + (float(feature_values["window_motion"]) - ref_motion) ** 2
        )
        scored.append((distance, ref))
    scored.sort(key=lambda item: item[0])

    output: list[dict[str, object]] = []
    for distance, ref in scored[:top_n]:
        output.append(
            {
                "title": ref["title"],
                "artist": ref["artist"],
                "year": ref["year"],
                "rank": ref["rank"],
                "distance": round(distance, 4),
            }
        )
    return output


def ffmpeg_export(input_wav: Path, output_wav: Path, output_mp3: Path) -> None:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_wav),
            "-af",
            "lowpass=f=6800,volume=-1dB,alimiter=limit=0.92",
            str(output_wav),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(output_wav),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(output_mp3),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def build_html_page(
    winner_demo: dict,
    winner_assessment: dict,
    nearest_refs: list[dict[str, object]],
    published_mp3_rel: str,
    published_wav_rel: str,
    generated_at: str,
) -> str:
    hook_items = "".join(f"<li>{html.escape(item)}</li>" for item in winner_demo.get("intended_clip_sections", []))
    lyric_items = "".join(f"<li>{html.escape(item)}</li>" for item in winner_demo.get("lyrics_lines", []))
    ref_items = "".join(
        f"<li><strong>{html.escape(str(ref['title']))}</strong> — {html.escape(str(ref['artist']))} <span class=\"muted\">({ref['year']} #{ref['rank']})</span></li>"
        for ref in nearest_refs
    )
    notes = "".join(f"<li>{html.escape(note)}</li>" for note in winner_demo.get("provenance_notes", []))
    raw_title = winner_assessment.get("title") or (winner_demo.get("title_options") or [winner_demo["slug"]])[0]
    title = html.escape(str(raw_title))
    slug = html.escape(str(winner_demo["slug"]))
    readiness = html.escape(str(winner_assessment["release_readiness"]))
    score = html.escape(f"{winner_assessment['overall_score']:.2f}")
    tempo = html.escape(str(winner_demo["tempo_bpm"]))
    duration = html.escape(str(winner_demo["duration_seconds"]))

    return f"""<!doctype html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Billboard AI Hit — Final Winner</title>
  <style>
    :root {{ color-scheme: dark; --bg:#08111f; --panel:#111b2d; --line:#223454; --text:#eef4ff; --muted:#a9b6cf; --accent:#7dd3fc; --warn:#f7d58a; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:linear-gradient(180deg,#08111f,#101a2e 45%,#08111f); color:var(--text); }}
    .wrap {{ max-width:980px; margin:0 auto; padding:40px 20px 72px; }}
    .panel {{ background:rgba(17,27,45,.94); border:1px solid var(--line); border-radius:22px; padding:24px; box-shadow:0 10px 28px rgba(0,0,0,.22); }}
    h1 {{ font-size:clamp(2rem,5vw,3.3rem); margin:0 0 10px; }}
    h2 {{ margin:0 0 12px; font-size:1.3rem; }}
    p, li {{ line-height:1.65; }}
    .muted {{ color:var(--muted); }}
    .badges {{ display:flex; flex-wrap:wrap; gap:10px; margin:16px 0 0; }}
    .badge {{ border:1px solid var(--line); border-radius:999px; padding:8px 12px; color:var(--accent); background:rgba(125,211,252,.08); font-size:.92rem; }}
    .warn {{ margin:18px 0 0; border:1px solid #5b4520; background:#2b210d; color:var(--warn); border-radius:16px; padding:14px 16px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; margin-top:18px; }}
    .sub {{ background:#0c1528; border:1px solid var(--line); border-radius:18px; padding:18px; }}
    audio {{ width:100%; margin:16px 0 14px; }}
    code {{ background:#0b1426; border:1px solid var(--line); padding:2px 6px; border-radius:8px; }}
    a {{ color:var(--accent); }}
  </style>
</head>
<body>
  <main class=\"wrap\">
    <section class=\"panel\">
      <p class=\"muted\">Billboard AI Hit · final automated winner</p>
      <h1>{title}</h1>
      <p>현재 웹에는 <strong>실제 AI 품질 점수가 가장 높은 곡</strong>만 표시합니다. 이 우승 곡은 Billboard preview reference calibration 기준에서 현재 배치 최고점입니다.</p>
      <div class=\"badges\">
        <span class=\"badge\">Winner slug: {slug}</span>
        <span class=\"badge\">AI score: {score}</span>
        <span class=\"badge\">Label: {readiness}</span>
        <span class=\"badge\">Generated: {html.escape(generated_at)}</span>
      </div>
      <audio controls preload=\"none\" src=\"{html.escape(published_mp3_rel)}\"></audio>
      <p><a href=\"{html.escape(published_mp3_rel)}\">MP3 듣기/다운로드</a> · <a href=\"{html.escape(published_wav_rel)}\">WAV 다운로드</a> · <a href=\"audio/published/current_release.json\">release metadata</a> · <a href=\"audio/shortform_hook_tests/quality_report.json\">full quality report</a></p>
      <div class=\"warn\">
        <strong>사운드 상태 메모</strong><br>
        현재 공개본은 곡별 가사 라인을 따라 부르도록 lyric-guided synthetic vocal을 렌더합니다. 아직 최종 사람 보컬은 아니어서 질감은 남아 있지만, 이전의 무의미한 guide vowel보다 훨씬 명확하게 가사를 따라갑니다.
      </div>
    </section>

    <section class=\"grid\">
      <article class=\"sub\">
        <h2>이 곡과 함께 표시하는 Billboard 레퍼런스</h2>
        <p class=\"muted\">아래 곡들은 법적/작곡적 원곡 표시가 아니라, 현재 AI 품질 게이트가 비교한 <strong>reference-calibration 근접 곡</strong>입니다.</p>
        <ol>{ref_items}</ol>
      </article>

      <article class=\"sub\">
        <h2>현재 우승 곡 정보</h2>
        <ul>
          <li><strong>Title:</strong> {title}</li>
          <li><strong>Tempo:</strong> {tempo} BPM</li>
          <li><strong>Duration:</strong> {duration}s</li>
          <li><strong>Original generated WAV:</strong> {html.escape(Path(winner_demo['audio_path']).name)}</li>
          <li><strong>Vocal mode:</strong> lyric-guided synthetic singing</li>
          <li><strong>Web export:</strong> low-pass + limiter applied</li>
        </ul>
      </article>

      <article class=\"sub\">
        <h2>현재 보컬 가사</h2>
        <ul>{lyric_items}</ul>
      </article>

      <article class=\"sub\">
        <h2>클립 훅 구간</h2>
        <ul>{hook_items}</ul>
      </article>

      <article class=\"sub\">
        <h2>프로비넌스 / 파이프라인</h2>
        <ul>{notes}</ul>
        <p class=\"muted\">Renderer: <code>scripts/run_hook_demo_batch.py</code><br>Judge: <code>scripts/evaluate_hook_demo_batch.py</code><br>Publisher: <code>scripts/publish_top_web_demo.py</code></p>
      </article>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the highest-quality hook-demo track to the web site.")
    parser.add_argument("--manifest", default="audio/shortform_hook_tests/manifest.json")
    parser.add_argument("--quality-report", default="audio/shortform_hook_tests/quality_report.json")
    parser.add_argument("--reference-csv", default="data/reference/billboard_preview_reference_tracks.csv")
    parser.add_argument("--winner-slug", default=None)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    manifest_path = repo / args.manifest
    quality_report_path = repo / args.quality_report
    reference_csv = repo / args.reference_csv

    manifest = load_json(manifest_path)
    report = load_json(quality_report_path)

    assessments = report["assessments"]
    if not assessments:
        raise SystemExit("quality report has no assessments")

    winner_slug = args.winner_slug or report.get("winner_slug")
    winner_assessment = next((item for item in assessments if item["slug"] == winner_slug), None)
    if winner_assessment is None:
        winner_assessment = max(assessments, key=lambda item: float(item["overall_score"]))
        winner_slug = winner_assessment["slug"]

    winner_demo = next((item for item in manifest["demos"] if item["slug"] == winner_slug), None)
    if winner_demo is None:
        raise SystemExit(f"winner slug {winner_slug!r} not found in manifest")

    nearest_refs = nearest_references(reference_csv, winner_assessment["feature_values"])
    input_wav = Path(winner_demo["audio_path"])
    published_dir = repo / "audio" / "published"
    published_dir.mkdir(parents=True, exist_ok=True)
    for stale in published_dir.glob("*-final-web.*"):
        stale.unlink()
    slug = winner_demo["slug"]
    published_wav = published_dir / f"{slug}-final-web.wav"
    published_mp3 = published_dir / f"{slug}-final-web.mp3"
    ffmpeg_export(input_wav, published_wav, published_mp3)

    published_mp3_rel = str(published_mp3.relative_to(repo))
    published_wav_rel = str(published_wav.relative_to(repo))
    generated_at = datetime.fromtimestamp(input_wav.stat().st_mtime).isoformat(timespec="seconds")

    current_release = {
        "winner_slug": winner_slug,
        "winner_title": winner_assessment.get("title"),
        "overall_score": winner_assessment["overall_score"],
        "release_readiness": winner_assessment["release_readiness"],
        "lyrics_lines": winner_demo.get("lyrics_lines", []),
        "source_manifest_path": str(manifest_path.relative_to(repo)),
        "source_quality_report_path": str(quality_report_path.relative_to(repo)),
        "published_mp3": published_mp3_rel,
        "published_wav": published_wav_rel,
        "reference_profile_path": report.get("reference_profile_path"),
        "reference_profile_name": report.get("reference_profile_name"),
        "nearest_billboard_reference_songs": nearest_refs,
        "known_issue_notes": [
            "Lyric-guided synthetic singing now follows explicit hook lines instead of generic vowel-only guide notes.",
            "Upper-register synthetic artifacts still remain audible because this is not yet a human-recorded final vocal.",
            "Published web audio applies gentle low-pass filtering and limiting to reduce harshness.",
        ],
    }
    (published_dir / "current_release.json").write_text(json.dumps(current_release, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    html_page = build_html_page(
        winner_demo=winner_demo,
        winner_assessment=winner_assessment,
        nearest_refs=nearest_refs,
        published_mp3_rel=published_mp3_rel,
        published_wav_rel=published_wav_rel,
        generated_at=generated_at,
    )
    (repo / "index.html").write_text(html_page, encoding="utf-8")

    static_root = repo / ".vercel" / "output" / "static"
    if static_root.exists():
        (static_root / "index.html").write_text(html_page, encoding="utf-8")
        static_audio_dir = static_root / "audio" / "published"
        static_audio_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(published_wav, static_audio_dir / published_wav.name)
        shutil.copy2(published_mp3, static_audio_dir / published_mp3.name)
        shutil.copy2(published_dir / "current_release.json", static_audio_dir / "current_release.json")

    review_doc = [
        "# AI Billboard-Like Quality Gate",
        "",
        "**Status:** final winner published to web from the automated Billboard-calibrated batch  ",
        f"**Winner:** `{winner_slug}`  ",
        f"**Title:** {winner_assessment.get('title') or winner_slug}  ",
        f"**AI score:** {winner_assessment['overall_score']:.2f}  ",
        f"**Release label:** `{winner_assessment['release_readiness']}`",
        "",
        "## Billboard reference-calibration neighbors shown on the site",
    ]
    for ref in nearest_refs:
        review_doc.append(f"- {ref['year']} #{ref['rank']} **{ref['title']}** — {ref['artist']}")
    review_doc.extend(
        [
            "",
            "These labels mean nearest audio-feature matches inside the Billboard preview reference set. They are not claims of melodic copying or source-song derivation.",
            "",
            "## Pipeline",
            "1. `scripts/run_hook_demo_batch.py config/sprint2_promoted_hook_demo.toml` renders the promoted candidates.",
            "2. `scripts/evaluate_hook_demo_batch.py ... --reference-profile data/reference/billboard_preview_reference_profile.json` scores them against the Billboard reference profile.",
            "3. `scripts/publish_top_web_demo.py` exports a softened web listening file and rewrites the site around the true top scorer.",
            "4. The published winner now uses lyric-guided synthetic singing based on explicit per-song hook lines.",
            "",
            "## Known remaining issue",
            "- Lyric-guided singing is clearer than the old generic guide-vowel pass, but it is still a synthetic prototype vocal.",
            "- The upper register still exposes some synthetic artifacts.",
            "- The web version reduces harshness but is still not a human-recorded final topline.",
            "",
        ]
    )
    (repo / "docs" / "reviews" / "ai-billboard-quality-gate.md").write_text("\n".join(review_doc), encoding="utf-8")

    print(
        json.dumps(
            {
                "winner_slug": winner_slug,
                "winner_title": winner_assessment.get("title"),
                "published_mp3": published_mp3_rel,
                "published_wav": published_wav_rel,
                "nearest_billboard_reference_songs": nearest_refs,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
