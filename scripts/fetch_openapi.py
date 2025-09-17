import json
import pathlib
import urllib.request

SPECS = {
    "jira-platform.v3.json": "https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8171.0",
    "jira-software.v3.json": "https://dac-static.atlassian.com/cloud/jira/software/swagger.v3.json?_v=1.8171.0",
    "jsm.v3.json": "https://dac-static.atlassian.com/cloud/jira/service-desk/swagger.v3.json?_v=1.8171.0",
}


def main() -> None:
    out_dir = pathlib.Path("schemas")
    out_dir.mkdir(parents=True, exist_ok=True)
    for fname, url in SPECS.items():
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        obj = json.loads(data)
        (out_dir / fname).write_bytes(data)
        print(f"saved {fname} with {len(json.dumps(obj))} bytes")


if __name__ == "__main__":
    main()
