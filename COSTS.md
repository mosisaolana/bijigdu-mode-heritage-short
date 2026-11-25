# Costs, Latency & Runtime Measurements

## 1. Billing & Quotas
- **Actual Spend**: $0.00 / free-tier or included quota ([update if any paid billing or overages occurred]).
- **API & Compute Quotas**: Keyframes were generated via Cloudflare Workers AI (`@cf/black-forest-labs/flux-1-schnell`, `steps=4`), and video/audio assembly ran locally on Windows using `FFmpeg 9.1` (`libass`, `libx264`, `aac`). Note any daily neuron/request limits or rate limits observed during testing.
- **Credential Hygiene**: Credentials remain in environment variables (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`) rather than `runs.jsonl` or Git.

## 2. Per-Stage Latency & Runtime
- **Narration & Radio Cut (`pipeline/narration.py` / `radio_cut.py`)**: [Add measured per-shot or total runtime for `.wav` generation and `outputs/final/radio_cut.mp4`.]
- **Keyframes (`pipeline/keyframes.py`)**: [Add measured latency per shot or full 10-shot run on `@cf/black-forest-labs/flux-1-schnell`, plus how much faster a single-shot regeneration is when unchanged shots hit `run_cached_stage_item` cache.]
- **Assembly & Loudness Normalization (`pipeline/assemble.py`)**: [Add measured wall-clock time for generating `9:16` (`1080x1920`) and `16:9` (`1920x1080`) MP4s, burning subtitles (`FontSize=8`, `MarginV=28`), appending the 2.5s AI end card, and applying two-pass `loudnorm` (`-14 LUFS`, `-1.0 dB` TP) or fallback limiter.]

## 3. List-Price Cost Equivalent
- **Estimated Equivalent Cost**: [Summarize approximate list-price cost if the same keyframe count, TTS audio duration, and local CPU/GPU video encoding were billed at commercial pay-as-you-go rates-noting that per-run cost is minimal for a ~75-second, 10-shot short.]
