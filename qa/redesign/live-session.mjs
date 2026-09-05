import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath, pathToFileURL } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url)),
  bench = path.resolve(root, "../.."),
  out = path.join(root, "docs/redesign/evidence");
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
      if (!r.ok) throw new Error(method + ": " + r.status);
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
  host = await page(1440, 1000, true);
  await host.goto("/play/", { waitUntil: "domcontentloaded" });
  await host.locator(".gp-game-card").first().waitFor();
  const packs = await api(host, "list_public_decks", {
    game_key: "crowd-compass",
  });
  const pack = packs.find((p) => p.demo_key === "crowd-compass-family-general");
  assert.ok(pack);
  const created = await api(host, "create_session", {
    game_key: "crowd-compass",
    configuration: {
      pack: pack.name,
      rounds: 1,
      vote_seconds: 20,
      prediction_seconds: 20,
      auto_progress: 0,
    },
  });
  id = created.session;
  await host.evaluate(
    (id) => localStorage.setItem("gp_hosted_session", id),
    id,
  );
  await host.goto(`/play/host?session=${id}`, {
    waitUntil: "domcontentloaded",
  });
  await host.getByRole("button", { name: "Start ·", exact: false }).waitFor();
  const players = [];
  for (const name of ["Team Mango", "Team Comet", "Avery"]) {
    const p = await page();
    await p.goto(`/play/join?pin=${created.game_pin}`, {
      waitUntil: "domcontentloaded",
    });
    await p.getByPlaceholder("Your name").fill(name);
    await p.locator("form button[type=submit]").click();
    await p.waitForURL(/\/play\/p\//);
    await p.getByText("You're in", { exact: false }).waitFor();
    players.push(p);
  }
  const screen = await page(1920, 1080);
  await screen.goto(`/play/s/${created.game_pin}/screen`, {
    waitUntil: "domcontentloaded",
  });
  await screen.getByText("3 in the room", { exact: false }).waitFor();
  await screenshot(host, "12-crowd-lobby");
  await screenshot(players[0], "13-shared-team-player");
  pass(
    "Three isolated guest browsers join: two household/team entries and an individual",
  );
  await host.getByRole("button", { name: "Start ·", exact: false }).click();
  let state = await phase("prompt_open");
  await Promise.all(
    players.map(async (p, i) => {
      await p.locator("main .grid button").first().waitFor();
      await p
        .locator("main .grid button")
        .nth(i % 2)
        .click();
      await p.getByText("Vote locked", { exact: false }).waitFor();
    }),
  );
  await screenshot(players[0], "14-player-vote");
  state = await phase("prediction_open");
  await Promise.all(
    players.map(async (p) => {
      await p.getByText("Predict the room", { exact: false }).waitFor();
      await p.locator("main .grid button").first().click();
      await p.getByRole("button", { name: "Lock prediction" }).click();
      await p.getByText("Prediction locked", { exact: false }).waitFor();
    }),
  );
  pass("Every guest submits a real vote and private prediction");
  const revealed = await phase("reveal");
  assert.equal(revealed.view.predictions, 3);
  await host.getByText("3 votes · 3 predictions", { exact: false }).waitFor();
  await screenshot(screen, "15-crowd-reveal");
  await screenshot(host, "16-crowd-host-reveal");
  await api(host, "host_command", { session: id, command: "next" });
  state = await phase("scoreboard");
  await players[0].reload({ waitUntil: "domcontentloaded" });
  await players[0].getByText("Team Mango", { exact: false }).first().waitFor();
  pass(
    "Shared-device identity survives reload; live reveal reaches shared screen",
  );
  await api(host, "host_command", { session: id, command: "next" });
  const final = await phase("Ended");
  assert.equal(final.podium.length, 3);
  assert.ok(
    final.podium.every((entry) => entry.score >= 500),
    "Prediction scores are persisted",
  );
  await host
    .getByRole("heading", { name: "Final results", exact: true })
    .waitFor();
  await screen
    .getByRole("heading", { name: "Final results", exact: true })
    .waitFor();
  await Promise.all(
    players.map((p) =>
      p
        .getByRole("button", { name: "Join another game", exact: true })
        .waitFor(),
    ),
  );
  await screenshot(host, "17-crowd-results");
  await host.reload({ waitUntil: "domcontentloaded" });
  await host
    .getByRole("heading", { name: "Final results", exact: true })
    .waitFor();
  pass("One scored round completes and persists results");
} catch (e) {
  console.error("FAILED:", e.message);
  process.exitCode = 1;
  if (host) await screenshot(host, "failure-live");
} finally {
  if (id)
    await fs.writeFile(
      "/tmp/gp-redesign-live-session.json",
      JSON.stringify([id]),
    );
  await fs.writeFile(
    path.join(out, "live-results.json"),
    JSON.stringify(
      {
        checks,
        errors,
        session: id,
        passed: !process.exitCode && errors.length === 0,
      },
      null,
      2,
    ),
  );
  if (errors.length) {
    console.log("Browser errors:", JSON.stringify(errors));
    process.exitCode = 1;
  }
  await browser.close();
}
