# Costs, Latency & Runtime Measurements

## 1. Billing & Quotas
- **Direct Spend**: [Add actual spend-e.g., $0 / free-tier / included quota-and note any Cloudflare Workers AI, TTS, or local compute limits observed.]
- **Secrets & Logs**: API tokens and account credentials stay in environment variables rather than `runs.jsonl` or Git.

## 2. Per-Stage Latency & Runtime
- **Narration (`pipeline/narration.py` / `radio_cut.py`)**: [Add measured per-shot or total runtime for generating `.wav` files in `outputs/audio/` and `outputs/final/radio_cut.mp4`.]
- **Keyframes (`pipeline/keyframes.py`)**: [Add average and total runtime for generating reference and `shot_01`-`shot_10` keyframes on `@cf/black-forest-labs/flux-1-schnell`, plus cache-hit speedup on single-shot runs.]
- **Assembly & Normalization (`pipeline/assemble.py`)**: [Add measured wall-clock time for rendering `9:16` (`1080x1920`) and `16:9` (`1920x1080`) exports, subtitle burning, AI end card, and `-14 LUFS` / `-1.0 dB` TP loudness pass.]

## 3. List-Price Cost Equivalent
- **Estimated Equivalent Cost**: [Summarize what equivalent image generation, TTS synthesis, and video rendering/compute would cost at standard commercial pay-as-you-go rates.]
