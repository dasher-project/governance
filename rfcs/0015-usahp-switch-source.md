---
rfc: 0015
title: "USAHP switch source: a local switch-event broker for switch capture"
status: proposed
platforms: [apple, windows, gtk, android, web, core]
created: 2026-08-02
updated: 2026-08-02
---

# USAHP switch source: a local switch-event broker for switch capture

## Summary

Dasher captures switch input ad hoc and inconsistently in every frontend (RFC
0010), and the OS-level switch services (Apple Switch Control, Windows, Android
Switch Access) conflict with in-app scanning. This RFC adopts a **local
switch-event broker** as Dasher's switch *capture* layer: a foreground daemon
(Owen's `usahp`, protocol 0.1) grabs and suppresses configured switch inputs,
normalises them to `pressed` / `released` edges, and broadcasts those edges to
local WebSocket clients. Each Dasher frontend connects, receives switch events,
and feeds them to the engine's existing input filters as `dasher_key_event`
calls.

The **interpretation** layer — DasherCore's One-Switch / Two-Switch / Two-Push /
Scanning / Direct filters — is **unchanged**. USAHP replaces how raw switch edges
*reach* Dasher, not how Dasher interprets them.

This RFC adopts the **narrow v0 broker** as the foundation. The full USAHP
draft (OS↔app handoff, analog confidence scores, multi-app arbitration) is the
north star, **not v1**. Dasher takes only the cheap, forward-compatible wire
fields now (`switch_id`, `pressed` / `released`, `confidence` defaulting to
`100.0`).

iOS and iPadOS cannot host the broker (sandbox; Apple owns switch routing), so
on iOS the only USAHP path is a **BLE hardware proxy** (prototyping only). Until
that exists, iOS stays on native Switch Control.

## Implementation status

Not started. Plan of record and companion specs live with the protocol work,
outside this repo:

- `switch-interface/USAHP Dasher Plan.md` — the integration plan.
- `switch-interface/USAHP iOS Hardware Proxy - Architecture.md` — the iOS device
  design.
- `switch-interface/usahp/` — Owen's reference broker (protocol 0.1) and its
  `docs/protocol-v0.md`.

## Motivation

RFC 0010 (still `active`) frames switch access as two things: *how you steer*
(pointer / touch / eye-gaze / tilt / joystick / switches) × *how you select*
(continuous / press-to-move / click-to-zoom / dwell / 1-switch / 2-switch /
2-push / scanning / direct). It notes that every frontend reinvents the
switch-capture side and that the matrices already diverge. Two concrete pains
follow:

1. **Capture is reinvented per frontend.** Each platform reads switches from
   keyboard keys, Bluetooth switches, or OS switch-access events through its own
   path, then maps them to `dasher_key_event`. The mappings drift; there is no
   shared "switch source."
2. **OS scanning and in-app scanning fight.** A switch user moving between
   OS-level navigation (Apple Switch Control, Windows) and Dasher's own
   one-switch / scanning modes hits conflicts over who owns the switch stream,
   with no handoff contract.

A single local broker fixes the *capture* side and gives the OS↔app handoff a
concrete place to happen later. Binary switches are the overwhelming majority of
today's users, so v0 (binary edges, no handoff) covers the real near-term need;
the analog/confidence and OS-handoff parts are genuinely useful but can follow
evidence, not lead it.

## Detailed design

### Capture vs interpretation (the seam)

- **USAHP = the capture layer.** It reads hardware, normalises to logical
  `pressed` / `released` edges, and delivers them to Dasher.
- **DasherCore's input filters = the interpretation layer (unchanged).** They
  already consume `dasher_key_event`. The only engine-facing change is mapping a
  `switch_event` to that call.

This keeps DasherCore almost untouched for v0.

### The v0 broker

`usahpd` (the `usahp` daemon) binds `ws://127.0.0.1:7312` (loopback only, no
auth, no TLS in v0). On connect it sends a `hello` snapshot of configured
logical switches, then ordered `switch_event` frames:

```json
{ "type": "switch_event", "switch_id": "switch_1",
  "action": "pressed", "sequence": 42, "monotonic_us": 1843201 }
```

Clients are passive in v0 (no client→daemon messages). Hardware capture and
suppression are the daemon's responsibility; the broker deliberately does not do
ownership, handoff, confidence, holds, or arbitration (see `usahp`'s
`docs/protocol-v0.md` → "Explicit exclusions").

### Frontend client (desktop)

Each desktop frontend adds a small WebSocket client in its bridge:

1. Connect to `ws://127.0.0.1:7312` when an **"USAHP (local switch daemon)"**
   access method is selected (probe the socket; if absent, fall back to existing
   key capture).
2. On `hello`, learn the configured `switch_id`s.
3. On `switch_event`, map `switch_id → configured engine key` and
   `action → dasher_key_event` direction (`pressed`/`released`).
4. Feed the existing engine filters. No engine change for binary switches.

macOS uses `URLSessionWebSocketTask`; Windows uses `System.Net.WebSockets`; GTK
uses a C WebSocket library.

### Engine boundary

The mapping can live per-frontend to start. If it repeats, lift a thin shared
helper into DasherCore — `dasher_feed_switch_event(ctx, switch_id, pressed)` —
that internally calls `dasher_key_event`. That is an optional follow-up, not
required for v0.

### iOS / iPadOS — hardware proxy only

iOS cannot run the broker. The only USAHP path is a BLE device that acts as the
OS-SD: it advertises **HID keyboard** (so Apple Switch Control consumes it by
default) **and** a custom GATT service. The Dasher app connects via
CoreBluetooth, handshakes, and the device stops HID and streams switch events
over GATT notifications. Failsafes: a sustained-hold escape hatch, an app
heartbeat, and **subscriber-loss** detection (the BLE link usually stays up for
HID after the app dies, so link-disconnect alone is unreliable). This also
unlocks analog/confidence inputs on iOS, which Apple gives no API for. See
`switch-interface/USAHP iOS Hardware Proxy - Architecture.md`. No MFi is
required. Until this exists, iOS uses native Switch Control.

### Android and web

- **Android** needs the broker as an `AccessibilityService` OS-SD (not in v0).
  Until then `Dasher-Android` keeps using Android Switch Access → key events.
- **Web** can connect a browser to `ws://127.0.0.1:7312` (mixed-content
  caveats). Deferred; a possible later client.

### Forward-compatible wire fields

Adopt `switch_id`, `pressed` / `released`, and a `confidence` field (defaulting
to `100.0` for binary) in any Dasher-side event model now, so adding confidence
and hold events later does not break the mapping.

## Drawbacks

- **Another process to install.** Desktop users must run `usahpd` and grant
  global-input permissions (Accessibility on macOS, low-level hook approval on
  Windows, `input` / `plugdev` on Linux). Friction.
- **iOS needs hardware.** The BLE proxy is firmware plus a device to carry —
  fine for a demo or a clinical pilot, not a scalable software deploy.
- **It overlaps OS-native switch services.** The full USAHP handoff asks the OS
  to cede control via an API that does not exist. v0 does not attempt that, but
  the ambition collides with Switch Control / Switch Access and must be handled
  honestly when reached.
- **"Universal standard" is a long road** (needs OS vendors and AAC vendors to
  adopt). Treat USAHP as Dasher's internal switch architecture first;
  standardisation is a possible later outcome, not the goal of this RFC.

## Alternatives considered

- **Per-frontend capture (status quo).** Rejected: it is the drift RFC 0010
  already flags, and it cannot solve the OS↔app conflict.
- **Engine owns the switch model.** Rejected in RFC 0010 and again here: the
  inputs are platform-specific; the engine already exposes the right knobs
  (`SP_INPUT_FILTER`, key events). The capture layer belongs at the frontend /
  OS boundary.
- **Adopt the full USAHP draft now** (OS handoff, confidence negotiation,
  arbitration tiers). Rejected for v1: too much surface before any platform
  proves the broker is useful. Keep the wire format forward-compatible instead.
- **Off-the-shelf BLE HID switch on iOS.** This is the Phase-0 baseline
  (switches work in Dasher via the keyboard path / Switch Control), but it is
  **not** USAHP — no handoff, no confidence.

## Prior art

- **USAHP draft** (`switch-interface/Universal Switch Access Handoff Protocol -
  Draft.md`) and Owen's `usahp` v0 broker.
- **Apple Switch Control, Windows Eye Control / Switch Access, Android Switch
  Access** — the OS-native switch systems whose boundary USAHP addresses.
- **Grid 3 / Tobii computer-control** — commercial AAC that drives the whole OS
  from one app (the "primary controller" tier the draft describes).
- Capture libraries the broker builds on: `gilrs`, `rdev`, `evdev`, and (web)
  WebHID.

## Testing

Per RFC 0011:

- **Broker** (`usahp`) has its own unit + CI tests; that is Owen's repo.
- **Dasher frontend (integration):** a test that injects a `switch_event` over
  the WebSocket and asserts the engine advances in a one-switch mode — i.e. the
  capture→interpretation seam works without a physical switch.
- **Manual / hardware:** physical switch → `usahpd` → Dasher on macOS; and, for
  iOS, the BLE proxy → CoreBluetooth → Dasher.

## Unresolved questions

1. **iOS commitment** — do we build the BLE proxy firmware as a real track, or
   leave iOS on native Switch Control and say so? `Open`.
2. **Desktop-first Dasher target** — macOS or Windows first? `Open`.
3. **Analog / confidence timeline** — when do we wire the confidence path beyond
   the wire-format placeholder? `Open`; follow evidence.
4. **Shared engine helper** — add `dasher_feed_switch_event` to DasherCore once
   the per-frontend mapping repeats, or keep it per-frontend? `Open`.
5. **Android OS-SD** — when does the `AccessibilityService` broker get built?
   `Open`; `Dasher-Android` is not yet cloned.

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _pending_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_

## History

- 2026-08-02 — initial proposal. Adopts the v0 broker as Dasher's switch capture
  layer, with the interpretation layer (DasherCore filters) unchanged; iOS via a
  BLE hardware proxy only; full USAHP handoff/confidence/arbitration deferred but
  wire-format forward-compatible. Sibling to RFC 0010 (selection) — this RFC is
  about capture.
