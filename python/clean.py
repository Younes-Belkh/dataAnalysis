import csv
import json
from pathlib import Path


# Helper function to safely dig into nested JSON without crashing
def dig(data, *keys):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        elif isinstance(data, list) and isinstance(key, int) and len(data) > key:
            data = data[key]
        else:
            return None
    return data


def clean_json_to_csv():
    input_path = Path("./output/PYresponse.json")
    output_path = Path("./results/PYproperties.csv")

    if not input_path.exists():
        print("Error: PYresponse.json not found. Run the fetcher first!")
        return

    properties = json.loads(input_path.read_text(encoding="utf-8"))
    rows = []

    for p in properties:
        link = dig(p, "content", "informationSummary", "propertyLinks", "propertyPage")
        price = (
            dig(p, "pricing", "offers", 0, "roomOffers", 0, "room", "pricing", 0, "price", "perNight", "exclusive", "display")
            or dig(p, "pricing", "offers", 0, "roomOffers", 0, "room", "pricing", 0, "price", "perNight", "inclusive", "display")
        )

        rows.append({
            "property_id": dig(p, "propertyId"),
            "name": dig(p, "content", "informationSummary", "displayName") or dig(p, "content", "informationSummary", "defaultName"),
            "search_city": dig(p, "city"),        # city you searched (added by fetcher)
            "search_city_id": dig(p, "cityId"),   # 1194 / 78480
            "members": dig(p, "members"),
            "property_type": dig(p, "content", "informationSummary", "propertyType"),
            "star_rating": dig(p, "content", "informationSummary", "rating"),
            "review_score": dig(p, "content", "reviews", "cumulative", "score"),
            "review_count": dig(p, "content", "reviews", "cumulative", "reviewCount"),
            "country": dig(p, "content", "informationSummary", "address", "country", "name"),
            "city": dig(p, "content", "informationSummary", "address", "city", "name"),  # city Agoda reports
            "area": dig(p, "content", "informationSummary", "address", "area", "name"),
            "latitude": dig(p, "content", "informationSummary", "geoInfo", "latitude"),
            "longitude": dig(p, "content", "informationSummary", "geoInfo", "longitude"),
            "price_per_night": price,
            "currency": dig(p, "pricing", "offers", 0, "roomOffers", 0, "room", "pricing", 0, "currency"),
            "is_available": dig(p, "pricing", "isAvailable"),
            "url": f"https://www.agoda.com{link}" if link else "",
        })

    if not rows:
        print("No data found to write to CSV.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Cleaned {len(rows)} properties and saved to {output_path}")