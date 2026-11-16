import json
import time
from pathlib import Path
from curl_cffi import requests

def fetch_agoda_data():
    body = json.loads(Path("./sources/body.json").read_text(encoding="utf-8"))
    header = json.loads(Path("./sources/header.json").read_text(encoding="utf-8"))

    headers = {
        **header,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    all_properties = []
    seen_ids = set()
    page = 1

    while True:
        # Update page number and max out page size to 100
        body["variables"]["CitySearchRequest"]["searchRequest"]["page"]["pageNumber"] = page
        body["variables"]["CitySearchRequest"]["searchRequest"]["page"]["pageSize"] = 100

        res = requests.post(
            "https://www.agoda.com/graphql/search",
            headers=headers,
            json=body,  # 'json=' automatically converts the dict back to text
            impersonate="chrome",
        )

        print(f"Page {page} | Status: {res.status_code}")

        if not res.ok:
            print(f"Request failed: {res.status_code} {res.reason}")
            break

        data = res.json()
        properties = data.get("data", {}).get("citySearch", {}).get("properties")

        # Stop looping if Agoda returns an empty list or None
        if not properties:
            print("No more properties returned. Stopping.")
            break

        # Filter out duplicates between pages
        new_count = 0
        for prop in properties:
            pid = prop.get("propertyId")
            if pid not in seen_ids:
                seen_ids.add(pid)
                all_properties.append(prop)
                new_count += 1

        print(f"Added {new_count} new properties (Total: {len(all_properties)})")

        # If a page returned only duplicates we already have, we're done
        if new_count == 0:
            break

        page += 1
        time.sleep(1)  # 1-second pause so Agoda doesn't block you

    # Save all collected properties to PYresponse.json
    output_path = Path("./output/PYresponse.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_properties, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"Saved {len(all_properties)} properties to {output_path}")