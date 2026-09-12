import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { chromium } from "../../../agent_harness/node_modules/playwright/index.mjs";
const base = "http://127.0.0.1:8081",
  out = new URL("../../docs/game-publishing/evidence/", import.meta.url)
    .pathname;
const browser = await chromium.launch({ headless: true });
const checks = [],
  errors = [],
  sessions = [];
function pass(value) {
  checks.push(value);
  console.log("PASS", value);
}
async function page(auth = false, width = 1280) {
  const c = await browser.newContext({
    baseURL: base,
    viewport: { width, height: 900 },
    extraHTTPHeaders: { "X-Frappe-Site-Name": "training.localhost" },
  });
  if (auth) {
    const r = await c.request.post("/api/method/login", {
      form: { usr: "Administrator", pwd: process.env.QUIZZLY_ADMIN_PASSWORD },
    });
    assert.equal(r.status(), 200);
  }
  const p = await c.newPage();
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto("/play/");
  await p.waitForFunction(() => window.csrf_token && window.site_name);
  return p;
}
async function api(p, method, params = {}) {
  return p.evaluate(
    async ({ method, params }) => {
      const r = await fetch("/api/method/" + method, {
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
        throw Error(
          method + ": " + r.status + " " + j.exc_type + " " + j._server_messages
        );
      return j.message;
    },
    { method, params }
  );
}
try {
  const host = await page(true);
  await host.goto("/play/games/common-ground?lang=en");
  await host.locator(".batch-picker input").waitFor();
  assert.equal(await host.locator(".batch-picker input").inputValue(), "3");
  await host.screenshot({
    path: out + "common-ground-setup.png",
    fullPage: true,
  });
  await host.getByRole("button", { name: "Set up our room" }).click();
  await host.waitForURL(/\/room\//);
  let session = host.url().split("/room/")[1].split("?")[0];
  sessions.push(session);
  const screen = await page();
  let state = await api(host, "quizzly.games.api.get_host_state", { session });
  await screen.goto("/play/room-screen/" + state.game_pin + "?lang=en");
  const seen = new Set();
  for (const expected of [3, 2]) {
    const [startResponse] = await Promise.all([
      host.waitForResponse((r) => r.url().includes("start_session")),
      host.getByRole("button", { name: /Everyone’s ready/ }).click(),
    ]);
    assert.equal(startResponse.status(), 200, await startResponse.text());
    for (let i = 0; i < expected; i++) {
      state = await api(host, "quizzly.games.api.get_host_state", { session });
      assert.equal(state.phase, "room_prompt");
      assert.ok(
        !seen.has(state.view.prompt),
        "no repeated conversation prompt"
      );
      seen.add(state.view.prompt);
      await host.reload();
      await host.locator("h1").waitFor();
      assert.equal(
        (await api(host, "quizzly.games.api.get_host_state", { session })).view
          .prompt,
        state.view.prompt
      );
      await api(host, "quizzly.games.api.advance_room", {
        session,
        expected_version: state.state_version,
      });
      state = await api(host, "quizzly.games.api.get_host_state", { session });
      await api(host, "quizzly.games.api.advance_room", {
        session,
        expected_version: state.state_version,
      });
    }
    await host.locator(".replay-controls").waitFor();
    state = await api(host, "quizzly.games.api.get_host_state", { session });
    assert.equal(state.batch.remaining, 5 - seen.size);
    await host.screenshot({
      path: out + `common-ground-ending-${expected}.png`,
      fullPage: true,
    });
    if (expected === 3) {
      await host.getByRole("button", { name: "Play next 2 prompts" }).click();
      await host.waitForURL((url) => !url.pathname.endsWith(session));
      session = host.url().split("/room/")[1].split("?")[0];
      sessions.push(session);
      await screen.waitForURL(
        (url) => url.pathname !== "/play/room-screen/" + state.game_pin,
        { timeout: 15000 }
      );
    }
  }
  pass(
    "Common Ground: 3 then 2 unseen prompts, durable reloads, projector follows, exhaustion shown"
  );
  assert.equal(
    await host.getByRole("button", { name: /Play next/ }).count(),
    0
  );
  await host
    .getByRole("button", { name: "Reset this group’s history" })
    .click();
  await host.getByRole("button", { name: "Reset and play again" }).click();
  await host.waitForURL((url) => !url.pathname.endsWith(session));
  session = host.url().split("/room/")[1].split("?")[0];
  sessions.push(session);
  state = await api(host, "quizzly.games.api.get_host_state", { session });
  assert.equal(state.batch.selected, 3);
  pass("Explicit reset retains the chosen batch size");
  await host.goto("/play/games/quiz?lang=am");
  await host.locator(".batch-picker input").waitFor();
  await host.setViewportSize({ width: 390, height: 844 });
  assert.ok(
    await host
      .locator(".batch-picker")
      .innerText()
      .then((t) => t.includes("ያለ ድግግሞሽ"))
  );
  assert.ok(
    await host.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth + 1
    )
  );
  await host.locator(".batch-picker").scrollIntoViewIfNeeded();
  await host.screenshot({
    path: out + "amharic-mobile-quiz-setup.png",
    fullPage: true,
  });
  pass("Amharic count controls render at 390px without horizontal overflow");
  // Use an existing public quiz; no pack content is changed by this check.
  const packs = await api(host, "quizzly.games.api.list_public_decks", {
    game_key: "quiz",
  });
  const pack = packs.find((p) => p.prompt_count >= 10);
  assert.ok(pack);
  const q = await api(host, "quizzly.api.create_session", {
    quiz: pack.name,
    question_count: 10,
  });
  sessions.push("quiz:" + q.session);
  await host.goto("/play/quizzly/host?session=" + q.session + "&lang=en");
  const player = await page(true, 390);
  const joined = await api(player, "quizzly.api.join_session", {
    pin: q.game_pin,
    nickname: "Batch Player",
  });
  await player.evaluate(
    (j) =>
      localStorage.setItem(
        "qz_player",
        JSON.stringify({
          token: j.participant_token,
          participant: j.participant,
          nickname: j.nickname,
          avatar: j.avatar,
          pin: j.game_pin,
        })
      ),
    joined
  );
  await player.goto("/play/quizzly/game?lang=en");
  await api(host, "quizzly.api.start_session", { session: q.session });
  await host.waitForTimeout(1200);
  const hs = await api(host, "quizzly.api.get_host_state", {
    session: q.session,
  });
  assert.equal(hs.batch.selected, 10);
  await api(host, "quizzly.api.end_session", { session: q.session });
  await host.waitForTimeout(1500);
  await host.reload();
  await host.locator(".replay-controls").waitFor();
  const playerReload = player.waitForEvent("framenavigated", {
    predicate: (frame) => frame === player.mainFrame(),
    timeout: 35000,
  });
  const next = await Promise.all([
    api(host, "quizzly.batches.replay", { session: q.session, quiz: true }),
    api(host, "quizzly.batches.replay", { session: q.session, quiz: true }),
  ]);
  assert.equal(next[0].session, next[1].session);
  sessions.push("quiz:" + next[0].session);
  await player.waitForFunction(
    (pin) => JSON.parse(localStorage.getItem("qz_player")).pin !== pin,
    q.game_pin,
    { timeout: 35000 }
  );
  await playerReload;
  await player.waitForFunction(() => window.csrf_token && window.site_name);
  const continued = await api(player, "quizzly.api.get_state", {
    pin: next[0].game_pin,
    token: joined.participant_token,
  });
  assert.equal(continued.status, "Lobby");
  pass(
    "Quiz: selected count honored, simultaneous replay requests return one room, original player token continues"
  );
  const crowdPacks = await api(host, "quizzly.games.api.list_public_decks", {
    game_key: "crowd-compass",
  });
  const crowd = await api(host, "quizzly.games.api.create_session", {
    game_key: "crowd-compass",
    configuration: {
      pack: crowdPacks.find((p) => p.prompt_count >= 3).name,
      rounds: 1,
      vote_seconds: 10,
      prediction_seconds: 10,
    },
  });
  sessions.push(crowd.session);
  const gpPlayer = await page(false, 390);
  const gpJoined = await api(gpPlayer, "quizzly.games.api.join_session", {
    pin: crowd.game_pin,
    nickname: "Replay Guest",
  });
  await gpPlayer.evaluate(
    (j) =>
      localStorage.setItem(
        "gp_player",
        JSON.stringify({
          token: j.participant_token,
          participant: j.participant,
          nickname: j.nickname,
          avatar: j.avatar,
          pin: j.game_pin,
          gameKey: j.game_key,
        })
      ),
    gpJoined
  );
  await gpPlayer.goto("/play/p/" + crowd.game_pin + "?lang=en");
  await host.goto("/play/host?session=" + crowd.session + "&lang=en");
  await host.waitForFunction(() => window.csrf_token);
  await api(host, "quizzly.games.api.start_session", {
    session: crowd.session,
  });
  const firstCrowd = await api(host, "quizzly.games.api.get_host_state", {
    session: crowd.session,
  });
  await gpPlayer.locator("button").first().waitFor();
  await api(host, "quizzly.games.api.end_session", { session: crowd.session });
  await host.waitForTimeout(1200);
  const following = await api(host, "quizzly.batches.replay", {
    session: crowd.session,
  });
  sessions.push(following.session);
  await gpPlayer.waitForURL(
    (url) => url.pathname === "/play/p/" + following.game_pin,
    { timeout: 35000 }
  );
  await gpPlayer.waitForFunction(() => window.csrf_token);
  const nextPlayer = await api(gpPlayer, "quizzly.games.api.get_player_state", {
    pin: following.game_pin,
    token: gpJoined.participant_token,
  });
  assert.equal(nextPlayer.status, "Lobby");
  await api(host, "quizzly.games.api.start_session", {
    session: following.session,
  });
  const nextCrowd = await api(host, "quizzly.games.api.get_host_state", {
    session: following.session,
  });
  assert.notEqual(nextCrowd.view.prompt, firstCrowd.view.prompt);
  await api(host, "quizzly.games.api.end_session", {
    session: following.session,
  });
  pass(
    "Crowd Compass: original guest token follows the new room and the next prompt is unseen"
  );
  assert.deepEqual(errors, []);
  await fs.writeFile(
    out + "browser.json",
    JSON.stringify({ checks, errors, sessions }, null, 2)
  );
} finally {
  await fs.writeFile(
    "/tmp/quizzly-publishing-qa-sessions.json",
    JSON.stringify(sessions)
  );
  await browser.close();
}
