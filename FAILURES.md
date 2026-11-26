# Failures & Troubleshooting Log

## 1. API & Quota Failures

* **Gemini `400 API_KEY_INVALID` & Downstream `FileNotFoundError`:** Running `pipeline/narration.py` failed with `400 INVALID_ARGUMENT` (`API_KEY_INVALID`) when `GEMINI_API_KEY` was missing in the active shell, followed by `FileNotFoundError` on `outputs/audio/shot_01.wav` when `pipeline/radio_cut.py` ran before narration completed. Set a valid `GEMINI_API_KEY`, ran `pipeline/narration.py` first, and then ran `pipeline/radio_cut.py`.
* **Outdated Model Name (`404 NOT_FOUND` on `gemini-2.5-flash`):** Quick verification against `gemini-2.5-flash` returned `404 NOT_FOUND` in favor of `gemini-3.8-flash` family models (`gemini-3.8-flash-tts` for narration). Updated model references to current `gemini-3.8-flash` models.
* **Transient Rate Limit on Narration Batch (`shot_08` - `shot_10`):** A 10-shot `pipeline/narration.py` run generated `shot_01.wav` through `shot_07.wav` before hitting transient throttling. Used `.wav.cachekey` caching and ran `python pipeline/narration.py --shots shot_08 shot_09 shot_10` to finish the remaining shots.
* **Free Tier Daily TTS Limit (`429 RESOURCE_EXHAUSTED`, 10 RPD):** Deleting cached `.wav` files and re-running narration hit the `gemini-3.8-flash-tts` free-tier daily cap (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`) on `shot_03`, blocking `pipeline/radio_cut.py`. Waited for quota reset / switched keys and avoided wiping cached `.wav` files unnecessarily.
* **Image Generation Quota & Historical Currency Accuracy (`shot_08`):** Automated regeneration of `outputs/keyframes/shot_08.png` hit image generation quota limits while updating `shot_08` to depict Oromo community members receiving a cow, an ox, and old Ethiopian silver currency (*Xegera*) with zero dollar bills or paper banknotes. Updated `shot_08` prompts and `seed` in `storyboard.json` and cleared cached `shot_08` clips for regeneration once quota resets.

## 2. Environment, FFmpeg & PowerShell Script Failures

* **Missing `ffmpeg` (`FileNotFoundError` / `[WinError 2]`):** `pipeline/radio_cut.py` failed on `subprocess.run(...)` when `ffmpeg.exe` was not installed or not on `PATH`. Installed FFmpeg and refreshed the PowerShell session `PATH`.
* **`winget` Interactive Prompt & Download Timeout:** `winget install --id=Gyan.FFmpeg -e` stalled on the `msstore` source agreement prompt and later timed out (`InternetReadFile() failed. 0x80072ee2`) downloading the archive. Used `--source winget --accept-source-agreements --accept-package-agreements` or downloaded/extracted FFmpeg directly to a local folder (`C:\ffmpeg`) added to `PATH`.
* **PowerShell Inline Script Encoding & Escaping Errors:** Piping multi-line Python patch scripts into `python -` in PowerShell triggered `SyntaxError` (`\x97` em-dash / non-UTF-8 and unterminated strings), `NameError: name 'nl' is not defined`, and `TerminatorExpectedAtEndOfString`. Switched to ASCII-safe patchers, `chr(10)` newlines, and `ast.parse(...)` syntax checks before saving `pipeline/assemble.py`.

## 3. Assembly, Audio Transitions & Subtitles

* **Background Music Dips Across Shot Boundaries:** Per-clip music slicing and fade-outs caused audio dips between clips. Updated `pipeline/assemble.py` to render per-shot clips with narration and subtle room bed first, blend visuals with `xfade` and concatenate audio with `concat`, and mix continuous background music across the full timeline with a single end fade-out.
* **Question-Mark Placeholders (`???`) in Burned Subtitles from `shot_05` to `shot_10`:** Burned-in subtitles rendered as `?` starting at `shot_05` due to `?` placeholders in `narration_am` for `shot_05` - `shot_10` and Amharic subtitle burn-in issues. Updated `pipeline/assemble.py` to support English subtitles (`subtitles_en`) or omit `--burn-subs` for clean visuals while keeping Amharic WAV narration files intact.
