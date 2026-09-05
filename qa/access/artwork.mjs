import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { chromium } from "/home/minte/projects/training-apps/apps/agent_harness/node_modules/playwright/index.mjs";
import { GAME_VISUALS } from "../../frontend/src/platform/discovery/gameVisuals.js";
const out = new URL("../../docs/artwork/evidence/", import.meta.url);
for (const visual of Object.values(GAME_VISUALS)) {
  for (const key of ["hero", "example"]) {
    await fs.access(new URL("../../quizzly/public/" + visual[key].replace("/assets/quizzly/", ""), import.meta.url));
  }
}
const browser = await chromium.launch();
const errors = [], checks = [];
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if(message.type() === "error") errors.push(message.text()); });
  for (const game of ["common-ground", "crowd-compass"]) {
    await page.goto(`http://127.0.0.1:8081/play/games/${game}`);
    const illustration = page.locator(".gp-game-illustration");
    await illustration.waitFor();
    await page.waitForFunction(() => document.querySelector(".gp-game-illustration img")?.naturalWidth > 0);
    assert.equal(await illustration.evaluate(element => !!element.closest("details")), false);
    await page.screenshot({ path: new URL(game + "-desktop.png", out).pathname });
    const popupPromise = page.waitForEvent("popup");
    await illustration.focus();
    await page.keyboard.press("Enter");
    const popup = await popupPromise;
    await popup.waitForLoadState();
    assert.ok(popup.url().includes("/assets/quizzly/images/games/" + game + "/"));
    await popup.close();
    checks.push(`${game}: actual illustration visible on entry and opens full size with keyboard`);
    if(game === "crowd-compass") {
      await page.getByText("Full visual guide and room setup", { exact: true }).click();
      await page.getByRole("button", {name: "See a worked Crowd Compass example", exact: true}).click();
      await page.getByRole("dialog").waitFor();
      await page.getByRole("button", {name: "Close", exact: true}).click();
      checks.push("Existing full guide and worked-example dialog remain available");
    }
    await page.setViewportSize({width: 390, height: 844});
    await page.evaluate(() => scrollTo(0,0));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: new URL(game + "-mobile.png", out).pathname, fullPage: true });
    await page.setViewportSize({width: 1440, height: 1100});
  }
  checks.push("Both game pages fit a 390px phone; every registered guide asset exists");
  assert.deepEqual(errors, []);
  await fs.writeFile(new URL("results.json", out), JSON.stringify({passed: true, checks, errors}, null, 2));
  console.log(JSON.stringify({passed: true, checks, errors}));
} finally { await browser.close(); }
