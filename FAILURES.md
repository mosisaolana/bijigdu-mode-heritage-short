Failures & Troubleshooting Log
Failure 1: Gemini 400 API_KEY_INVALID and Downstream FileNotFoundError in radio_cut.py
- Stage / Script: Phase 1 Narration (pipeline/narration.py) and Radio Cut (pipeline/radio_cut.py)
- Symptom: pipeline/narration.py returned 400 INVALID_ARGUMENT (API_KEY_INVALID), followed by FileNotFoundError on outputs/audio/shot_01.wav in pipeline/radio_cut.py.
- Root Cause: GEMINI_API_KEY was not properly set in the active shell on the initial attempt, and radio_cut.py was executed before narration.py completed.
- Fix / Workaround: Set a valid GEMINI_API_KEY in PowerShell, ran pipeline/narration.py standalone first to generate the .wav files, and then ran pipeline/radio_cut.py.
- Takeaway: Run stages sequentially during first-time setup and verify prerequisites before assembly.
Failure 2: 404 NOT_FOUND on gemini-2.5-flash During Key Verification
- Stage / Script: Quick API key check
- Symptom: Calling gemini-2.5-flash returned 404 NOT_FOUND indicating it is no longer available to new users and pointing to gemini-3.8-flash.
- Root Cause: Outdated model name in the quick test command, not an invalid API key.
- Fix / Workaround: Used current gemini-3.8-flash family models (gemini-3.8-flash-tts for narration).
- Takeaway: Keep model names current and document API/model quirks right away.
Failure 3: Transient Rate Limit During 10-Shot Narration Batch (shot_08-shot_10)
- Stage / Script: Phase 1 Narration (pipeline/narration.py)
- Symptom: Running pipeline/narration.py across all 10 shots stopped after generating shot_01.wav through shot_07.wav, leaving shot_08, shot_09, and shot_10 ungenerated.
- Root Cause: API request-per-minute throttling / transient interruption mid-batch.
- Fix / Workaround: Leveraged .wav.cachekey caching to skip the 7 completed shots and re-ran python pipeline/narration.py --shots shot_08 shot_09 shot_10 to complete the remaining audio files cleanly.
- Takeaway: Per-shot hash caching prevents wasted API calls and allows clean recovery from mid-batch rate limits.
Failure 4: FileNotFoundError: [WinError 2] in pipeline/radio_cut.py (Missing FFmpeg)
- Stage / Script: Phase 1 Radio Cut (pipeline/radio_cut.py)
- Symptom: Running python pipeline/radio_cut.py failed on subprocess.run(...) with FileNotFoundError: [WinError 2] The system cannot find the file specified.
- Root Cause: ffmpeg.exe was not installed or registered on the Windows PATH.
- Fix / Workaround: Installed FFmpeg on Windows and refreshed the PowerShell session PATH before re-running radio_cut.py.
- Takeaway: Document ffmpeg as an explicit system prerequisite in README.md.
Failure 5: winget install Hanging on Interactive msstore Source Agreement Prompt
- Stage / Script: Environment Setup (Installing Gyan.FFmpeg)
- Symptom: Running winget install --id=Gyan.FFmpeg -e stalled at Do you agree to all the source agreements terms? even after typing Y and pressing Enter.
- Root Cause: winget defaults to querying the msstore source and waiting on interactive agreement confirmation/catalog refresh.
- Fix / Workaround: Passed --source winget --accept-source-agreements --accept-package-agreements to bypass the msstore prompt and install cleanly.
- Takeaway: Use non-interactive flags (--source winget --accept-source-agreements --accept-package-agreements) when scripting or documenting Windows package installs.
Failure 6: winget Download Timeout (InternetReadFile() failed. 0x80072ee2)
- Stage / Script: Environment Setup (Installing Gyan.FFmpeg Version 9.1)
- Symptom: winget resolved Gyan.FFmpeg Version 9.1 and began downloading ffmpeg-9.1-full_build.zip from GitHub, then failed with InternetReadFile() failed. 0x80072ee2 : unknown error.
- Root Cause: Network timeout or interrupted connection in winget's built-in downloader while retrieving the large release archive from GitHub.
- Fix / Workaround: Download the FFmpeg release archive directly via browser or curl with retry/resumable transfer, extract ffmpeg.exe to a local folder (such as C:\ffmpeg), and add its bin directory to PATH.
- Takeaway: Keep a direct download fallback ready when winget times out on large external release archives.
Failure 9: 429 RESOURCE_EXHAUSTED on gemini-3.8-flash-tts Free Tier Daily Limit (10 RPD)
- Stage / Script: Phase 1 Narration Regeneration (pipeline/narration.py -> pipeline/radio_cut.py)
- Symptom: After deleting cached .wav files to regenerate narration with updated storyboard text, narration.py failed on shot_03 with 429 RESOURCE_EXHAUSTED (GenerateRequestsPerDayPerProjectPerModel-FreeTier, limit 10), causing radio_cut.py to fail with Missing narration file: outputs\audio\shot_03.wav.
- Root Cause: Free Tier daily request quota (10 requests/day) on gemini-3.8-flash-tts was exhausted after earlier runs and full regeneration attempts.
- Fix / Workaround: Wait for the quota reset window (~87 minutes), switch to a project/key with available quota, or advance non-TTS work (such as FAILURES.md logging, Git commits, and Phase 2 keyframe generation) while waiting, then re-run python pipeline/narration.py and python pipeline/radio_cut.py.
- Takeaway: Avoid wiping all cached .wav files unnecessarily when daily TTS request caps are tight, and batch/verify shots carefully before regenerating.
Failure 10: Image Generation Quota Exhaustion & Historical Currency Accuracy on shot_08
- Stage / Script: Storyboard & Keyframe Generation (storyboard.json / pipeline/keyframes.py)
- Symptom: Automated regeneration of shot_08 was blocked by image generation quota exhaustion while updating shot_08 to remove modern dollar bills/paper money and depict Oromo community members taking a cow and an ox offer with additional old Ethiopian silver currency called Xegera.
- Root Cause: Image generation quota was reached, and initial shot_08 prompts/keyframes required explicit exclusion of modern currency/dollar bills alongside the cow, ox, and Xegera silver currency details.
- Fix / Workaround: Updated shot_08 reason, image_prompt, motion_prompt, and seed in storyboard.json to depict Oromo community members taking a cow and an ox offer plus Xegera silver currency with zero dollar bills or paper banknotes, and cleared cached shot_08 clips for regeneration once quota resets.
- Takeaway: Put explicit historical currency constraints into storyboard.json and clear stale shot_08 clip caches when prompts change.
Failure 11: PowerShell Inline Script Encoding & Escaping Errors (SyntaxError, NameError, TerminatorExpectedAtEndOfString)
- Stage / Script: Storyboard & Assembly Patching (PowerShell -> python -)
- Symptom: Piping multi-line Python scripts into python - in PowerShell triggered SyntaxError: Non-UTF-8 code starting with '\x97', SyntaxError: unterminated string literal, NameError: name 'nl' is not defined, and TerminatorExpectedAtEndOfString.
- Root Cause: Non-ASCII characters (em-dash), doubled newline escapes inside triple-quoted patch strings, and long pasted blocks clipping in PowerShell.
- Fix / Workaround: Used ASCII-safe patch scripts, chr(10) line breaks, and ast.parse(...) validation before writing pipeline/assemble.py.
- Takeaway: Keep PowerShell-piped Python scripts ASCII-safe and syntax-checked with ast.parse before saving.
Failure 12: Background Music Dips Across Shot Transitions
- Stage / Script: Video Assembly (pipeline/assemble.py)
- Symptom: Background music experienced audible dips or interruptions across shot boundaries during assembly.
- Root Cause: Per-clip music slicing and fade-outs interacted with clip joins instead of running a continuous music track across the stitched timeline.
- Fix / Workaround: Updated pipeline/assemble.py to render per-shot clips with narration and subtle room bed first, blend video with xfade and concatenate audio with concat, and mix background music continuously across the full duration with a single fade-out at the end.
- Takeaway: Mix continuous background music across the stitched timeline rather than per clip.
Failure 13: Burned Amharic Subtitle Rendering Glitches ("???") Starting at shot_05
- Stage / Script: Subtitle Generation & Burn-In (storyboard.json / pipeline/assemble.py)
- Symptom: Burned-in Amharic subtitles rendered as question marks ("???") from shot_05 through shot_10.
- Root Cause: narration_am for shot_05 through shot_10 contained ? placeholders in storyboard.json, and Amharic subtitle burn-in continued to fail on those shots.
- Fix / Workaround: Updated pipeline/assemble.py to use English subtitles (subtitles_en) or omit --burn-subs when clean visuals are preferred, leaving narration WAV files intact.
- Takeaway: Check storyboard text for ? placeholders before burning subtitles, and keep an English-only or subtitle-free fallback ready near deadlines.
-------------------
