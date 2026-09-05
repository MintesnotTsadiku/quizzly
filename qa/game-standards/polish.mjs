import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath, pathToFileURL } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url)),
  bench = path.resolve(root, "../.."),
  out = path.join(root, "docs/game-standards/evidence");
const { chromium } = await import(
  pathToFileURL(
    path.join(bench, "apps/agent_harness/node_modules/playwright/index.mjs"),
  )
);
const browser = await chromium.launch({ headless: true });
const config = JSON.parse(
  await fs.readFile(
    path.join(bench, "sites/training.localhost/site_config.json"),
    "utf8",
  ),
);
const base = "http://127.0.0.1:8081",
  checks = [],
  errors = [];
let host;
async function api(page, method, params = {}) {
  return page.evaluate(
    async ({ method, params }) => {
      const r = await fetch("/api/method/quizzly.games.api." + method, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": window.csrf_token,
          "X-Frappe-Site-Name": window.site_name,
        },
        body: JSON.stringify(params),
      });
      const j = await r.json();
      if (!r.ok)
        throw new Error(
          method +
            ": " +
            r.status +
            " " +
            (j.exc_type || "") +
            " " +
            (j._server_messages || ""),
        );
      return j.message;
    },
    { method, params },
  );
}
async function page(width = 390, height = 844, auth = false) {
  const context = await browser.newContext({
    baseURL: base,
    viewport: { width, height },
    colorScheme: "light",
  });
  if (auth) {
    const r = await context.request.post("/api/method/login", {
      form: {
        usr: "church-browser-qa@circle.localhost",
        pwd: config.church_browser_qa_password,
      },
    });
    assert.equal(r.status(), 200);
  }
  const p = await context.newPage();
  p.on("pageerror", (e) => errors.push(e.message));
  p.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  return p;
}
function pass(message) {
  checks.push(message);
  console.log("PASS:", message);
}
async function screenshot(p, name) {
  await p.screenshot({ path: path.join(out, name + ".png") });
}
try {
  host = await page(1440, 1000, true);
  const ended = JSON.parse(
    await fs.readFile(path.join(out, "live-results.json"), "utf8"),
  ).session;
  await host.goto("/play/");
  await host.evaluate(
    (id) => localStorage.setItem("gp_hosted_session", id),
    ended,
  );
  await host.goto(`/play/host?session=${ended}&lang=am`);
  await host.locator(".story-card").waitFor();
  const state = await api(host, "get_host_state", { session: ended });
  for (const lang of ["am", "en"]) {
    await host
      .getByRole("button", {
        name: lang === "am" ? "አማርኛ" : "English",
        exact: true,
      })
      .click();
    await host.locator(".story-card").waitFor();
    await host.locator(".story-consent input").check();
    const pending = host.waitForEvent("download");
    await host
      .getByRole("button", {
        name: lang === "am" ? "የውጤት ካርዱን አስቀምጥ" : "Save results card",
        exact: true,
      })
      .click();
    await (await pending).saveAs(path.join(out, `shared-card-${lang}.png`));
    await screenshot(host, `results-story-${lang}`);
  }
  await host.goto(`/play/host?session=${ended}&lang=am`);
  await host.locator(".story-card").waitFor();
  await host.setViewportSize({ width: 360, height: 800 });
  await host
    .locator(".story-card")
    .evaluate((el) => el.scrollIntoView({ block: "start" }));
  assert.ok((await host.locator(".story-card").boundingBox()).y >= 0);
  assert.ok(
    await host.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await screenshot(host, "mobile-results-polished-am");
  pass(
    "Polished Amharic/English exports and 360px results show the full card without horizontal overflow",
  );
  // Verify the production build through the real CMS iframe, retaining the existing authenticated user.
  const ctx = await browser.newContext({
    baseURL: "http://127.0.0.1:18033",
    viewport: { width: 1440, height: 1000 },
    extraHTTPHeaders: { "X-Frappe-Site-Name": "training.localhost" },
  });
  await ctx.addCookies(await host.context().cookies());
  const p = await ctx.newPage();
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto("/home/games");
  await p.locator("#community-quizzly").waitFor();
  await p.evaluate((id) => {
    localStorage.setItem("gp_hosted_session", id);
    document.querySelector("#community-quizzly").src =
      "/play/host?session=" + id + "&lang=am&embedded=1";
  }, ended);
  const frame = p.frameLocator("#community-quizzly");
  await frame.locator(".story-card").waitFor();
  await frame.locator(".story-consent input").check();
  const dl = p.waitForEvent("download");
  await frame
    .getByRole("button", { name: "የውጤት ካርዱን አስቀምጥ", exact: true })
    .click();
  await (await dl).saveAs(path.join(out, "embedded-card-am.png"));
  await screenshot(p, "embedded-results-am");
  pass(
    "Production CMS iframe preserves authentication, shows persisted results and downloads the Amharic card",
  );
  const screen = await page(1920, 1080);
  await screen.goto(`/play/s/${state.game_pin}/screen?lang=am`);
  await screen.locator(".story-card").waitFor();
  await screenshot(screen, "screen-ending-polished-am");
  assert.equal(errors.length, 0);
} catch (e) {
  console.error(e.message);
  process.exitCode = 1;
  if (host) await screenshot(host, "polish-failure");
} finally {
  await fs.writeFile(
    path.join(out, "polish-results.json"),
    JSON.stringify({ checks, errors, passed: !process.exitCode }, null, 2),
  );
  await browser.close();
}
