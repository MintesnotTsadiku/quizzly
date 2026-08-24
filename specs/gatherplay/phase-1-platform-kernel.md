# GatherPlay Phase 1: Platform Kernel

Status: Approved for implementation
Related: [product-spec](../../docs/gatherplay/product-spec.md) · [platform-architecture](../../docs/gatherplay/platform-architecture.md) · [implementation-plan](../../docs/gatherplay/implementation-plan.md) · [Phase 2: CueCast](phase-2-cuecast.md)

## Problem

Quizzly is one game welded to its content: `QZ Session` links straight to a quiz, the
engine dispatches on quiz phases, and there is no place a second game could attach.
GatherPlay needs a game-neutral session platform inside this app, with Quizzly as its
first registered module.

## Scope

In:

- Game module contract (`GameManifest`, `GameModule`, value objects) and registry,
  discovered via a `quizzly_game_modules` hook.
- Shared DocTypes: `GP Session`, `GP Participant`, `GP Team`, `GP Team Membership`,
  `GP Round`, `GP Action`, `GP Score Event`.
- GP engine: Redis hot state envelope, shared self-looping ticker (same pattern as the
  proven `qz_ticker`), join/start/host-command APIs, the submit gauntlet, an immutable
  score-event ledger with materialized totals, and role-aware serializer dispatch.
- A QuizGame **compatibility adapter**: registers as game key `quiz`, delegates to the
  existing `quizzly.engine`. No QZ data is migrated; every existing route, payload and
  screen keeps working unchanged.
- `/play` discovery home + per-game how-to pages in the SPA (existing `/quizzly` routes
  untouched). Public projector route separate from the host console.
- Guest socket rooms for GP sessions (`gp_join` / `gp_leave`).

Out (later phases):

- Tournaments, moderation queue/cases, content packs, `GP Game Template`,
  percentage-normalized team scoring, Redis due-session sorted set, video guides,
  migrating QZ rows onto GP tables.

## Contracts

### Module registration

```python
quizzly_game_modules = ["quizzly.games.quiz.game:QuizGame", "quizzly.games.cuecast.game:CueCastGame"]
```

The backend manifest is authoritative for availability and capabilities. Modules never
publish realtime events, mint tokens, mutate materialized totals, or touch another
session model. They return value objects; the orchestrator persists and publishes.

### Value objects

- `Transition(phase, next_ts=None, ttl=None, publish=None, module_state=None)` — one
  state-machine step.
- `ActionDecision(accepted, reason=None)` — verdict on one guest action.
- `Resolution(summary, deltas, publish=None)` — round outcome.
- `ScoreDelta(subject_type, subject, points, category, idempotency_key, raw_metric=None)`.
- `GameResult(leaderboard, publish)` — final standings payload.

### State envelope (Redis `gp:{session}:state`)

`schema_version`, `game_key`, `session_status`, `phase`, `version` (bumped by the
orchestrator on every write), `round_index`, `deadline_ts`, `next_ts`, `module_state`.
Controls ride `gp:{session}:control`; the active set is `gp:active_sessions`.

### Events

Public room `gp_session_{pin}`, envelope `{contract, event_id, seq, type, game,
state_version, server_ts, deadline_ts?, payload}`. Events notify; snapshot APIs are
authoritative; clients drop stale `seq`/`state_version` and resync on gaps. Private
prompts, unrevealed answers, and host controls never enter public payloads.

### APIs (`quizzly.api.gp`)

Guest: `join_session(pin, nickname, avatar)`, `get_state(pin, token)`,
`submit_action(pin, token, action_type, payload, idempotency_key)`,
`leave_session(pin, token)`. Host: `create_session(game_key, ...)`, `get_host_state`,
`host_command(session, command, payload)`, plus deck CRUD through `frappe.client.*`.
Same gauntlet order as the quiz API: rate limit → session active → token hash → phase
gate in Redis → deadline grace → dedupe set → DB unique constraint → server-side scoring.

### Scoring

Modules return deltas at resolve time. The platform inserts immutable `GP Score Event`
rows (unique on `(session, idempotency_key)`) and applies totals to participant/team
rows. Corrections are compensating events.

## Data model notes

- Pins are generated against both QZ and GP sessions so a live quiz and a live GatherPlay
  game can never share a PIN.
- `GP Action` unique index on `(session, actor_participant, idempotency_key)` via
  `on_doctype_update`; retries and double-taps die at the DB.
- `GP Participant` carries `role` (Player, Captain, Performer, Spectator) and `status`
  (Active, Disconnected, Benched, Kicked); kicked tokens fail everywhere, same as QZ.
- Teams are real rows so assignments are queryable; membership tracks the effective round.

## Frontend

- Router serves both bases: `/quizzly/*` (existing) and `/play/*` (new), chosen from the
  location at boot; both map to the same www page via `website_route_rules`.
- `frontend/src/platform/` holds discovery + shells; each game contributes
  `frontend/src/games/<key>/` with host/player/screen components behind a compile-time
  registry keyed by the backend manifest key.
- Design tokens stay in `index.css`/`tailwind.config.js`; games consume tokens and
  data-driven palettes (team colors come from one backend constant), never ad-hoc hexes.

## Test plan

- Registry: duplicate keys throw; manifest shape validated.
- Secret-leak: public serializer/event snapshots assert no prompt/answer/control fields.
- Submit gauntlet: late, wrong-phase, kicked, duplicate (Redis bypassed → DB constraint).
- Ledger: delta idempotency under retry; compensating event math.
- Adapter: a scripted quiz game through the platform reaches a podium with correct scores.
- Recovery: reload mid-phase returns the right snapshot; abandoned sessions settle.
