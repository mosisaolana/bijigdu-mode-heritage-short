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

DEFAULT_MUSIC_PATH = Path(r"C:\Users\Dude\Downloads\Legacy_of_the_Plateau.mp3")


def find_ethiopic_font() -> str:
    fonts_dir = Path(r"C:\Windows\Fonts")
    candidates = [
        ("Abyssinica SIL", ["*abyssinica*.ttf", "*abyssinica*.otf"]),
        ("Nyala", ["*nyala*.ttf"]),
        ("Noto Sans Ethiopic", ["*ethiopic*.ttf", "*ethiopic*.otf"]),
        ("Ebrima", ["*ebrima*.ttf"]),
    ]
    if fonts_dir.exists():
        for font_name, patterns in candidates:
            for pat in patterns:
                if list(fonts_dir.glob(pat)):
                    return font_name
    return "Abyssinica SIL"


def get_wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def effective_shot_duration(shot: dict, audio_dir: Path) -> tuple[float, float]:
    base_dur = float(shot["duration_sec"])
    wav_path = audio_dir / f"{shot['shot_id']}.wav"
    spoken_dur = get_wav_duration(wav_path) if wav_path.exists() else base_dur
    # Prevent cutting off spoken Amharic audio when WAV runs slightly longer than storyboard_dur
    clip_dur = max(base_dur, spoken_dur + 0.15)
    return round(clip_dur, 3), spoken_dur


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
        clip_dur, spoken_dur = effective_shot_duration(shot, audio_dir)
        cue_dur = min(clip_dur, max(spoken_dur + 0.10, clip_dur * 0.85))
        start_t = cursor
        end_t = cursor + cue_dur

        am = (shot.get("narration_am") or "").strip()
        en = (shot.get("subtitles_en") or "").strip()
        text = f"{am}\n{en}".strip() if (am and en) else (am or en or shot["shot_id"])

        blocks.append(f"{idx}\n{format_srt_time(start_t)} --> {format_srt_time(end_t)}\n{text}\n")
        cursor += clip_dur

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
        base = (
            f"scale=-1:{pre_h}:force_original_aspect_ratio=decrease,"
            f"pad={pre_w}:{pre_h}:(ow-iw)/2:0:black,setsar=1"
        )
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


def effective_shot_duration(shot: dict, audio_dir: Path) -> tuple[float, float]:
    base_dur = float(shot["duration_sec"])
    wav_path = audio_dir / f"{shot['shot_id']}.wav"
    spoken_dur = get_wav_duration(wav_path) if wav_path.exists() else base_dur
    return round(max(base_dur, spoken_dur + 0.25), 3), spoken_dur


def stitch_with_xfade(
    clips_and_durs: list[tuple[Path, float]],
    stitched_mp4: Path,
    fps: int = 24,
    xfade_dur: float = 0.30,
) -> float:
    cmd = ["ffmpeg", "-y"]
    for cp, _ in clips_and_durs:
        cmd.extend(["-i", str(cp)])

    n = len(clips_and_durs)
    parts: list[str] = []
    for i in range(n):
        parts.append(f"[{i}:v]fps={fps},format=yuv420p,setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,asetpts=PTS-STARTPTS[a{i}]")

    if n == 1:
        parts.append("[v0]copy[vfinal]")
        parts.append("[a0]anull[afinal]")
        total_out_dur = clips_and_durs[0][1]
    else:
        prev_v = "v0"
        cum_dur = clips_and_durs[0][1]
        for i in range(1, n):
            offset = max(0.0, cum_dur - xfade_dur)
            out_v = "vfinal" if i == n - 1 else f"vx{i}"
            parts.append(
                f"[{prev_v}][v{i}]xfade=transition=fade:duration={xfade_dur:.3f}:offset={offset:.3f}[{out_v}]"
            )
            prev_v = out_v
            cum_dur = offset + clips_and_durs[i][1]
        total_out_dur = cum_dur
        a_inputs = "".join(f"[a{i}]" for i in range(n))
        parts.append(f"{a_inputs}concat=n={n}:v=0:a=1,asetpts=PTS-STARTPTS[afinal]")

    cmd.extend([
        "-filter_complex", ";".join(parts),
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(stitched_mp4),
    ])
    subprocess.run(cmd, check=True)
    return total_out_dur


