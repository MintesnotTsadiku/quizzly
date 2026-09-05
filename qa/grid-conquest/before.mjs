// Baseline recorder: run against commit 9acce59, before the board redesign.
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath, pathToFileURL } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url)),
  bench = path.resolve(root, "../.."),
  out = path.join(root, "docs/grid-conquest/evidence");
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
let id, host;
const ownedSessions = [];
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
    ...(auth
      ? { recordVideo: { dir: out, size: { width: 960, height: 640 } } }
      : {}),
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
async function phase(expected, timeout = 35000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const s = await api(host, "get_host_state", { session: id });
    if (s.phase === expected || s.status === expected) return s;
    await host.waitForTimeout(500);
  }
  throw new Error("Phase did not become " + expected);
}
async function screenshot(p, name) {
  await p.screenshot({ path: path.join(out, name + ".png") });
}
try {
  host = await page(1360, 900, true);
  await host.goto("/play/");
  const packs = await api(host, "list_public_decks", {
    game_key: "grid-conquest",
  });
  const pack = packs.find((p) => p.content_language !== "am") || packs[0];
  assert.ok(pack);
  const room = await api(host, "create_session", {
    game_key: "grid-conquest",
    configuration: {
      pack: pack.name,
      rounds: 1,
      seconds: 30,
      auto_progress: 0,
    },
  });
  id = room.session;
  ownedSessions.push(id);
  await host.evaluate(
    (id) => localStorage.setItem("gp_hosted_session", id),
    id,
  );
  await host.goto(`/play/host?session=${id}&lang=en`);
  const players = [];
  for (const nickname of ["Grid QA X", "Grid QA O"]) {
    const p = await page();
    await p.goto(`/play/join?pin=${room.game_pin}&lang=en`);
    await p.getByPlaceholder("Your name").fill(nickname);
    await p.locator("form button[type=submit]").click();
    await p.waitForURL(/\/play\/p\//);
    players.push(p);
  }
  await host.getByRole("button", { name: "Start ·", exact: false }).click();
  await phase("round_open");
  await players[0].locator("main button").first().waitFor();
  await screenshot(host, "before-host");
  await screenshot(players[0], "before-player");
  console.log(
    "Actual player choices:",
    await players[0].locator("main button").allTextContents(),
  );
  await players[0].locator("main button").first().click();
  await screenshot(players[0], "before-answer");
  pass("Reproduced: a text question and answer buttons; no playable X/O board");
  await api(host, "end_session", { session: id });
} catch (e) {
  console.error(e.message);
  process.exitCode = 1;
} finally {
  await fs.writeFile(
    "/tmp/gp-grid-before-sessions.json",
    JSON.stringify(ownedSessions),
  );
  await fs.writeFile(
    path.join(out, "before-results.json"),
    JSON.stringify({ checks, errors, passed: !process.exitCode }, null, 2),
  );
  const v = host?.video();
  await Promise.all(browser.contexts().map((c) => c.close()));
  if (v) await v.saveAs(path.join(out, "before-session.webm"));
  await browser.close();
}
