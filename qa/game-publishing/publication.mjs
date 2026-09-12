import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { chromium } from "../../../agent_harness/node_modules/playwright/index.mjs";
const b = await chromium.launch({ headless: true }),
  base = "http://127.0.0.1:8081";
const output = new URL("../../docs/game-publishing/evidence/", import.meta.url)
  .pathname;
const checks = [];
let host, original;
async function api(page, method, params = {}) {
  return page.evaluate(
    async ({ method, params }) => {
      const r = await fetch("/api/method/" + method, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": window.csrf_token,
        },
        body: JSON.stringify(params),
      });
      return { status: r.status, body: await r.json() };
    },
    { method, params }
  );
}
async function page(auth) {
  const ctx = await b.newContext({
    baseURL: base,
    extraHTTPHeaders: { "X-Frappe-Site-Name": "training.localhost" },
  });
  if (auth) {
    const r = await ctx.request.post("/api/method/login", {
      form: { usr: "Administrator", pwd: process.env.QUIZZLY_ADMIN_PASSWORD },
    });
    assert.equal(r.status(), 200);
  }
  const p = await ctx.newPage();
  await p.goto("/play/");
  await p.waitForFunction(() => window.csrf_token);
  return p;
}
try {
  host = await page(true);
  const guest = await page(false);
  const catalog = await api(host, "quizzly.games.api.list_games");
  assert.equal(catalog.body.message.length, 6);
  original = (
    await api(host, "quizzly.publishing.management")
  ).body.message.games
    .filter((g) => g.published)
    .map((g) => g.key);
  await host.goto("/play/manage/games?lang=en");
  await host.locator("input[type=checkbox]").first().waitFor();
  assert.equal(await host.locator("input[type=checkbox]").count(), 26);
  await host.screenshot({
    path: output + "publication-management.png",
    fullPage: true,
  });
  assert.equal(
    (await api(guest, "quizzly.publishing.save", { published: [] })).status,
    403
  );
  assert.equal((await api(guest, "quizzly.publishing.management")).status, 403);
  const prior = (
    await api(host, "quizzly.games.api.create_session", {
      game_key: "common-ground",
      configuration: { pack: "everyday", rounds: 1 },
    })
  ).body.message;
  await host.locator('input[value="common-ground"]').uncheck();
  const [saved] = await Promise.all([
    host.waitForResponse((r) => r.url().includes("quizzly.publishing.save")),
    host.getByRole("button", { name: "Save publication settings" }).click(),
  ]);
  assert.equal(saved.status(), 200);
  assert.equal(
    (await api(guest, "quizzly.games.api.list_games")).body.message.length,
    5
  );
  await guest.goto("/play/games/common-ground?lang=en");
  await guest
    .getByRole("heading", { name: "We couldn’t find that game." })
    .waitFor();
  assert.equal(
    (
      await api(host, "quizzly.games.api.create_session", {
        game_key: "common-ground",
        configuration: { pack: "everyday" },
      })
    ).status,
    403
  );
  assert.equal(
    (
      await api(host, "quizzly.games.api.start_session", {
        session: prior.session,
      })
    ).status,
    200
  );
  assert.equal(
    (
      await api(host, "quizzly.games.api.get_host_state", {
        session: prior.session,
      })
    ).body.message.status,
    "Active"
  );
  await api(host, "quizzly.games.api.end_session", { session: prior.session });
  assert.equal(
    (await api(host, "quizzly.batches.replay", { session: prior.session }))
      .status,
    403
  );
  const embedded = await host.context().newPage();
  await embedded.goto("http://127.0.0.1:18033/home/games");
  const frame = embedded.frameLocator("#community-quizzly");
  await frame
    .locator('a[href*="/games/quiz"]')
    .first()
    .waitFor({ timeout: 45000 });
  assert.equal(
    await frame.locator('a[href*="/games/common-ground"]').count(),
    0
  );
  await embedded.screenshot({
    path: output + "embedded-publication.png",
    fullPage: true,
  });
  checks.push("Authenticated CMS iframe uses the same published catalog");
  await embedded.close();
  checks.push(
    "System Manager UI saves; guests cannot inspect or write; catalog, detail and hosting gate consistently; existing room finishes; successor requires publication"
  );
  for (const box of await host.locator("input[type=checkbox]").all())
    await box.uncheck();
  const [empty] = await Promise.all([
    host.waitForResponse((r) => r.url().includes("quizzly.publishing.save")),
    host.getByRole("button", { name: "Save publication settings" }).click(),
  ]);
  assert.equal(empty.status(), 200);
  assert.deepEqual(
    (await api(guest, "quizzly.games.api.list_games")).body.message,
    []
  );
  checks.push("An explicit empty selection publishes no formats");
  await fs.writeFile(
    output + "publication.json",
    JSON.stringify({ checks }, null, 2)
  );
  console.log(checks.join("\n"));
} finally {
  if (host && original)
    await api(host, "quizzly.publishing.save", { published: original });
  await b.close();
}
