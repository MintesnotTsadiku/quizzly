# GatherPlay Platform Architecture

Status: Proposed
Scope: Reusable multiplayer platform inside the existing `quizzly` Frappe app
Related documents: [Product specification](product-spec.md) · [Implementation plan](implementation-plan.md)

## 1. Architectural objective

Evolve Quizzly into a modular live-game platform without rewriting its proven realtime core. The platform owns identity, sessions, teams, rounds, timing, persistence, reconnection, scoring ledgers, presentation, moderation, and tournaments. A game module owns configuration validation, content semantics, allowed actions, module state, resolution, module scoring, and role-aware serialization.

The technical package remains `quizzly` during the GatherPlay product expansion. Renaming an installed Frappe app or existing DocTypes would add migration risk without product value.

## 2. Existing foundation to preserve

The current implementation already provides important production-grade patterns:

- `QZ Quiz` and child `QZ Question` authoring content.
- `QZ Session`, currently linked directly to one quiz.
- `QZ Participant` with a 32-byte raw guest token and stored SHA-256 hash.
- `QZ Answer` with a participant/question uniqueness constraint.
- Public rooms named `qz_session_{pin}`.
- Server-to-client Socket.IO push and HTTP APIs for client actions.
- Redis hot session state, answered sets, controls, and active-session set.
- One shared RQ ticker that advances all active games.
- Absolute, server-set `deadline_ts`; clients render their own countdown.
- Server-received response times and server-side scoring.
- Throttled live answer counts rather than a broadcast per submit.
- Durable answers and participant totals in MariaDB.
- Host and player snapshot APIs for reload and reconnect.
- A 20-second client resynchronization watchdog and unlimited socket reconnect attempts.
- Load-test tooling for large simultaneous answer salvos.

These patterns become platform services. Quizzly first runs through a compatibility adapter so existing QZ data and routes keep working.

## 3. Responsibility boundary

### Platform infrastructure

- Game discovery and registry.
- Authenticated hosts and token-authenticated guests.
- PIN/QR joining, lobby, nicknames, avatars, kicks, and lobby lock.
- Participant roles and team assignment.
- Session and round envelopes.
- State versioning, transition orchestration, deadlines, pause/resume, and recovery.
- Accepted-action persistence, idempotency, and rate limiting.
- Immutable score events and materialized standings.
- Public, host, and player delivery channels.
- Shared projector shell, host shell, player shell, and connection UX.
- Content-pack metadata, visibility, language, safety, and licensing.
- Moderation, reporting, retention, and audit trail.
- Tournament entries, stages, matches, brackets, and cross-game scoring.
- Contract, security, browser, recovery, and load-test harnesses.

### Individual game module

- Module manifest and capability declarations.
- Configuration and content validation.
- Initial module state and module-defined phases.
- Player role/eligibility augmentation.
- Allowed action types and schemas.
- Round start, resolution, and advance rules.
- Score-delta calculation and raw performance metrics.
- Host/player/public state serializers.
- Module-specific host commands.
- Purpose-built content DocTypes and editors.
- Module-specific host, player, projector, preview, and authoring components.
- Module-specific unit and scenario tests.

Modules must not directly publish events, create their own guest tokens, mutate materialized totals, implement another session/team/tournament model, or expose raw DocTypes to guests.

## 4. Shared DocTypes

### `GP Game Template`

A saved playable setup.

- Title, description, owner, visibility.
- Registered `game_key`.
- Dynamic content reference (`content_doctype`, `content_name`).
- Validated configuration JSON and schema version.
- Suggested group size/duration.
- Optional source demo template and cover image.

### `GP Session`

One lobby or live game.

- Host, game key, game-template reference, and immutable configuration snapshot.
- Unique join PIN and status: Lobby, Active, Paused, Ended, Cancelled.
- Lobby lock, late-join policy, public visibility, and state version.
- Optional tournament match.
- Current round, started/ended timestamps, durable checkpoint JSON/version.
- Public-screen token policy and recovery metadata.

### `GP Participant`

One session-scoped guest or authenticated participant.

- Session, nickname, avatar, join sequence, joined/left timestamps.
- Token hash; raw token is never stored.
- Role: Player, Captain, Performer, Spectator, Assistant Moderator.
- Status: Active, Disconnected, Benched, Eliminated, Kicked.
- Tournament entry link and materialized score/rank.
- Optional device fingerprint hash for abuse controls, not cross-event tracking.

### `GP Team`

- Session, name, color, seed, captain, status, and materialized score/rank.

### `GP Team Membership`

