import copy
import json
import time
from pathlib import Path
from curl_cffi import requests

CITIES = [
    {"name": "Algiers", "id": 1194},
    {"name": "Oran", "id": 78480},
]

MEMBERS = [
    {"name": "1 person", "adults": 1, "children": 0, "children_ages": []},
    {"name": "2 ppl", "adults": 2, "children": 0, "children_ages": []},
    # Ages change pricing on Agoda, adjust to what you actually want.
    {"name": "family of 4 (2 adults and 2 children)", "adults": 2, "children": 2, "children_ages": [8, 8]},
]

PAGE_SIZE = 100
DELAY_S = 1


def build_body(base, city, member):
    """Fresh copy of the base body with this city/member applied."""
    body = copy.deepcopy(base)
    v = body["variables"]

    # City (both places)
    v["CitySearchRequest"]["cityId"] = city["id"]
    v["ContentSummaryRequest"]["context"]["searchCriteria"]["cityId"] = city["id"]

    # Occupancy
    criteria = v["CitySearchRequest"]["searchRequest"]["searchCriteria"]
    criteria["adults"] = member["adults"]
    criteria["children"] = member["children"]
    if "childrenAges" in criteria or member["children"] > 0:
        criteria["childrenAges"] = member["children_ages"]

    occ = v.get("ContentSummaryRequest", {}).get("context", {}).get("occupancy")
    if occ is not None:
        occ["numberOfAdults"] = member["adults"]
        occ["numberOfChildren"] = member["children"]

    v["CitySearchRequest"]["searchRequest"]["page"]["pageSize"] = PAGE_SIZE
    return body


def fetch_agoda_data():
    base_body = json.loads(Path("./sources/body.json").read_text(encoding="utf-8"))
    header = json.loads(Path("./sources/header.json").read_text(encoding="utf-8"))

    headers = {
        **header,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    all_properties = []

    for city in CITIES:
        for member in MEMBERS:
            label = f"{city['name']} | {member['name']}"
            body = build_body(base_body, city, member)
            seen_ids = set()
            count = 0
            page = 1

            print(f"\n--- Fetching: {label} ---")

            while True:
                body["variables"]["CitySearchRequest"]["searchRequest"]["page"]["pageNumber"] = page

                res = requests.post(
                    "https://www.agoda.com/graphql/search",
                    headers=headers,
                    json=body,
                    impersonate="chrome",
                )

                print(f"[{label}] Page {page} | Status: {res.status_code}")

                if not res.ok:
                    print(f"Request failed: {res.status_code} {res.reason}")
                    print(res.text[:500])
                    break

                data = res.json()
                properties = ((data.get("data") or {}).get("citySearch") or {}).get("properties")

                if not properties:
                    print(f"[{label}] No more properties. Stopping.")
                    break

                new_count = 0
                for prop in properties:
                    pid = prop.get("propertyId")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        all_properties.append({
                            **prop,
                            "city": city["name"],
                            "cityId": city["id"],
                            "members": member["name"],
                        })
                        new_count += 1

                count += new_count
                print(f"[{label}] +{new_count} new (combo: {count}, overall: {len(all_properties)})")

                if new_count == 0:
                    break

                page += 1
                time.sleep(DELAY_S)

    output_path = Path("./output/PYresponse.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_properties, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved {len(all_properties)} properties to {output_path}")