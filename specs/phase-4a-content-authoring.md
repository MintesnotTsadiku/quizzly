# Phase 4a: Content (images + authoring UI)

Slice 1 of Phase 4 juice. See `phase-4-juice.md` for the umbrella.

## Goal

A host can create and edit a quiz entirely in the SPA, including a picture on any question, and play it. Removes the Desk-only authoring constraint that makes the app unusable for a real host.

## Tracer bullet

Ship the thinnest end-to-end path first, then widen:

1. `image` Attach Image field on `QZ Question` + question payload carries `image_url` + player and host question views render it. Author the image in Desk for this step. **Feedback: an image shows up mid-game on both screens.**
2. `/host/quizzes` list + `/host/quizzes/new` create form that saves a quiz with one question through a whitelisted API. **Feedback: a quiz authored in the SPA is playable.**
3. Widen the form: edit, delete, reorder, per-question time limit and multiplier, upload image from the form.

## Data model

`QZ Question` gains:

- `image` — Attach Image, optional.

No other schema change. Images ride on the standard `File` doctype and are served from `/files/...`.

## APIs (`quizzly/api.py`, host-only, logged in)

- `list_quizzes()` — quizzes owned by the host: name, title, question count.
- `get_quiz(quiz)` — full quiz with questions for the editor.
- `save_quiz(quiz, title, description, default_time_limit, questions)` — create when `quiz` is empty, else update. `questions` is a JSON list of rows in display order. Server replaces the child table wholesale, so reorder and delete are the same call.
- `delete_quiz(quiz)` — refuses when any `QZ Session` references it. Built as "any", not "non-Cancelled": the Link field blocks the delete either way, so a narrower rule would only produce a worse error message.

Image upload reuses the framework's `/api/method/upload_file` through frappe-ui's `FileUploader`, and the returned `file_url` is stored on the question row. No custom upload endpoint. The file is not attached to the parent quiz, because a brand new quiz has no name yet when the host picks the picture.

Ownership is enforced the same way as existing host APIs (`if_owner` on `QZ Quiz` plus an explicit owner check in the API), never trusting a client-supplied quiz name.

## Validation (server-side)

In the `QZ Quiz` controller, so nothing can write a quiz the engine cannot play:

- At least one question.
- Each question: non-empty text, all four options non-empty, `correct_option` in 1..4.

In `save_quiz`, because it is an authoring rule rather than an integrity one:

- `time_limit` within 5..120 seconds, falling back to the quiz default when unset.

The range sits in the API and not the controller on purpose. The engine plays any window correctly, and both the test suite and a Desk-authored fixture use 1 to 2 second questions to keep runs fast; a controller-level range would have broken 26 existing tests to buy nothing. `save_quiz` is the only client path, so a rogue client still cannot save a 3600 second question.

## Question payload change

`publish_question` adds `image_url` (null when absent). Everything else stays byte-identical, so a quiz with no images produces the exact payload v1 produced.

## Screens

- `/host/quizzes` — list, create button, edit and delete per row.
- `/host/quizzes/:name` — question-by-question editor: text, image picker with preview and remove, four option inputs, correct-option radio, time limit, multiplier. Add, delete, and reorder questions. Reorder is a pair of up/down buttons, not drag: a drag library is a dependency, and a quiz is a handful of rows. Revisit when a host writes 30-question quizzes and starts moving a row across a screenful.
- Existing `/host` quiz picker links out to the editor when the host has no quizzes yet.

Image display rules: contained, max 40% of the question area's height on the host screen, above the options on the player screen. Never letterboxed or cropped, never pushing options below the fold on a phone.

## Tests

- `save_quiz` round-trips: create, reload, reorder, delete a row, all reflected in `tabQZ Question` `idx` order.
- Validation rejects: zero questions, blank option, `correct_option` out of range.
- `delete_quiz` refuses while a live session references the quiz.
- A question with an image produces `image_url` in the published payload; one without produces `null`.

## Exit criteria

- Host creates a quiz in the SPA with an image on one question, starts a session on it, plays it to podium with a real player, never touching Desk.
- A pre-existing image-free quiz plays with byte-identical payloads to v1.
