import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import assert from "node:assert/strict";
const root = fileURLToPath(new URL("../../", import.meta.url)),
  bench = path.resolve(root, "../.."),
  out = path.join(root, "docs/localization/evidence");
const { chromium } = await import(
  pathToFileURL(
    path.join(bench, "apps/agent_harness/node_modules/playwright/index.mjs"),
  )
);
const browser = await chromium.launch();
const c = await browser.newContext({
  baseURL: "http://127.0.0.1:18033",
  viewport: { width: 1440, height: 1000 },
  extraHTTPHeaders: { "X-Frappe-Site-Name": "training.localhost" },
});
const config = JSON.parse(
  await fs.readFile(
    path.join(bench, "sites/training.localhost/site_config.json"),
    "utf8",
  ),
);
const checks = [],
  errors = [];
try {
  const login = await c.request.post("/api/method/login", {
    form: {
      usr: "church-browser-qa@circle.localhost",
      pwd: config.church_browser_qa_password,
    },
  });
  assert.equal(login.status(), 200);
  const p = await c.newPage();
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto("/home/games", { waitUntil: "domcontentloaded" });
  await p.locator("#community-quizzly").waitFor({ timeout: 45000 });
  const frame = p.frameLocator("#community-quizzly");
  await frame
    .getByRole("heading", { name: "Good company. Great games." })
    .waitFor();
  await p.evaluate(() => document.querySelector("#community-quizzly").contentWindow.postMessage({type:"cms:appearance",version:1,mode:"light",language:"am",tokens:{}},location.origin));
  await frame.getByRole("button",{name:"አማርኛ",exact:true}).waitFor();
  await p.waitForFunction(() => document.querySelector("#community-quizzly").contentDocument.documentElement.lang === "am");
  await p.screenshot({ path: path.join(out, "embedded-am.png") });
  await frame.getByRole("button",{name:"English",exact:true}).click();
  await p.evaluate(() => document.querySelector("#community-quizzly").contentWindow.postMessage({type:"cms:appearance",version:1,mode:"light",language:"am",tokens:{}},location.origin));
  assert.equal(await frame.locator("html").getAttribute("lang"),"en");
  checks.push("Trusted parent sets Amharic; an explicit English choice wins over later parent messages");
  await frame.getByRole("link", { name: "Your access", exact: true }).click();
  await frame
    .getByRole("heading", { name: "Ready when you are.", exact: true })
    .waitFor();
  assert.equal(await frame.locator(".gp-install").count(), 0);
  await p.screenshot({ path: path.join(out, "20-embedded-access.png") });
  checks.push(
    "Actual authenticated CMS /home/games embeds the redesigned product",
  );
  const d = await browser.newContext({
    viewport: { width: 768, height: 1024 },
    colorScheme: "dark",
  });
  const dp = await d.newPage();
  await dp.goto("http://127.0.0.1:8081/play/?lang=am", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await dp
    .getByRole("heading", { name: "ደስ የሚል አብሮነት። አስደሳች ጨዋታዎች።" })
    .waitFor();
  assert.equal(
    await dp.evaluate(() => document.documentElement.scrollWidth > innerWidth),
    false,
  );
  await dp.screenshot({ path: path.join(out, "19-tablet-dark.png") });
  checks.push("768px dark-theme tablet renders without horizontal overflow");
  console.log(checks.join("\n"));
} catch (e) {
  console.log("FAILED:", e.message);
  process.exitCode = 1;
} finally {
  await fs.writeFile(
    path.join(out, "embedded-results.json"),
    JSON.stringify(
      { checks, errors, passed: !process.exitCode && errors.length === 0 },
      null,
      2,
    ),
  );
  await browser.close();
}
