# Progress

## Fixes found in end-to-end testing (2026-07-19)

A full host + two-player run in a real browser turned up three defects, all now fixed.

- **Host stuck on a dead game.** A session whose loop worker died stayed `Active` forever, and `get_live_host_session` kept handing it back, so the quiz picker never returned and "New game" was a no-op. `end_session` was no better: it only set a Redis control flag that no loop was left to read. `engine.is_abandoned` now names the condition (Active, no loop state, older than the state TTL), `get_live_host_session` reaps every abandoned session it walks past, `get_host_state` settles a remembered one into its podium, and `end_active_session` ends a loopless game directly instead of flagging it. Five tests in `test_game_ux.py`, including one that a Lobby waiting for players is never reaped.
- **Countdown bar was invisible.** Both the host and player timer bars used `bg-ink-gray-9`, which frappe-ui defines as an ink (text) token only, so the fill computed to `rgba(0,0,0,0)` and the bar always read as empty. Now `bg-surface-gray-7`.
- **Locked-in shape rendered black.** The confirmation shape built its SVG class at runtime with `fill.replace("bg-", "fill-")`, so Tailwind never saw those class names and only generated the ones that happened to appear elsewhere: red worked, blue, amber and green came out black. `SHAPES` now carries an `svgFill` literal per shape.
- **A quiet socket froze a screen for good.** Two player tabs stopped receiving events mid-game and never recovered: the design has no polling fallback, and `useSessionRoom` only re-joined the room on a `connect` event that never came. It now tracks the time of the last event and re-joins (plus resyncs) after 20 seconds of silence, so a lost room membership or a reconnect that never lands costs one `get_state` instead of the rest of the game. Long pauses between questions are normal, hence the generous threshold; verified in the browser that a silent stats pause triggers exactly one resync per interval and an active game triggers none.
- **Result badge was unreadable.** The correct/wrong circle used `bg-surface-green-3` and `bg-surface-red-3`, two tokens with opposite lightness, so no single glyph colour worked: a black ✓ on dark green, then a white ✕ on pale red. Both now use the strong game palette (`bg-green-600` / `bg-red-500`) with white glyphs.
- **Tests leaked their fixtures onto the site.** Engine steps commit mid-test, so the framework rollback left every test quiz and session behind; the host's quiz picker had grown to 26 stray "Engine Quiz" entries and 6 sessions stuck `Active`. `GameTestCase.tearDown` now deletes what it created, and the existing junk was purged.

### Verified

Full 4-question game, host plus two guests, played through get-ready, live answer counts, reveal with distribution, streak callout and podium. Scores matched the engine (Ada 2043, Grace 2041).

## Phase 4c: Player fun (2026-07-19)

Phase 4 was split into four independently shippable slices (`specs/phase-4a..4d`); this is the third.

### Done

- Avatar packs. A pack is a JSON manifest in `quizzly/avatar_packs/` holding the roster, the background palette, and the framing; `site_config.quizzly_avatar_pack` picks the active one. `quizzly/avatars.py` loads it and hands it to the SPA through the existing portal boot context, so the roster has one source of truth and the join path costs no extra request. Shipped pack is DiceBear `notionists` (CC0, 24 avatars).
- `yarn build:avatars` pre-renders `kind: "dicebear"` packs to static SVG under `quizzly/public/avatars/<pack>/`, output committed. The DiceBear libraries are devDependencies only and never reach the runtime bundle; at runtime an avatar id is just an `<img>` URL, which is also how a bought `kind: "static"` pack drops in with no code change.
- `QZ Participant.avatar`, validated in the controller against the active roster. `join_session` takes an optional `avatar` and falls back to a crc32-of-nickname pick. `avatar` now rides along on lobby updates, leaderboards, top-5, streak callouts, podium, and `get_state`.
- Nickname generator: three suggestions with a reroll on the join screen. Word lists live in `quizzly/nicknames.py` and reach the SPA through the boot context.
- Sound synthesised with Web Audio (`frontend/src/sound.js`): countdown tick, submit blip, correct/wrong stings, podium arpeggio, plus a persisted mute toggle on both screens.
- Tests: 9 new (`test_avatars.py`, `test_nicknames.py`). 45 green across the app.

