# Phase 3: Game UX

## Goal

Polished player and host screens over the Phase 2 engine, plus reconnect resilience and the nickname filter.

## Player screens (guest, mobile-first)

- `/join`: PIN entry (QR link `/join?pin=XXXXXX` prefills), nickname screen.
- `/play`: one screen, state machine:
  lobby -> get-ready countdown -> question -> locked-in wait -> result interstitial -> podium.
- Question view: full question on player device (remote-friendly), 4 colored shape buttons for options (Kahoot feel), local countdown bar driven by `deadline_ts`.
- Per-participant answer-order shuffle on display, seeded by token client-side; canonical option ids sent on the wire.
- Result interstitial: correct/wrong, +points, rank, top-5.
- Reconnect: token in localStorage, `get_state` on load rejoins mid-game with correct remaining time.

## Host screens (logged in, big-screen-first)

- `/host`: quiz picker -> session created: lobby screen with giant PIN + QR (client-side QR lib) + join URL + player names grid + lock/kick/start.
- Game view: current question, live answer count, distribution reveal (bar chart), top-5 leaderboard, streak callouts, controls: next / skip / end / auto-advance toggle.
- Podium screen: top-3 animation, full leaderboard.
- Host-drop resilience: host reloads, host screen state API restores current view, game loop unaffected.

## Between-question presentation

- Correct answer reveal.
- Answer distribution bar chart.
- Top-5 leaderboard.
- Streak callouts ("X is on a 3 answer streak"), position-change messages.

## Nickname profanity filter

Applied in `join_session` validation. Dirty or duplicate nickname rejected with a clear message.

## Exit criteria

- Full game feels like Kahoot on both sides: countdowns, shapes, interstitials, podium animation.
- Player and host both survive reload mid-question and land back in the right state.
- Profanity filter blocks bad nicknames.
