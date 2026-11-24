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
