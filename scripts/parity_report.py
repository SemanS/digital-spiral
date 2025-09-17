from __future__ import annotations

import json
import pathlib
import sys


def main(json_path: str) -> None:
    payload = json.loads(pathlib.Path(json_path).read_text(encoding="utf-8"))
    total = payload.get("total_responses", 0)
    responses = payload.get("responses", [])
    bad = sum(1 for item in responses if item.get("detail"))
    ok = total - bad
    ratio = ok / max(1, total)
    print(f"Contract OK: {ok}/{total} ({ratio:.1%})")
    if ratio < 0.95:
        print("FAIL: below 95% threshold")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/parity_report.py artifacts/parity.json")
        raise SystemExit(2)
    main(sys.argv[1])
