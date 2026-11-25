import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import load_json, run_cached_stage_item, validate_storyboard


def get_wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def format_srt_time(seconds: float) -> str:
    ms_total = max(0, int(round(seconds * 1000.0)))
    hours = ms_total // 3_600_000
    rem = ms_total % 3_600_000
    minutes = rem // 60_000
    rem %= 60_000
    secs = rem // 1000
    millis = rem % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_srt(shots: list[dict], audio_dir: Path, srt_path: Path) -> float:
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    cursor = 0.0
    blocks: list[str] = []

    for idx, shot in enumerate(shots, start=1):
        dur = float(shot["duration_sec"])
        wav_path = audio_dir / f"{shot['shot_id']}.wav"
        spoken_dur = get_wav_duration(wav_path) if wav_path.exists() else dur
        cue_dur = min(dur, max(spoken_dur, dur * 0.6))
        start_t = cursor
        end_t = cursor + cue_dur

        am = (shot.get("narration_am") or "").strip()
        en = (shot.get("subtitles_en") or "").strip()
        text = f"{am}\n{en}".strip() if (am and en) else (am or en or shot["shot_id"])

        blocks.append(f"{idx}\n{format_srt_time(start_t)} --> {format_srt_time(end_t)}\n{text}\n")
        cursor += dur

    srt_path.write_text("\n".join(blocks), encoding="utf-8")
    return cursor


def dims_for_aspect(aspect: str) -> tuple[int, int, int, int]:
    if aspect == "16:9":
        return 1920, 1080, 3840, 2160
    return 1080, 1920, 2160, 3840


def ken_burns_filter(
    idx: int,
    duration_sec: float,
    motion_prompt: str,
    out_w: int,
    out_h: int,
    pre_w: int,
    pre_h: int,
    fps: int = 24,
    aspect: str = "9:16",
) -> str:
    frames = max(1, int(round(duration_sec * fps)))
    mp = (motion_prompt or "").lower()
    is_wide = aspect == "16:9"

    if is_wide:
        # Fit full portrait height cleanly with zoomed-out framing and top-biased y (near 0 = top of frame)
        base = f"scale=-1:{pre_h}:force_original_aspect_ratio=decrease,pad={pre_w}:{pre_h}:(ow-iw)/2:0:black,setsar=1"
        y_expr = "0"
        if "pull" in mp or "wide" in mp or idx % 3 == 2:
            z_expr = f"0.96-0.06*(on/{max(frames-1, 1)})"
            x_expr = "(iw-iw/zoom)/2"
        elif "pan" in mp or "track" in mp or idx % 3 == 1:
            z_expr = "0.90"
            x_expr = f"max(0,min(iw-iw/zoom,(iw-iw/zoom)*(0.5+0.25*sin(2*PI*on/{max(frames, 1)}))))"
        else:
            z_expr = f"0.88+0.06*(on/{max(frames-1, 1)})"
            x_expr = "(iw-iw/zoom)/2"
    else:
        base = f"scale={pre_w}:{pre_h}:force_original_aspect_ratio=increase,crop={pre_w}:{pre_h},setsar=1"
        y_expr = "max(0,(ih-ih/zoom)*0.30)"
        if "pull" in mp or "wide" in mp or idx % 3 == 2:
            z_expr = f"1.10-0.10*(on/{max(frames-1, 1)})"
            x_expr = "(iw-iw/zoom)/2"
        elif "pan" in mp or "track" in mp or idx % 3 == 1:
            z_expr = "1.06"
            x_expr = f"(iw-iw/zoom)*(on/{max(frames-1, 1)})"
        else:
            z_expr = f"1.0+0.10*(on/{max(frames-1, 1)})"
            x_expr = "(iw-iw/zoom)/2"

    return (
        f"{base},"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s={out_w}x{out_h}:fps={fps},"
        f"format=yuv420p"
    )



