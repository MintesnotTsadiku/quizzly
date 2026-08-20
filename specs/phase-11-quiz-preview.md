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

## What it shows

Per question, in order:

```
question -> [explanation] -> answer                 (explanations before stats)
question -> answer -> [explanation]                 (explanations after stats)
```

- **question**: index, text, image, the four answers, the countdown ring parked
  at the question's own time limit.
- **answer**: the same screen with the correct option ticked and the rest dimmed.
- **explanation**: text and image, only when the quiz explains answers and the
  question has something to say. This is the same skip rule the engine uses.

Left/right or the footer buttons step through, Esc closes.

## Deliberately not shown

Every screen that only exists because players do: the lobby, the answer
distribution bars, the top 5, the streaks and the podium. Rendering those in
preview means inventing players and inventing scores, and a made-up scoreboard
teaches an author nothing about their quiz. The get-ready read screen is left out
too: it is the question screen with the answers held back, so it shows nothing
the question step does not.

## Where the data comes from

The editor's own reactive state, not the saved doc. Preview therefore covers
unsaved edits, needs no API, and works on a quiz that has never been saved.

## Reuse

`AnswerGrid.vue` is the single copy of the projector answer grid, used by both
the host screen and preview. A preview that drifts from the real screen is worse
than no preview, so the shared markup is shared for real rather than copied.
