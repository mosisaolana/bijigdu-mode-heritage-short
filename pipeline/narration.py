import argparse
import os
from pathlib import Path
import sys
import wave
import io

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import load_json, run_cached_stage_item, validate_storyboard


def _extract_wav_bytes(response) -> bytes:
    for cand in getattr(response, "candidates", []) or []:
        content = getattr(cand, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                data = inline.data
                if isinstance(data, bytes):
                    # If already a RIFF WAV, return directly; otherwise wrap 24kHz 16-bit mono PCM
                    if data[:4] == b"RIFF":
                        return data
                    buf = io.BytesIO()
                    with wave.open(buf, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(data)
                    return buf.getvalue()
    raise RuntimeError("No audio bytes returned by Gemini TTS.")


def generate_shot_narration(
    client: genai.Client,
    shot: dict,
    voice_name: str,
    style_hint: str,
    out_path: Path,
) -> dict:
    # Keep spoken text strictly clean (no stage directions inside text)
    text = shot["narration_am"]
    response = client.models.generate_content(
        model="gemini-3.8-flash-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        ),
    )
    wav_bytes = _extract_wav_bytes(response)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(wav_bytes)
    return {"bytes": len(wav_bytes), "style_hint": style_hint}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate per-shot Amharic narration via Gemini TTS.")
    parser.add_argument("--shots", nargs="*", help="Optional subset of shot_ids, e.g., shot_01 shot_06")
    parser.add_argument("--voice", default="Kore", help="Prebuilt Gemini voice name (default: Kore)")
    parser.add_argument("--style", default="calm, warm, dignified, unhurried storytelling", help="Delivery style note")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set. Add it to your environment or .env file.")

    sb = load_json(ROOT / "storyboard.json")
    validate_storyboard(sb, ROOT / "schema/storyboard.schema.json")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(api_version="v1beta"),
    )

    selected = set(args.shots) if args.shots else None
    for shot in sb["shots"]:
        sid = shot["shot_id"]
        if selected and sid not in selected:
            continue

        out_wav = ROOT / "outputs/audio" / f"{sid}.wav"
        payload = {
            "model": "gemini-3.8-flash-tts",
            "voice": args.voice,
            "style": args.style,
            "narration_am": shot["narration_am"],
            "duration_sec": shot["duration_sec"],
        }
        res = run_cached_stage_item(
            stage="narration",
            shot_id=sid,
            model="gemini-3.8-flash-tts",
            cache_payload=payload,
            output_path=out_wav,
            fn=lambda s=shot, p=out_wav: generate_shot_narration(client, s, args.voice, args.style, p),
            log_path=ROOT / "runs.jsonl",
            seed=None,
            estimated_cost_usd=0.0,
        )
        print(f"{sid}: cached={res['cached']} -> {out_wav}")


if __name__ == "__main__":
    main()
