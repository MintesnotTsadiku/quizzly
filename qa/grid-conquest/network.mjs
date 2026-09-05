import { execFileSync } from "node:child_process";
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
const base = process.env.GP_QA_BASE || "http://127.0.0.1:8081",
  checks = [],
  errors = [];
let id, host;
const ownedSessions = [];
const previousSessions = JSON.parse(
  await fs
    .readFile("/tmp/gp-grid-after-sessions.json", "utf8")
    .catch(() => "[]"),
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
const players = [];
async function join(pin, nickname) {
  const p = await page();
  await p.goto(`/play/join?pin=${pin}&lang=en`);
  await p.getByPlaceholder("Your name").fill(nickname);
  await p.locator("form button[type=submit]").click();
  await p.waitForURL(/\/play\/p\//);
  players.push(p);
  return p;
}
async function state() {
  return api(host, "get_host_state", { session: id });
}
async function waitBoard(p, cell, mark) {
  await p.waitForFunction(
    ({ cell, mark }) =>
      document
        .querySelector(`.gc-cell[data-cell="${cell}"]`)
        ?.getAttribute("data-mark") === mark,
    { cell, mark },
    { timeout: 15000 },
  );
}
const controllersUsed = new Set();
async function move(cell) {
  const s = await state();
  let actor;
  if (s.view.can_move) actor = host;
  else {
    for (const p of players) {
      const identity = await p.evaluate(() =>
        JSON.parse(localStorage.getItem("gp_player")),
      );
      if (!identity) continue;
      const v = await api(p, "get_player_state", {
        pin: s.game_pin,
        token: identity.token,
      });
      if (v.view?.can_move) {
        actor = p;
        break;
      }
    }
  }
  assert.ok(actor, "A controller can place the mark");
  controllersUsed.add(actor);
  await actor
    .locator(`.gc-cell[data-cell="${cell}"][aria-disabled="false"]`)
    .waitFor();
  await actor.locator(`.gc-cell[data-cell="${cell}"]`).click();
  await waitBoard(host, cell, s.view.turn);
  return actor;
}
async function badMove(p, cell, revision) {
  const identity = await p.evaluate(() =>
    JSON.parse(localStorage.getItem("gp_player")),
  );
  const r = await p.request.post(
    "/api/method/quizzly.games.api.submit_action",
    {
      data: {
        pin: (await state()).game_pin,
        token: identity.token,
        action_type: "place_mark",
        idempotency_key: crypto.randomUUID(),
        payload: { cell, revision },
      },
    },
  );
  return r;
}
try {
  host = await page(1360, 1000, true);
  await host.goto("/play/games/grid-conquest?lang=en");
  await host.locator('.gc-demo .gc-cell[data-cell="2"]').click();
  assert.equal(await host.locator(".gc-demo .winning").count(), 3);
  await screenshot(host, "after-discovery");
  await host.getByRole("button", { name: "Reset practice board" }).click();
  pass(
    "Discovery teaches the same playable board; practice win and reset work",
  );
  // Create through the real setup rather than a seeded question pack.
  await host
    .getByRole("button", { name: "Open the lobby", exact: false })
    .click();
  await host.waitForURL(/\/play\/host/);
  id = await host.evaluate(() => localStorage.getItem("gp_hosted_session"));
  assert.ok(id);
  ownedSessions.push(id);
  let s = await state();
  assert.equal(s.configuration.rules_version, 2);
  const pin = s.game_pin;
  await join(pin, "Grid QA X");
  await join(pin, "Grid QA O");
  await host.getByRole("button", { name: "Start match", exact: false }).click();
  await phase("grid_turn");
  const screen = await page(1440, 1000);
  await screen.goto(`/play/s/${pin}/screen?lang=en`);
  await screen.locator(".gc-board").waitFor();
  s = await state();
  assert.equal(s.view.board.length, 9);
  assert.equal(await players[0].locator(".gc-cell").count(), 9);
  await screenshot(host, "after-host");
  await screenshot(players[0], "after-player");
  let x;
  for (const p of players) {
    const i = await p.evaluate(() =>
      JSON.parse(localStorage.getItem("gp_player")),
    );
    const v = await api(p, "get_player_state", { pin, token: i.token });
    if (v.view.can_move) x = p;
  }
  const o = players.find((p) => p !== x);
  assert.equal((await badMove(o, 0, s.view.revision)).status(), 403);
  pass("Server rejects a move from the wrong side");
  await move(0);
  assert.ok((await badMove(o, 1, s.view.revision)).status() >= 400);
  assert.ok(
    (await badMove(o, 0, (await state()).view.revision)).status() >= 400,
  );
  pass("Stale revisions and occupied squares are rejected");
  await host.getByRole("button", { name: "Pause", exact: true }).click();
  await host.getByRole("heading", { name: "A moment to think" }).waitFor();
  assert.ok(
    (await badMove(o, 3, (await state()).view.revision)).status() >= 400,
  );
  await host.getByRole("button", { name: "Resume", exact: true }).click();
  await move(3);
  await x.reload();
  await waitBoard(x, 0, "X");
  pass("Pause blocks moves; reloading a player restores board and role");
  await join(pin, "Grid QA third");
  await move(1);
  const saved = (await state()).view;
  execFileSync(path.join(bench, "env/bin/python"), [
    path.join(root, "qa/grid-conquest/drop-cache.py"),
    id,
  ]);
  await x.reload();
  await waitBoard(x, 1, "X");
  assert.deepEqual((await state()).view.board, saved.board);
  pass("Lost Redis board state restores from the durable database snapshot");
  await move(4);
  await move(2);
  await phase("grid_round_over");
  await screen.locator(".winning").first().waitFor();
  assert.equal(await screen.locator(".winning").count(), 3);
  await screenshot(screen, "after-shared-screen");
  await screenshot(x, "after-winning-board");
  pass(
    "Two sides and a late joiner play a winning line; shared screen stays synchronized",
  );
  await host.getByRole("button", { name: "Next board", exact: true }).click();
  s = await phase("grid_turn");
  assert.equal(s.view.turn, "O");
  for (const cell of [0, 1, 2, 4, 3, 5, 7, 6, 8]) await move(cell);
  s = await phase("grid_round_over");
  assert.equal(s.view.winner, "draw");
  assert.deepEqual(s.view.wins, { X: 1, O: 0 });
  assert.equal(await host.locator(".winning").count(), 0);
  await screenshot(host, "after-drawn-board");
  assert.ok(controllersUsed.has(players[2]));
  pass(
    "Next board alternates starter; a full draw awards no points; the late joiner takes a turn",
  );
  await host.getByRole("button", { name: "Next board", exact: true }).click();
  await phase("grid_turn");
  await move(0);
  await host
    .getByRole("button", { name: "Help play this turn", exact: true })
    .click();
  await host.locator('.gc-cell[data-cell="3"][aria-disabled="false"]').click();
  await waitBoard(host, 3, "O");
  assert.equal((await state()).view.host_turn, false);
  pass("Host can help place one mark, then control returns to the players");
  await move(1);
  await move(4);
  await move(2);
  await host.getByRole("button", { name: "See match results" }).click();
  s = await phase("Ended");
  assert.equal(s.ending.winner, "X");
  assert.deepEqual(s.ending.wins, { X: 2, O: 0 });
  await host.locator(".gc-ending").waitFor();
  await screenshot(host, "after-match-results");
  await x.reload();
  await x.locator(".gc-ending").waitFor();
  pass("Three-board match ends 2–0 with persistent results after reload");
  await host
    .getByRole("button", { name: "Play again with a new room" })
    .click();
  await host
    .getByRole("button", { name: "Start match", exact: false })
    .waitFor();
  id = await host.evaluate(() => localStorage.getItem("gp_hosted_session"));
  ownedSessions.push(id);
  assert.notEqual(id, ownedSessions[0]);
  assert.equal((await state()).participants.length, 0);
  await api(host, "end_session", { session: id });
  pass("Replay opens a fresh room with the same board settings");
  const shared = await api(host, "create_session", {
    game_key: "grid-conquest",
    configuration: { control_mode: "shared" },
  });
  id = shared.session;
  ownedSessions.push(id);
  await host.goto(`/play/host?session=${id}&lang=en`);
  await host.getByRole("button", { name: "Start match", exact: false }).click();
  await phase("grid_turn");
  for (const cell of [0, 3, 1, 4, 2]) await move(cell);
  await screenshot(host, "after-host-only");
  await host.getByRole("button", { name: "Next board", exact: true }).click();
  await phase("grid_turn");
  for (const cell of [0, 3, 1, 4, 2]) await move(cell);
  await host.getByRole("button", { name: "Next board", exact: true }).click();
  await phase("grid_turn");
  for (const cell of [0, 1, 2, 4, 3, 5, 7, 6, 8]) await move(cell);
  await host.getByRole("button", { name: "See match results" }).click();
  s = await phase("Ended");
  assert.equal(s.ending.winner, "draw");
  assert.ok(s.podium.every((p) => p.rank === 1));
  await host.getByRole("heading", { name: "The match is a draw!" }).waitFor();
  await screenshot(host, "after-match-draw");
  pass(
    "Host-only play needs no joining devices; a tied match gives both sides equal rank",
  );
  const raceRoom = await api(host, "create_session", {
    game_key: "grid-conquest",
    configuration: { control_mode: "shared" },
  });
  id = raceRoom.session;
  ownedSessions.push(id);
  await host.goto(`/play/host?session=${id}&lang=en`);
  await host.getByRole("button", { name: "Start match", exact: false }).click();
  s = await phase("grid_turn");
  const request = {
    session: id,
    command: "place_mark",
    payload: { cell: 0, revision: s.view.revision },
  };
  const csrf = await host.evaluate(() => window.csrf_token);
  const replies = await Promise.all(
    [1, 2].map(() =>
      host.request.post("/api/method/quizzly.games.api.host_command", {
        headers: { "X-Frappe-CSRF-Token": csrf },
        data: request,
      }),
    ),
  );
  assert.equal(replies.filter((r) => r.status() === 200).length, 1);
  assert.equal((await state()).view.board.filter(Boolean).length, 1);
  pass("Two simultaneous requests place exactly one mark");
  const embedded = await host.context().newPage();
  await embedded.goto("/play/");
  await embedded.setContent(
    `<iframe title="Embedded GatherPlay" src="/play/host?session=${id}&embedded=1&lang=en" style="width:100%;height:900px"></iframe>`,
  );
  const frame = embedded.frameLocator("iframe");
  await frame.locator(".gc-board").waitFor();
  await frame.locator('.gc-cell[data-cell="4"][aria-disabled="false"]').click();
  await waitBoard(host, 4, "O");
  await screenshot(embedded, "after-embedded");
  await embedded.close();
  pass(
    "Authenticated iframe preserves host controls and live board synchronization",
  );
  await api(host, "end_session", { session: id });
  await host.setViewportSize({ width: 360, height: 800 });
  await host.goto("/play/games/grid-conquest?lang=am");
  await host.locator(".gc-board").waitFor();
  assert.ok(
    await host.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await host.locator(".gc-board").scrollIntoViewIfNeeded();
  await screenshot(host, "after-amharic-mobile");
  pass("Amharic mobile layout fits a 360px screen");
  assert.deepEqual(errors, []);
  pass("No browser console errors or uncaught exceptions");
} catch (e) {
  console.error(e.stack);
  if (host) await screenshot(host, "failure");
  process.exitCode = 1;
} finally {
  await fs.writeFile(
    "/tmp/gp-grid-after-sessions.json",
    JSON.stringify([...previousSessions, ...ownedSessions]),
  );
  await fs.writeFile(
    path.join(out, "after-results.json"),
    JSON.stringify({ checks, errors, passed: !process.exitCode }, null, 2),
  );
  const v = host?.video();
  await Promise.all(browser.contexts().map((c) => c.close()));
  if (v) await v.saveAs(path.join(out, "after-session.webm"));
  await browser.close();
}
