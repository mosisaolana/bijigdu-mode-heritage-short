import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import load_json, run_cached_stage_item, validate_storyboard

DEFAULT_MODEL = "@cf/black-forest-labs/flux-1-schnell"
DEFAULT_REF_MODEL = "@cf/black-forest-labs/flux-2-klein-9b"


def _build_multipart_body(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8") + b"\r\n")
    for name, (filename, data, content_type) in files.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
        )
        chunks.append(data + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _decode_image_response(raw: bytes, content_type: str) -> bytes:
    if "application/json" in content_type:
        data = json.loads(raw.decode("utf-8"))
        if not data.get("success", True):
            raise RuntimeError(f"Cloudflare Workers AI error: {data}")
        result = data.get("result") or {}
        b64 = result.get("image")
        if not b64:
            raise RuntimeError(f"No image field in JSON response: {list(result.keys())}")
        return base64.b64decode(b64)
    return raw


def _call_workers_ai_image(
    account_id: str,
    api_token: str,
    model: str,
    prompt: str,
    steps: int = 4,
    ref_image_path: Path | None = None,
    seed: int | None = None,
) -> bytes:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"

    if ref_image_path is not None or "flux-2" in model:
        fields: dict[str, str] = {
            "prompt": prompt,
            "width": "1024",
            "height": "1024",
        }
        if seed is not None:
            fields["seed"] = str(seed)
        files: dict[str, tuple[str, bytes, str]] = {}
        if ref_image_path is not None:
            files["input_image_0"] = (ref_image_path.name, ref_image_path.read_bytes(), "image/png")
        body, content_type = _build_multipart_body(fields, files)
    else:
        body = json.dumps({"prompt": prompt, "steps": steps}).encode("utf-8")
        content_type = "application/json"

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": content_type,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp_ct = resp.headers.get("Content-Type", "")
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare Workers AI HTTP {exc.code}: {err_body}") from exc

    return _decode_image_response(raw, resp_ct)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reference sheet and shot keyframes via Cloudflare Workers AI.")
    parser.add_argument("--storyboard", default="storyboard.json", help="Path to storyboard.json")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Cloudflare Workers AI text-to-image model")
    parser.add_argument("--ref-model", default=DEFAULT_REF_MODEL, help="Cloudflare Workers AI reference-conditioned model")
    parser.add_argument("--steps", type=int, default=4, help="Diffusion steps (1-8 for flux-1-schnell)")
    parser.add_argument("--only", default=None, help="Generate only 'ref' or a specific shot_id (e.g. shot_01)")
    args = parser.parse_args()

    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CF_ACCOUNT_ID")
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get("CF_API_TOKEN")
    if not account_id or not api_token:
        raise EnvironmentError("Missing CLOUDFLARE_ACCOUNT_ID and/or CLOUDFLARE_API_TOKEN in environment.")

    sb = load_json(args.storyboard)
    validate_storyboard(sb)

    style_block = sb.get("style_block", "").strip()
    char_ref = sb.get("character_ref", {})
    ref_path = Path(char_ref.get("reference_image_path", "outputs/refs/bijigdu_mode_sheet.png"))

    if args.only in (None, "ref"):
        ref_prompt = (
            f"Character design reference sheet, three views (front, three-quarter, side profile) on a clean neutral studio backdrop, "
            f"{char_ref.get('name', 'Emebet Bijigdu Mode')}, {char_ref.get('role', '')}: "
            f"{char_ref.get('description', '')} {style_block}"
        ).strip()

        def _gen_ref() -> dict:
            img_bytes = _call_workers_ai_image(account_id, api_token, args.model, ref_prompt, steps=args.steps)
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            ref_path.write_bytes(img_bytes)
            return {"bytes": len(img_bytes)}

        res = run_cached_stage_item(
            stage="reference_sheet",
            shot_id="character_ref",
            model=args.model,
            cache_payload={"prompt": ref_prompt, "steps": args.steps, "model": args.model},
            output_path=ref_path,
            fn=_gen_ref,
            seed=100,
        )
        print(f"[ref] {ref_path} -> cached={res['cached']}")

    if args.only == "ref":
        return

    for shot in sb["shots"]:
        shot_id = shot["shot_id"]
        if args.only and args.only != shot_id:
            continue

        out_path = Path("outputs/keyframes") / f"{shot_id}.png"
        full_prompt = f"{shot['image_prompt'].strip()} {style_block}".strip()
        seed = shot.get("seed")

        shot_ref_str = shot.get("reference_image_path")
        shot_ref_path = Path(shot_ref_str) if shot_ref_str else None
        if shot_ref_path is not None:
            if not shot_ref_path.exists():
                raise FileNotFoundError(f"Reference image not found for {shot_id}: {shot_ref_path}")
            active_model = args.ref_model
            ref_hash = hashlib.sha256(shot_ref_path.read_bytes()).hexdigest()[:16]
            cache_payload = {
                "prompt": full_prompt,
                "model": active_model,
                "ref_image": str(shot_ref_path),
                "ref_hash": ref_hash,
                "seed": seed,
            }
        else:
            active_model = args.model
            cache_payload = {"prompt": full_prompt, "steps": args.steps, "model": active_model}

        def _gen_shot(
            p: str = full_prompt,
            out: Path = out_path,
            m: str = active_model,
            r_path: Path | None = shot_ref_path,
            s: int | None = seed,
        ) -> dict:
            img_bytes = _call_workers_ai_image(
                account_id,
                api_token,
                m,
                p,
                steps=args.steps,
                ref_image_path=r_path,
                seed=s,
            )
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(img_bytes)
            return {"bytes": len(img_bytes), "ref": str(r_path) if r_path else None}

        res = run_cached_stage_item(
            stage="keyframe",
            shot_id=shot_id,
            model=active_model,
            cache_payload=cache_payload,
            output_path=out_path,
            fn=_gen_shot,
            seed=seed,
        )
        print(f"[{shot_id}] {out_path} ({active_model}) -> cached={res['cached']}")


if __name__ == "__main__":
    main()