- Session, team, participant, effective round, active/bench state, and timestamps.
- A separate DocType is preferred over only a child table because assignments are queried, audited, and may change between tournament stages.

### `GP Round`

- Session, round index, module round key, status.
- Active participant/team references.
- Opened, deadline, resolved timestamps.
- Durable state checkpoint and checkpoint schema.
- Resolution summary and audit metadata.

### `GP Action`

- Session, round, participant/team actor, action type.
- Validated payload JSON, received timestamp, accepted/rejected state.
- Client idempotency key and state version observed.
- Optional moderation status and source action.
- Unique index across session, actor, and idempotency key.

Do not persist every drawing point as a `GP Action`. Keep bounded stroke segments in Redis and persist a compact final artifact or stroke log.

### `GP Score Event`

Immutable ledger entry.

- Session, round, participant or team subject.
- Signed points, category/reason, source action.
- Raw metric JSON and module idempotency key.
- Optional reversal-of link.

Corrections create compensating events instead of silently editing history.

### `GP Content Pack`

- Title, summary, cover, game compatibility.
- Theme: Church/Bible, Child/Family, General, Educational, Conference, Custom.
- Language/locale, age band, difficulty, estimated duration.
- Ownership, visibility, license/source attribution.
- Draft, In Review, Approved, Archived status.
- Media and accessibility requirements.

### `GP Content Item`

An optional generic content row for simple prompt-driven games: text, answer, aliases, image/audio file, difficulty, tags, and private metadata JSON. Complex content such as quizzes and escape missions remains in purpose-built DocTypes.

### Tournament and moderation DocTypes

- `GP Tournament`: format, entry type, scoring policy, team policy, status.
- `GP Tournament Entry`: persistent person or team identity.
- `GP Tournament Stage`: round robin, group, knockout, final, or mixed-game stage.
- `GP Match`: entries, module, configuration, scheduled time, linked session, result.
- `GP Moderation Case`: flagged participant/content/action, reason, decision, moderator, timestamp.

## 5. Module-specific DocTypes

- Quiz: existing `QZ Quiz`, `QZ Question`.
- CueCast: `GP Cue Deck`, child `GP Cue Prompt`.
- Crowd Compass: `GP Crowd Pack`, child `GP Crowd Prompt`.
- Doodle Dash: `GP Draw Deck`, child `GP Draw Prompt`, `GP Draw Answer Alias` if aliases are not a child table.
- Bluffline: `GP Bluff Pack`, child `GP Bluff Prompt` with truth and accepted variations.
- Sequence Sprint: `GP Sequence Pack`, prompt and ordered-item children.
- Picture Peek: `GP Picture Pack`, prompt and reveal-stage configuration.
- Sound Snap: `GP Sound Pack`, prompt and licensed private audio file.
- Story Loom: `GP Story Template`, constraint/branch children.
- Signal Spectrum: `GP Spectrum Pack`, scale and target configuration.
- Escape Together: `GP Puzzle Mission`, `GP Puzzle Stage`, transition children.

A module creates a new durable DocType only when generic content, round actions, or checkpoints cannot represent the information cleanly.

## 6. Session and round state

Common state envelope:

```json
{
  "schema_version": 1,
  "game_key": "cuecast",
  "session_status": "Active",
  "phase": "turn_open",
  "version": 37,
  "round": {"id": "GP-RND-0042", "index": 3},
  "active": {
    "team_ids": ["TEAM-BLUE"],
    "participant_ids": ["PLAYER-7"]
  },
  "deadline_ts": 1787583600.25,
  "next_transition_ts": 1787583600.25,
  "module_state": {
    "prompt_index": 5,
    "correct_count": 3
  }
}
```

Common lifecycle:

```text
Lobby → Ready → Round Open → Resolving → Reveal/Results → Intermission
                         ↘ Paused ↗
Intermission → next Ready, or Game Finished
```

Modules can define richer phase names but must declare capabilities per phase: can join, submit, pause, advance, reveal, or replace actor.

### Hot state and durability

- Redis keys use `gp:session:{session}:...` and TTLs with safe margins.
- Redis stores live state, controls, action dedupe sets, progress counters, drawing strokes, and due-session indexes.
- MariaDB stores accepted actions, score events, round transitions, and periodic checkpoints.
- Checkpoint at round boundaries and material phase transitions.
- On Redis loss or worker restart, reconstruct from latest checkpoint and deterministically apply overdue transitions.
- State transitions use a session lock or compare-and-swap version.
- Normal high-concurrency submissions do not take a session-wide lock: atomically dedupe by participant/round, validate the immutable open state, persist uniquely, and resolve under the transition lock after deadline.

