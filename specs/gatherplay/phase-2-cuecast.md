# GatherPlay Phase 2: CueCast

Status: Approved for implementation
Related: [Phase 1: Platform Kernel](phase-1-platform-kernel.md) · [implementation-plan §6](../../docs/gatherplay/implementation-plan.md)

## Problem

CueCast is the first native GatherPlay module. It has to prove the parts the quiz never
exercised: teams, a private performer role, rotation, adjudication, and prompt secrecy —
through the Phase 1 kernel, not beside it.

## Scope (MVP)

- Text prompt decks; **Act** and **Describe** modes.
- 2–6 teams, one performer per turn, automatic equal-turns rotation.
- 30/60/90 second rounds (host picks at setup).
- Correct (+1) / pass (0) from performer controls or host; host invalidate = compensating −1.
- Team scoreboard after every turn, final podium, 30-second sudden-death tie round.
- Prompt decks authored in the SPA (`GP Cue Deck` + `GP Cue Prompt`); three demo decks.
- The live prompt exists only in the performer's private snapshot and Redis module state.
  It is never in a public payload, the projector screen, or any lobby/scoreboard event.

Out: restricted words, picture prompts, speech detection, remote mode, tournaments.

## Round flow

1. Host picks deck + mode + seconds → GP Session in Lobby.
2. Guests join; host balances teams (`host_command: balance_teams`) or renames/recolors.
3. Start → ticker drives: `turn_ready` (public countdown 3s) → `turn_open` (performer
   gets the private prompt on their phone; public screen shows team, mode, timer,
   solved count) → performer taps Correct/Pass per prompt until deadline →
   `turn_review` (public: which prompts were solved; host can invalidate) →
   `scoreboard`.
4. Next team's turn. After every team has played equally many turns → podium.

## State machine (module phases)

`turn_ready` → `turn_open` → `turn_review` → `scoreboard` → next turn … → `finished`.

Host commands: `balance_teams`, `rename_team`, `recolor_team`, `mark_correct`,
`pass_prompt`, `invalidate_prompt`, `skip_turn`, `end`. All audited as host commands;
invalidate writes a compensating ScoreDelta.

## Data

- `GP Cue Deck`: title, mode (Act/Describe), is_demo, visibility, owner.
- `GP Cue Prompt`: deck (parent), text, order. Prompts are drawn without replacement per
  game; exhaustion recycles the least-recently-played prompts.
- Turn state lives in `module_state`: `{team_order, turn_index, performer_participant,
  prompt_ids, current_prompt_index, solved, passed}`.

## Screens

| Screen | Where | Shows |
|---|---|---|
| Setup | `/play/host` console | deck picker, mode, seconds, team count |
| Lobby | projector + phones | PIN, QR, joiners, teams filling up |
| Performer ready | performer phone only | "You're up for {team}" + big Go |
| Turn | performer phone | prompt word huge, ✓ Pass buttons, count |
| Turn (public) | projector | team name, performer avatar, timer ring, solved count — never the word |
| Guessers' phones | everyone else | "Watch {performer}!" + live solved count |
| Review | projector + phones | solved/pass lists, Invalidate control |
| Scoreboard | projector + phones | team totals with animated bars |
| Podium | projector + phones | top teams, winning word count |

## Edge cases covered

Performer disconnect mid-prompt → grace, then host reassign/skip; the prompt never hits
the projector either way. Prompt exhaustion → recycle. One-person team → allowed, they
perform for themselves. Simultaneous correct+pass double-tap → idempotency key dedupes.
Late joiner → benched until next turn. Projector reload → public snapshot only.

## Scoring & tie

Correct = +1 team point (ledger category `correct_prompt`). Invalidate = compensating
−1 (`invalidated_prompt`). Equal turns enforced by rotation order computed from team
count and turns-per-team. Tie at podium → sudden-death 30s turn per tied team, highest
count wins; still tied → shared podium.

## Demos

`quizzly/demo_data/cuecast/{church_bible,family_general,big_room}.json` — 24 prompts
each, original and respectfully phrased (Bible scenes / family actions / big-room
charades), idempotently seeded via `quizzly/demo/seed.py seed_all`, verified by
`verify_all`.

## Test plan

Module unit: rotation equality, mode validation, prompt secrecy in every serializer,
scoring incl. compensating invalidate, sudden-death flow, exhaustion recycling.
Platform integration: full scripted game to podium over the real APIs; duplicate
correct taps collapse; kicked performer token rejected; reload snapshots leak nothing.
Browser E2E: host + 3 guests across two teams, full game, screenshots at phone and
projector sizes; Agent Plane QA manifests for catalog/detail/console pages.