def mix_continuous_music(
    stitched_mp4: Path,
    music_path: Path,
    music_mixed_mp4: Path,
    total_duration_sec: float,
    music_vol: float = 0.16,
) -> None:
    fade_out_dur = 2.0
    fade_out_start = max(0.0, total_duration_sec - fade_out_dur)
    filter_complex = (
        f"[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[nar];"
        f"[1:a]aloop=loop=-1:size=2e+09,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"atrim=0:{total_duration_sec:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=out:st={fade_out_start:.3f}:d={fade_out_dur:.3f},volume={music_vol:.3f}[mus];"
        f"[nar][mus]amix=inputs=2:duration=first:dropout_transition=0,asetpts=PTS-STARTPTS[aout]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(stitched_mp4),
            "-i", str(music_path),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(music_mixed_mp4),
        ],
        check=True,
    )


def render_shot_clip(
    idx: int,
    shot: dict,
    keyframe_path: Path,
    wav_path: Path,
    clip_path: Path,
    aspect: str,
    fps: int = 24,
    clip_dur: float | None = None,
) -> None:
    out_w, out_h, pre_w, pre_h = dims_for_aspect(aspect)
    dur = float(clip_dur if clip_dur is not None else shot["duration_sec"])
    dur_str = f"{dur:.3f}"
    frames = max(1, int(round(dur * fps)))
    vf = ken_burns_filter(idx, dur, shot.get("motion_prompt", ""), out_w, out_h, pre_w, pre_h, fps=fps, aspect=aspect)
    filter_complex = (
        f"[0:v]{vf},fps={fps},setpts=PTS-STARTPTS[vout];"
        f"[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad,atrim=0:{dur_str},asetpts=PTS-STARTPTS,volume=1.0[voice];"
        f"[2:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,atrim=0:{dur_str},asetpts=PTS-STARTPTS,volume=0.015[bed];"
        f"[voice][bed]amix=inputs=2:duration=first:dropout_transition=0,atrim=0:{dur_str},asetpts=PTS-STARTPTS[aout]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(keyframe_path),
        "-i", str(wav_path),
        "-f", "lavfi", "-i", f"anoisesrc=d={dur_str}:c=brown:a=0.015",
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-frames:v", str(frames), "-t", dur_str,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
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
    music_path: Path | None = None,
    music_vol: float = 0.16,
    xfade_dur: float = 0.30,
) -> tuple[Path, float]:
    tag = "16x9" if aspect == "16:9" else "9x16"
    out_w, out_h, _, _ = dims_for_aspect(aspect)
    aspect_clips_dir = clips_dir / tag
    aspect_clips_dir.mkdir(parents=True, exist_ok=True)
    clips_and_durs: list[tuple[Path, float]] = []

    for idx, shot in enumerate(sb["shots"]):
        shot_id = shot["shot_id"]
        kf = keyframes_dir / f"{shot_id}.png"
        wav = audio_dir / f"{shot_id}.wav"
        if not kf.exists():
            raise FileNotFoundError(f"Missing keyframe: {kf}. Run pipeline/keyframes.py first.")
        if not wav.exists():
            raise FileNotFoundError(f"Missing narration WAV: {wav}. Run pipeline/narration.py first.")

        clip_dur, _ = effective_shot_duration(shot, audio_dir)
        clip_path = aspect_clips_dir / f"{shot_id}_{tag}.mp4"
        cache_payload = {
            "shot_id": shot_id,
            "aspect": aspect,
            "framing_v": "headroom_16x9" if aspect == "16:9" else "center",
            "duration_sec": clip_dur,
            "motion_prompt": shot.get("motion_prompt", ""),
            "fps": fps,
            "kf_size": kf.stat().st_size,
            "wav_size": wav.stat().st_size,
            "music_mode": "continuous_post_stitch",
        }

        def _render_one(
            i: int = idx,
            s: dict = shot,
            c_dur: float = clip_dur,
            k: Path = kf,
            w: Path = wav,
            c: Path = clip_path,
            asp: str = aspect,
        ) -> dict:
            render_shot_clip(i, s, k, w, c, aspect=asp, fps=fps, clip_dur=c_dur)
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
        clips_and_durs.append((clip_path, clip_dur))

    end_card_dur = 2.5
    end_card_path = aspect_clips_dir / f"end_card_{tag}.mp4"
    render_end_card(end_card_path, out_w=out_w, out_h=out_h, fps=fps, card_dur=end_card_dur)
    clips_and_durs.append((end_card_path, end_card_dur))

    stitched_mp4 = aspect_clips_dir / f"stitched_{tag}.mp4"
    total_blended_dur = stitch_with_xfade(clips_and_durs, stitched_mp4, fps=fps, xfade_dur=xfade_dur)

    if music_path is not None and music_path.exists() and music_vol > 0.0:
        music_mixed_mp4 = aspect_clips_dir / f"music_mixed_{tag}.mp4"
        mix_continuous_music(stitched_mp4, music_path, music_mixed_mp4, total_blended_dur, music_vol=music_vol)
        base_for_subs = music_mixed_mp4
    else:
        base_for_subs = stitched_mp4

    subbed_mp4 = aspect_clips_dir / f"subbed_{tag}.mp4"
    if burn_subs:
        escaped_srt = escape_ffmpeg_path(srt_path)
        vf_subs = (
            f"subtitles='{escaped_srt}':force_style="
            f"'FontName=Abyssinica SIL,FontSize={font_size},MarginV=28,Outline=1,Shadow=0,Alignment=2'"
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(base_for_subs),
                "-vf", vf_subs,
                "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(subbed_mp4),
            ],
            check=True,
        )
    else:
        subbed_mp4 = base_for_subs

    final_mp4 = final_dir / f"bijigdu_mode_75s_{tag}.mp4"
    loudnorm_two_pass(subbed_mp4, final_mp4)
    return final_mp4, total_blended_dur


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble heritage short film in 9:16 and/or 16:9.")
    parser.add_argument("--storyboard", default="storyboard.json")
    parser.add_argument("--aspect", choices=["9:16", "16:9", "both"], default="both")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--font-size", type=int, default=10)
    parser.add_argument("--burn-subs", action="store_true", help="Burn generated SRT subtitles into final MP4")
    parser.add_argument("--music", default=str(DEFAULT_MUSIC_PATH), help="Path to background music track")
    parser.add_argument("--music-vol", type=float, default=0.16, help="Background music volume under narration")
    parser.add_argument("--xfade-dur", type=float, default=0.30, help="Cross-dissolve duration between shots (sec)")
    args = parser.parse_args()

    sb = load_json(ROOT / args.storyboard)
    validate_storyboard(sb, ROOT / "schema/storyboard.schema.json")

    music_path = Path(args.music) if args.music else None
    if music_path and not music_path.exists():
        raise FileNotFoundError(f"Background music file not found: {music_path}")

    keyframes_dir = ROOT / "outputs/keyframes"
    audio_dir = ROOT / "outputs/audio"
    clips_dir = ROOT / "outputs/clips"
    final_dir = ROOT / "outputs/final"
    final_dir.mkdir(parents=True, exist_ok=True)

    nl = chr(10)
    srt_path = final_dir / "bijigdu_mode_75s.srt"
    cursor = 0.0
    blocks = []
    for i, shot in enumerate(sb["shots"], start=1):
        clip_dur, spoken_dur = effective_shot_duration(shot, audio_dir)
        start_t = max(0.0, cursor - (args.xfade_dur if i > 1 else 0.0))
        effective_slot = clip_dur - (args.xfade_dur if i > 1 else 0.0)
        cue_dur = min(max(0.4, effective_slot - 0.05), max(spoken_dur + 0.10, effective_slot * 0.85))
        en = (shot.get("subtitles_en") or "").strip()
        am = (shot.get("narration_am") or "").strip()
        text = en or am or shot["shot_id"]
        blocks.append(f"{i}{nl}{format_srt_time(start_t)} --> {format_srt_time(start_t + cue_dur)}{nl}{text}{nl}")
        cursor += effective_slot
    srt_path.write_text(nl.join(blocks), encoding="utf-8")

    aspects = ["9:16", "16:9"] if args.aspect == "both" else [args.aspect]
    for asp in aspects:
        out_p, out_dur = assemble_for_aspect(
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
            music_path=music_path,
            music_vol=args.music_vol,
            xfade_dur=args.xfade_dur,
        )
        print(f"Exported: {out_p} (~{out_dur:.1f}s) | SRT: {srt_path}")


if __name__ == "__main__":
    main()
