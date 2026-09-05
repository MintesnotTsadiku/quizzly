import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath, pathToFileURL } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url)),
  bench = path.resolve(root, "../.."),
  out = path.join(root, "docs/game-ui-audit/evidence");
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
  for (const key of [
    "group-sudoku",
    "dots-and-boxes",
    "path-weaver",
    "hidden-picture",
    "quilt-puzzle",
  ]) {
    const room = await api(host, "create_session", {
      game_key: key,
      configuration: { control_mode: "shared" },
    });
    id = room.session;
    ownedSessions.push(id);
    await fs.writeFile(
      "/tmp/gp-ui-audit-sessions.json",
      JSON.stringify(ownedSessions),
    );
    await host.goto("/play/host?session=" + id);
    await host.getByRole("button", { name: /Start/ }).last().click();
    await host.locator(".puzzle-room").waitFor({ timeout: 25000 });
    let before = await api(host, "get_host_state", { session: id });
    if (key === "group-sudoku") {
      await host.locator('[data-cell="1"]').click();
      await host.locator(".tools button").filter({ hasText: /^2$/ }).click();
    }
    if (key === "dots-and-boxes")
      await host.locator('[data-edge="h:0:0"]').click();
    if (key === "path-weaver") await host.locator('[data-cell="1"]').click();
    if (key === "hidden-picture") await host.locator('[data-cell="1"]').click();
    if (key === "quilt-puzzle") await host.locator('[data-cell="0"]').click();
    await host.waitForTimeout(1500);
    let after = await api(host, "get_host_state", { session: id });
    assert.ok(
      after.state_version > before.state_version,
      key + " click persisted",
    );
    await host.reload();
    await host.locator(".puzzle-room").waitFor();
    await screenshot(host, key + "-after");
    pass(key + " host control and reload");
    await api(host, "end_session", { session: id });
  }
  console.log(JSON.stringify({ checks, errors }));
  await fs.writeFile(
    path.join(out, "after/shared-device.json"),
    JSON.stringify({ checks, errors }, null, 2),
  );
} finally {
  await browser.close();
}
