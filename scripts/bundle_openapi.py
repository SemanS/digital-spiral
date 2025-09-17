from __future__ import annotations

import json
import pathlib

from prance import ResolvingParser


def bundle(src: str | pathlib.Path, dst: str | pathlib.Path) -> None:
    parser = ResolvingParser(str(src))
    with open(dst, "w", encoding="utf-8") as handle:
        json.dump(parser.specification, handle, ensure_ascii=False)


def main() -> None:
    for name in [
        "jira-platform.v3.json",
        "jira-software.v3.json",
        "jsm.v3.json",
    ]:
        bundle(f"schemas/{name}", f"schemas/{name}.bundled.json")


if __name__ == "__main__":
    main()
