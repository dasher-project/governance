---
rfc: 0010
title: Input & access methods (steering/selection/dwell/switch/eye-gaze/joystick)
status: active
platforms: [apple, windows, gtk, android, core]
created: 2026-06-28
updated: 2026-08-01
---

# Input & access methods (steering/selection/dwell/switch/eye-gaze/joystick)

> **Status (August 2026):** the canonical model below is agreed — the nine
> selection methods, the seven steering methods, and the compatibility matrix.
> Apple and Windows were verified to match for the methods they share, so this
> RFC is now `active`. What remains open is the switch-access design (consume the
> OS Switch Access / Switch Control vs. in-app capture) and the eye-gaze tracker
> abstraction; see "Proposals still open".

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

## Implementation status

Audited August 2026. Promoted from `draft` to `active`: the canonical model
below is now agreed. The Apple and Windows compatibility matrices were verified
identical for the steering methods both platforms share.

| Platform | Steering methods available | Notable gaps |
| --- | --- | --- |
| Dasher-Apple | pointer, touch, eye gaze (hover), tilt, switches, hand tracking (visionOS) | Joystick is listed but has no `GCController` capture. iOS switch capture is partial. |
| Dasher-Windows | pointer, touch, eye gaze (WinRT + UDP), joystick | No switch-capture UI. No dwell rendering. |
| Dasher-GTK | pointer, joystick (SDL), switch (keyboard) | No eye-gaze path of its own. |
| Dasher-Mobile (Android) | touch, tilt | No switch, dwell, or eye gaze. |
| dasher-web | pointer, touch, keyboard | No eye gaze, joystick, switch, or dwell. |

The canonical lists and the compatibility matrix are agreed. The eye-gaze
tracker abstraction and the switch-access design remain open.

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

## Canonical model (agreed August 2026)

The lists and the matrix below are **normative**: every frontend must use these
names and must match this matrix. They were verified identical across Apple
(`DasherShared/SelectionMethod.swift`, `AccessMethod.swift`) and Windows
(`Engine/SelectionMethod.cs`, `AccessMethod.cs`) for the steering methods both
platforms share.

### Selection methods — the engine contract

There are nine selection methods. Each maps 1:1 to an `SP_INPUT_FILTER` value in
DasherCore, so the engine is the source of truth for this side. The mapping
below must live in `DasherCore/docs` (next to `C_API.md`) so every frontend
reads one table, not two. (Follow-up task for the DasherCore repo.)

| Selection method | `SP_INPUT_FILTER` | Switch-based | Switches |
| --- | --- | --- | --- |
| continuous | `Normal Control` | no | 0 |
| pressToMove | `Press Mode` | no | 0 |
| clickToZoom | `Click Mode` | no | 0 |
| dwell | `Normal Control` | no | 0 |
| oneSwitch | `One Button Dynamic Mode` | yes | 1 |
| twoSwitches | `Two Button Dynamic Mode` | yes | 2 |
| twoPush | `Two Push Dynamic Mode` | yes | 1 |
| scanning | `Menu Mode` | yes | 1 |
| directBoxes | `Direct Mode` | yes | 1 |

### Steering methods — per-platform, hardware-gated

Steering methods are not a shared enum. They differ by hardware, and that is
correct. The names are shared; availability is not.

| Steering method | Apple | Windows | GTK | Android | Web |
| --- | --- | --- | --- | --- | --- |
| pointer | yes | yes | yes | yes | yes |
| touch | yes | yes | yes | yes | yes |
| eyeGaze | yes | yes | — | — | — |
| tilt | iOS only | — | — | yes | — |
| joystick | listed (no capture yet) | yes | yes (SDL) | — | — |
| handTracking | visionOS only | — | — | — | — |
| switchesOnly | yes | yes | yes | — | — |

### Compatibility matrix — normative

A frontend must offer only the selection methods marked for the active steering
method. Apple and Windows already match this matrix for the methods they share.

| Steering \ Selection | continuous | pressToMove | clickToZoom | dwell | oneSwitch | twoSwitches | twoPush | scanning | directBoxes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pointer | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| touch | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| eyeGaze | ✓ | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| tilt | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| joystick | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | ✓ |
| handTracking | ✓ | — | — | ✓ | ✓ | ✓ | — | — | — |
| switchesOnly | — | — | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |

## Proposals still open (eye-gaze, switch profile, dwell)

The canonical model above is agreed. The sections below are proposals for the
parts that are still open. They are not normative yet.

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

1. **Canonical method enums.** ~~Can Apple and Windows agree on a single shared
   list of `SteeringMethod` × `SelectionMethod` values (and a compatibility
   matrix)? If yes, does it live in DasherCore as documentation, or only in this
   RFC?~~ **Resolved (August 2026):** yes — see the Canonical model. The nine
   selection methods are agreed, the matrix is agreed, and the selection →
   `SP_INPUT_FILTER` mapping will live in `DasherCore/docs` as the SSOT.
   Steering methods stay per-platform (hardware-gated), names shared.
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

- Status: _accepted (canonical model agreed; switch-access design still open)_
- Decided by: _maintainers_
- Date: _2026-08-01_
- Decision: _The nine selection methods, the seven steering methods, and the
  compatibility matrix are normative. The selection → `SP_INPUT_FILTER` mapping
  is engine-owned and moves to `DasherCore/docs`. Steering methods stay
  per-platform. The switch-access question (Q2) stays open and blocks deeper
  switch work, not the model itself._

## History

- 2026-06-28 — initial proposal, marked `draft` to frame the problem.
- 2026-08-01 — promoted to `active`. Verified that Apple and Windows already
  share identical selection-method lists, identical `SP_INPUT_FILTER` mappings,
  and identical compatibility matrices for the steering methods they share. Made
  those the normative Canonical model. Resolved Q1 (the mapping lives in
  DasherCore). Q2 (switch access) remains open.
