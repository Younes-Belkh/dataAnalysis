// cleaner.js
import fs from "fs";

// Wraps strings in quotes if they contain commas or quotes so the CSV columns don't break
function escapeCsv(val) {
  if (val === null || val === undefined) return "";
  const str = String(val);
  return str.includes(",") || str.includes('"') || str.includes("\n")
    ? `"${str.replace(/"/g, '""')}"`
    : str;
}

export default async function cleanJsonToCsv() {
  const raw = await fs.promises.readFile("./output/JSresponse.json", "utf8");
  const properties = JSON.parse(raw);

  if (!properties.length) {
    console.log("No properties found to clean.");
    return;
  }

  const rows = properties.map((p) => {
    const info = p?.content?.informationSummary;
    const address = info?.address;
    const reviews = p?.content?.reviews?.cumulative;
    const roomPricing = p?.pricing?.offers?.[0]?.roomOffers?.[0]?.room?.pricing?.[0];
    const perNight = roomPricing?.price?.perNight;
    const link = info?.propertyLinks?.propertyPage;

    return {
      property_id: p?.propertyId,
      name: info?.displayName || info?.localeName || info?.defaultName,
      search_city: p?.city, // city you searched (added by fetcher)
      search_city_id: p?.cityId, // 1194 / 78480
      members: p?.members,
      property_type: info?.propertyType,
      star_rating: info?.rating,
      review_score: reviews?.score,
      review_count: reviews?.reviewCount,
      country: address?.country?.name,
      city: address?.city?.name, // city Agoda reports for the property
      area: address?.area?.name,
      latitude: info?.geoInfo?.latitude,
      longitude: info?.geoInfo?.longitude,
      price_per_night: perNight?.exclusive?.display ?? perNight?.inclusive?.display,
      currency: roomPricing?.currency,
      is_available: p?.pricing?.isAvailable,
      url: link ? `https://www.agoda.com${link}` : "",
    };
  });

  // Build CSV text
  const headers = Object.keys(rows[0]);
  const csvLines = [
    headers.join(","),
    ...rows.map((row) => headers.map((h) => escapeCsv(row[h])).join(",")),
  ];

  // Ensure results folder exists
  fs.mkdirSync("./results", { recursive: true });

  // "\uFEFF" is the UTF-8 BOM so Excel reads Arabic/French/symbols properly
  fs.writeFileSync("./results/JSproperties.csv", "\uFEFF" + csvLines.join("\n"), "utf8");
  console.log(`Saved ${rows.length} rows to ./results/JSproperties.csv`);
}