### Scheduler

The current shared ticker is retained initially. Later, replace full active-set scanning with a Redis sorted set whose score is `next_transition_ts`. A single generic ticker claims due sessions, invokes `advance_state`, commits, publishes, and continues. One failing module/session must not stall the rest.

## 7. Player and team policies

Assignment modes:

- Host-assigned.
- Random balanced.
- Self-selected team code.
- Persistent tournament roster.
- Cooperative whole-room team.

Module interaction modes:

- Individual: every participant acts.
- Aggregate: individual results become a normalized team result.
- Captain: one team submission.
- Representative: one performer/artist/clue-giver acts for team.
- Cooperative: room shares outcome.

Late join policy is explicit: reject, spectator, bench until next round, balanced assignment, or replacement. Roster changes during an active round are prohibited unless the host performs an audited replacement.

## 8. Host controls

Universal controls:

- Lock/unlock lobby; enable/disable late join.
- Admit, kick, mute, bench, or replace a participant.
- Create, rename, recolor, assign, and balance teams.
- Start, pause, resume, extend, skip, replay, or end.
- Hide/reveal projector content and put the projector into a safe intermission state.
- Accept/reject guest content before projection.
- Apply an auditable score adjustment.
- Undo an unresolved transition where safe.
- Trigger full state resynchronization.

The module manifest declares extra commands such as `mark_correct`, `pass_prompt`, `replay_audio`, `grant_hint`, `approve_caption`, or `invalidate_drawing`.

## 9. Realtime and HTTP contracts

Continue the current safe division:

- Socket.IO: server-to-client public notifications and bounded public media deltas.
- Whitelisted HTTP methods: joins, snapshots, guest actions, host controls, and private result reads.

Public event envelope:

```json
{
  "contract": 1,
  "event_id": "01K...",
  "seq": 84,
  "type": "platform.state_changed",
  "session": "GP-SESSION-123",
  "game": "cuecast",
  "state_version": 37,
  "server_ts": 1787583540.15,
  "deadline_ts": 1787583600.25,
  "payload": {}
}
```

Core events:

- `platform.lobby_updated`
- `platform.state_changed`
- `platform.timer_changed`
- `platform.action_progress`
- `platform.team_updated`
- `platform.scoreboard_updated`
- `platform.session_paused`
- `platform.session_ended`
- `platform.participant_removed`
- Namespaced events such as `cuecast.prompt_resolved` or `doodle.stroke_batch`

Contract rules:

1. Events notify; snapshot APIs remain authoritative.
2. Clients ignore older sequence/state versions.
3. A sequence gap triggers snapshot recovery.
4. Public room payloads are safe for anyone knowing the PIN.
5. Private prompts, roles, unrevealed answers, personal moderation, and host-only controls never enter public events.
6. Every client action has a UUID/ULID idempotency key and observed state version.
7. Action schemas and payload sizes are bounded.
8. Module event names and contracts are versioned.

Because the current custom room handler accepts a valid six-digit PIN without participant-token validation, the server publishes only public state to it. A player receives a public state-change notification and fetches private state with their token.

### API shape

- `create_session(game_key, template, configuration)` — authenticated host.
- `join_session(pin, nickname, avatar, team_code?)` — rate-limited guest POST.
- `get_public_state(pin, since_version?)` — safe snapshot.
- `get_player_state(pin, token, since_version?)` — token-gated private snapshot.
- `submit_action(pin, token, action_type, payload, idempotency_key, state_version)` — guest POST.
- `leave_session(pin, token)` — guest POST; lobby removal only by default.
- `get_host_state(session)` — owner/authorized cohost.
- `host_command(session, command, payload, expected_version)` — authenticated POST.

Guests never use Frappe resource CRUD APIs for these DocTypes.

## 10. Guest identity and abuse controls

- At least 256 bits of random token material; store only a hash.
- Scope token to one session participant and reject kicked/replaced/expired tokens everywhere.
- Rate-limit by token, PIN, IP, and endpoint class.
- Sanitize names and bounded free text; keep current profanity and duplicate-nickname checks.
- Persist token locally with expiry; do not treat nickname as authentication.
- Rotate token after host-assisted recovery.
- Optional host-issued recovery code or private QR; otherwise rejoin as a new participant.
- Prevent token reuse for multiple incompatible active roles.
- Do not use a device identifier for cross-event behavioral tracking.

## 11. Reconnection and state recovery

On load/reconnect:

