from pathlib import Path
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import load_json, validate_storyboard


def get_wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def main() -> None:
    sb = load_json(ROOT / "storyboard.json")
    validate_storyboard(sb, ROOT / "schema/storyboard.schema.json")

    audio_dir = ROOT / "outputs/audio"
    out_mp4 = ROOT / "outputs/final/radio_cut.mp4"
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    concat_list = audio_dir / "radio_concat.txt"
    lines = []
    total_dur = 0.0
    for shot in sb["shots"]:
        wav_path = audio_dir / f"{shot['shot_id']}.wav"
        if not wav_path.exists():
            raise FileNotFoundError(f"Missing narration file: {wav_path}. Run pipeline/narration.py first.")
        total_dur += get_wav_duration(wav_path)
        safe_p = str(wav_path.resolve()).replace("\\", "/").replace("'", "'\\''")
        lines.append(f"file '{safe_p}'")

    concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")
    merged_wav = audio_dir / "radio_narration_merged.wav"

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:a", "pcm_s16le", str(merged_wav)],
        check=True,
    )

    # Black video + narration + quiet placeholder ambient bed (low-level pink/brown noise stand-in)
    dur_arg = f"{max(total_dur, 1.0):.2f}"
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=24:d={dur_arg}",
        "-i", str(merged_wav),
        "-f", "lavfi", "-i", f"anoisesrc=d={dur_arg}:c=brown:a=0.015",
        "-filter_complex", "[1:a]volume=1.0[voice];[2:a]volume=0.25[bed];[voice][bed]amix=inputs=2:duration=first[aout]",
        "-map", "0:v:0",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    print(f"Radio cut created: {out_mp4} (~{total_dur:.1f}s)")


if __name__ == "__main__":
    main()
