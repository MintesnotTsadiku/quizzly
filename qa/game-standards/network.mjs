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
  host = await page(1440, 1000, true);
  await host.goto("/play/", { waitUntil: "domcontentloaded" });
  await host
    .getByRole("heading", { name: "Good company. Great games." })
    .waitFor();
  const packs = await api(host, "list_public_decks", {
    game_key: "crowd-compass",
  });
  const pack = packs.find((p) => p.demo_key === "crowd-compass-am-starter-v1");
  assert.ok(pack);
  const created = await api(host, "create_session", {
    game_key: "crowd-compass",
    configuration: {
      pack: pack.name,
      rounds: 3,
      gathering_arc: true,
      vote_seconds: 20,
      prediction_seconds: 20,
      auto_progress: 0,
    },
  });
  id = created.session;
  ownedSessions.push(id);
  await host.evaluate(
    (id) => localStorage.setItem("gp_hosted_session", id),
    id,
  );
  await host.goto(`/play/host?session=${id}&lang=am`, {
    waitUntil: "domcontentloaded",
  });
  await host.getByRole("button", { name: "ጀምር ·", exact: false }).waitFor();
  const players = [];
  for (const name of ["ቡድን ማንጎ", "ቡድን ኮከብ", "ሀና"]) {
    const p = await page();
    await p.goto(`/play/join?pin=${created.game_pin}&lang=am`, {
      waitUntil: "domcontentloaded",
    });
    await p.getByPlaceholder("ስምዎ").fill(name);
    await p.locator("form button[type=submit]").click();
    await p.waitForURL(/\/play\/p\//);
    await p.getByText("ተቀላቅለዋል", { exact: false }).waitFor();
    players.push(p);
  }
  const screen = await page(1920, 1080);
  await screen.goto(`/play/s/${created.game_pin}/screen?lang=am`, {
    waitUntil: "domcontentloaded",
  });
  await screen.getByText("3 በክፍሉ ውስጥ", { exact: false }).waitFor();
  await screenshot(host, "12-crowd-lobby");
  await screenshot(players[0], "13-shared-team-player");
  pass(
    "Three isolated guest browsers join: two household/team entries and an individual",
  );
  await host.getByRole("button", { name: "ጀምር ·", exact: false }).click();
  let state;
  for (let round = 1; round <= 3; round++) {
    state = await phase("prompt_open");
    assert.equal(state.view.arc.round, round);
    assert.equal(state.view.arc.prediction_points, round === 3 ? 1000 : 500);
    await players[0].locator(".journey").waitFor();
    assert.ok(
      (await players[0].locator(".journey").innerText()).includes(
        String(round === 3 ? 1000 : 500),
      ),
    );
    await Promise.all(
      players.map(async (p, i) => {
        await p.locator("main .grid button").first().waitFor();
        await p
          .locator("main .grid button")
          .nth(i % 2)
          .click();
        await p.getByText("ድምፅዎ ተቆልፏል", { exact: false }).waitFor();
      }),
    );
    await screenshot(players[0], `round-${round}-player-vote`);
    state = await phase("prediction_open");
    await Promise.all(
      players.map(async (p) => {
        await p.getByText("የቡድኑን ምርጫ ይገምቱ", { exact: false }).waitFor();
        await p.locator("main .grid button").first().click();
        await p.getByRole("button", { name: "ግምት ቆልፍ" }).click();
        await p.getByText("ግምትዎ ተቆልፏል", { exact: false }).waitFor();
      }),
    );
    pass("Every guest submits a real vote and private prediction");
    const revealed = await phase("reveal");
    assert.equal(revealed.view.predictions, 3);
    assert.ok(/[\u1200-\u137f]/.test(revealed.view.prompt));
    await screenshot(screen, `round-${round}-screen-reveal`);
    await screenshot(host, `round-${round}-host-reveal`);
    await api(host, "host_command", { session: id, command: "next" });
    state = await phase("scoreboard");
    await players[0].reload({ waitUntil: "domcontentloaded" });
    await players[0].getByText("ቡድን ማንጎ", { exact: false }).first().waitFor();
    pass(
      "Shared-device identity survives reload; live reveal reaches shared screen",
    );
    await api(host, "host_command", { session: id, command: "next" });
  }
  const final = await phase("Ended");
  assert.equal(final.podium.length, 3);
  assert.equal(final.ending.rounds_completed, 3);
  assert.equal(final.ending.entries, 3);
  assert.equal(final.ending.moments.length, 3);
  assert.ok(final.podium.every((p) => [2000, 2300].includes(p.score)));
  await host.locator(".story-card").waitFor();
  assert.ok(
    final.podium.every((entry) => entry.score >= 2000),
    "Prediction scores are persisted",
  );
  await host
    .getByRole("heading", { name: "የመጨረሻ ውጤቶች", exact: true })
    .waitFor();
  await screen
    .getByRole("heading", { name: "የመጨረሻ ውጤቶች", exact: true })
    .waitFor();
  await Promise.all(
    players.map((p) =>
      p.getByRole("button", { name: "ሌላ ጨዋታ ይቀላቀሉ", exact: true }).waitFor(),
    ),
  );
  await screenshot(host, "17-crowd-results");
  await host.reload({ waitUntil: "domcontentloaded" });
  await host
    .getByRole("heading", { name: "የመጨረሻ ውጤቶች", exact: true })
    .waitFor();
  pass(
    "Three rounds build to the 1,000-point finale and persist exact scores and aggregate recap",
  );
  await players[0].locator(".story-card").waitFor();
  await players[0].setViewportSize({ width: 360, height: 800 });
  await players[0].locator(".story-card").scrollIntoViewIfNeeded();
  assert.ok(
    await players[0].evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await screenshot(players[0], "mobile-results-am");
  const preview = await host.locator(".story-card").innerText();
  assert.ok(!preview.includes(created.game_pin));
  for (const name of ["ቡድን ማንጎ", "ቡድን ኮከብ", "ሀና"])
    assert.ok(!preview.includes(name));
  assert.equal(await host.locator(".story-moment").count(), 0);
  await host.locator(".story-consent input").check();
  await host.locator(".story-moment").waitFor();
  let download = host.waitForEvent("download");
  await host
    .getByRole("button", { name: "የውጤት ካርዱን አስቀምጥ", exact: true })
    .click();
  await (await download).saveAs(path.join(out, "shared-card-am.png"));
  pass(
    "Amharic card downloads; room moment requires opt-in and names/PIN are excluded",
  );
  await screenshot(host, "results-story-am");
  await screenshot(screen, "screen-ending-am");
  await host.goto(`/play/host?session=${id}&lang=en`);
  await host.locator(".story-card").waitFor();
  await host.locator(".story-consent input").check();
  download = host.waitForEvent("download");
  await host
    .getByRole("button", { name: "Save results card", exact: true })
    .click();
  await (await download).saveAs(path.join(out, "shared-card-en.png"));
  await screenshot(host, "results-story-en");
  await host
    .getByRole("button", { name: "Play again with a new room", exact: true })
    .click();
  await host.getByRole("button", { name: "Start ·", exact: false }).waitFor();
  const replayId = await host.evaluate(() =>
    localStorage.getItem("gp_hosted_session"),
  );
  ownedSessions.push(replayId);
  assert.notEqual(replayId, id);
  const replay = await api(host, "get_host_state", { session: replayId });
  assert.notEqual(replay.game_pin, created.game_pin);
  assert.equal(replay.participants.length, 0);
  assert.equal(replay.configuration.gathering_arc, true);
  await screenshot(host, "replay-lobby");
  pass(
    "Replay creates an authorized fresh lobby with the same settings and a new PIN",
  );
  const room = await api(host, "create_session", {
    game_key: "common-ground",
    configuration: { pack: "everyday", language: "am" },
  });
  ownedSessions.push(room.session);
  await host.goto(`/play/room/${room.session}?lang=am`);
  await host.getByRole("button", { name: "ሁሉም ዝግጁ ናቸው", exact: false }).click();
  await host
    .getByRole("button", { name: "ለማጋራት ዝግጁ ነን", exact: false })
    .waitFor();
  const roomState = await api(host, "get_host_state", {
    session: room.session,
  });
  await screen.goto(`/play/room-screen/${room.game_pin}?lang=am`);
  await screen
    .getByRole("heading", { name: roomState.view.prompt, exact: true })
    .waitFor();
  await screenshot(host, "room-host-am");
  await screenshot(screen, "room-screen-am");
  for (let i = 0; i < 3; i++) {
    await host
      .getByRole("button", { name: "ለማጋራት ዝግጁ ነን", exact: false })
      .click();
    await host
      .getByRole("button", {
        name: i === 2 ? "አብረን እንጨርስ" : "ቀጣይ ውይይት",
        exact: false,
      })
      .click();
  }
  await host.getByRole("heading", { name: "ትንሽ ተጨማሪ", exact: false }).waitFor();
  await screenshot(host, "room-finish-am");
  pass(
    "Amharic device-free host and shared-screen prompts agree; three conversations and shares finish through the UI",
  );
} catch (e) {
  console.error("FAILED:", e.message);
  process.exitCode = 1;
  if (host) await screenshot(host, "failure-live");
} finally {
  const inventoryFile = "/tmp/gp-arc-sessions.json";
  const prior = JSON.parse(
    await fs.readFile(inventoryFile, "utf8").catch(() => "[]"),
  );
  await fs.writeFile(
    inventoryFile,
    JSON.stringify([...new Set([...prior, ...ownedSessions])]),
  );
  if (id)
    await fs.writeFile("/tmp/gp-arc-latest-network.json", JSON.stringify([id]));
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
  const video = host?.video();
  await Promise.all(browser.contexts().map((context) => context.close()));
  if (video && !process.exitCode)
    await video.saveAs(path.join(out, "working-session.webm"));
  await browser.close();
}