### Exit criteria verified

Full 4-question game in headless Chrome (host + two players) against the live site: both players picked distinct avatars and generated nicknames, and those avatars showed on the host lobby chips, the live leaderboard, the player header, and both podiums. No console errors from the audio path. Contact sheet of all 24 avatars reviewed at render size.

### Notes

- No free avatar library matches the 3D-rendered reference look (Inner Teens); that style is a commercial category. The pack system exists so that decision stays reversible: swapping to a bought 3D pack is a manifest plus a folder.
- `notionists` draws half-body portraits that read as a cropped torso in a circle. Framing (`scale: 140`, `translateY: 25`) is per-pack manifest data, chosen by rendering a comparison sheet.
- An unknown avatar id is rejected rather than defaulted, so a stale client or a manifest entry that was never rendered fails loudly instead of showing a blank circle. A test asserts every manifest id has a file on disk.
- `quizzly/avatars.py` (module) and `quizzly/avatar_packs/` (data) are deliberately not the same name; a module and a package directory sharing a name in one directory breaks imports.
- Players default to muted and the host defaults to audible: a classroom of phones all unmuting at once is a bad time.
- Lobby background music is dropped from scope. A listenable loop is a composition, not a synth line.
- Cleared three stale `Active` sessions from earlier phase testing; `get_live_host_session` picks the newest live session, so an abandoned one hides the quiz picker forever. Worth a real fix (auto-expire) if it recurs outside tests.

## Phase 3: Game UX (2026-07-19)

### Done

