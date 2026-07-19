# Phase 4: Juice (v2)

## Goal

Quizizz-inspired fun layer plus host conveniences. Everything here is additive; the v1 game must stay fully playable without it.

## Features

### Player fun

- Avatars (customizable).
- Nickname generator: 3 safe options to pick from, avoids inappropriate names.
- Memes between questions.
- Sounds: music and sfx.
- Power-ups: x2 points, immunity (second chance), power play. Earned by streaks/correct answers.

### Game modes

- Team mode.
- Shared-screen mode: question + options only on the host screen, players see only 4 colored shape buttons (classic Kahoot mode).

### Content

- Question images.
- Custom quiz authoring UI in SPA (replaces Desk-only authoring).

### Host conveniences

- Results export (CSV).
- Session history.

## Notes

- Power-up point math stays server-side, same rule as all scoring: client never computes points.
- Shared-screen mode changes only the question payload sent to players (options hidden), not the engine.

## Exit criteria

- Each feature shippable independently; no feature blocks another.
- v1 flows regression-free with juice disabled.
