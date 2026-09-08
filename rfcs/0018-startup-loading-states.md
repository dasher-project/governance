---
rfc: 0018
title: Startup loading states — no frozen or black windows
status: proposed
platforms: [apple, windows, gtk, android, web, core]
created: 2026-08-28
updated: 2026-08-28
---

# Startup loading states — no frozen or black windows

## Summary

Every Dasher frontend shows a **loading state** — platform spinner plus the
shared string `preparing_dasher` — over a themed (never black) background
whenever a startup-blocking operation is in flight: first-launch data
installation, engine creation, or settings/training migration. The rule: if the
UI cannot draw Dasher content and input is not possible for more than ~300 ms,
the user sees that something is loading, not a dead window.

## Implementation status

Audited 2026-08-28.

| Platform | State | Notes |
| --- | --- | --- |
| Dasher-Android | Implemented | v0.1.13: `engineReady`-gated loading screen in `MainActivity`; first-show overlay in `DasherImeService` (canvas host FrameLayout). Emulator-verified cold launch and IME first-show. |
| Dasher-GTK | Not started | `DasherBridge` is constructed synchronously inside the rendering canvas (`RenderingCanvas.cpp:35`); first run shows a blank/unresponsive window while data installs and `dasher_create` runs. |
| Dasher-Apple | Not started | `dasher_create` is called synchronously in `DasherBridge.init` (Keyboard, Vision); extensions render nothing until it returns. |
| Dasher-Windows | Not started | Same synchronous C API call on the UI thread at startup. |
| dasher-web | Not started | WASM instantiation + first-run data fetch; page shows blank canvas until ready. |
| DasherCore | n/a | `dasher_create` stays synchronous (see Design). Progress callbacks are an open sub-question. |

## Motivation

DasherCore's `dasher_create` is synchronous and does real work before the
first frame can render: on first launch it installs the bundled data
(alphabets, colours, training text — ~4 s measured on an API 35 emulator with
fast virtual storage), then builds the language model and realises the engine.
On slower devices and spinning storage this window is multiples longer.

Two user-visible symptoms, both reported:

- **Black window.** Dasher-Android v0.1.12 showed a pure-black screen for the
  entire window on first launch (the activity rendered its dark theme over a
  canvas with no frames). Heide reported it as "the UI goes black when
  starting". The IME had it worse: the keyboard region was black not just on
  first launch but on **every first show**, because the engine was created on
  a posted handler after the canvas had already laid out — its size callback
  hit a null engine and was dropped, so the engine never realised and rendered
  nothing at all (fixed in v0.1.13 by pushing the canvas size after creation).
- **Frozen window.** On desktop frontends (GTK, Windows, Apple) the same
  synchronous call runs on the UI thread: the window appears and does not
  respond — no spinner, no paint, sometimes the system "not responding"
  treatment.

Users cannot distinguish "installing" from "broken". A loading state is the
cheapest possible trust signal, and the fix is known-good: Android shipped it
in v0.1.13 and the dead window is gone (pixel-verified in CI-adjacent
emulator testing).

## Detailed design

### The rule

1. **Never a dead window.** Any window region that will show Dasher content
   must never sit on a bare theme background (worse: a black surface) with no
   signal. If content cannot appear within ~300 ms, show a loading state.
