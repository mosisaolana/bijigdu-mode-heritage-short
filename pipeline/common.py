import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    import jsonschema
except ImportError:
    jsonschema = None


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def validate_storyboard(storyboard: dict[str, Any], schema_path: str | Path = "schema/storyboard.schema.json") -> None:
    if jsonschema is None:
        return
    schema = load_json(schema_path)
    jsonschema.validate(instance=storyboard, schema=schema)


def compute_cache_key(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:16]


def append_run_log(
    log_path: str | Path,
    stage: str,
    shot_id: str | None,
    model: str,
    parameters: dict[str, Any],
    seed: int | None,
    latency_sec: float,
    estimated_cost_usd: float,
    status: str,
    cache_hit: bool,
    error: str | None = None,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "shot_id": shot_id,
        "model": model,
        "parameters": parameters,
        "seed": seed,
        "latency_sec": round(latency_sec, 3),
        "estimated_cost_usd": estimated_cost_usd,
        "status": status,
        "cache_hit": cache_hit,
        "error": error,
    }
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_cached_stage_item(
    stage: str,
    shot_id: str | None,
    model: str,
    cache_payload: dict[str, Any],
    output_path: str | Path,
    fn: Callable[[], dict[str, Any]],
    log_path: str | Path = "runs.jsonl",
    seed: int | None = None,
    estimated_cost_usd: float = 0.0,
) -> dict[str, Any]:
    out = Path(output_path)
    cache_key = compute_cache_key(cache_payload)
    marker = out.with_suffix(out.suffix + ".cachekey")

    if out.exists() and marker.exists() and marker.read_text(encoding="utf-8").strip() == cache_key:
        append_run_log(
            log_path=log_path,
            stage=stage,
            shot_id=shot_id,
            model=model,
            parameters=cache_payload,
            seed=seed,
            latency_sec=0.0,
            estimated_cost_usd=0.0,
            status="cached",
            cache_hit=True,
        )
        return {"output_path": str(out), "cache_key": cache_key, "cached": True}

    start = time.perf_counter()
    try:
        result = fn()
        elapsed = time.perf_counter() - start
        out.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(cache_key + "\n", encoding="utf-8")
        append_run_log(
            log_path=log_path,
            stage=stage,
            shot_id=shot_id,
            model=model,
            parameters=cache_payload,
            seed=seed,
            latency_sec=elapsed,
            estimated_cost_usd=estimated_cost_usd,
            status="ok",
            cache_hit=False,
        )
        return {"output_path": str(out), "cache_key": cache_key, "cached": False, "result": result}
    except Exception as exc:
        elapsed = time.perf_counter() - start
        append_run_log(
            log_path=log_path,
            stage=stage,
            shot_id=shot_id,
            model=model,
            parameters=cache_payload,
            seed=seed,
            latency_sec=elapsed,
            estimated_cost_usd=0.0,
            status="error",
            cache_hit=False,
            error=str(exc),
        )
        raise
