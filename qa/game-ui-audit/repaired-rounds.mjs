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
    roundImages: await p.locator('img[data-clue="round"]').count(),
    audio: await p.locator("audio").count(),
    sliders: await p.locator('input[type="range"],[role="slider"]').count(),
  };
}
await fs.mkdir(out, { recursive: true });
const testedKeys = [
  "picture-peek",
  "memory-mosaic",
  "sound-snap",
  "signal-spectrum",
  "sequence-sprint",
  "phrase-forge",
  "caption-clash",
  "story-loom",
  "seek-and-show",
  "one-word-chorus",
  "common-thread",
  "closest-call",
  "bluffline",
  "bracket-bash",
  "escape-together",
];
async function privateView(p, j, pin) {
  return (await api(p, "get_player_state", { pin, token: j.participant_token }))
    .view;
}
async function next(expected) {
  await api(host, "host_command", { session: id, command: "next" });
  if (expected) return phase(expected);
  await host.waitForTimeout(1300);
}
try {
  host = await page(1360, 960, true);
  await host.goto("/play/");
  const a = await page(),
    b = await page(),
    screen = await page(1440, 1000);
  await a.goto("/play/");
  await b.goto("/play/");
  for (const key of testedKeys) {
    const row = { key };
    findings.push(row);
    try {
      const packs = await api(host, "list_public_decks", {
        game_key: key,
        language: "en",
      });
      const pack = packs.find((p) => p.demo_key.startsWith("curated-v2-"));
      assert.ok(pack, key + " curated pack");
      const room = await api(host, "create_session", {
        game_key: key,
        configuration: {
          pack: pack.name,
          rounds: ["story-loom", "one-word-chorus"].includes(key)
            ? 2
            : key === "escape-together"
              ? 3
              : 1,
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
      await Promise.all([
        host.goto("/play/host?session=" + id),
        a.goto("/play/p/" + room.game_pin),
        b.goto("/play/p/" + room.game_pin),
      ]);
      await api(host, "start_session", { session: id });
      await host.waitForTimeout(1800);
      await screen.goto("/play/s/" + room.game_pin + "/screen");
      let rounds = 0,
        secret = "";
      for (let step = 0; step < 28; step++) {
        const state = await api(host, "get_host_state", { session: id });
        const v = state.view;
        if (state.status === "Ended") {
          row.ending = state.ending;
          row.completed = true;
          break;
        }
        if (state.phase === "memory_study") {
          await a.locator('img[data-clue="study"]').waitFor();
          assert.equal(
            (await privateView(a, ja, room.game_pin)).choices.length,
            0,
          );
          await screenshot(a, key + "-study");
          await next("round_open");
          continue;
        }
        if (state.phase === "chorus_clues") {
          for (const [p, j] of [
            [a, ja],
            [b, jb],
          ]) {
            const pv = await privateView(p, j, room.game_pin);
            if (pv.is_guesser) {
              assert.ok(!pv.secret);
              continue;
            }
            secret = pv.secret;
            await p.locator("main input").fill("shelter");
            await p
              .getByRole("button", { name: "Lock clue", exact: true })
              .click();
          }
          await next("round_open");
          continue;
        }
        if (state.phase === "round_open") {
          rounds++;
          await a
            .getByRole("heading", { name: v.prompt, exact: true })
            .waitFor();
          if (key === "memory-mosaic")
            assert.equal(
              await a
                .locator('img[data-clue="study"], img[data-clue="round"]')
                .count(),
              0,
            );
          if (["picture-peek", "caption-clash"].includes(key)) {
            await a.locator('img[data-clue="round"]').waitFor();
            assert.ok(
              await a
                .locator('img[data-clue="round"]')
                .evaluate((img) => img.complete && img.naturalWidth > 0),
            );
          }
          if (key === "sound-snap") {
            await a.locator("audio").waitFor();
            await a.locator("audio").evaluate((el) => el.play());
            assert.ok(await a.locator("audio").evaluate((el) => !el.paused));
          }
          await screenshot(a, key + "-play");
          for (const [p, j, n] of [
            [a, ja, 0],
            [b, jb, 1],
          ]) {
            const pv = await privateView(p, j, room.game_pin);
            if (key === "one-word-chorus" && !pv.is_guesser) continue;
            if (v.mechanic === "choice") {
              const choice =
                key === "escape-together"
                  ? ["430", "7", "8"][rounds - 1]
                  : v.choices[0];
              await p
                .getByRole("button", { name: choice, exact: true })
                .click();
            } else if (v.mechanic === "order") {
              for (const card of v.choices)
                await p
                  .getByRole("button", { name: card, exact: true })
                  .click();
              await p
                .getByRole("button", { name: "Undo", exact: true })
                .click();
              await p
                .getByRole("button", { name: v.choices.at(-1), exact: true })
                .click();
              await p
                .getByRole("button", { name: "Lock order", exact: true })
                .click();
            } else if (key === "signal-spectrum") {
              await p.locator('input[type="range"]').fill("50");
              await p
                .getByRole("button", { name: "Lock position", exact: true })
                .click();
            } else {
              await p
                .locator("main input")
                .fill(
                  key === "one-word-chorus"
                    ? secret
                    : v.mechanic === "number"
                      ? "50"
                      : key === "picture-peek"
                        ? v.media_url.split("/").at(-1).split(".")[0]
                        : n
                          ? "We invited the moon inside."
                          : "The little door began to sing.",
                );
              await p
                .getByRole("button", { name: "Lock response", exact: true })
                .click();
            }
            await p.waitForTimeout(450);
            const locked = await privateView(p, j, room.game_pin);
            assert.equal(locked.locked, true, key + " response locked");
          }
          await a.reload();
          await a
            .getByRole("heading", { name: v.prompt, exact: true })
            .waitFor();
          assert.equal(
            await a
              .getByRole("button", { name: "Lock response", exact: true })
              .count(),
            0,
            key + " reload lock",
          );
          await next();
          continue;
        }
        if (state.phase === "vote_open") {
          for (const [p, j] of [
            [a, ja],
            [b, jb],
          ]) {
            const pv = await privateView(p, j, room.game_pin);
            if (pv.choices.length) {
              await p
                .getByRole("button", { name: pv.choices[0].value, exact: true })
                .click();
              await p.waitForTimeout(350);
            }
          }
          await next("round_reveal");
          continue;
        }
        if (state.phase === "seek_review") {
          await host.locator('input[type="checkbox"]').first().check();
          await host
            .getByRole("button", { name: "Confirm and reveal", exact: true })
            .click();
          await phase("round_reveal");
          continue;
        }
        if (state.phase === "round_reveal") {
          assert.ok(Array.isArray(v.results), key + " persisted reveal");
          row.reveal = v;
          await screen
            .getByRole("heading", { name: "Reveal", exact: true })
            .waitFor();
          await screenshot(screen, key + "-reveal");
          await next("scoreboard");
          continue;
        }
        if (state.phase === "scoreboard") {
          await next();
          continue;
        }
        await host.waitForTimeout(700);
      }
      assert.ok(row.completed, key + " reaches ending");
      pass(key + " full session, rendered inputs, locked reconnect and reveal");
    } catch (e) {
      row.error = e.message;
      console.log("FAILED", key, e.message);
      await screenshot(host, key + "-failure");
    } finally {
      if (id) await api(host, "end_session", { session: id }).catch(() => {});
      await fs.writeFile(
        path.join(out, "sessions.json"),
        JSON.stringify({ findings, errors }, null, 2),
      );
    }
  }
} finally {
  await Promise.all(browser.contexts().map((c) => c.close()));
  await browser.close();
}
if (findings.some((r) => !r.completed)) process.exitCode = 1;
