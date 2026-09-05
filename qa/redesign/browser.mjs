// Uses Agent Harness's pinned browser runtime. Credentials stay in memory.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import assert from "node:assert/strict";
const root = fileURLToPath(new URL("../../", import.meta.url));
const bench = path.resolve(root, "../..");
const { chromium } = await import(
  pathToFileURL(
    path.join(bench, "apps/agent_harness/node_modules/playwright/index.mjs"),
  )
);
const base = process.env.GP_QA_URL || "http://127.0.0.1:8081";
const output = path.join(root, "docs/redesign/evidence");
await fs.mkdir(output, { recursive: true });
const config = JSON.parse(
  await fs.readFile(
    path.join(bench, "sites/training.localhost/site_config.json"),
    "utf8",
  ),
);
const browser = await chromium.launch({ headless: true });
const checks = [],
  errors = [],
  sessions = [];
const contexts = [];
function pass(name) {
  checks.push(name);
  console.log("PASS:", name);
}
async function context(
  viewport = { width: 1440, height: 1000 },
  auth = false,
  video = false,
) {
  const c = await browser.newContext({
    baseURL: base,
    viewport,
    colorScheme: "light",
    reducedMotion: "reduce",
    ...(video
      ? {
          recordVideo: {
            dir: "/tmp/gp-redesign-final-video",
            size: { width: 1440, height: 1000 },
          },
        }
      : {}),
  });
  contexts.push(c);
  if (auth) {
    const r = await c.request.post("/api/method/login", {
      form: {
        usr: "church-browser-qa@circle.localhost",
        pwd: config.church_browser_qa_password,
      },
    });
    assert.equal(r.status(), 200, "QA login succeeds");
  }
  return c;
}
function monitor(page, label) {
  page.on("pageerror", (e) =>
    errors.push({ label, type: "pageerror", message: e.message }),
  );
  page.on("console", (m) => {
    if (m.type() === "error")
      errors.push({ label, type: "console", message: m.text() });
  });
}
async function shot(page, name) {
  await page.screenshot({
    path: path.join(output, name + ".png"),
    fullPage: false,
  });
}
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
      if (!r.ok) throw new Error(method + ": HTTP " + r.status());
      return j.message;
    },
    { method, params },
  );
}
async function go(page, url) {
  await page.goto(url, { waitUntil: "domcontentloaded" });
}
async function noOverflow(page) {
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
    "No viewport overflow",
  );
}
let host, hostContext, videoPage;
try {
  const guestContext = await context();
  const guest = await guestContext.newPage();
  monitor(guest, "guest");
  await go(guest, "/play/");
  await guest
    .getByRole("heading", { name: "Good company. Great games." })
    .waitFor();
  await guest.locator(".gp-game-card").first().waitFor();
  assert.equal(await guest.locator(".gp-game-card").count(), 6);
  assert.equal(
    await guest.getByText("Circle Church", { exact: true }).count(),
    0,
  );
  assert.equal(
    await guest.getByRole("button", { name: "Sign out" }).count(),
    0,
  );
  await shot(guest, "01-catalog-desktop");
  pass("Independent guest identity and curated six-game collection");
  await guest
    .getByRole("button", { name: "Just the host", exact: false })
    .click();
  assert.equal(await guest.locator(".gp-game-card").count(), 1);
  await guest.getByRole("button", { name: "Perform", exact: true }).click();
  await guest.getByText("No games with that combination yet.").waitFor();
  await guest
    .getByRole("button", { name: "Show all games", exact: true })
    .click();
  pass("Device/category intersection and recoverable empty state");
  await guest
    .getByRole("searchbox", { name: "Search games" })
    .fill("no such game");
  await guest.getByText("No games with that combination yet.").waitFor();
  await guest
    .getByRole("button", { name: "Show all games", exact: true })
    .click();
  await go(guest, "/play/games/crowd-compass");
  await guest
    .getByRole("heading", { name: "Crowd Compass", exact: true })
    .waitFor();
  await guest.getByRole("button", { name: "A · Outside", exact: true }).click();
  await guest.getByRole("button", { name: "A · Outside", exact: true }).click();
  await guest
    .getByText("Outside: 6 votes · Inside: 4 votes", { exact: true })
    .waitFor();
  await shot(guest, "02-crowd-detail");
  pass("Interactive worked example without authentication");
  await go(guest, "/play/games/not-a-real-game");
  await guest
    .getByRole("heading", { name: "We couldn’t find that game." })
    .waitFor();
  pass("Unknown detail has explicit recovery");
  await go(guest, "/play/room/not-a-real-session");
  await guest.waitForURL(/\/login/);
  pass("Guest host-route authorization redirect");
  const mobileContext = await context({ width: 390, height: 844 });
  const mobile = await mobileContext.newPage();
  monitor(mobile, "mobile");
  await go(mobile, "/play/");
  await mobile.locator(".gp-game-card").first().waitFor();
  await noOverflow(mobile);
  await shot(mobile, "03-catalog-mobile");
  await go(mobile, "/play/games/common-ground");
  await mobile
    .getByRole("heading", { name: "Common Ground", exact: true })
    .waitFor();
  await noOverflow(mobile);
  await shot(mobile, "04-detail-mobile");
  await mobileContext.close();
  pass("390px catalog and detail without horizontal overflow");
  hostContext = await context(undefined, true, true);
  host = await hostContext.newPage();
  videoPage = host;
  monitor(host, "host");
  await go(host, "/play/games/common-ground");
  await host
    .getByRole("heading", { name: "Common Ground", exact: true })
    .waitFor();
  await host.getByRole("button", { name: "Show me how it feels" }).click();
  await shot(host, "05-common-ground-detail");
  await host.getByRole("button", { name: "Set up our room" }).click();
  await host.waitForURL(/\/play\/room\//);
  let session = host.url().split("/").pop();
  sessions.push(session);
  await host.getByRole("button", { name: "Everyone’s ready" }).waitFor();
  let state = await api(host, "get_host_state", { session });
  assert.equal(state.participants.length, 0);
  await shot(host, "06-room-ready");
  const screenContext = await context({ width: 1920, height: 1080 });
  const screen = await screenContext.newPage();
  monitor(screen, "screen");
  await go(screen, `/play/room-screen/${state.game_pin}`);
  await screen.getByRole("heading", { name: /Put the phones down/ }).waitFor();
  assert.equal(
    await screen.getByRole("button", { name: "Everyone’s ready" }).count(),
    0,
  );
  await host.getByRole("button", { name: "Everyone’s ready" }).click();
  await host.getByRole("button", { name: "We’re ready to share" }).waitFor();
  await screen
    .getByText("Talk it through together", { exact: false })
    .waitFor();
  await shot(host, "07-room-live");
  await shot(screen, "08-shared-screen");
  pass(
    "Real host-only session starts with zero participants; public screen has no host controls",
  );
  const prompt = await host.locator("h1").innerText();
  await host.reload({ waitUntil: "domcontentloaded" });
  await host.getByRole("button", { name: "We’re ready to share" }).waitFor();
  assert.equal(await host.locator("h1").innerText(), prompt);
  pass("Host reload resumes the same conversation");
  await hostContext.setOffline(true);
  await host
    .getByText("Connection interrupted.", { exact: false })
    .waitFor({ timeout: 12000 });
  assert.equal(await host.locator("h1").innerText(), prompt);
  await hostContext.setOffline(false);
  await host.locator(".gp-error").waitFor({ state: "hidden", timeout: 20000 });
  pass("Disconnected host retains prompt and recovers");
  await host.getByRole("button", { name: "We’re ready to share" }).click();
  await host.getByRole("button", { name: "Next conversation" }).waitFor();
  await shot(host, "09-room-share");
  for (let i = 0; i < 2; i++) {
    await host.getByRole("button", { name: "Next conversation" }).click();
    await host.getByRole("button", { name: "We’re ready to share" }).click();
  }
  await host.getByRole("button", { name: "Finish together" }).click();
  await host
    .getByRole("heading", { name: "A little more in common." })
    .waitFor();
  await shot(host, "10-room-finish");
  await screen
    .getByRole("heading", { name: "A little more in common." })
    .waitFor();
  pass("Three conversations and shares finish on both host and public display");
  await host.getByRole("button", { name: "Play another round" }).click();
  await host.getByRole("button", { name: "Everyone’s ready" }).waitFor();
  const replay = host.url().split("/").pop();
  assert.notEqual(replay, session);
  sessions.push(replay);
  await host.getByRole("button", { name: "End game", exact: true }).click();
  await host.getByRole("button", { name: "Keep playing" }).click();
  await host.getByRole("button", { name: "Everyone’s ready" }).waitFor();
  pass("Replay creates a fresh session; end confirmation can be cancelled");
  await api(host, "end_session", { session: replay });
  await screenContext.close();
  await hostContext.close();
  await videoPage.video().saveAs(path.join(output, "working-session.webm"));
  // Exercise the exact first-party embedding contract with a real iframe and origin-checked appearance message.
  const embed = await guestContext.newPage();
  monitor(embed, "embed");
  await embed.route("**/qa-embed", (r) =>
    r.fulfill({
      contentType: "text/html",
      body: `<!doctype html><html><body style="margin:0"><iframe title="GatherPlay in community" src="/play/?embed=cms" style="border:0;width:100%;height:950px"></iframe><script>addEventListener('message',e=>{if(e.data.type==='quizzly:ready')e.source.postMessage({type:'cms:appearance',version:1,mode:'light',tokens:{'--cms-page':'#f6f8fa','--cms-surface':'#ffffff','--cms-text':'#202630','--cms-border':'#dce1e6','--cms-brand-primary':'#295b4b','--cms-brand-accent':'#477e70','--cms-danger':'#b23030'},branding:{short_name:'Community QA'}},location.origin)})</script></body></html>`,
    }),
  );
  await go(embed, "/qa-embed");
  const frame = embed.frameLocator("iframe");
  await frame
    .getByRole("heading", { name: "Good company. Great games." })
    .waitFor();
  await frame.getByText("Community QA", { exact: true }).waitFor();
  await shot(embed, "11-embedded");
  pass(
    "Same-origin embedded branding keeps GatherPlay identity and host context",
  );
  await go(guest, "/play/room-screen/000000");
  await guest
    .getByRole("heading", { name: "This room isn’t available." })
    .waitFor();
  pass("Unknown shared-screen room has recovery");
} catch (e) {
  console.error("FAILED:", e.message);
  process.exitCode = 1;
  if (host && !host.isClosed()) await shot(host, "failure-host");
} finally {
  // Preserve only sessions explicitly created by this run; cleanup is performed by the companion audit.
  await fs.writeFile(
    "/tmp/gp-redesign-session-ids.json",
    JSON.stringify(sessions),
  );
  const unexpected = errors.filter(
    (e) => !e.message.includes("ERR_INTERNET_DISCONNECTED"),
  );
  await fs.writeFile(
    path.join(output, "browser-results.json"),
    JSON.stringify(
      {
        base,
        checks,
        errors: unexpected,
        expectedOfflineErrors: errors.length - unexpected.length,
        sessionIds: sessions,
        passed: !process.exitCode && unexpected.length === 0,
      },
      null,
      2,
    ),
  );
  if (unexpected.length) {
    console.log("Unexpected browser errors:", JSON.stringify(unexpected));
    process.exitCode = 1;
  }
  await browser.close();
}
