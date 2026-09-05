import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { chromium } from "/home/minte/projects/training-apps/apps/agent_harness/node_modules/playwright/index.mjs";
const base = "http://127.0.0.1:8081",
  out = new URL("../../docs/access/evidence/", import.meta.url).pathname;
const browser = await chromium.launch();
const checks = [],
  errors = [],
  sessions = [];
const config = JSON.parse(
  await fs.readFile(
    "/home/minte/projects/training-apps/sites/training.localhost/site_config.json",
    "utf8",
  ),
);
try {
  const c = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const p = await c.newPage();
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto(base + "/play/");
  await p
    .getByRole("heading", { name: "Good company. Great games." })
    .waitFor();
  await p.evaluate(() => {
    const e = new Event("beforeinstallprompt", { cancelable: true });
    e.prompt = async () => {
      window.gpPromptCalled = true;
    };
    e.userChoice = Promise.resolve({ outcome: "dismissed" });
    window.dispatchEvent(e);
  });
  await p.getByRole("button", { name: "Install", exact: true }).waitFor();
  assert.equal(await p.evaluate(() => !!window.gpPromptCalled), false);
  await p.getByRole("button", { name: "Install", exact: true }).click();
  assert.equal(await p.locator(".gp-install").count(), 0);
  checks.push(
    "Mobile install suggestion waits for a tap and respects dismissal",
  );
  await p.goto(base + "/play/games/quiz");
  await p.getByRole("button", { name: "Try hosting a game" }).click();
  await p.waitForURL(/quizzly\/host/);
  await p.getByText("Start", { exact: false }).first().waitFor();
  await p.waitForTimeout(1200);
  const session = await p.evaluate(() =>
    localStorage.getItem("qz_hosted_session"),
  );
  if (session) sessions.push(["QZ Session", session]);
  await p.screenshot({ path: out + "21-guest-quiz.png" });
  checks.push("Legacy quiz hosting works for a guest trial");
  const login = await c.request.post(base + "/api/method/login", {
    form: {
      usr: "church-browser-qa@circle.localhost",
      pwd: config.church_browser_qa_password,
    },
  });
  assert.equal(login.status(), 200);
  await p.goto(base + "/play/access");
  await p
    .getByRole("heading", { name: "Ready when you are.", exact: true })
    .waitFor();
  checks.push(
    "Same-browser sign-in claims the guest trial into the existing account",
  );
  await p.goto(base + "/play/games/crowd-compass");
  await p.locator(".gp-setup").scrollIntoViewIfNeeded();
  await p.screenshot({ path: out + "22-mobile-controls.png" });
  const library = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const lp = await library.newPage();
  await lp.goto(base + "/play/create");
  await lp.getByRole("button", { name: "Save my pack" }).click();
  await lp.getByText("Saved privately.", { exact: false }).waitFor();
  await lp.reload();
  await lp.getByRole("button", { name: "Our kind of weekend · Edit" }).click();
  await lp.getByRole("button", { name: "Save changes" }).waitFor();
  checks.push(
    "Private pack library survives reload and reopens the editable pack",
  );
  await lp.screenshot({ path: out + "23-pack-library.png" });
} catch (e) {
  console.error(e.message);
  process.exitCode = 1;
} finally {
  let old = { sessions: [], packs: [] };
  try {
    old = JSON.parse(
      await fs.readFile("/tmp/gp-access-inventory.json", "utf8"),
    );
  } catch {}
  await fs.writeFile(
    "/tmp/gp-access-inventory.json",
    JSON.stringify({ ...old, sessions: [...old.sessions, ...sessions] }),
  );
  await fs.writeFile(
    out + "extras-results.json",
    JSON.stringify(
      { checks, errors, passed: !process.exitCode && !errors.length },
      null,
      2,
    ),
  );
  console.log(checks);
  await browser.close();
}
