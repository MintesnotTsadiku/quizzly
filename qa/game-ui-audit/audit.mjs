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
const keys = [
  "dots-and-boxes",
  "path-weaver",
  "quilt-puzzle",
  "group-sudoku",
  "hidden-picture",
  "signal-spectrum",
  "picture-peek",
  "memory-mosaic",
  "sound-snap",
  "bracket-bash",
  "escape-together",
  "sequence-sprint",
  "phrase-forge",
  "caption-clash",
  "story-loom",
  "seek-and-show",
  "one-word-chorus",
  "common-thread",
  "closest-call",
  "bluffline",
];
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
    b = await page(),
    screen = await page(1440, 1000);
  await a.goto("/play/");
  await b.goto("/play/");
  for (const key of keys) {
    const row = { key };
    findings.push(row);
    try {
      await host.goto(`/play/games/${key}?lang=en`);
      row.guide = await host.locator("body").innerText();
      const packs = await api(host, "list_public_decks", { game_key: key });
      const pack = packs.find((p) => p.content_language !== "am");
      assert.ok(pack, "English demo pack exists");
      row.pack = pack.title;
      const room = await api(host, "create_session", {
        game_key: key,
        configuration: {
          pack: pack.name,
          seconds: 60,
          rounds: 1,
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
      await Promise.all([
        host.goto(`/play/host?session=${id}&lang=en`),
        a.goto(`/play/p/${room.game_pin}?lang=en`),
        b.goto(`/play/p/${room.game_pin}?lang=en`),
      ]);
      await host.getByRole("button", { name: "Start ·", exact: false }).click();
      await phase("round_open");
      await screen.goto(`/play/s/${room.game_pin}/screen?lang=en`);
      await a.locator("main h1").waitFor();
      const s = await api(host, "get_host_state", { session: id });
      row.view = s.view;
      await a
        .getByRole("heading", { name: s.view.prompt, exact: true })
        .waitFor();
      await b
        .getByRole("heading", { name: s.view.prompt, exact: true })
        .waitFor();
      await screen
        .getByRole("heading", { name: s.view.prompt, exact: true })
        .waitFor();
      row.player = await inspect(a);
      row.host = await inspect(host);
      row.screen = await inspect(screen);
      await screenshot(a, key + "-player");
      await screenshot(screen, key + "-screen");
      for (const [p, j, n] of [
        [a, ja, 0],
        [b, jb, 1],
      ]) {
        if (s.view.mechanic === "choice")
          await p
            .locator("main button")
            .filter({ hasText: s.view.choices[n % s.view.choices.length] })
            .first()
            .click();
        else if (s.view.mechanic === "order") {
          for (const c of s.view.choices)
            await p.getByRole("button", { name: c, exact: true }).click();
          await p.getByRole("button", { name: "Lock order" }).click();
        } else {
          await p
            .locator("main input")
            .fill(
              s.view.mechanic === "number"
                ? "50"
                : n
                  ? "A bright new beginning"
                  : "A surprising family adventure",
            );
          await p.getByRole("button", { name: "Lock response" }).click();
        }
      }
      row.submitted = true;
      await api(host, "host_command", { session: id, command: "next" });
      if (["bluffline", "caption-clash", "story-loom"].includes(key)) {
        await phase("vote_open");
        await a.locator("main button").first().click();
        await b.locator("main button").first().click();
        await api(host, "host_command", { session: id, command: "next" });
        row.voted = true;
      }
      const revealed = await phase("round_reveal");
      row.reveal = revealed.view;
      await screen
        .getByText(revealed.view.answer, { exact: true })
        .first()
        .waitFor();
      await screenshot(screen, key + "-reveal");
      row.completed = true;
      console.log(
        "REVIEWED",
        key,
        s.view.mechanic,
        "image:",
        Boolean(s.view.media_url),
        "canvas:",
        row.player.canvas,
        "slider:",
        row.player.sliders,
      );
    } catch (e) {
      row.error = e.message;
      console.log("FAILED", key, e.message);
      await screenshot(host, key + "-failure");
    } finally {
      if (id) await api(host, "end_session", { session: id }).catch(() => {});
      await fs.writeFile(
        path.join(out, "audit.json"),
        JSON.stringify({ findings, errors }, null, 2),
      );
    }
  }
} finally {
  await fs.writeFile(
    path.join(out, "audit.json"),
    JSON.stringify({ findings, errors }, null, 2),
  );
  await Promise.all(browser.contexts().map((c) => c.close()));
  await browser.close();
}
