import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { chromium } from "/home/minte/projects/training-apps/apps/agent_harness/node_modules/playwright/index.mjs";
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto("http://127.0.0.1:8081/play/access#verify=qa-link-preservation");
  await page.getByRole("heading", { name: "Come as you are.", exact: true }).waitFor();
  const href = await page.getByRole("link", { name: "Sign in or create an account" }).getAttribute("href");
  assert.equal(new URL(href, page.url()).searchParams.get("redirect-to"), "/play/access#verify=qa-link-preservation");
  assert.equal(await page.getByRole("button", { name: "Confirm my email" }).isDisabled(), true);
  const response = await page.request.get("http://127.0.0.1:8081/api/method/quizzly.access.configuration");
  assert.equal(response.status(), 200);
  assert.equal((await response.json()).message.access_mode, "Community");
  await page.setViewportSize({width: 1440, height: 1100});
  await page.goto("http://127.0.0.1:8081/play/");
  await page.getByRole("heading", { name: "Good company. Great games." }).waitFor();
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({path: new URL("../../docs/access/evidence/01-landing.png", import.meta.url).pathname});
  await page.setViewportSize({width: 390, height: 844});
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.screenshot({path: new URL("../../docs/access/evidence/07-mobile.png", import.meta.url).pathname});
  await fs.writeFile(new URL("../../docs/access/evidence/smoke-results.json", import.meta.url), JSON.stringify({ passed: true, checks: ["Verification fragment survives the sign-in redirect; confirmation requires sign-in", "Final backend serves the public configuration and leaves Community mode enabled"] }, null, 2));
  console.log("PASS: Sign-in preserves verification link; final site is reachable in Community mode");
} finally {
  await browser.close();
}