def render_shot_clip(
    idx: int,
    shot: dict,
    keyframe_path: Path,
    wav_path: Path,
    clip_path: Path,
    aspect: str,
    fps: int = 24,
) -> None:
    out_w, out_h, pre_w, pre_h = dims_for_aspect(aspect)
    dur = float(shot["duration_sec"])
    dur_str = f"{dur:.3f}"
    vf = ken_burns_filter(idx, dur, shot.get("motion_prompt", ""), out_w, out_h, pre_w, pre_h, fps=fps, aspect=aspect)

    filter_complex = (
        f"[0:v]{vf}[vout];"
        f"[1:a]apad,atrim=0:{dur_str},asetpts=PTS-STARTPTS,volume=1.0[voice];"
        f"[2:a]atrim=0:{dur_str},asetpts=PTS-STARTPTS,volume=0.25[bed];"
        f"[voice][bed]amix=inputs=2:duration=first:dropout_transition=0,aresample=48000[aout]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(keyframe_path),
        "-i", str(wav_path),
        "-f", "lavfi",
        "-i", f"anoisesrc=d={dur_str}:c=brown:a=0.015",
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", dur_str,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(clip_path),
    ]
    subprocess.run(cmd, check=True)


def escape_ffmpeg_path(p: Path) -> str:
    s = str(p.resolve()).replace("\\", "/")
    s = re.sub(r"^([A-Za-z]):", r"\1\\:", s)
    return s.replace("'", "\\'")


def render_end_card(end_card_path: Path, out_w: int, out_h: int, fps: int = 24, card_dur: float = 2.5) -> None:
    dur_str = f"{card_dur:.2f}"
    sub_file = end_card_path.parent / f"end_card_{out_w}x{out_h}.srt"
    srt_content = (
        "1\n"
        f"00:00:00,000 --> 00:00:02,500\n"
        "Made with AI - Heritage Short Pipeline\n"
        "Emebet Bijigdu Mode (Guduru Malole Warada, Wellega Awraja)\n"
    )
    sub_file.write_text(srt_content, encoding="utf-8")
    escaped_sub = escape_ffmpeg_path(sub_file)
    fs = 18 if out_w >= 1920 else 14
    vf = f"subtitles='{escaped_sub}':force_style='FontSize={fs},Alignment=5,Outline=1,Shadow=0'"
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={out_w}x{out_h}:r={fps}:d={dur_str}",
        "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
        "-t", dur_str,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(end_card_path),
    ]
    subprocess.run(cmd, check=True)


def loudnorm_two_pass(input_mp4: Path, output_mp4: Path) -> None:
    probe_cmd = [
        "ffmpeg", "-y",
        "-i", str(input_mp4),
        "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
        "-f", "null", "-",
    ]
    proc = subprocess.run(probe_cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        blocks = re.findall(r"\{[\s\S]*?\}", proc.stderr)
        for raw_json in reversed(blocks):
            try:
                stats = json.loads(raw_json)
                if "input_i" in stats and "input_tp" in stats:
                    af = (
                        f"loudnorm=I=-14:TP=-1.0:LRA=11:"
                        f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
                        f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
                        f"offset={stats['target_offset']}:linear=true:print_format=summary"
                    )
                    res = subprocess.run(
                        [
                            "ffmpeg", "-y",
                            "-i", str(input_mp4),
                            "-c:v", "copy",
                            "-af", af,
                            "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart",
                            str(output_mp4),
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if res.returncode == 0:
                        return
            except Exception:
                continue

    # Fallback: normalize sample format/rate and apply safe true-peak ceiling near -1 dB
    fallback_af = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,alimiter=limit=0.891:attack=5:release=50"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(input_mp4),
            "-c:v", "copy",
            "-af", fallback_af,
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_mp4),
        ],
        check=True,
    )