1. Restore PIN and participant token.
2. Fetch `get_player_state` with last known version.
3. Replace local state with authoritative snapshot.
4. Rejoin the public room.
5. Compute clock offset from returned `server_ts`.
6. Resume countdown from absolute deadline.
7. Retry only idempotent queued actions whose server deadline is still open.

Socket reconnect attempts continue indefinitely with backoff. A watchdog fetches state if no transition has been observed. Phase-aware fallback polling is faster around expected transitions and slower during stable phases; no per-second timer polling is needed.

Performer disconnect policy:

- Show a short grace period.
- Preserve accepted actions and private prompt assignment.
- Host may pause, reassign, or skip.
- Reassignment does not expose the prompt to the projector.

Host loss does not stop a server-driven game. A reloaded host reacquires control from the host snapshot. Worker loss is detected by heartbeat/checkpoint age, then state is recovered or the session is safely settled.

## 12. Timer authority and fairness

- Server time and server receipt time are authoritative.
- Every timed phase has absolute `deadline_ts`; no per-second push.
- Clients estimate server offset from `server_ts` and render locally.
- Pause records remaining time and clears the active deadline.
- Resume writes and broadcasts a new deadline/version.
- A small grace may accept requests already in flight, but offline clients cannot backdate actions.
- Speed bonuses are used only when latency is unlikely to dominate the mechanic.
- Host extensions apply equally and become auditable timer events.
- Actor-ready handshakes prevent a private turn from expiring before the performer receives it.

## 13. Scoring interface

Modules return score deltas, not direct total mutations:

```json
{
  "subject_type": "Participant",
  "subject": "PLAYER-7",
  "points": 740,
  "category": "correct_guess",
  "round": "GP-RND-0042",
  "source_action": "GP-ACT-991",
  "raw_metric": {"response_ms": 6200},
  "idempotency_key": "round-42:player-7:correct"
}
```

The platform persists immutable `GP Score Event` rows, materializes totals for display, applies deterministic ties, supports compensating reversals, and separately exposes player, team, match, and tournament standings.

For team quiz play, supported policies are:

1. Captain submits one collaborative answer.
2. Average all eligible player results, treating non-response as zero.
3. Count a fixed best-N contribution declared before play.

Never use unadjusted raw sums when rosters differ.

## 14. Routes and frontend modules

Recommended routes:

```text
/play                              Game discovery catalog
/play/games/:game                  How-to and demo-pack detail
/play/join                         PIN/QR join
/play/p/:pin                       Mobile player controller
/play/s/:session/screen            Public projector
/play/host                         Host dashboard
/play/host/session/:session        Private host console
/play/host/content/:game           Module authoring
/play/tournament/:tournament       Tournament overview/bracket
```

Keep `/quizzly` and existing deep links as compatible aliases or redirects. Host and public projector views are separate routes so private answers, prompts, moderation, and destructive controls are never projected.

Frontend structure:

```text
frontend/src/
  platform/
    discovery/
    host/
    player/
    screen/
    session/
    teams/
    tournaments/
  games/
    quiz/
    cuecast/
    crowd-compass/
    doodle-dash/
```

Shared shells handle connection state, theme, sound preference, error recovery, lobby, countdowns, scores, and route authorization. Game components render only module-specific interaction.

## 15. Content packs and moderation

Every pack declares compatible game, locale, audience, age, difficulty, duration, required media, license/source, accessibility notes, and review state. Church packs additionally identify intended tradition/context where wording may be doctrinally specific.

Safety controls:

- Nickname profanity and impersonation checks.
- Host approval before guest text, drawings, or photos reach projector.
- Similarity and duplicate detection.
- No guest HTML or arbitrary SVG.
- Sanitized drawing coordinates with fixed tools/palette.
- Upload type/size/dimension limits and private storage.
- Draft → Review → Approved → Archived content workflow.
- Age and sensitivity labels.
- Participant reporting/blocking and moderation audit.
- Configurable retention for captions, drawings, and photos.
- Child-focused “no participant media” mode.
- Accessible alternatives for sound, color, animation, dragging, and fine motor control.

## 16. Standard game-module contract

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GameManifest:
    key: str
    title: str
    version: str
    min_players: int
    max_players: int | None
    supports_teams: bool
    supports_tournaments: bool
    capabilities: tuple[str, ...]
    host_commands: tuple[str, ...]
    frontend_key: str


