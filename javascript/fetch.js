// fetcher.js
import fs from "fs";
import { Impit } from "impit";

const CITIES = [
  { name: "Algiers", id: 1194 },
  { name: "Oran", id: 78480 },
];

const MEMBERS = [
  { name: "1 person", adults: 1, children: 0, childrenAges: [] },
  { name: "2 ppl", adults: 2, children: 0, childrenAges: [] },
  // Ages change pricing on Agoda, adjust to what you actually want.
  { name: "family of 4 (2 adults and 2 children)", adults: 2, children: 2, childrenAges: [8, 8] },
];

const PAGE_SIZE = 100;
const DELAY_MS = 1000;

// Returns a fresh copy of the base body with this city/member applied.
function buildBody(base, city, member) {
  const body = structuredClone(base);
  const v = body.variables;

  // City (both places)
  v.CitySearchRequest.cityId = city.id;
  v.ContentSummaryRequest.context.searchCriteria.cityId = city.id;

  // Occupancy
  const criteria = v.CitySearchRequest.searchRequest.searchCriteria;
  criteria.adults = member.adults;
  criteria.children = member.children;
  if ("childrenAges" in criteria || member.children > 0) {
    criteria.childrenAges = member.childrenAges;
  }

  const occ = v.ContentSummaryRequest?.context?.occupancy;
  if (occ) {
    occ.numberOfAdults = member.adults;
    occ.numberOfChildren = member.children;
  }

  v.CitySearchRequest.searchRequest.page.pageSize = PAGE_SIZE;
  return body;
}

export default async function fetchAgodaData() {
  const impit = new Impit({ browser: "chrome" });

  const [bodyText, headerText] = await Promise.all([
    fs.promises.readFile("./sources/body.json", "utf8"),
    fs.promises.readFile("./sources/header.json", "utf8"),
  ]);
  const baseBody = JSON.parse(bodyText);
  const header = JSON.parse(headerText);

  const allProperties = [];

  for (const city of CITIES) {
    for (const member of MEMBERS) {
      const label = `${city.name} | ${member.name}`;
      const seenIds = new Set();
      const body = buildBody(baseBody, city, member);
      let page = 1;
      let count = 0;

      console.log(`\n--- Fetching: ${label} ---`);

      while (true) {
        body.variables.CitySearchRequest.searchRequest.page.pageNumber = page;

        const res = await impit.fetch("https://www.agoda.com/graphql/search", {
          method: "POST",
          headers: {
            ...header,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(body),
        });

        const text = await res.text();
        console.log(`[${label}] Page ${page} | Status: ${res.status}`);

        if (!res.ok) {
          console.error("Request failed:", res.status, res.statusText);
          console.error(text.slice(0, 500));
          break;
        }

        const properties = JSON.parse(text)?.data?.citySearch?.properties;
        if (!properties?.length) {
          console.log(`[${label}] No more properties. Stopping.`);
          break;
        }

        let newCount = 0;
        for (const prop of properties) {
          const pid = prop?.propertyId;
          if (pid && !seenIds.has(pid)) {
            seenIds.add(pid);
            allProperties.push({ ...prop, city: city.name, cityId: city.id, members: member.name });
            newCount++;
          }
        }
        count += newCount;
        console.log(`[${label}] +${newCount} new (combo: ${count}, overall: ${allProperties.length})`);

        if (newCount === 0) break;
        page++;
        await new Promise((r) => setTimeout(r, DELAY_MS));
      }
    }
  }

  fs.mkdirSync("./output", { recursive: true });
  fs.writeFileSync("./output/JSresponse.json", JSON.stringify(allProperties, null, 2), "utf8");
  console.log(`\nSaved ${allProperties.length} properties to ./output/JSresponse.json`);
}