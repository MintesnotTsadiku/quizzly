import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath, pathToFileURL } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url)),
  bench = path.resolve(root, "../.."),
  out = path.join(root, "docs/game-ui-audit/evidence/after");
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
const base = "http://127.0.0.1:18033",
  checks = [],
  errors = [];
let id, host;
const ownedSessions = JSON.parse(
  await fs.readFile("/tmp/gp-ui-audit-sessions.json", "utf8").catch(() => "[]"),
);
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
    extraHTTPHeaders: { "X-Frappe-Site-Name": "training.localhost" },
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
const findings = [];
let lastJoin = 0;
async function join(p, pin, nickname) {
  const wait = 6500 - (Date.now() - lastJoin);
  if (wait > 0) await p.waitForTimeout(wait);
  lastJoin = Date.now();
  const r = await api(p, "join_session", { pin, nickname });
  await p.evaluate(
    (r) =>
      localStorage.setItem(
        "gp_player",
        JSON.stringify({
          token: r.participant_token,
          participant: r.participant,
          nickname: r.nickname,
          pin: r.game_pin,
          gameKey: r.game_key,
          participants: r.participants,
        }),
      ),
    r,
  );
  return r;
}
async function inspect(p) {
  return {
    text: await p.locator("body").innerText(),
    canvas: await p.locator("canvas").count(),
    roundImages: await p.locator('img[alt="Round clue"]').count(),
    audio: await p.locator("audio").count(),
    sliders: await p.locator('input[type="range"],[role="slider"]').count(),
  };
}
try {
  host = await page(1360, 960, true);
  await host.goto("/play/");
  const a = await page(),
    b = await page();
  await a.goto("/play/");
  await b.goto("/play/");
  const pack = (
    await api(host, "list_public_decks", {
      game_key: "common-thread",
      language: "am",
    })
  ).find((p) => p.demo_key.startsWith("curated-v2-"));
  const room = await api(host, "create_session", {
    game_key: "common-thread",
    configuration: {
      pack: pack.name,
      rounds: 1,
      seconds: 60,
      auto_progress: 0,
    },
  });
  id = room.session;
  ownedSessions.push(id);
  await fs.writeFile(
    "/tmp/gp-ui-audit-sessions.json",
    JSON.stringify(ownedSessions),
  );
  const ja = await join(a, room.game_pin, "UI QA Hana"),
    jb = await join(b, room.game_pin, "UI QA Dawit");
  await a.goto("/play/p/" + room.game_pin + "?lang=am");
  await b.goto("/play/p/" + room.game_pin + "?lang=am");
  await api(host, "start_session", { session: id });
  let state = await phase("round_open");
  const answer = state.view.prompt.includes("ገጾች")
    ? "መጽሐፍ"
    : state.view.prompt.includes("ሥር")
      ? "ዛፍ"
      : "ብስክሌት";
  await a.locator("main input").fill(answer);
  await a.locator("main form button").click();
  await b.locator("main input").fill("ውሻ");
  await b.locator("main form button").click();
  await a.waitForTimeout(600);
  await api(host, "host_command", { session: id, command: "next" });
  state = await phase("round_reveal");
  assert.equal(state.view.results.filter((r) => r.correct).length, 1);
  assert.equal(state.view.results.filter((r) => !r.correct).length, 1);
  await a.reload();
  await a.getByText(answer, { exact: true }).first().waitFor();
  await screenshot(a, "amharic-scoring");
  assert.equal(
    await a.evaluate(() => document.documentElement.scrollWidth > innerWidth),
    false,
  );
  pass(
    "Distinct Amharic answers score correctly through real player controls and survive reload",
  );
  await api(host, "end_session", { session: id });
  await fs.writeFile(
    path.join(out, "amharic.json"),
    JSON.stringify({ checks, errors }, null, 2),
  );
} finally {
  await Promise.all(browser.contexts().map((c) => c.close()));
  await browser.close();
}
