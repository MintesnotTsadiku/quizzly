# GatherPlay Phase 3: Crowd Compass

Status: Approved for implementation (full feature set)
Related: [Phase 1: Platform Kernel](phase-1-platform-kernel.md) · [Phase 2: CueCast](phase-2-cuecast.md) · [product-spec §3.5](../../docs/gatherplay/product-spec.md) · [implementation-plan §7](../../docs/gatherplay/implementation-plan.md)

## Problem

Crowd Compass proves what neither earlier module exercised: two-stage simultaneous
input (every player acts twice per round), hidden aggregation where the distribution
is a reveal-time secret, and mass one-tap voting at room scale — plus the game's full
scoring depth: estimation, team matching, rank-choice prompts, live host prompts and
result invalidation.

## Feature set

### Core round

Per prompt: **vote** for yourself → **predict** the room's plurality → animated
reveal → scoreboard. Distribution counts are hidden until reveal; public state
carries only participation counts. One `GP Round` per prompt; votes and predictions
are typed `GP Action`s (one of each per participant per round).

### Choices and rank-choice

- Normal prompts: 2–4 fixed choices, one pick.
- Ranked packs (pack-level `ranked` toggle): every prompt takes a **first and second
  choice** (must differ). Room aggregation is weighted — first = 2, second = 1 — and
  the plurality is the highest weighted total (ties all count). Predictions target
  the weighted winner; match bonuses use the first choice.

### Scoring

| Event | Points |
|---|---|
| Prediction in the plurality set | +500 |
| Own first-choice vote matches the room plurality (`room_match`) | +100 |
| Team mode: own vote matches your **team's** plurality (`team_match`) | +100 |
| Estimation bonus (correct predictors only): share error ≤3pp / ≤7pp / ≤12pp | +300 / +150 / +50 |

- **Percentage estimation**: during prediction, players also estimate the share their
  predicted choice will earn (0–100). At reveal the actual share is
  `weight / total × 100`; correct predictors score the tiered bonus.
- Tied pluralities: every tied choice counts as winning.
- **Quorum**: below `quorum` votes the round reveals with a notice and no deltas.
- Nonresponse scores nothing.
- **Team average**: ledger deltas always target participants; team display score =
  average of member scores, computed at scoreboard/podium — averages never enter the
  ledger.

### Host powers

- Lobby set: balance/rename/recolor teams, lock, kick.
- **Live prompts**: compose a prompt (text + 2–4 choices) between prompts and push it
  onto the queue; sessions may start with **no pack at all** (live prompts only).
- **Void prompt**: after a round resolves, void it — compensating negative ledger
  events reverse every delta, the scoreboard marks the prompt voided, and the game
  moves on. The ledger stays immutable.
- Skip stage; end game.

### Authoring

`/play/host/content/crowd-compass` — pack list, create/edit/delete packs and prompts
with the choice pills previewing the player's screen. Demo packs are visible but
read-only ("duplicate to customize" follows the content-platform phase).

## Data

- `GP Crowd Pack`: title, `ranked` (Check), is_demo, demo_key (stable), prompts child.
- `GP Crowd Prompt`: prompt_text, choice_1..choice_4 (≥2 non-empty). No correct
  answer — plurality is emergent.
- Config: `{pack, ranked, vote_seconds, prediction_seconds, estimation, scoring_mode,
  teams_count, room_match, team_match, quorum, rounds}` validated and normalized by
  the module. Live prompts ride module state; blank-room sessions persist none.

## State machine

`prompt_open` → `prediction_open` → `reveal` (resolution + distribution publish) →
`scoreboard` → next prompt … → podium. Host `skip_turn` closes the current stage;
`push_prompt` and `void_prompt` are module commands.

## Screens

| Screen | Where | Shows |
|---|---|---|
| Setup | host console | pack picker (or blank room), stage timers, mode, toggles |
| Lobby | projector + phones | PIN, QR, joiners, teams (team mode) |
| Vote | player phone | prompt + shape-coloured choices (ranked: two picks), locked, "N voted" |
| Predict | player phone | choices, prediction lock, estimation slider, "N predicted" |
| Stage | projector | giant prompt, choices, participation counters — never per-choice counts |
| Reveal | projector + phones | animated distribution, plurality crown, your points privately |
| Scoreboard / podium | projector + phones | standings (team average or individual), voided marker |
| Pack editor | `/play/host/content/crowd-compass` | pack + prompt CRUD |

Serializer rows match the platform's `{name, team_name, color, score, rank}` contract
— in individual mode participants wear display names — so shared shells render
unchanged.

## Demos

`quizzly/demo_data/crowd_compass/{church_bible,family_general,big_room}.json` — 12
prompts each (poll games target 12–15 rounds), idempotent via the seeder, which
dispatches by `game_key`.

## Edge cases covered

Exact ties (all tied choices win); vote-without-prediction and the reverse;
nonresponse; quorum miss; ranked second-equals-first rejection; resync during
vote/prediction leaks nothing; double-tap collapses via idempotency keys; per-round
duplicate votes/predictions rejected; void after scoreboard; live prompt on a
blank-room session; estimation scored only for correct predictors.

## Deferred (platform-level, per implementation plan §7 future)

Privacy-safe opt-in comparisons (needs a consent model); instant-runoff rank-choice
(this phase ships weighted 2/1 rank-choice). Both are additive config later.

## Test plan

Config validation; full round ledger math (vote + predict + estimate + match); tie
round; quorum miss; ranked weighted aggregation and second-equals-first rejection;
secrecy of vote/prediction snapshots; per-round duplicate rejection; team-average
podium math; void reversal restores prior totals; live prompt on blank room;
nonresponse zeros. Browser E2E: host + 3 guests + projector through two prompts
(including estimation) to the podium with screenshots; Agent Plane scenario for the
how-to page.
