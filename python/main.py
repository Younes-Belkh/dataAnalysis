import csv
import json
import time
from pathlib import Path
from curl_cffi import requests

# Base paths
base_dir = Path(__file__).resolve().parent
body_file = base_dir / "../body.json"
header_file = base_dir / "../header.json"
results_dir = base_dir / "../results"
results_dir.mkdir(parents=True, exist_ok=True)

# Load request payload and headers
body_data = json.loads(body_file.read_text(encoding="utf-8"))
header = json.loads(header_file.read_text(encoding="utf-8"))

headers = {
    **header,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

all_properties = []
seen_ids = set()
page = 1

print("Starting to fetch all available data from Agoda...")

while True:
    # Agoda maximum allowed pageSize is 100
    body_data["variables"]["CitySearchRequest"]["searchRequest"]["page"]["pageNumber"] = page
    body_data["variables"]["CitySearchRequest"]["searchRequest"]["page"]["pageSize"] = 100

    try:
        res = requests.post(
            "https://www.agoda.com/graphql/search",
            headers=headers,
            json=body_data,
            impersonate="chrome",
            timeout=30,
        )
    except Exception as e:
        print(f"Request error on page {page}: {e}")
        break

    if not res.ok:
        print(f"Request failed at page {page}: {res.status_code} {res.reason}")
        break

    data = res.json()
    properties = data.get("data", {}).get("citySearch", {}).get("properties") or []
    if not properties:
        print(f"No properties returned on page {page}. Reached end of results.")
        break

    new_items = 0
    for prop in properties:
        pid = prop.get("propertyId")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            all_properties.append(prop)
            new_items += 1

    print(f"Page {page}: received {len(properties)} properties ({new_items} new). Total collected: {len(all_properties)}")

    # Stop if no new properties were found (all results exhausted)
    if new_items == 0:
        print(f"No new unique properties on page {page}. Finished fetching.")
        break

    page += 1
    time.sleep(1)  # Respectful pause between requests

print(f"\nFinished fetching! Total unique properties collected: {len(all_properties)}")

# 1. Save full JSON
json_output_path = results_dir / "PYresponse.json"
json_output_path.write_text(json.dumps(all_properties, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved raw JSON to {json_output_path}")


# 2. Flatten and save to CSV
rows = []
for p in all_properties:
    info = p.get("content", {}).get("informationSummary", {})
    address = info.get("address", {})
    reviews = p.get("content", {}).get("reviews", {}).get("cumulative", {}) or {}
    geo = info.get("geoInfo", {})
    pricing = p.get("pricing", {})

    # Extract price info if available
    price_val = None
    currency = None
    offers = pricing.get("offers", [])
    if offers:
        room_offers = offers[0].get("roomOffers", [])
        if room_offers:
            pricing_list = room_offers[0].get("room", {}).get("pricing", [])
            if pricing_list:
                currency = pricing_list[0].get("currency")
                per_night = pricing_list[0].get("price", {}).get("perNight", {})
                price_val = (per_night.get("exclusive") or per_night.get("inclusive") or {}).get("display")

    link = info.get("propertyLinks", {}).get("propertyPage", "")
    url = f"https://www.agoda.com{link}" if link else ""

    rows.append({
        "property_id": p.get("propertyId"),
        "name": info.get("displayName") or info.get("localeName") or info.get("defaultName"),
        "property_type": info.get("propertyType"),
        "star_rating": info.get("rating"),
        "review_score": reviews.get("score"),
        "review_count": reviews.get("reviewCount"),
        "country": address.get("country", {}).get("name"),
        "city": address.get("city", {}).get("name"),
        "area": address.get("area", {}).get("name"),
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "price_per_night": price_val,
        "currency": currency,
        "is_available": pricing.get("isAvailable"),
        "url": url,
    })

csv_output_path = results_dir / "properties.csv"
if rows:
    fieldnames = list(rows[0].keys())
    with open(csv_output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved CSV with {len(rows)} rows to {csv_output_path}")
else:
    print("No property rows to save.")

