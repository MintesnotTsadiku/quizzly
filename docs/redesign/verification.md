# Verification and limits

5 September 2026 · training.localhost

## Evidence

- Agent Plane exploratory sessions **BSR-2026-00948–00952** captured the original catalog, detail, authenticated lobby and joined guest surfaces. A development hot reload interrupted the long exploratory session; it is not counted as a clean passing run.
- Agent Plane **BSR-2026-00953** independently opened and interacted with the redesigned guest catalog and Common Ground explanation, with successful screenshots. Moving the development port generated expected hot-reload/old-origin connection errors in this exploratory session. The clean Playwright suites below are the authoritative error checks. A separate attempt to use Agent Plane’s Desk API was denied because the QA account lacks its runner role; no role or policy was changed.
- `qa/redesign/browser.mjs`, using Agent Harness's pinned Playwright runtime, completed **13 browser checks** with zero unexpected browser errors. The two deliberately induced offline errors are classified separately. It drives a real host-only session through all six conversation/share beats and completion, shared screen, reload, connection loss, replay and cancellation. It also checks guest hosting redirects, examples, unknown routes, empty filters, 390px layout and the first-party appearance contract.
- `qa/redesign/live-session.mjs` completes **four multiplayer checks** with three isolated guest controllers, collective team entries, real votes/predictions, shared-screen reveal, reload and persisted final scores. No console or page errors.
- `qa/redesign/embedded.mjs` passes inside the actual authenticated CMS `/home/games` tab (not just a standalone embed flag), and verifies a 768px dark-theme tablet.
- Eight focused Python tests pass (Common Ground mechanics, reveal snapshot counts and shared-branding provider compatibility).
- `qa/redesign/integration.py` passes against Frappe and Redis: zero-controller start, safe public snapshot, repeated-version advance, guest rejection and cooperative completion. It removes its exact test record.
- Production build succeeds with the installed Node 24 runtime. No schema migration is required.

The repeatable browser suites read the existing QA password directly from site configuration into memory. They never print it, put it in reports, or record login-form input.

## Visual review

`evidence/` contains before/after screenshots, browser result JSON and `working-session.webm`. The video follows a real Common Ground host from explanation to setup, shared play, recovery, completion and replay. It is a working-session recording, not a narrated tutorial.

Representative screens: `01-catalog-desktop.png`, `03-catalog-mobile.png`, `05-common-ground-detail.png`, `06-room-ready.png`, `08-shared-screen.png`, `10-room-finish.png`, `18-cms-actual.png`, `19-tablet-dark.png`. Original screenshots use the `before-` prefix.

## Product defects found and addressed

- Standalone branding inherited the church identity; guests saw Logout. Standalone now has an independent identity and preferences; embedding retains a validated appearance bridge.
- The dev plugin silently selected port 18113 despite a command-line request for 8081. The frontend now explicitly defaults to 8081, with `VITE_PORT` override for isolated environments.
- Projector snapshot did not populate participants already in the lobby. The initial snapshot now paints the roster. Reveal snapshots also omitted the prediction count, displaying zero after a refresh despite correctly recorded scores; the count now comes from persisted actions.
- Host and projector subscriptions registered cleanup after an asynchronous mount continuation. Cleanup is now registered during setup and the subscription helper avoids invalid lifecycle injection.
- A completed session could leave the host and players on the previous round's scoreboard. Final results now take priority, including after reloading; the multiplayer browser suite checks the host, all three players and projector.
- Invalid game URLs silently fell back to another game. They now show an explicit recovery state.
- Identical setup controls were reused for unrelated mechanics. The redesigned detail offers voting timers for Crowd Compass and round timers for performance/puzzle formats, while the host-only game has no timer or online roster.

## Boundaries, not implied certifications

- Tested three simultaneous guest controllers for Crowd Compass, not a 100-controller load test. Do not claim event-scale capacity from these runs.
- Shared-device play means a collective entry and score on compatible games. Separate household members, rotating controllers and true controller/team identity are roadmap work.
- Digital late joining is still rejected after the lobby. Existing reconnection resumes an established identity. Physical Common Ground participation can change freely.
- Common Ground needs a connection to create/advance a session. The browser preserves the current prompt during a short interruption, but this is not an offline app. Redis hot state expires after 24 hours without advancement; durable run status remains in Frappe.
- Common Ground content ships as two curated code-owned packs with five prompts each; each run samples three. General pack authoring, localization and moderation are subsequent work.
- Existing networked live-game visuals largely remain the established implementation. New discovery/detail and cooperative stage demonstrate the future direction; this release does not imply every game has been redesigned.
- Keyboard/native controls, contrast-conscious palette, reduced motion and small viewports were checked. A full screen-reader/assistive-technology audit and international user research remain necessary.
- The CMS continues to label its navigation tab “Quizzly”; changing that belongs to its own product scope. Inside the tab, GatherPlay keeps its identity while receiving context and theme.
