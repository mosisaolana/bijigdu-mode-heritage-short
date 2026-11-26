# Emebet Bijigdu Mode: The Generous Governor

A reproducible AI heritage short film pipeline turning `storyboard.json` into a ~75-second Amharic narration film with burned-in English subtitles and a 2.5-second AI disclosure end card in both vertical (`9:16`, `1080x1920`) and widescreen (`16:9`, `1920x1080`) formats.

## Deliverables & Links

* **Vertical Film (`9:16`, `1080x1920`):** https://drive.google.com/file/d/1IAa7yfMDjEAqMu5gDHo_Iq7EOeAMH5Ip/view?usp=drive_link
* **Horizontal Film (`16:9`, `1920x1080`):** https://drive.google.com/file/d/1wGcwO2nrftp2tMvIcqCC_r64GAeiBUgQ/view?usp=drive_link
* **Walkthrough Video (<= 5 min):** https://www.loom.com/share/6bde1feff5a44896b98fb13e87bfdcf6
* **LinkedIn Post:** https://lnkd.in/p/d9CtHZH8
## Subject & Creative Overview

* **Subject:** Emebet Bijigdu Mode, Governor of Guduru Malole Warada in Wellega Awraja, remembered in family and regional history for leadership, generosity, traditional regalia (*Kaba*, *Zinar*, pistol), and a silver-chained mule.
* **Format & Target Length:** ~75-second heritage short film (`60-90s` window) in `9:16` (`1080x1920`) and `16:9` (`1920x1080`) with `FontSize=8` subtitles, `16:9` zoomed-out top headroom framing, music ducked under narration, and loudness normalized to `-14 LUFS` / `-1.0 dB` true peak.

## Prerequisites & Environment Setup

* Python `3.x` and `FFmpeg 9.1` (with `libass`, `libx264`, `aac`) on `PATH`.
* Environment variables (keep secrets out of Git): `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, and TTS settings used by `pipeline/narration.py`.

## Running the Pipeline

1. **Narration & radio cut:** `python pipeline/narration.py`
2. **Keyframes:** `python pipeline/keyframes.py`
3. **Final `9:16` & `16:9` assembly:** `python pipeline/assemble.py --aspect both --font-size 8 --burn-subs`

## Single-Shot Iteration

Edit a shot in `storyboard.json` and rerun the stage (`--only <shot_id>` where supported) so unchanged shots reuse cached artifacts via `run_cached_stage_item`.

## Key Outputs & Logs

* `outputs/final/bijigdu_mode_75s_9x16.mp4`
* `outputs/final/bijigdu_mode_75s_16x9.mp4`
* `outputs/final/bijigdu_mode_75s.srt`
* `outputs/final/radio_cut.mp4`
* `runs.jsonl`

## Documentation

* `ETHICS.md`
* `DESIGN.md`
* `ARCHITECTURE.md`
* `EXPERIMENTS.md`
* `FAILURES.md`
* `COSTS.md`
