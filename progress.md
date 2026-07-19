# Progress

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
