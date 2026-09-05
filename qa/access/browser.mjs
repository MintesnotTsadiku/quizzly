import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { chromium } from "/home/minte/projects/training-apps/apps/agent_harness/node_modules/playwright/index.mjs";
const base = "http://127.0.0.1:8081",
  out = new URL("../../docs/access/evidence/", import.meta.url).pathname;
const browser = await chromium.launch({ headless: true });
const checks = [],
  errors = [],
  sessions = [],
  packs = [];
let page;
function pass(s) {
  checks.push(s);
  console.log("PASS:", s);
}
async function api(p, method, params = {}) {
  return p.evaluate(
    async ({ method, params }) => {
      const r = await fetch("/api/method/" + method, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": window.csrf_token,
        },
        body: JSON.stringify(params),
      });
      const text = await r.text();
      let j = {};
      try {
        j = JSON.parse(text);
      } catch {}
      return { status: r.status, data: j.message, error: j.exception };
    },
    { method, params },
  );
}
async function host(p, method, params = {}, legacy = false) {
  return api(p, "quizzly.access.guest_host", { method, params, legacy });
}
async function shot(p, name) {
  await p.screenshot({ path: out + name + ".png" });
}
try {
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
    recordVideo: {
      dir: "/tmp/gp-access-video",
      size: { width: 1440, height: 1100 },
    },
  });
  page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => {
    if (m.type() === "error" && !/status of 403/.test(m.text()))
      errors.push(m.text());
  });
  await page.goto(base + "/play/");
  await page
    .getByRole("heading", { name: "Good company. Great games." })
    .waitFor();
  await shot(page, "01-landing");
  pass("Landing loads with site branding");
  await page.goto(base + "/play/games/common-ground");
  await page.getByRole("combobox").waitFor();
  await page.getByRole("combobox").click();
  await shot(page, "02-pack-picker");
  await page.keyboard.press("End");
  await page.keyboard.press("Enter");
  assert.match(await page.getByRole("combobox").innerText(), /imagination/);
  pass("Pack picker supports keyboard selection");
  await page.getByRole("button", { name: "Try hosting a game" }).click();
  await page.waitForURL(/\/room\//);
  const first = page.url().split("/").at(-1);
  sessions.push(["GP Session", first]);
  await page.getByRole("button", { name: "Everyone’s ready" }).click();
  await page.getByRole("button", { name: "We’re ready to share" }).waitFor();
  await shot(page, "03-guest-room");
  const cookie = (await ctx.cookies()).find(
    (c) => c.name === "gatherplay_trial",
  );
  assert.ok(cookie?.httpOnly);
  assert.equal(cookie.sameSite, "Lax");
  pass("Guest hosts a real room with an HttpOnly private trial cookie");
  const other = await browser.newContext();
  const foreign = await other.newPage();
  await foreign.goto(base + "/play/");
  const denied = await host(foreign, "get_host_state", { session: first });
  assert.equal(denied.status, 403);
  pass("Another guest cannot read host state");
  for (let i = 0; i < 3; i++) {
    await page.getByRole("button", { name: "We’re ready to share" }).click();
    await page
      .getByRole("button", {
        name: i === 2 ? "Finish together" : "Next conversation",
      })
      .click();
  }
  await page
    .getByRole("heading", { name: "A little more in common." })
    .waitFor();
  pass("Guest completes all cooperative rounds");
  await page.goto(base + "/play/create");
  await page.getByRole("button", { name: "Save my pack" }).click();
  await page.getByText("Saved privately.", { exact: false }).waitFor();
  const mine = await api(page, "quizzly.access.my_packs");
  assert.equal(mine.data.length, 1);
  packs.push(mine.data[0].name);
  await shot(page, "04-create-pack");
  const another = await api(page, "quizzly.access.save_pack", {
    title: "Should not save",
    prompts: [{ text: "Try?", choices: ["A", "B"] }],
  });
  assert.equal(another.status, 403);
  const foreignPacks = await api(foreign, "quizzly.access.my_packs");
  assert.equal(foreignPacks.data.length, 0);
  pass(
    "Private question pack saves; second guest pack is blocked; another guest sees none",
  );
  await page.getByRole("button", { name: "Host this pack" }).click();
  await page.waitForURL(/\/host\?session=/);
  sessions.push([
    "GP Session",
    new URL(page.url()).searchParams.get("session"),
  ]);
  await page.getByRole("button", { name: "Start ·" }).waitFor();
  const third = await host(page, "create_session", {
    game_key: "common-ground",
    configuration: { pack: "everyday" },
  });
  assert.equal(third.status, 403);
  pass("Custom pack opens a real lobby; third guest-hosted game is denied");
  await page.goto(base + "/play/access");
  await page.getByRole("heading", { name: "No payment required." }).waitFor();
  await shot(page, "05-access");
  await page.evaluate(() => navigator.serviceWorker.ready);
  const scope = await page.evaluate(
    async () => (await navigator.serviceWorker.ready).scope,
  );
  assert.ok(scope.endsWith("/play/"));
  const manifest = await ctx.request.get(
    base + "/api/method/quizzly.pwa.manifest",
  );
  assert.equal(manifest.status(), 200);
  assert.equal((await manifest.json()).icons.length, 2);
  pass("PWA manifest and scoped service worker are active");
  await ctx.setOffline(true);
  await page.goto(base + "/play/explore");
  await page
    .getByRole("heading", { name: "Keep the company. Reconnect the game." })
    .waitFor();
  await shot(page, "06-offline");
  await ctx.setOffline(false);
  pass("Offline navigation shows an honest recovery screen");
  const mobile = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  const mp = await mobile.newPage();
  await mp.goto(base + "/play/");
  await mp
    .getByRole("heading", { name: "Good company. Great games." })
    .waitFor();
  await shot(mp, "07-mobile");
  assert.ok(
    await mp.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  );
  await mp.goto(base + "/play/games/crowd-compass");
  await mp.getByRole("combobox").waitFor();
  await mp.locator(".gp-setup").scrollIntoViewIfNeeded();
  await shot(mp, "08-mobile-controls");
  assert.ok(
    await mp.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  );
  pass("390px landing and controls have no horizontal overflow");
} catch (e) {
  process.exitCode = 1;
  console.error(e);
  if (page) await shot(page, "failure");
} finally {
  let old = { sessions: [], packs: [] };
  try {
    old = JSON.parse(
      await fs.readFile("/tmp/gp-access-inventory.json", "utf8"),
    );
  } catch {}
  await fs.writeFile(
    "/tmp/gp-access-inventory.json",
    JSON.stringify({
      sessions: [...old.sessions, ...sessions],
      packs: [...old.packs, ...packs],
    }),
  );
  await fs.writeFile(
    out + "browser-results.json",
    JSON.stringify(
      { checks, errors, passed: !process.exitCode && !errors.length },
      null,
      2,
    ),
  );
  await browser.close();
  if (page?.video())
    await fs.copyFile(await page.video().path(), out + "working-session.webm");
}
