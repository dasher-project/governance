---
rfc: 0010
title: Input & access methods (steering/selection/dwell/switch/eye-gaze/joystick)
status: draft
platforms: [apple, windows, gtk, android, core]
created: 2026-06-28
updated: 2026-06-28
---

# Input & access methods (steering/selection/dwell/switch/eye-gaze/joystick)

> **This RFC is a DRAFT.** It exists to frame a large, under-specified area that
> is implemented ad-hoc and inconsistently across the v6 frontends. It is **not**
> ready for consensus; the Unresolved Questions section is the most important
> part. The intent is to align maintainers on the shape of the problem before any
> platform invests in deeper work.

## Summary

DasherCore's selection behaviour is governed by a single engine parameter,
`SP_INPUT_FILTER` (e.g. "Normal Control", "Click Mode", "Menu Mode", "Two Push
Dynamic Mode"), plus a handful of bool/long params (`BP_STOP_OUTSIDE`,
`BP_AUTOCALIBRATE`, `LP_START_MODE`, etc.). But the **user-facing concept** of an
"access method" — *how do you steer* (pointer / touch / eye-gaze / tilt / joystick
/ switches) × *how do you select* (continuous / press-to-move / click-to-zoom /
dwell / 1-switch / 2-switch / 2-push / scanning / direct-boxes) — is a
**frontend concern** that each platform has reinvented with different UX, a
different data model, and different gaps. This RFC proposes a shared
**access-method model** and a per-platform integration spec so that "set up your
access method" means the same thing on Apple, Windows, GTK, and Android.

## Motivation

- Dasher is an assistive text-entry tool. The access-method choice is the single
  most consequential configuration a user makes — it determines whether they can
  use Dasher at all with their motor abilities.
- Today:
  - **Apple** has the richest model (`AccessMethod` × `SelectionMethod` matrices,
    `SwitchProfile`, `TiltCalibrationView`, app-level dwell with a radial
    indicator) but no joystick/gamepad implementation and a partially-stubbed
    iOS switch-capture.
  - **Windows** has `AccessMethod` + `SelectionMethod` + native eye-gaze
    (WinRT) + UDP gaze + gamepad, but no switch-capture UI and no dwell
    rendering.
  - **GTK** has none of this surfaced (hand-built 3-page Preferences window).
  - **Android** has touch + tilt only; the Input settings tab shows raw engine
    parameters with no curated access-method UX.
- The matrices on Apple and Windows already **diverge** (different method enums,
  different compatibility rules). Without an RFC they will diverge further.
- Eye-gaze in particular is implemented three different ways (Apple hover /
  Windows WinRT+UDP / nothing on Android) with no shared tracker abstraction or
  wire protocol.

## Detailed design (shape — to be refined)

### Shared concepts

1. **Steering method** — what produces the continuous (x, y) the engine's pointer
   consumes. Values: `pointer`, `touch`, `eyeGaze`, `tilt`, `joystick`,
   `handTracking`, `switchesOnly`. Platform availability varies (see table below).
2. **Selection method** — when/how a zoom/select happens. Maps 1:1 to an
   `SP_INPUT_FILTER` value plus zero or more engine bool/long params. Values:
   `continuous`, `pressToMove`, `clickToZoom`, `dwell`, `oneSwitch`,
   `twoSwitches`, `twoPush`, `scanning`, `directBoxes`.
3. **Switch profile** — for switch-driven selection methods, the binding of
   physical inputs (keys / Bluetooth switches / platform switch-access events)
   to DasherCore "key events" (`dasher_key_event`). Includes scan speed.
4. **Dwell rendering** — an **app-level** affordance (not an engine concept) that
   shows a radial progress indicator after a configurable dwell duration and
   synthesises the select. Required on any platform offering dwell.
5. **Compatibility matrix** — which selection methods are valid for a given
   steering method (e.g. `scanning` is valid for `switchesOnly` but not for
   `pointer`).

### Per-platform availability (proposed target)

| Steering method | Apple | Windows | GTK | Android |
| --- | --- | --- | --- | --- |
| pointer (mouse/trackpad) | ✓ (Mac) | ✓ | ✓ (planned) | ✓ (mouse/Bluetooth) |
| touch | ✓ | ✓ | ✓ | ✓ |
| eyeGaze | ✓ (hover / iPadOS 18 Eye Tracking) | ✓ (WinRT + UDP) | TBD | **TBD (new)** |
| tilt | ✓ (iOS, CoreMotion) | — | — | ✓ (existing `TiltInputProvider`) |
| joystick / gamepad | listed, **not implemented** | ✓ (WinRT Gamepad) | TBD | **TBD (new)** |
| handTracking | listed (visionOS Phase 3) | — | — | — |
| switchesOnly | ✓ | ✓ (method exists, **no capture UI**) | TBD | **TBD (new)** |

### Eye-gaze tracker abstraction (proposal)

- A **tracker interface** per platform with one job: produce a stream of
  `(x_screen, y_screen, timestamp)` gaze points.
