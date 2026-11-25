# Ethics, Consent, Licences & AI Labelling

## 1. Consent Record (Likeness, Photo & Voice)
- **Historical Figure & Likeness**: Emebet Bijigdu Mode (Governor of Guduru Malole Warada, Wellega Awraja). Historical photograph (`Bijigdu picture.jpg`, archived at `outputs/refs/bijigdu_actual.jpg`) and AI-generated keyframes depicting her traditional regalia (*Kaba*, *Zinar*, pistol) and silver-chained mule.
- **Consent & Family Permission**: [Add who gave informed consent/permission from your family or stakeholders to depict Emebet Bijigdu Mode's likeness, photograph, and family history, and when that consent was confirmed.]
- **Narration Voice**: Amharic narration is synthesized via text-to-speech (`pipeline/narration.py`), not cloned from a living or real person's voice.

## 2. Model & Tool Licences
- **Keyframe Image Model (`@cf/black-forest-labs/flux-1-schnell`)**: Called via Cloudflare Workers AI; verify and note the exact Black Forest Labs / Cloudflare licence terms for your usage.
- **Narration TTS**: [Add exact TTS model name/provider and terms used in `pipeline/narration.py`.]
- **Video & Audio Assembly (`FFmpeg 9.1` with `libass`, `libx264`, `aac`)**: Open-source / GPL tooling; check distribution terms for any bundled binaries or scripts.
- **Repository Code & Storyboard**: [Add your chosen repository licence, e.g., MIT or Apache-2.0.]

## 3. AI Labelling & Provenance Plan
- **Burned-In End Card**: Both `9:16` and `16:9` exports include a visible 2.5-second end card (`Made with AI - Heritage Short Pipeline`) generated in `pipeline/assemble.py`.
- **Platform Disclosure**: When publishing the film publicly, switch on the platform's native AI-generated/altered content label (e.g., YouTube, TikTok, Meta, or your hosting platform).
- **Provenance & Privacy**: Retain output metadata where possible and keep private family details and API secrets out of the public repository.
