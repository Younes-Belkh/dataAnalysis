// fetcher.js
import fs from "fs";
import { Impit } from "impit";

export default async function fetchAgodaData() {
  const impit = new Impit({
    browser: "chrome",
  });

  const [bodyText, headerText] = await Promise.all([
    fs.promises.readFile("./sources/body.json", "utf8"),
    fs.promises.readFile("./sources/header.json", "utf8"),
  ]);

  const body = JSON.parse(bodyText);
  const header = JSON.parse(headerText);

  const allProperties = [];
  const seenIds = new Set();
  let page = 1;

  while (true) {
    // Modify page number and max out pageSize in memory
    body.variables.CitySearchRequest.searchRequest.page.pageNumber = page;
    body.variables.CitySearchRequest.searchRequest.page.pageSize = 100;

    const res = await impit.fetch("https://www.agoda.com/graphql/search", {
      method: "POST",
      headers: {
        ...header,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
    });

    console.log(`Page ${page} | Status:`, res.status, res.headers.get("content-type"));

    const text = await res.text();

    if (!res.ok) {
      console.error("Request failed:", res.status, res.statusText);
      console.error(text);
      break;
    }

    const data = JSON.parse(text);
    const properties = data?.data?.citySearch?.properties;

    if (!properties?.length) {
      console.log("No more properties returned. Stopping.");
      break;
    }

    let newCount = 0;
    for (const prop of properties) {
      const pid = prop?.propertyId;
      if (pid && !seenIds.has(pid)) {
        seenIds.add(pid);
        allProperties.push(prop);
        newCount++;
      }
    }

    console.log(`Added ${newCount} new properties (Total: ${allProperties.length})`);

    if (newCount === 0) break;

    page++;
    await new Promise((r) => setTimeout(r, 1000)); // 1s pause
  }

  // Ensure results folder exists and write once at the end
  fs.mkdirSync("./results", { recursive: true });
  fs.writeFileSync("./output/JSresponse.json", JSON.stringify(allProperties, null, 2), "utf8");
  console.log(`Saved ${allProperties.length} properties to ./output/JSresponse.json`);
}