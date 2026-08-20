# Phase 11: Quiz preview

## Goal

An author wants to see their quiz on the projector before a room does. Today the
only way is to host a real session, and a session will not start without a
player in the lobby. **Preview** in the editor plays the quiz screens straight
from what is on the page, with no session, no PIN and nobody joining.

## Tracer bullet

1. Extract the projector answer grid out of `Host.vue` into `AnswerGrid.vue`.
   **Feedback: the live host screen still renders exactly as before.**
2. `QuizPreview.vue`, a fullscreen dialog that walks the editor state through
   those same screens. **Feedback: Preview shows question 1 on a blank site.**
3. Preview button in the editor header.

## What it plays

Preview runs itself. It opens playing and moves on when the clock runs out, on
the same timings the engine uses, so an author watches the quiz rather than
clicking through slides.

Per question, in order:

```
read -> question -> [explanation] -> answer         (explanations before stats)
read -> question -> answer -> [explanation]         (explanations after stats)
```

| Screen | Clock |
| --- | --- |
| **read**: the question alone, answers held back | `GETREADY_SECONDS`, 3s |
| **question**: text, image, the four answers | the question's own time limit |
| **answer**: correct option ticked, the rest dimmed | `STATS_SECONDS`, 5s |
| **explanation**: text and image | the quiz's `explanation_time_limit` |

The ring drains like the real one and turns red under five seconds. The
explanation screen appears only when the quiz explains answers and the question
has something to say, the same skip rule the engine uses.

Pause holds the clock where it is and resumes from there: the ring is measured
against the beat's own window, not the countdown's, so a resume does not refill
it. Back and Next jump a beat and restart its clock, left/right arrows and space
do the same from the keyboard, and the last beat offers Replay. Esc closes and
stops the clock.

Preview mirrors the engine's constants rather than asking the server for them. A
timing change would have to be made twice, which is cheaper than an API round
trip and a payload for two integers.

## Deliberately not shown

Every screen that only exists because players do: the lobby, the answer
distribution bars, the top 5, the streaks and the podium. Rendering those in
preview means inventing players and inventing scores, and a made-up scoreboard
teaches an author nothing about their quiz. Sound is left out too: a preview at a
desk is not the room.

## Where the data comes from

The editor's own reactive state, not the saved doc. Preview therefore covers
unsaved edits, needs no API, and works on a quiz that has never been saved.

## Reuse

`AnswerGrid.vue` is the single copy of the projector answer grid, used by both
the host screen and preview. A preview that drifts from the real screen is worse
than no preview, so the shared markup is shared for real rather than copied.
