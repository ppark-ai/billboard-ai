# AI Billboard-Like Quality Gate

**Status:** final winner published to web from the automated Billboard-calibrated batch  
**Winner:** `promo-name-on-neon-direct-chorus`  
**Title:** Name on Neon  
**AI score:** 93.49  
**Release label:** `release_watchlist`

## Billboard reference-calibration neighbors shown on the site
- 2024 #3 **Beautiful Things** — Benson Boone
- 2015 #1 **Uptown Funk** — Mark Ronson featuring Bruno Mars
- 1975 #2 **Rhinestone Cowboy** — Glen Campbell

These labels mean nearest audio-feature matches inside the Billboard preview reference set. They are not claims of melodic copying or source-song derivation.

## Pipeline
1. `scripts/run_hook_demo_batch.py config/sprint2_promoted_hook_demo.toml` renders the promoted candidates.
2. `scripts/evaluate_hook_demo_batch.py ... --reference-profile data/reference/billboard_preview_reference_profile.json` scores them against the Billboard reference profile.
3. `scripts/publish_top_web_demo.py` exports a softened web listening file and rewrites the site around the true top scorer.
4. The published winner now uses lyric-guided synthetic singing based on explicit per-song hook lines.

## Known remaining issue
- Lyric-guided singing is clearer than the old generic guide-vowel pass, but it is still a synthetic prototype vocal.
- The upper register still exposes some synthetic artifacts.
- The web version reduces harshness but is still not a human-recorded final topline.
