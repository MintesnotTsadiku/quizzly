# Phase 4c: Player fun (avatars, nickname generator, sound)

Slice 3 of Phase 4 juice. See `phase-4-juice.md` for the umbrella.

## Goal

Joining and playing feel like a game rather than a form. No engine changes: scoring, timing, and payload contracts are all untouched.

## Tracer bullet

1. `avatar` field on `QZ Participant`, picked on the join screen, rendered on the host lobby and leaderboard. **Feedback: a player's face shows up on the big screen.**
2. Nickname generator: three safe suggestions on the join screen, tap to accept, still free to type your own.
3. Sound: lobby music, countdown tick, answer sfx, podium sting, with a mute toggle that persists.

## Avatars

Generated, not uploaded. A fixed set of emoji-style avatars rendered client-side from a seed, so there is no file storage, no moderation problem, and no upload endpoint.

- `QZ Participant.avatar` — Data, stores the chosen avatar id (e.g. `fox`), validated in the controller against the known set. An unknown id is rejected rather than silently defaulted, because it would otherwise render as a blank on the host screen.
- `join_session` accepts an optional `avatar`, defaulting to one derived from the nickname hash so an old client still gets something reasonable.
- `lobby_update`, leaderboard, and podium payloads carry `avatar` alongside `nickname`.

## Nickname generator

Client-side, from a curated adjective + noun word list shipped in the SPA (`frontend/src/nicknames.js`). Three options, a reroll button, all guaranteed to pass the Phase 3 profanity filter because the word list is curated.

Server behaviour is unchanged: `join_session` still validates and still rejects duplicates and dirty names, so the generator is a convenience and never a trust boundary.

## Sound

- Assets in `frontend/src/assets/sound/`, short and small, preloaded on the join screen.
- Cues: lobby loop (host screen only), 5-second countdown tick, answer-submitted blip, correct and wrong stings, podium fanfare.
- Mute toggle on both host and player, persisted in localStorage, defaulting to **on for host, off for player**. Phones in a classroom all unmuting at once is a bad time.
- Audio starts only after a user gesture, satisfying browser autoplay policy: the join tap and the host start tap both count.

## Screens

- `/join` — nickname field with three suggestion chips and a reroll, avatar picker grid below.
- `/play` — avatar shown in the header, next to the score.
- `/host` — avatars in the lobby player grid, in the live leaderboard, and on the podium.

## Tests

- `join_session` with a valid avatar stores it; with an unknown avatar id it errors; with none it derives a stable one from the nickname.
- Lobby and leaderboard payloads carry `avatar`.
- Nickname generator output passes the profanity filter for the entire word list (a loop over the list, cheap and it catches a bad word slipping into the file later).

## Exit criteria

- Two players join with distinct avatars and generated names, both visible on the host screen through lobby, game, and podium.
- Sound plays on both sides, mute persists across reload.
- A client that sends no avatar and never plays sound still completes a full game.
