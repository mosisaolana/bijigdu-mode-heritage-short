# Ethics, Consent, Licences & AI Labelling

## 1. Consent Record (Likeness, Photo & Voice)
- **Historical Figure & Likeness**: Emebet Bijigdu Mode (Governor of Guduru Malole Warada, Wellega Awraja). Includes family photograph (`Bijigdu picture.jpg`, archived at `outputs/refs/bijigdu_actual.jpg`) and AI-generated keyframes depicting her traditional regalia (*Kaba*, *Zinar*, pistol) and silver-chained mule.
- **Informed Consent & Family Permission**: Informed consent to share Emebet Bijigdu Mode's heritage story and use `Bijigdu picture.jpg` in this project was granted by the user's mother (daughter of Emebet Bijigdu Mode) on [Add date, e.g., November 2026]. No private or sensitive personal details of living individuals are exposed without consent.
- **Narration Voice**: Amharic narration is synthesized via text-to-speech (`pipeline/narration.py`), not cloned from a living or real person's voice.

## 2. Model & Tool Licences
- **Keyframe Image Model (`@cf/black-forest-labs/flux-1-schnell`)**: Invoked via Cloudflare Workers AI; subject to Black Forest Labs and Cloudflare Workers AI usage/licence terms.
- **Narration TTS**: [Add exact TTS model/provider name and licence terms used in `pipeline/narration.py`.]
- **Video & Audio Assembly (`FFmpeg 9.1` with `libass`, `libx264`, `aac`)**: Open-source / GPL tooling; subject to applicable FFmpeg and codec licence terms.
- **Repository Code & Storyboard**: [Add your chosen repository licence, e.g., MIT or Apache-2.0.]

## 3. AI Labelling & Provenance Plan
- **Burned-In End Card**: Both `9:16` and `16:9` exports include a visible 2.5-second end card (`Made with AI - Heritage Short Pipeline`) generated in `pipeline/assemble.py`.
- **Platform Disclosure**: When publishing the film publicly, the platform's native AI-generated/altered content label is switched on.
- **Provenance & Privacy**: Output metadata is preserved where supported, and API keys, tokens, and private records remain excluded from the public repository.
