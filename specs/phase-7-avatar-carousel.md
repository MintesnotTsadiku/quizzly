# Phase 7: Avatar Carousel

## Goal

The join screen's avatar strip (phase 5) scrolls, but every face in it is the
same size. The selected one is marked with a gold ring and the unselected ones
sit at 55% opacity, which is a checkbox, not a carousel. Nothing moves when you
pick, so on a phone the strip reads as a row of stickers rather than a thing you
spin.

Two changes, both on `Join.vue`:

1. The selected face is visibly bigger than its neighbours, and the change is
   animated.
2. The strip goes back to the bottom of the form on desktop, where it already
   is on a phone.

No backend, no new data, no new dependency.

## Non-goals

- **No carousel library.** This is one flex row with `overflow-x: auto`. Every
  library that does this also does infinite loop, autoplay, pagination dots,
  and drag inertia, none of which a face picker wants.
- **No scroll-driven selection.** Selection stays on tap. Making whatever face
  is centred become the selection needs an `IntersectionObserver` plus
  scroll-end debouncing, and it makes the picker fire selections while you are
  just browsing the roster.
- **No 3D perspective / coverflow tilt.** Scale and opacity say "this one" well
  enough at 40px.
- **No search field.** Still deferred from phase 5, still nothing needs it
  under ~60 avatars.

## Tracer bullet

1. Selected face scales up, transition on. **Feedback: tap a face on a phone,
   it grows into place while the old one shrinks.**
2. Tapping a half-visible face at the edge scrolls it to centre.
3. Strip moves to the full-width bottom row on desktop.

## Bigger selected face

The strip keeps its current shape: one flex row, `snap-x`, `shrink-0`
`snap-center` buttons, gutter bleed on mobile.

What changes per button:

- Every button reserves the **large** slot size, always. The face inside is
  what scales, using `transform: scale()`. Sizing the element itself would
  reflow the row on every tap, which fights the scroll position and makes the
  strip jump under the thumb. A transform does not reflow.
- Selected: `scale-100`, full opacity, keeps the gold ring.
- Unselected: roughly `scale-[0.62]`, current 55% opacity, no ring. Hover
  brings opacity up as it does today, but not scale, because the selected one
  must stay the only big face.
- `transition-transform` + `transition-opacity`, ~200ms, standard ease. The
  global `prefers-reduced-motion` rule in `index.css` already flattens every
  transition duration, so nothing extra is needed for that.

The row's height is then fixed by the large slot, so the form below it does not
shift when the selection moves.

`AvatarPic` renders at the base size it renders at today (40px) and the
transform does the rest. No new prop.

## Centring on select

The strip already centres the opening random pick on mount, once. That becomes
every selection: pick a face and it scrolls itself to the middle, so a face
tapped at the cut-off edge is no longer half off-screen while it is the big one.

`scroll-smooth` on the container, so the existing
`scrollIntoView({ inline: "center" })` animates instead of jumping, and the
mount-time centring reads as the strip settling on your face. Reduced motion is
handled by adding it as `motion-safe:scroll-smooth`, since CSS
`scroll-behavior` is not covered by the transition-duration override.

The one-shot `onMounted` call becomes a `watch` on the selection, run immediately.

## Strip back to the bottom

`a889371` gave the form two columns on desktop and parked the avatar block in
the right column spanning both rows, because as a 6-column grid it was tall and
a tall block next to two short inputs was the only layout that balanced. As a
strip it is one row high, so that reason is gone, and the desktop order
(PIN, nickname, faces, join) no longer matches the phone's.

The avatar block drops `md:col-start-2 md:row-span-2 md:row-start-1` and takes
`md:col-span-2`, putting it under the two inputs and above the join button, the
same order a phone already reads top to bottom. The strip also drops its
`md:max-w-sm` cap and runs the full form width, which is the point of moving it:
a full-width row shows roughly twice the faces at once.

Desktop layout after:

```
[ Game PIN        ] [ Nickname       ]
[ Your face — strip, full width      ]
[ Join game                          ]
```

## Verify

- Phone (390x844): tap faces across the strip, the big one is always centred
  and the join button never moves.
- Desktop: strip sits between the inputs and the join button, full width.
- Reload a few times: the random opening pick is centred and big, whatever its
  position in the roster.
- With reduced motion on, selection still works and nothing animates.

## Deferred

- Scroll-snap-driven selection, if the tap target ever feels small enough that
  people scroll-and-tap instead of tapping directly.
- Search, past ~60 avatars (carried from phase 5).
