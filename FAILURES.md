# Failures & Troubleshooting Log

## Failure 1: Gemini `400 API_KEY_INVALID` and Downstream `FileNotFoundError` in `radio_cut.py`
- **Stage / Script:** Phase 1 Narration (`pipeline/narration.py`) and Radio Cut (`pipeline/radio_cut.py`)
- **Symptom:** `pipeline/narration.py` returned `400 INVALID_ARGUMENT` (`API_KEY_INVALID`), followed by `FileNotFoundError` on `outputs/audio/shot_01.wav` in `pipeline/radio_cut.py`.
- **Root Cause:** `GEMINI_API_KEY` was not properly set in the active shell on the initial attempt, and `radio_cut.py` was executed before `narration.py` completed.
- **Fix / Workaround:** Set a valid `GEMINI_API_KEY` in PowerShell, ran `pipeline/narration.py` standalone first to generate the `.wav` files, and then ran `pipeline/radio_cut.py`.
- **Takeaway:** Run stages sequentially during first-time setup and verify prerequisites before assembly.

## Failure 2: `404 NOT_FOUND` on `gemini-2.5-flash` During Key Verification
- **Stage / Script:** Quick API key check
- **Symptom:** Calling `gemini-2.5-flash` returned `404 NOT_FOUND` indicating it is no longer available to new users and pointing to `gemini-3.8-flash`.
- **Root Cause:** Outdated model name in the quick test command, not an invalid API key.
- **Fix / Workaround:** Used current `gemini-3.8-flash` family models (`gemini-3.8-flash-tts` for narration).
- **Takeaway:** Keep model names current and document API/model quirks right away.

## Failure 3: Transient Rate Limit During 10-Shot Narration Batch (`shot_08`–`shot_10`)
- **Stage / Script:** Phase 1 Narration (`pipeline/narration.py`)
- **Symptom:** Running `pipeline/narration.py` across all 10 shots stopped after generating `shot_01.wav` through `shot_07.wav`, leaving `shot_08`, `shot_09`, and `shot_10` ungenerated.
- **Root Cause:** API request-per-minute throttling / transient interruption mid-batch.
- **Fix / Workaround:** Leveraged `.wav.cachekey` caching to skip the 7 completed shots and re-ran `python pipeline/narration.py --shots shot_08 shot_09 shot_10` to complete the remaining audio files cleanly.
- **Takeaway:** Per-shot hash caching prevents wasted API calls and allows clean recovery from mid-batch rate limits.

## Failure 4: `FileNotFoundError: [WinError 2]` in `pipeline/radio_cut.py` (Missing FFmpeg)
- **Stage / Script:** Phase 1 Radio Cut (`pipeline/radio_cut.py`)
- **Symptom:** Running `python pipeline/radio_cut.py` failed on `subprocess.run(...)` with `FileNotFoundError: [WinError 2] The system cannot find the file specified`.
- **Root Cause:** `ffmpeg.exe` was not installed or registered on the Windows `PATH`.
- **Fix / Workaround:** Installed FFmpeg on Windows and refreshed the PowerShell session `PATH` before re-running `radio_cut.py`.
- **Takeaway:** Document `ffmpeg` as an explicit system prerequisite in `README.md`.

## Failure 5: `winget install` Hanging on Interactive `msstore` Source Agreement Prompt
- **Stage / Script:** Environment Setup (Installing `Gyan.FFmpeg`)
- **Symptom:** Running `winget install --id=Gyan.FFmpeg -e` stalled at `Do you agree to all the source agreements terms?` even after typing `Y` and pressing Enter.
- **Root Cause:** `winget` defaults to querying the `msstore` source and waiting on interactive agreement confirmation/catalog refresh.
- **Fix / Workaround:** Passed `--source winget --accept-source-agreements --accept-package-agreements` to bypass the `msstore` prompt and install cleanly.
- **Takeaway:** Use non-interactive flags (`--source winget --accept-source-agreements --accept-package-agreements`) when scripting or documenting Windows package installs.

## Failure 6: `winget` Download Timeout (`InternetReadFile() failed. 0x80072ee2`)
- **Stage / Script:** Environment Setup (Installing `Gyan.FFmpeg` Version 9.1)
- **Symptom:** `winget` resolved `Gyan.FFmpeg` Version 9.1 and began downloading `ffmpeg-9.1-full_build.zip` from GitHub, then failed with `InternetReadFile() failed. 0x80072ee2 : unknown error`.
- **Root Cause:** Network timeout or interrupted connection in `winget`'s built-in downloader while retrieving the large release archive from GitHub.
- **Fix / Workaround:** Download the FFmpeg release archive directly via browser or `curl` with retry/resumable transfer, extract `ffmpeg.exe` to a local folder (such as `C:\ffmpeg`), and add its `bin` directory to `PATH`.
- **Takeaway:** Keep a direct download fallback ready when `winget` times out on large external release archives.
