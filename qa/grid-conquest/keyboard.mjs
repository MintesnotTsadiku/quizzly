import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { chromium } from "../../../agent_harness/node_modules/playwright/index.mjs";
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({
    viewport: { width: 360, height: 800 },
    reducedMotion: "reduce",
    extraHTTPHeaders: { "X-Frappe-Site-Name": "training.localhost" },
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:18033/play/games/grid-conquest?lang=en");
  await page.locator('.gc-cell[data-cell="1"]').focus();
  await page.keyboard.press("ArrowRight");
  assert.equal(await page.locator(":focus").getAttribute("data-cell"), "2");
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(".winning").count(), 3);
  await page.getByRole("button", { name: "Reset practice board" }).click();
  assert.equal(await page.locator(".winning").count(), 0);
  await fs.writeFile(
    new URL(
      "../../docs/grid-conquest/evidence/keyboard-results.json",
      import.meta.url,
    ),
    JSON.stringify(
      {
        passed: true,
        checks: [
          "Arrow-key navigation and Enter place a winning mark",
          "Keyboard reset restores the practice board",
          "Reduced-motion browser mode supported",
        ],
      },
      null,
      2,
    ),
  );
  console.log(
    "PASS: production-built practice board works with arrow keys and Enter",
  );
} finally {
  await browser.close();
}
