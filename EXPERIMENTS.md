# Experiments Log

This log records iterative experiments across keyframe generation, framing, subtitles, audio normalization, and multi-aspect rendering (~10 structured entries).

1. **Exp 01 - Subtitle Font Size & Vertical Margin (`FontSize=8`, `MarginV=28`)**
   - **Hypothesis**: Large default subtitle sizes on `1080x1920` vertical video cover too much of the frame, whereas `FontSize=8` with `MarginV=28` keeps captions readable while preserving visual space.
   - **Change**: Updated burned-in subtitle styling in `pipeline/assemble.py` to `FontSize=8` and `MarginV=28`.
   - **Result / Evidence**: Subtitles render cleanly without crowding the subject; verified in `pipeline/assemble.py` and `9:16` / `16:9` exports.

2. **Exp 02 - `16:9` Widescreen Zoom-Out & Top Headroom Alignment**
   - **Hypothesis**: Standard center-aligned `zoompan` crops off the top of the head/crown when converting vertical/portrait compositions into `16:9` (`1920x1080`).
   - **Change**: Adjusted `16:9` motion framing in `pipeline/assemble.py` to use zoomed-out scaling (`z < 1.0`) and top-biased vertical alignment (`y=0`).
   - **Result / Evidence**: Preserves headroom and prevents head clipping in `outputs/final/bijigdu_mode_75s_16x9.mp4`.

3. **Exp 03 - Real Reference Photo (`Bijigdu picture.jpg`) vs. Direct Original Keyframes**
   - **Hypothesis**: Anchoring `Bijigdu picture.jpg` across shots improves identity consistency, while keeping direct keyframes preserves the original visual composition.
   - **Change**: Tested copying `Bijigdu picture.jpg` into `outputs/refs/bijigdu_actual.jpg` and composite anchoring, then reverted `pipeline/assemble.py` back to reading `outputs/keyframes` directly to keep the original visual flow.
   - **Result / Evidence**: Confirmed that `pipeline/keyframes.py` uses text-only prompts on `@cf/black-forest-labs/flux-1-schnell` and reverted assembly to direct `outputs/keyframes` per visual preference.

4. **Exp 04 - End-Card Rendering via `.srt` + `libass` Instead of `drawtext`**
   - **Hypothesis**: Rendering the 2.5-second AI disclosure end card through a temporary `.srt` subtitle filter avoids native `drawtext` filter crashes in FFmpeg 9.1 on Windows.
   - **Change**: Replaced `drawtext` in `render_end_card` with ASCII text rendered via `subtitles` (`libass`).
   - **Result / Evidence**: Eliminated crash exit code `3221225477` (`0xC0000005`) during end-card generation.

5. **Exp 05 - Two-Pass `loudnorm` (`-14 LUFS` / `-1.0 dB` TP) with Safe Fallback**
   - **Hypothesis**: Two-pass loudness normalization hits `-14 LUFS` and `-1.0 dB` true peak, while a fallback limiter prevents pipeline failure if measurement parsing fails on concatenated audio.
   - **Change**: Hardened JSON metric parsing in `loudnorm_two_pass` and added an `aformat` + `alimiter` fallback path.
   - **Result / Evidence**: Prevented non-zero exit `4294967274` (`EINVAL`) and produced normalized `9:16` and `16:9` exports.

6. **Exp 06 - Character Regalia & Setting Prompts (*Kaba*, *Zinar*, Pistol, Silver-Chained Mule)**
   - **Hypothesis**: Explicitly specifying Emebet Bijigdu Mode's *Kaba*, *Zinar*, pistol, and silver-chained mule in `storyboard.json` anchors her historical identity across scenes.
   - **Change**: [Add specific prompt phrasing or shot updates in `storyboard.json` and note which shots improved most.]
   - **Result / Evidence**: [Add observed consistency across shots from `outputs/keyframes/` and `runs.jsonl`.]

7. **Exp 07 - Per-Shot Seeds & Cache Invalidation (`run_cached_stage_item`)**
   - **Hypothesis**: Fixed per-shot seeds and input-keyed caching allow single-shot regeneration without re-rendering unchanged shots.
   - **Change**: [Note specific seed values or `--only <shot_id>` tests run on `storyboard.json`.]
   - **Result / Evidence**: [Record cache hits vs. single-shot regeneration from `runs.jsonl`.]

8. **Exp 08 - Shot Durations & Pacing for 75s Target Arc**
   - **Hypothesis**: Tuning per-shot `duration_sec` around the Amharic narration keeps the cut within the 60-90s target window without rushed or dead air.
   - **Change**: [Note any `duration_sec` or `narration_am` edits tested across `shot_01`-`shot_10`.]
   - **Result / Evidence**: [Record total duration and narration pacing from `outputs/audio/` and `outputs/final/`.]

9. **Exp 09 - `9:16` Vertical vs. `16:9` Horizontal Motion Prompts**
   - **Hypothesis**: Tailoring `motion_prompt` (pan, pull/wide, zoom) to each aspect ratio reduces awkward cropping compared to identical motion across both ratios.
   - **Change**: [Note which `motion_prompt` keywords or shot motions were compared between `9x16` and `16x9`.]
   - **Result / Evidence**: [Summarize visual smoothness in `bijigdu_mode_75s_9x16.mp4` and `bijigdu_mode_75s_16x9.mp4`.]

10. **Exp 10 - Diffusion Step Count (`steps=4`) on `@cf/black-forest-labs/flux-1-schnell`**
    - **Hypothesis**: Four steps on `flux-1-schnell` balances visual clarity against generation speed and quota usage.
    - **Change**: [Note if you tested `steps=4` vs. another step count or prompt variation in `pipeline/keyframes.py`.]
    - **Result / Evidence**: [Record speed/quality observation from `runs.jsonl`.]
