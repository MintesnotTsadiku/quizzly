# Live Quiz Rework — Tracer-Bullet Phases

Full design + rationale: [`../live-quiz-latency-rework.md`](../live-quiz-latency-rework.md).

This folder slices that rework into **tracer bullets** — each phase is a thin slice
through *all* layers (API → Redis → engine → realtime → browser) that you can watch work
end to end before building the next. Ordered by **risk, not by size**: prove the new
architecture is sound first, then scale it, then optimize.

| Phase | Slice | Proves | Ship-alone? |
| ----- | ----- | ------ | ----------- |
| [1](phase-1-ticker-tracer.md) | Shared ticker drives **one** full game through every phase | New control flow (state machine, not per-game loop) works end to end | Yes |
| [2](phase-2-multi-game-scale.md) | One ticker drives **N concurrent** games on 3 workers | Worker-per-game starvation is gone — the payoff of the redesign | Yes |
| [3](phase-3-batch-scoring.md) | Batch scoring/rank writes | Reveal latency flat vs player count | Yes |
| [4](phase-4-submit-and-count.md) | Trim submit path + throttle `answer_count` | Submit cost + O(players²) fan-out gone | Yes |

Each phase file has: **Goal** (the thin slice), **Proves**, **Changes**, **Test**
(the end-to-end feedback loop — the whole point of a tracer bullet), **Done when**.

Rule: no phase merges until its browser test passes and the app test suite is green.
Commit per phase (branch `feat/live-quiz-ticker`).
