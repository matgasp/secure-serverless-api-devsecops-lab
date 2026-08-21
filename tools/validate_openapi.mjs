import { readFile } from "node:fs/promises";


const path = process.argv[2] ?? "openapi/openapi.json";
const document = JSON.parse(await readFile(path, "utf8"));
const failures = [];

if (document.openapi !== "3.0.3")
{
  failures.push("openapi must be 3.0.3");
}

if (!document.info?.title || !document.info?.version)
{
  failures.push("info.title and info.version are required");
}

for (const route of ["/health", "/licenses", "/licenses/{license_id}", "/licenses/{license_id}/validate"])
{
  if (!document.paths?.[route])
  {
    failures.push(`missing path: ${route}`);
  }
}

if (failures.length > 0)
{
  console.error(failures.join("\n"));
  process.exitCode = 1;
}
else
{
  console.log(`Validated ${path}`);
}
