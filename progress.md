# Progress

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
