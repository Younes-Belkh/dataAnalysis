import json
from pathlib import Path
from curl_cffi import requests

body = Path("../body.json").read_text(encoding="utf-8")
header = json.loads(Path("../header.json").read_text(encoding="utf-8"))

headers = {
    **header,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

res = requests.post(
    "https://www.agoda.com/graphql/search",
    headers=headers,
    data=body,
    impersonate="chrome",
)

print(res.status_code, res.headers.get("content-type"))

# Ensure output directory exists and write response text
output_path = Path("../results/PYresponse.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(res.text, encoding="utf-8")

if not res.ok:
    print(f"Request failed: {res.status_code} {res.reason}")
    print(res.text)
    exit(1)

data = res.json()
print(list(data.keys()))

properties = data.get("data", {}).get("citySearch", {}).get("properties")
print(len(properties) if properties is not None else None)