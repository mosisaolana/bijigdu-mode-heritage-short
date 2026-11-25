# Pipeline Architecture

## 1. Single Source of Truth Contract
- **Storyboard Input (`storyboard.json`)**: Defines `project_title`, `language`, `target_duration_seconds`, `character_ref`, `style_block`, and ordered `shots` (`shot_id`, `duration_sec`, `shot_type`, `reason`, `image_prompt`, `motion_prompt`, `narration_am`, `subtitles_en`, `music_cue`, `seed`).
- **Schema Validation (`schema/storyboard.schema.json`)**: Validated before execution via `validate_storyboard` in `pipeline/common.py` so malformed fields or missing shot attributes fail fast before making remote API or rendering calls.

## 2. Pipeline Stages & Artifacts
1. **Narration & Radio Cut (`pipeline/narration.py` / `radio_cut.py`)**: Synthesizes per-shot Amharic narration audio (`.wav`) into `outputs/audio/` and assembles the audio-first preview cut (`outputs/final/radio_cut.mp4`).
2. **Keyframes (`pipeline/keyframes.py`)**: Generates the character reference sheet and per-shot images (`outputs/keyframes/<shot_id>.png`) via Cloudflare Workers AI (`@cf/black-forest-labs/flux-1-schnell`) using shot prompts plus `style_block` and `seed`.
3. **Multi-Aspect Assembly & Finishing (`pipeline/assemble.py`)**:
   - Generates timed subtitles (`outputs/final/bijigdu_mode_75s.srt`) aligned to shot durations and narration.
   - Applies Ken Burns motion (`zoompan`) tailored per aspect ratio: vertical `9:16` (`1080x1920`) and widescreen `16:9` (`1920x1080`) with zoomed-out scaling (`z < 1.0`) and top-biased vertical alignment (`y=0`) to preserve headroom.
   - Appends a 2.5-second AI disclosure end card (`Made with AI - Heritage Short Pipeline`) rendered via a temporary `.srt` + `libass` filter.
   - Burns subtitles (`FontSize=8`, `MarginV=28`) and runs two-pass loudness normalization (`-14 LUFS`, `-1.0 dB` true peak) to produce `outputs/final/bijigdu_mode_75s_9x16.mp4` and `outputs/final/bijigdu_mode_75s_16x9.mp4`.

## 3. Caching, Retries & Observability
- **Incremental Caching (`run_cached_stage_item` in `pipeline/common.py`)**: Hashes relevant stage inputs and parameters per item so editing a single shot in `storyboard.json` and rerunning regenerates only that shot while reusing cached outputs for unchanged shots.
- **Retry & Resilience**: Handles transient network/HTTP errors on external API calls and includes fallback handling in audio normalization and end-card subtitle rendering.
- **Run Logging (`runs.jsonl`)**: Records stage executions, parameters, cache status, and outcomes for reproducibility without storing secrets or API keys in the repository.