2. **Loading state content.** A platform-standard indeterminate indicator
   (spinner, `NSProgressIndicator`, `ProgressBar`, GTK `Spinner`) centred in
   the affected region, plus the shared string **`preparing_dasher`**
   ("Preparing Dasher…" and translations — already in the shared catalogue,
   32 locales, RFC 0003). Frontends may add phase detail (e.g. "installing
   data") but the shared string is the baseline so all platforms say the same
   thing.
3. **Themed background.** The loading state renders over the app's normal
   background colour for the current light/dark mode (RFC 0007) — not over a
   black or transparent surface.
4. **Flash avoidance.** On warm starts the whole window is typically <300 ms;
   do not flash a spinner for it. Either delay showing the indicator by
   ~200 ms or gate on "engine not ready at first frame".

### Where it applies

| Moment | Why it blocks |
| --- | --- |
| First-launch data install | Bundled alphabets/colours/training copied to the user dir (~4 s emulator; longer on slow storage) |
| Engine creation (`dasher_create`) | Model build + training load + engine realise; even on later launches this is non-trivial |
| Settings/training migration | v5→v6 migration (RFC 0005) imports user text and settings before the engine can start |
| IME/extension first show | The keyboard surface creates its own engine instance on first focus — the same window inside a smaller frame |

### Platform mapping

- **Dasher-Android (shipped, v0.1.13 — reference implementation).**
  `MainActivity` gates its whole UI on an `engineReady` state flag set after
  engine setup completes; while false, a `CircularProgressIndicator` +
  `preparing_dasher` renders. `DasherImeService` wraps its canvas in a host
  `FrameLayout` carrying a spinner overlay, hidden when the engine is live.
  Creation itself stays off the composition path (`lifecycleScope.launch` +
  `Dispatchers.IO` for the data install).
- **Dasher-GTK.** Construct `DasherBridge` on a worker thread while the window
  maps; draw a `GtkSpinner` + label on the canvas until the bridge is ready.
  The canvas must not call into the bridge before readiness. The first frame
  swap happens on the existing idle/frame path once creation completes.
- **Dasher-Apple.** The main apps show a `ProgressView` (SwiftUI) until
  `DasherBridge` finishes initialising on a background queue. The keyboard
  extension (which cannot use some system UI) draws a small custom spinner +
  label in the input view — the Android IME overlay is the model.
- **Dasher-Windows.** Same shape: create the engine on a background thread,
  keep the window responsive, swap the loading `ContentControl` for the
  canvas when ready.
- **dasher-web.** Show the loading state while the WASM module instantiates
  and first-run data downloads; a plain CSS spinner + localised label needs
  no framework.

### DasherCore's role

None required — and deliberately so. `dasher_create` remains a synchronous,
thread-owning call: the frontend calls it from its own worker and owns the UI
feedback. This avoids a double API (`dasher_create_async` + completion
callback) that every frontend would have to marshal anyway, and keeps the C
API surface stable. (A progress callback for phased feedback — "installing
data" vs "building model" — is an open sub-question below, not a requirement.)

### Edge cases

- **Engine creation fails.** The loading state is replaced by an error row
  (existing error paths, RFC 0009 A2 on Android) — never a return to a blank
  window.
- **Slow storage / corrupted archive.** The indicator keeps animating; the
  window must stay responsive (creation on a worker thread guarantees this).
- **IME first show with data already installed.** Engine creation is fast
  (~50 ms measured); the overlay appears for at most a frame or two, or is
  skipped by the flash-avoidance rule.
- **Keyboard extensions with strict memory limits.** The overlay must be
  trivially light (one spinner + one text view), not a web view or image.

## Drawbacks

- Every frontend now has two code paths at startup (loading → content) and a
  readiness flag to keep honest. Android's gate initially hid a latent bug of
  its own (a plain `var engine` field does not recompose Compose — the gate
  must read real state), so implementers should copy the shipped pattern, not
  reinvent it.
- Thread-owned engine creation means frontends must not touch the engine from
  the UI thread until ready — an easy discipline to break. (All frontends
  already obey this after creation; the loading state just makes the boundary
  explicit.)

## Alternatives considered

- **Splash screen only.** A static splash hides the freeze but gives no
  progress affordance and cannot cover the IME case (no splash surface inside
  a keyboard). Rejected as incomplete.
- **Async C API (`dasher_create_async`).** Pushes threading into every
  frontend's callback marshalling anyway, duplicates the existing
  synchronous path, and complicates the C API contract. Rejected for now;
  revisit if a frontend genuinely cannot own a worker thread (none today).
- **Do nothing / accept the freeze.** The status quo produces "app looks
  broken" reports within weeks of each release. Rejected.

## Prior art

- Dasher-Android v0.1.13 (shipped; the reference implementation this RFC
  describes).
- Every browser, IDE, and editor shows a loading state during first-run data
  work; Android's own window previews exist precisely to avoid dead frames.

## Testing

Per [RFC 0011](./0011-testing.md): manual verification, recorded per release.

- Automated: the interesting claim ("the UI never shows a dead window") is a
  rendering property; the existing frontend test suites don't cover it. Where
  a frontend has UI tests, a "cold start reaches loading state within 500 ms"
  case is welcome but optional.
- Manual release checklist addition (all platforms): **clear app data →
  launch → a spinner with localised "Preparing Dasher…" appears over the
  themed background within 1 s → the canvas renders without further input.**
  For IMEs: enable the keyboard before ever opening the app, focus a text
  field, same expectation inside the keyboard frame.
- Android additionally: pixel-level cold-launch verification was done during
  development (emulator, API 35) and the steps are in the v0.1.13 PR
  (dasher-project/Dasher-Android#30).

## Unresolved questions

1. **Progress phases.** Should DasherCore grow an optional progress callback
   (`installing data` / `building model` / `ready`) so frontends can show
   phased status instead of one indeterminate spinner? **Open.** Low cost on
   the Core side; only worth it if frontends will use it.
2. **Threshold value.** Is ~300 ms the right show-the-spinner threshold, or
   should each platform follow its own convention (Apple's human-interface
   guidance suggests indicators for >1 s waits on macOS)? **Open.** The RFC's
   stance: treat 300 ms as an upper bound; faster is fine.
3. **Warm-start flash.** Delay-before-showing vs gate-on-first-frame: which
   pattern should be canonical, or is per-platform choice acceptable?
   **Open.**

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- State: _pending — open for discussion_
- Decided by: _maintainers + stewards_
- Date: _—_
- Decision: _—_
- Open sub-questions: _1–3 (see above)_

## History

- _2026-08-28_ — _(initial proposal; Android implementation already shipped as v0.1.13, serving as the reference)_
