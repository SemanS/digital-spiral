from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    run([sys.executable, "scripts/fetch_openapi.py"])
    run(["pytest", "tests/contract"])
    run([sys.executable, "scripts/parity_report.py", "artifacts/parity.json"])


if __name__ == "__main__":
    main()
