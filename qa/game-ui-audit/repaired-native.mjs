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
  await fs
    .readFile("/tmp/gp-ui-native-sessions.json", "utf8")
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
  p.on("response", async (response) => {
    if (response.url().endsWith("quizzly.games.api.submit_action")) {
      const body = response.request().postDataJSON();
      const result = await response.json().catch(() => ({}));
      responseLog.push({
        action_type: body.action_type,
        status: response.status(),
        error: result.exc_type,
        messages: result._server_messages,
      });
    }
  });
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
const responseLog = [];
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
  for (const key of process.env.GP_UI_PROBE
    ? ["doodle-dash"]
    : ["doodle-dash", "cuecast"]) {
    const row = { key };
    findings.push(row);
    try {
      const packs = await api(host, "list_public_decks", { game_key: key });
      const pack = packs.find((p) => p.content_language !== "am") || packs[0];
      assert.ok(pack);
      const configuration =
        key === "cuecast"
          ? { deck: pack.name, seconds: 90, teams_count: 2, turns_per_team: 1 }
          : { pack: pack.name, seconds: 90, rounds: 1 };
      const room = await api(host, "create_session", {
        game_key: key,
        configuration,
      });
      id = room.session;
      ownedSessions.push(id);
      await fs.writeFile(
        "/tmp/gp-ui-native-sessions.json",
        JSON.stringify(ownedSessions),
      );
      const ja = await join(a, room.game_pin, "UI QA artist"),
        jb = await join(b, room.game_pin, "UI QA guesser");
      await Promise.all([
        host.goto(`/play/host?session=${id}&lang=en`),
        a.goto(`/play/p/${room.game_pin}?lang=en`),
        b.goto(`/play/p/${room.game_pin}?lang=en`),
      ]);
      await host.getByRole("button", { name: "Start ·", exact: false }).click();
      await phase(key === "cuecast" ? "turn_open" : "draw_open");
      await screen.goto(`/play/s/${room.game_pin}/screen?lang=en`);
      const va = await api(a, "get_player_state", {
          pin: room.game_pin,
          token: ja.participant_token,
        }),
        vb = await api(b, "get_player_state", {
          pin: room.game_pin,
          token: jb.participant_token,
        });
      const active = va.view.is_artist || va.view.is_performer ? a : b,
        other = active === a ? b : a;
      const privateView = active === a ? va.view : vb.view;
      if (key === "doodle-dash") {
        await active.locator("canvas").waitFor();
        const box = await active.locator("canvas").boundingBox();
        await active.mouse.move(box.x + 20, box.y + 30);
        await active.mouse.down();
        await active.mouse.move(box.x + 100, box.y + 80, { steps: 12 });
        await active.mouse.up();
        await host.waitForTimeout(700);
        let pub = await api(host, "get_public_state", { pin: room.game_pin });
        row.shortStrokeSegments = pub.view.strokes.length;
        assert.ok(row.shortStrokeSegments > 0);
        await active.mouse.move(box.x + 30, box.y + 100);
        await active.mouse.down();
        await active.mouse.move(box.x + box.width - 20, box.y + 150, {
          steps: 120,
        });
        await active.mouse.up();
        await host.waitForTimeout(700);
        pub = await api(host, "get_public_state", { pin: room.game_pin });
        for (
          let attempt = 0;
          attempt < 30 &&
          pub.view.strokes.length < row.shortStrokeSegments + 120;
          attempt++
        ) {
          await host.waitForTimeout(250);
          pub = await api(host, "get_public_state", { pin: room.game_pin });
        }
        row.longStrokeSegments =
          pub.view.strokes.length - row.shortStrokeSegments;
        row.requestedLongSegments = 120;
        assert.equal(
          row.longStrokeSegments,
          120,
          "Long stroke must retain every segment",
        );
        await screenshot(active, key + "-artist");
        await screenshot(other, key + "-guesser");
        await screenshot(screen, key + "-screen");
        await other
          .getByPlaceholder("Type your guess")
          .fill(privateView.prompt);
        await other.getByRole("button", { name: "Guess", exact: true }).click();
        await other.getByText("Correct — nice one!", { exact: true }).waitFor();
        row.correctGuess = true;
        assert.equal(
          responseLog.filter((r) => r.action_type === "submit").length,
          0,
          "Guess must not emit a generic submission",
        );
      } else {
        assert.ok(privateView.prompt);
        const otherView = active === a ? vb.view : va.view;
        assert.ok(!otherView.prompt);
        assert.ok(
          !(await api(host, "get_public_state", { pin: room.game_pin })).view
            .prompt,
        );
        await active
          .getByRole("button", { name: "Solved it", exact: false })
          .click();
        await host.waitForTimeout(500);
        await active
          .getByRole("button", { name: "Pass", exact: false })
          .click();
        row.privatePrompt = true;
        row.solvedAndPassed = true;
        await screenshot(active, key + "-performer");
        await screenshot(other, key + "-watcher");
      }
      row.completed = true;
      console.log("REVIEWED NATIVE", key, JSON.stringify(row));
    } catch (e) {
      row.error = e.message;
      console.log("NATIVE ERROR", key, e.message);
      await screenshot(host, key + "-failure");
    } finally {
      if (id) await api(host, "end_session", { session: id }).catch(() => {});
    }
  }
} finally {
  await fs.writeFile(
    path.join(
      out,
      process.env.GP_UI_PROBE ? "doodle-probe.json" : "native.json",
    ),
    JSON.stringify({ findings, errors, responseLog }, null, 2),
  );
  await Promise.all(browser.contexts().map((c) => c.close()));
  await browser.close();
}
