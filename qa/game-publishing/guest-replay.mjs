import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { chromium } from "../../../agent_harness/node_modules/playwright/index.mjs";
const b = await chromium.launch({ headless: true });
async function page() {
  const c = await b.newContext({
    baseURL: "http://127.0.0.1:8081",
    extraHTTPHeaders: { "X-Frappe-Site-Name": "training.localhost" },
  });
  const p = await c.newPage();
  await p.goto("/play/");
  await p.waitForFunction(() => window.csrf_token);
  return p;
}
async function host(p, method, params = {}) {
  return p.evaluate(
    async ({ method, params }) => {
      const r = await fetch("/api/method/quizzly.access.guest_host", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": window.csrf_token,
        },
        body: JSON.stringify({ method, params, legacy: false }),
      });
      return { status: r.status, body: await r.json() };
    },
    { method, params }
  );
}
try {
  const owner = await page(),
    other = await page();
  const first = await host(owner, "create_session", {
    game_key: "common-ground",
    configuration: { pack: "everyday", rounds: 1 },
  });
  assert.equal(first.status, 200);
  const source = first.body.message.session;
  await host(owner, "start_session", { session: source });
  let state = (await host(owner, "get_host_state", { session: source })).body
    .message;
  await host(owner, "advance_room", {
    session: source,
    expected_version: state.state_version,
  });
  state = (await host(owner, "get_host_state", { session: source })).body
    .message;
  await host(owner, "advance_room", {
    session: source,
    expected_version: state.state_version,
  });
  assert.equal((await host(other, "replay", { session: source })).status, 403);
  const next = await host(owner, "replay", { session: source });
  assert.equal(next.status, 200);
  const retried = await host(owner, "replay", { session: source });
  assert.equal(retried.body.message.session, next.body.message.session);
  const second = next.body.message.session;
  await host(owner, "start_session", { session: second });
  await host(owner, "end_session", { session: second });
  assert.equal(
    (await host(owner, "replay", { session: second, reset: true })).status,
    403
  );
  const checks = [
    "Browser capability authorizes only its own replay",
    "Duplicate replay consumes no additional allowance",
    "Explicit reset cannot bypass the two-game guest trial",
  ];
  await fs.writeFile(
    new URL(
      "../../docs/game-publishing/evidence/guest-replay.json",
      import.meta.url
    ),
    JSON.stringify({ checks }, null, 2)
  );
  console.log(checks.join("\n"));
} finally {
  await b.close();
}
