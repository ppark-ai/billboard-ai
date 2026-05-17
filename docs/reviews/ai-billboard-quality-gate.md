# AI Billboard-Like Quality Gate

**Status:** final winner published to web from the automated Billboard-calibrated batch  
**Winner:** `promo-name-on-neon-direct-chorus`  
**Title:** Name on Neon  
**AI score:** 94.32  
**Release label:** `release_watchlist`

## Billboard reference-calibration neighbors shown on the site
- 2015 #1 **Uptown Funk** — Mark Ronson featuring Bruno Mars
- 2024 #3 **Beautiful Things** — Benson Boone
- 1985 #1 **Careless Whisper** — George Michael

These labels mean nearest audio-feature matches inside the Billboard preview reference set. They are not claims of melodic copying or source-song derivation.

## Pipeline
1. `scripts/run_hook_demo_batch.py config/sprint2_promoted_hook_demo.toml` renders the promoted candidates.
2. `scripts/evaluate_hook_demo_batch.py ... --reference-profile data/reference/billboard_preview_reference_profile.json` scores them against the Billboard reference profile.
3. `scripts/publish_top_web_demo.py` exports a softened web listening file and rewrites the site around the true top scorer.

## Known remaining issue
- The upper register still exposes synthetic guide-vocal artifacts.
- The web version reduces harshness but is still a prototype render rather than a final vocal production.