class GameModule(ABC):
    manifest: GameManifest

    @abstractmethod
    def validate_configuration(self, ctx, configuration: dict) -> None: ...

    @abstractmethod
    def create_session_state(self, ctx, configuration: dict) -> dict: ...

    def join_player(self, ctx, state: dict, participant) -> dict:
        return {}

    @abstractmethod
    def start_game(self, ctx, state: dict) -> "Transition": ...

    @abstractmethod
    def start_round(self, ctx, state: dict) -> "Transition": ...

    @abstractmethod
    def submit_action(
        self, ctx, state: dict, participant, action: dict
    ) -> "ActionDecision": ...

    @abstractmethod
    def resolve_round(self, ctx, state: dict) -> "Resolution": ...

    @abstractmethod
    def calculate_score(
        self, ctx, state: dict, accepted_actions: list[dict]
    ) -> list["ScoreDelta"]: ...

    @abstractmethod
    def advance_state(
        self, ctx, state: dict, trigger: str
    ) -> "Transition": ...

    @abstractmethod
    def finish_game(self, ctx, state: dict) -> "GameResult": ...

    @abstractmethod
    def serialize_host_state(self, ctx, state: dict) -> dict: ...

    @abstractmethod
    def serialize_player_state(
        self, ctx, state: dict, participant
    ) -> dict: ...

    @abstractmethod
    def serialize_public_state(self, ctx, state: dict) -> dict: ...

    def handle_host_command(
        self, ctx, state: dict, command: str, payload: dict
    ) -> "Transition":
        raise UnsupportedCommand(command)
```

`Transition`, `ActionDecision`, `Resolution`, `ScoreDelta`, and `GameResult` are value objects. The platform orchestrator owns locking, version increments, persistence, score-event creation, and publishing.

## 17. Registration and discovery

Frappe hook:

```python
quizzly_game_modules = [
    "quizzly.games.quiz.game:QuizGame",
    "quizzly.games.cuecast.game:CueCastGame",
    "quizzly.games.crowd_compass.game:CrowdCompassGame",
    "quizzly.games.doodle_dash.game:DoodleDashGame",
]
```

Backend registry:

```python
import frappe


def discover_game_modules():
    registry = {}
    for dotted_path in frappe.get_hooks("quizzly_game_modules"):
        module = frappe.get_attr(dotted_path)()
        key = module.manifest.key
        if key in registry:
            frappe.throw(f"Duplicate game module key: {key}")
        registry[key] = module
    return registry
```

Frontend discovery is compile-time and safe:

```typescript
const imports = import.meta.glob("./games/*/index.ts", { eager: true });

export const gameViews = Object.values(imports).reduce((registry, entry: any) => {
  registry[entry.manifest.key] = entry;
  return registry;
}, {} as Record<string, any>);
```

Backend manifest is authoritative; frontend entry supplies module-specific host, player, public, authoring, and preview components.

## 18. Tournament and team architecture

```text
Tournament
  ├── Entries: individuals or persistent teams
  ├── Stages
  │    ├── Group / Round Robin
  │    ├── Knockout
  │    └── Final
  └── Matches
       └── one GP Session using one registered module
```

Supported formats:

- Multiple rounds within one module session.
- Elimination, with eliminated contestants retained as spectators/voters.
- Round robin.
- Seeded knockout with deterministic byes.
- Group stage followed by finals.
- Mixed-game schedules where each match selects a different module.
- Cumulative tournament standings.

Raw game scores are never added across unlike games. Use match/placement points, for example win 3, draw 1, loss 0 and stage placement 10/7/5. Percentile normalization is available but placement points are the default because hosts and audiences understand them.

Default tie order:

1. Tournament points.
2. Head-to-head result.
3. Wins.
4. Score differential or normalized module performance.
5. Sudden-death match.
6. Deterministic seeded draw if host policy explicitly allows it.

Participants join a tournament once and link into individual sessions through `GP Tournament Entry`. Rosters lock per stage; substitutes, late arrivals, performer rotation, self-voting restrictions, and eligible contributor counts are configured before play.

## 19. Extensibility acceptance rules

Every module must:

1. Register a stable unique key and versioned manifest.
2. Use core sessions, participants, teams, rounds, actions, and score events.
3. Keep server authority over actions, deadlines, outcomes, and scores.
4. Serialize host, player, and public state separately.
5. Pass automated secret-leak tests for public state/events.
6. Validate phase, actor, state version, deadline, and payload for every action.
7. Behave idempotently under retry and duplicate delivery.
8. Avoid direct realtime publishing and materialized-score mutation.
9. Declare supported group sizes, capabilities, content, host commands, and tournament modes.
10. Recover from player reconnect and worker restart.
11. Supply contract, unit, API, browser, recovery, and proportional load tests.
12. Keep frontend assets and module logic inside its module directory.
13. Use localization keys and accessibility metadata.
14. Remain playable during temporary Socket.IO loss through snapshots and fallback polling.