def assemble_for_aspect(
    sb: dict,
    aspect: str,
    fps: int,
    burn_subs: bool,
    font_size: int,
    srt_path: Path,
    keyframes_dir: Path,
    audio_dir: Path,
    clips_dir: Path,
    final_dir: Path,
) -> Path:
    tag = "16x9" if aspect == "16:9" else "9x16"
    out_w, out_h, _, _ = dims_for_aspect(aspect)
    aspect_clips_dir = clips_dir / tag
    aspect_clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths: list[Path] = []
    for idx, shot in enumerate(sb["shots"]):
        shot_id = shot["shot_id"]
        kf = keyframes_dir / f"{shot_id}.png"
        wav = audio_dir / f"{shot_id}.wav"
        if not kf.exists():
            raise FileNotFoundError(f"Missing keyframe: {kf}. Run pipeline/keyframes.py first.")
        if not wav.exists():
            raise FileNotFoundError(f"Missing narration WAV: {wav}. Run pipeline/narration.py first.")

        clip_path = aspect_clips_dir / f"{shot_id}_{tag}.mp4"
        cache_payload = {
            "shot_id": shot_id,
            "aspect": aspect,
            "framing_v": "headroom_16x9" if aspect == "16:9" else "center",
            "duration_sec": shot["duration_sec"],
            "motion_prompt": shot.get("motion_prompt", ""),
            "fps": fps,
            "kf_size": kf.stat().st_size,
            "wav_size": wav.stat().st_size,
        }

        def _render_one(i: int = idx, s: dict = shot, k: Path = kf, w: Path = wav, c: Path = clip_path, asp: str = aspect) -> dict:
            render_shot_clip(i, s, k, w, c, aspect=asp, fps=fps)
            return {"clip": str(c), "bytes": c.stat().st_size}

        run_cached_stage_item(
            stage="assemble_clip",
            shot_id=f"{shot_id}_{tag}",
            model="ffmpeg-9.1-zoompan",
            cache_payload=cache_payload,
            output_path=clip_path,
            fn=_render_one,
            seed=shot.get("seed"),
        )
        clip_paths.append(clip_path)

    end_card_path = aspect_clips_dir / f"end_card_{tag}.mp4"
    render_end_card(end_card_path, out_w=out_w, out_h=out_h, fps=fps, card_dur=2.5)
    clip_paths.append(end_card_path)

    concat_file = aspect_clips_dir / f"concat_{tag}.txt"
    concat_lines = []
    for cp in clip_paths:
        safe_p = str(cp.resolve()).replace("\\", "/").replace("'", "'\\''")
        concat_lines.append(f"file '{safe_p}'")
    concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    stitched_mp4 = aspect_clips_dir / f"stitched_{tag}.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(stitched_mp4)],
        check=True,
    )

    subbed_mp4 = aspect_clips_dir / f"subbed_{tag}.mp4"
    if burn_subs:
        escaped_srt = escape_ffmpeg_path(srt_path)
        vf_subs = f"subtitles='{escaped_srt}':force_style='FontSize={font_size},MarginV=28,Outline=1,Shadow=0,Alignment=2'"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(stitched_mp4),
                "-vf", vf_subs,
                "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(subbed_mp4),
            ],
            check=True,
        )
    else:
        subbed_mp4 = stitched_mp4

    final_mp4 = final_dir / f"bijigdu_mode_75s_{tag}.mp4"
    loudnorm_two_pass(subbed_mp4, final_mp4)
    return final_mp4


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble heritage short film in 9:16 and/or 16:9.")
    parser.add_argument("--storyboard", default="storyboard.json")
    parser.add_argument("--aspect", choices=["9:16", "16:9", "both"], default="both")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--font-size", type=int, default=8)
    parser.add_argument("--burn-subs", action="store_true", help="Burn generated SRT subtitles into final MP4")
    args = parser.parse_args()

    sb = load_json(ROOT / args.storyboard)
    validate_storyboard(sb, ROOT / "schema/storyboard.schema.json")

    keyframes_dir = ROOT / "outputs/keyframes"
    audio_dir = ROOT / "outputs/audio"
    clips_dir = ROOT / "outputs/clips"
    final_dir = ROOT / "outputs/final"
    final_dir.mkdir(parents=True, exist_ok=True)

    srt_path = final_dir / "bijigdu_mode_75s.srt"
    total_dur = build_srt(sb["shots"], audio_dir, srt_path)

    aspects = ["9:16", "16:9"] if args.aspect == "both" else [args.aspect]
    built: list[Path] = []
    for asp in aspects:
        built.append(
            assemble_for_aspect(
                sb=sb,
                aspect=asp,
                fps=args.fps,
                burn_subs=args.burn_subs,
                font_size=args.font_size,
                srt_path=srt_path,
                keyframes_dir=keyframes_dir,
                audio_dir=audio_dir,
                clips_dir=clips_dir,
                final_dir=final_dir,
            )
        )

    for p in built:
        print(f"Exported: {p} (~{total_dur + 2.5:.1f}s incl. end card) | SRT: {srt_path}")


if __name__ == "__main__":
    main()
