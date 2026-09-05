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
await fs.mkdir(out, { recursive: true });
async function waitVersion(version) {
  for (let i = 0; i < 40; i++) {
    const s = await api(host, "get_host_state", { session: id });
    if (s.state_version > version) return s;
    await host.waitForTimeout(150);
  }
  throw Error("Move did not persist");
}
try {
  host = await page(1360, 960, true);
  await host.goto("/play/");
  const a = await page(),
    b = await page(),
    screen = await page(1440, 1000);
  await a.goto("/play/");
  await b.goto("/play/");
  for (const key of [
    "group-sudoku",
    "dots-and-boxes",
    "path-weaver",
    "hidden-picture",
    "quilt-puzzle",
  ]) {
    const room = await api(host, "create_session", {
      game_key: key,
      configuration: { control_mode: "players" },
    });
    id = room.session;
    ownedSessions.push(id);
    await fs.writeFile(
      "/tmp/gp-ui-audit-sessions.json",
      JSON.stringify(ownedSessions),
    );
    const ja = await join(a, room.game_pin, "UI QA Hana"),
      jb = await join(b, room.game_pin, "UI QA Dawit");
    await Promise.all([
      host.goto("/play/host?session=" + id),
      a.goto("/play/p/" + room.game_pin),
      b.goto("/play/p/" + room.game_pin),
    ]);
    await api(host, "start_session", { session: id });
    await screen.goto("/play/s/" + room.game_pin + "/screen");
    await a.locator(".puzzle-room").waitFor();
    await b.locator(".puzzle-room").waitFor();
    let state = await api(host, "get_host_state", { session: id });
    let n = 0;
    const version = state.state_version;
    await api(host, "host_command", {
      session: id,
      command: "pause",
      payload: { revision: version },
    });
    state = await waitVersion(version);
    assert.equal(state.view.paused, true);
    const pausedVersion = state.state_version;
    await api(host, "host_command", {
      session: id,
      command: "resume",
      payload: { revision: pausedVersion },
    });
    state = await waitVersion(pausedVersion);
    assert.equal(state.view.paused, false);
    async function move({ cell, value, edge, piece, rotation = 0 }) {
      const p =
        key === "dots-and-boxes"
          ? state.view.controller.name === ja.participant
            ? a
            : b
          : n % 2
            ? a
            : b;
      await p.waitForFunction(
        (revision) =>
          document.querySelector(".puzzle-room")?.dataset.revision ==
          String(revision),
        state.state_version,
      );
      if (key === "dots-and-boxes")
        await p.locator(`[data-edge="${edge}"]`).click();
      else if (key === "group-sudoku") {
        await p.locator(`[data-cell="${cell}"]`).click();
        await p
          .locator(".tools button")
          .filter({ hasText: new RegExp("^" + value + "$") })
          .click();
      } else if (key === "quilt-puzzle") {
        await p
          .getByRole("button", { name: "Patch " + (piece + 1), exact: true })
          .click();
        for (let r = 0; r < rotation; r++)
          await p.getByRole("button", { name: /^Rotate/ }).click();
        await p.locator(`[data-cell="${cell}"]`).click();
      } else await p.locator(`[data-cell="${cell}"]`).click();
      try {
        state = await waitVersion(state.state_version);
      } catch (e) {
        console.log(await p.locator("main").innerText());
        await screenshot(p, key + "-failure-player");
        throw e;
      }
      n++;
    }
    if (key === "group-sudoku") {
      const solution = [1, 2, 3, 4, 3, 4, 1, 2, 2, 1, 4, 3, 4, 3, 2, 1];
      for (let cell = 0; cell < 16; cell++)
        if (!state.view.puzzle.givens.includes(cell))
          await move({ cell, value: solution[cell] });
    }
    if (key === "dots-and-boxes") {
      const wrong = state.view.controller.name === ja.participant ? jb : ja;
      await assert.rejects(() =>
        api(a, "submit_action", {
          pin: room.game_pin,
          token: wrong.participant_token,
          action_type: "edge",
          payload: { edge: "h:0:0", revision: state.state_version },
          idempotency_key: "qa-wrong-turn",
        }),
      );
      for (let r = 0; r < 4; r++)
        for (let c = 0; c < 3; c++) await move({ edge: `h:${r}:${c}` });
      for (let r = 0; r < 3; r++)
        for (let c = 0; c < 4; c++) await move({ edge: `v:${r}:${c}` });
      assert.equal(state.view.puzzle.scores.X + state.view.puzzle.scores.O, 9);
    }
    if (key === "path-weaver")
      for (const cell of [
        1, 2, 3, 4, 9, 14, 13, 12, 11, 10, 15, 20, 21, 22, 23, 24,
      ])
        await move({ cell });
    if (key === "hidden-picture") {
      const picture = ["01010", "11111", "11111", "01110", "00100"];
      for (let r = 0; r < 5; r++)
        for (let c = 0; c < 5; c++)
          if (picture[r][c] === "1") await move({ cell: r * 5 + c });
    }
    if (key === "quilt-puzzle")
      for (const [piece, cell] of [
        [0, 0],
        [1, 4],
        [2, 5],
        [3, 10],
      ])
        await move({ piece, cell });
    assert.equal(state.view.puzzle.done, true);
    await a.reload();
    await a.locator(".success").waitFor();
    await screen.locator(".success").waitFor();
    await screenshot(a, key + "-complete-player");
    await screenshot(screen, key + "-complete-screen");
    assert.equal(
      await a.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
    );
    await host
      .getByRole("button", { name: "Finish game", exact: true })
      .click();
    await host.waitForTimeout(500);
    const ending = await api(host, "get_host_state", { session: id });
    assert.equal(ending.status, "Ended");
    assert.ok(ending.ending.puzzle.done);
    if (key === "dots-and-boxes") {
      assert.equal(
        ending.podium.reduce((sum, t) => sum + t.score, 0),
        9,
      );
    }
    pass(
      key + " two-player full solution, projector, mobile reload and ending",
    );
  }
  await fs.writeFile(
    path.join(out, "puzzles.json"),
    JSON.stringify({ checks, errors }, null, 2),
  );
} finally {
  await Promise.all(browser.contexts().map((c) => c.close()));
  await browser.close();
}