- Three concrete sources to standardise:
  1. **Platform-native eye tracker** (WinRT `GazeInputSourcePreview`; iPadOS 18
     Eye Tracking surfaced as a pointer; Android Camera Switch / future eye-track
     APIs).
  2. **Mouse-presenting trackers** (Tobii and others that appear as a mouse) —
     consumed via the platform pointer path, no special code.
  3. **Network gaze (UDP)** — adopt Dasher-Windows's existing UDP protocol as the
     cross-platform wire format:
     - `STREAM_DATA <ts> <x> <y>` (spaces), or
     - `GazePoint X:<x> Y:<y> Timestamp:<ts>`
     Default port 5555 on loopback. This lets a gaze-emulator or a separate
     tracker process feed any frontend.
- The frontend transforms `(x_screen, y_screen)` → canvas-local →
  `dasher_mouse_move(x, y)`.

### Switch profile (proposal)

- A `SwitchProfile` is an ordered list of up to 4 switches, each binding a
  **physical input** to a **DasherCore key event** (`dasher_key_event(ctx, key, dir)`).
- Physical inputs are platform-specific:
  - Apple: keyboard keys (Space/Enter/Tab/Arrows/F1–F12/A–Z/0–9) on Mac;
    Bluetooth switches / AssistiveTouch / the system Switch Control events on iOS.
  - Windows: keyboard keys; XInput gamepad buttons.
  - GTK: keyboard keys; evdev joysticks.
  - Android: keyboard keys; **Android Switch Access** events
    (`AccessibilityService`); Bluetooth switches via `KeyEvent`.
- Persisted as JSON sidecar (`access.json`) per platform, **outside** the engine
  parameter schema (mirrors RFC 0007's appearance-settings pattern).

### Dwell (proposal)

- App-level. Configurable duration (proposed defaults: 0.3 / 0.5 / 0.8 / 1.0 /
  1.5 s). A radial progress indicator is drawn over the canvas at the pointer;
  on completion, synthesise a select (`dasher_mouse_down` + `dasher_mouse_up` or
  the appropriate `dasher_key_event`).
- On platforms with no app-level rendering budget for it (keyboard extension,
  low-memory IME mode), dwell may be disabled with a clear note.

### Settings IA

A dedicated **Access** sub-screen (per RFC 0006 IA): steering method → selection
method (filtered by compatibility) → switch profile (if needed) → dwell settings
(if dwell) → tilt calibration (if tilt). Today Apple has this; the RFC proposes
all four platforms adopt the same shape.

## Drawbacks

- **Large surface area.** This is several engineering-months per platform; an RFC
  does not make it cheap.
- **Platform-specific fragmentation is real.** Switch Access on Android, Switch
  Control on iOS, and XInput on Windows are genuinely different APIs; a shared
  *model* is achievable, a shared *implementation* is not.
- **UX research gap.** The compatibility matrix and the access-screen IA need
  user research with the actual target population (AAC users, clinicians) —
  building this top-down risks the same "developer-assigned tiers" problem RFC
  0006 flagged.

## Alternatives considered

- **Engine owns the access-method model.** Rejected: the inputs are inherently
  platform-specific (CoreMotion, WinRT, Android Sensor/Accessibility). The
  engine already exposes the right knobs (`SP_INPUT_FILTER`, key events,
  `dasher_mouse_move`); the frontend owns the model.
- **Per-platform free-for-all.** Status quo. The matrices already diverge;
  without alignment, "I use Dasher with 2 switches" will mean different things on
  different platforms.

## Prior art

- **Dasher v5** (`IPhoneInputs.mm`, switch/dynamic modes) is the lineage for the
  iOS tilt + switch math.
- **Apple Switch Control / Android Switch Access / Windows Eye Control** are the
  platform-native assistive-input systems a frontend can consume instead of
  reinventing switch handling.
- **Tobii / eyeX / PCEye** hardware ecosystems established the UDP-gaze
  de-facto pattern.

## Unresolved questions (the most important section)

1. **Canonical method enums.** Can Apple and Windows agree on a single shared
   list of `SteeringMethod` × `SelectionMethod` values (and a compatibility
   matrix)? If yes, does it live in DasherCore as documentation, or only in this
   RFC?
2. **Switch Access vs. in-app switch capture on mobile.** On Android and iOS,
   should Dasher consume the **system** switch-access/switch-control events
   (lower friction, honours the user's existing switch setup) or capture its own
   (more control, requires the user to re-bind)? This is the biggest open
   design question.
3. **UDP gaze protocol.** Is Windows's existing format the right cross-platform
   standard, or should we define a cleaner JSON/binary format now?
4. **Android eye-gaze path.** Camera Switch presents as an accessibility
   service, not a mouse; Tobii on Android presents as a mouse. Which do we
   target first?
5. **Dwell rendering in the IME/keyboard extension.** Out of scope, or a
   reduced-capability version?
6. **Where does the access-method state live?** Sidecar JSON (per RFC 0007
   pattern) vs. engine parameters (per RFC 0006 manifest)?
7. **UX research prerequisite.** What is the minimum user research required
   before promoting this RFC out of `draft`?
8. **Does Android need an `AccessibilityService`** (for Switch Access
   consumption) alongside the existing `InputMethodService`? That has app-store
   and permission implications worth its own sub-RFC.

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _draft — not ready for consensus_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_
