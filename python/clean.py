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

    print(f"Extracted {len(rows)} rows from JSON.")

    # ==================================================================
    # CLEANING STEP 1 — Handle missing values
    # ==================================================================
    cleaned = 0

    for row in rows:
        # -- price_per_night: convert to float, set invalid/missing to None --
        try:
            row["price_per_night"] = float(row["price_per_night"]) if row["price_per_night"] is not None else None
        except (ValueError, TypeError):
            row["price_per_night"] = None

        # -- review_score / review_count: convert to float, keep None if missing --
        for col in ("review_score", "review_count"):
            try:
                row[col] = float(row[col]) if row[col] is not None else None
            except (ValueError, TypeError):
                row[col] = None

        # -- star_rating: convert to float --
        try:
            row["star_rating"] = float(row["star_rating"]) if row["star_rating"] is not None else None
        except (ValueError, TypeError):
            row["star_rating"] = None

        # -- latitude / longitude: convert to float --
        for col in ("latitude", "longitude"):
            try:
                row[col] = float(row[col]) if row[col] is not None else None
            except (ValueError, TypeError):
                row[col] = None

    # Fill missing review_score with the median of non-null values
    valid_scores = [r["review_score"] for r in rows if r["review_score"] is not None]
    if valid_scores:
        median_score = sorted(valid_scores)[len(valid_scores) // 2]
        for row in rows:
            if row["review_score"] is None:
                row["review_score"] = median_score
                cleaned += 1

    # Fill missing review_count with 0 (no reviews)
    for row in rows:
        if row["review_count"] is None:
            row["review_count"] = 0
            cleaned += 1

    # Fill missing price_per_night with the median of non-null values
    valid_prices = [r["price_per_night"] for r in rows if r["price_per_night"] is not None]
    if valid_prices:
        median_price = sorted(valid_prices)[len(valid_prices) // 2]
        for row in rows:
            if row["price_per_night"] is None:
                row["price_per_night"] = median_price
                cleaned += 1

    # Fill missing currency (always EUR when price exists)
    for row in rows:
        if not row.get("currency"):
            row["currency"] = "EUR"

    print(f"  → Handled {cleaned} missing values (filled with median/default).")

    # ==================================================================
    # CLEANING STEP 2 — Correct formatting errors
    # ==================================================================
    formatted = 0

    for row in rows:
        # -- star_rating 0.0 means unrated on Agoda → treat as None --
        if row["star_rating"] == 0.0:
            row["star_rating"] = None
            formatted += 1

        # -- is_available: normalize string "True"/"False" → proper bool string --
        val = str(row.get("is_available", "")).strip().lower()
        row["is_available"] = "True" if val == "true" else "False"

        # -- property_type: normalize inconsistent labels --
        pt = str(row.get("property_type", "")).strip()
        if pt == "NonHotel":
            row["property_type"] = "Non-Hotel"
            formatted += 1
        elif pt == "SingleRoom":
            row["property_type"] = "Single Room"
            formatted += 1

        # -- name: strip extra whitespace --
        name = row.get("name")
        if name:
            stripped = " ".join(str(name).split())
            if stripped != name:
                formatted += 1
            row["name"] = stripped

        # -- area: strip whitespace and capitalize properly --
        area = row.get("area")
        if area:
            stripped = " ".join(str(area).split()).strip()
            if stripped != area:
                formatted += 1
            row["area"] = stripped

    print(f"  → Corrected {formatted} formatting errors.")

    # ==================================================================
    # CLEANING STEP 3 — Check and remove duplicate records
    # ==================================================================
    unique_rows = []
    seen_keys = set()
    duplicates_removed = 0

    for row in rows:
        # A record is unique by property_id + search criteria (members)
        key = (row.get("property_id"), row.get("members"))
        if key in seen_keys:
            duplicates_removed += 1
        else:
            seen_keys.add(key)
            unique_rows.append(row)

    rows = unique_rows
    print(f"  → Checked and removed {duplicates_removed} duplicate records.")

    # ==================================================================
    # Write cleaned CSV
    # ==================================================================
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} cleaned rows to {output_path}")