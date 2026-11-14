import fs from "fs";
import { Impit } from "impit";

const impit = new Impit({
  browser: "chrome",
});

const [body, headerText] = await Promise.all([
  fs.promises.readFile("../body.json", "utf8"),
  fs.promises.readFile("../header.json", "utf8"),
]);

const header = JSON.parse(headerText);

const res = await impit.fetch("https://www.agoda.com/graphql/search", {
  method: "POST",
  headers: {
    ...header,
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  body,
});

console.log(res.status, res.headers.get("content-type"));

const text = await res.text();
fs.writeFileSync("../results/JSresponse.json", text);

if (!res.ok) {
  console.error("Request failed:", res.status, res.statusText);
  console.error(text);
  process.exit(1);
}

const data = JSON.parse(text);
console.log(Object.keys(data));
console.log(data?.data?.citySearch?.properties?.length);