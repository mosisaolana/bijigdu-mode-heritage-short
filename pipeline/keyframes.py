import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import load_json, run_cached_stage_item, validate_storyboard

DEFAULT_MODEL = "@cf/black-forest-labs/flux-1-schnell"


def _call_workers_ai_image(
    account_id: str,
    api_token: str,
    model: str,
    prompt: str,
    steps: int = 4,
) -> bytes:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    payload = json.dumps({"prompt": prompt, "steps": steps}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare Workers AI HTTP {exc.code}: {err_body}") from exc

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reference sheet and shot keyframes via Cloudflare Workers AI.")
    parser.add_argument("--storyboard", default="storyboard.json", help="Path to storyboard.json")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Cloudflare Workers AI image model")
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

        def _gen_shot(p: str = full_prompt, out: Path = out_path) -> dict:
            img_bytes = _call_workers_ai_image(account_id, api_token, args.model, p, steps=args.steps)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(img_bytes)
            return {"bytes": len(img_bytes)}

        res = run_cached_stage_item(
            stage="keyframe",
            shot_id=shot_id,
            model=args.model,
            cache_payload={"prompt": full_prompt, "steps": args.steps, "model": args.model},
            output_path=out_path,
            fn=_gen_shot,
            seed=seed,
        )
        print(f"[{shot_id}] {out_path} -> cached={res['cached']}")


if __name__ == "__main__":
    main()
