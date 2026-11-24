from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import load_json, validate_storyboard


def main() -> None:
    sb = load_json(ROOT / "storyboard.json")
    validate_storyboard(sb, ROOT / "schema/storyboard.schema.json")
    total_sec = sum(float(s["duration_sec"]) for s in sb["shots"])
    print(f"Valid storyboard: {len(sb['shots'])} shots, total duration = {total_sec:.1f}s")


if __name__ == "__main__":
    main()