- Player screen (`Play.vue`) is one state machine: lobby -> get-ready -> question -> locked-in -> result -> podium, plus a kicked terminal state. Kahoot shapes (triangle/diamond/circle/square, colour keyed to the canonical option id), local countdown bar, per-player answer shuffle seeded by the participant token, result interstitial with correct/wrong, points, streak, rank and top-5.
- Host screen (`Host.vue`): lobby with giant PIN, client-side QR (`qrcode`), join URL, name grid, lock/kick/auto-advance/start; game view with live answer count, timer bar, correct-answer reveal, distribution bar chart, top-5 and streak callouts, next/skip/end; podium with a 1-2-3 stand and the full leaderboard.
- Engine: a 3-second `get_ready` read-the-question pause before each question (own Redis phase, so reconnect lands in it too). `question` payloads now carry `window_ms` (clients count down from receipt, so client clock skew cannot matter) and `randomize_answer_order`.
- New APIs: `get_host_state` (whole host screen in one call; finds the host's live session when no name is passed, so a reload restores mid-game), `get_result` (own outcome for the interstitial, keeping per-player data out of the broadcast), `set_auto_advance` (loop re-reads the flag each pause, so it can flip mid-game). `get_state` gained rank/leaderboard and now resolves Ended sessions so a player who reloads on the podium keeps it.
- Nickname profanity filter in `quizzly/profanity.py`, applied in `join_session`: leetspeak folded, matched as a substring against a curated wordlist.
- Tests: 9 new in `tests/test_game_ux.py` (filter both ways, host state in lobby/mid-question/non-host, own result and rank, podium after reload). 36 green across the app.

### Exit criteria verified

Full 4-question game driven in headless Chrome with three browser sessions (host + two players) against the live site and a real RQ worker: get-ready countdown, shapes, per-player shuffle confirmed different for each player, correct/wrong interstitials with points, distribution chart, "Ada is on a 3 answer streak" callout, podium. Player and host both reloaded mid-question and landed back in the right phase with the right remaining time; both also restored the podium after reload. Profanity filter rejected `Sh1tLord` in the real join form.

### Notes

- Socket reconnects used to go silently deaf: socket.io reconnects on its own but the server-side room membership is gone, and `qz_join` was only emitted on mount. Found in E2E when a backgrounded host tab stopped receiving events and missed the podium. `useSessionRoom` now re-emits `qz_join` on every `connect` and resyncs from the state API.
- A centered flex column (`justify-center`) clips its own top when the content overflows; the host game view uses `m-auto` on an inner wrapper instead.
- Percentage heights collapse inside an `items-end` flex row (the parent's height is content-derived), which is why the first distribution chart rendered blank.
- frappe-ui's tailwind preset caps `fontSize` at `3xl`; `5xl` and `6xl` joined the existing `4xl`/`8xl` overrides.
- The game loop occupies one `long`-queue worker for the whole game. On this bench a single shared worker serves short/default/long, so an unrelated stuck job stalls every game; deployment wants dedicated long workers.

## Phase 2: Game Engine (2026-07-19)

### Done

- `quizzly/engine.py`: RQ game loop (`queue="long"`, `job_id=qz_session_{name}`, `deduplicate`, timeout sized to quiz length). Per question: Redis state write, `question` publish (no correct answer, server `deadline_ts`), sleep-with-poll until deadline + 1s grace, close, score, `question_closed` publish (correct option, distribution, top-5, streak callouts >= 3), then auto-advance after 5s stats or wait for host (capped at 5 min, then advances anyway). After last question: ranks persisted, `podium` published, status Ended, Redis state cleared.
- Redis keys per spec: `qz:{session}:state` (dict, TTL window+30s), `qz:{session}:answered:{question_row}` (set, duplicate pre-check), plus `qz:{session}:control` for host commands (`skip`/`advance`/`end`) polled by the loop. Host controls never touch the loop process directly; the flag survives web/worker process boundary.
- Scoring: Kahoot formula, `response_ms` clamped to window so grace submits floor at 500 base. Streak bonus capped at 250, multiplier 0/1/2. Non-answerers get streak reset at close.
- APIs: host `start_session` (Lobby -> Active, enqueue loop, rejects empty lobby), `next_question`, `skip_question`, `end_session` (Lobby -> Cancelled, Active -> control flag). Guest `submit_answer` (full gauntlet in spec order, returns only `{"ok": true}`, publishes `answer_count`) and `get_state` (reconnect: phase, question sans answer, `remaining_seconds`, own score/answered). Both token-scoped rate-limited.
- Tests: 19 in `tests/test_engine.py`, all green. Whole spec checklist covered: late/duplicate/wrong-question/kicked rejection, DB unique constraint as final word (Redis pre-check bypassed), scoring boundaries + streak reset + multipliers, no `correct` substring in any pre-close payload, reconnect remaining time, full loop to podium with scripted answers.

### Exit criteria verified

Full game played start to podium over HTTP against the live site with the real RQ worker (2 players, 2 questions): questions arrived with correct remaining time, correct answer absent from payloads, duplicate submits got 417, scores/streaks/ranks persisted exactly per formula (checked in DB: 946 + 1982 = 2928, streak 2, rank 1), session Ended with podium event.

### Notes

- Loop commits after each publish so `after_commit` realtime events flush from the worker; submits land in separate web transactions and are visible at close.
- `wait_before_next` accepts host `advance` even during the 5s stats pause; auto-advance mode ignores stray flags.
- Host game-screen state API deliberately deferred to phase 3 (spec lists only guest `get_state`); host reconnect currently rides on the socket events.

## Phase 1: Content + Session Shell (2026-07-19)

### Done

- All five DocTypes per spec: `QZ Quiz` (+ child `QZ Question`), `QZ Session`, `QZ Participant`, `QZ Answer`. Permissions as specified: Quiz Host `if_owner` on Quiz/Session, System Manager only on Participant/Answer. `QZ Answer` gets a DB-level unique index on (participant, question_row) via `on_doctype_update`.
- `quizzly/api.py`: host APIs `create_session`, `lock_lobby`, `unlock_lobby`, `kick_participant`, `get_lobby` (host-only via session.host check); guest APIs `join_session`, `leave_session` (`allow_guest`, IP rate-limited 10/min). Tokens: 32-byte random, sha256 stored, raw returned once. Lobby changes publish `lobby_update` (and `kicked`) to room `qz_session_{pin}` with `after_commit=True`.
- Nickname uniqueness (per session, non-kicked) validated in the `QZ Participant` controller; kicked nicknames are freed for reuse.
- `quizzly/www/quizzly.py` boot context injects `csrf_token` + `site_name` so frappe-ui requests work for logged-in hosts.
- Frontend: `Join.vue` (PIN prefilled from `?pin=`, nickname, error display), `Play.vue` (waiting room, live lobby count, kicked banner, leave), `Host.vue` (quiz picker, giant PIN, join link, live participant chips, lock toggle, click-to-kick). Player identity kept in localStorage (`player.js`), thin `api.js` wrapper over `frappeRequest`.
- Tests: 8 integration tests in `quizzly/tests/test_api.py`, all green (`bench --site quizzly.localhost run-tests --module quizzly.tests.test_api`; needed `set-config allow_tests true` once).

### Exit criteria verified

All checked E2E: over HTTP+socket (node client: join publishes `lobby_update` into the room), and in a real headless browser (two tabs, host + player): PIN/QR-link join, name pops on host screen live, wrong PIN 404, locked lobby 417 (error shown in UI), duplicate nickname 409, kick 200 with player seeing "The host removed you" and the kicked token rejected (403).

### Notes

- frappe-ui's tailwind preset caps `fontSize` at `3xl` (24px); display sizes (`4xl`, `8xl`) added in `tailwind.config.js` for the big PIN.
- `frappe.rate_limiter.rate_limit` no-ops when `frappe.request` is absent, so direct calls in tests skip rate limits.
- Deliberate shortcuts: host lobby state is in-memory (page refresh loses the session view; rejoin comes with `get_state` in phase 2); `leave_session` deletes the participant row and only in Lobby status.

## Phase 0: Foundation + Spike (2026-07-19)

### Done

- App `quizzly` installed on `quizzly.localhost` (module `Quizzly`).
- Role `Quiz Host` created via fixture (`quizzly/fixtures/role.json`, synced on migrate).
- SPA scaffold in `frontend/`: Vue 3 + frappe-ui + Vite, socket.io-client, vue-router with `/join`, `/play`, `/host` stubs. Production build outputs to `quizzly/public/frontend` and writes `quizzly/www/quizzly.html`. Served at `/quizzly/*` via `website_route_rules`. Verified: `yarn build` passes, `/quizzly/join` returns the SPA, `yarn dev` runs.

### Spike decision: socket push for players. WON.

Question: can a guest (no login) socket.io connection receive events published to a custom room?

Answer: **yes**, verified empirically on this bench (frappe develop, v17):

- Guest sockets authenticate with the `sid=Guest` cookie. `frappe.realtime.get_user_info` returns `installed_apps` from the site (not the user), so app-level socket handlers load for guests too.
- The realtime node server loads `apps/<app>/realtime/handlers.js` per connecting socket. `quizzly/realtime/handlers.js` registers `qz_join` / `qz_leave`, which join/leave room `qz_session_{pin}` (PIN validated as 6 digits).
- Test: node socket.io-client connected as Guest, emitted `qz_join 123456`, then `frappe.publish_realtime(event="qz_session_123456", room="qz_session_123456")` from the server. Event received by the guest client.

Consequence: players subscribe over socket.io (`qz_join` after joining a session). No 1s polling fallback is built. `get_state` stays planned for reconnect only.

### Notes

- Bench runs frappe **v17.x-develop**, not stable v16 as plan.md assumes. Spike result applies to this version.
- `bench start` must be restarted after installing a new app: web workers only pick up the editable install at interpreter startup (symptom: `ModuleNotFoundError: No module named 'quizzly'` on every request).
- Found and cleared a stale global `maintenance_mode: 1` in `common_site_config.json` that 503'd every site on the bench.
