---
rfc: 0015
title: Direct-entry mode (typing into other applications)
status: proposed
platforms: [apple, windows, gtk, android, core]
created: 2026-08-21
updated: 2026-08-26
---

# Direct-entry mode (typing into other applications)

## Summary

Dasher's "direct entry" / "keyboard mode" turns the app from a text editor into
an on-screen input method: the output pane is hidden and text is injected into
whatever other application the user is working in. Windows and Apple already
implement this (SendInput, CGEvent posting); GTK implements it via
`ydotool`/uinput; Android's analogue is the IME (RFC 0008). This RFC writes
down the cross-platform contract those frontends have converged on — window
behaviour, availability probing, failure surfacing, delete semantics — so the
remaining gaps (notably GTK's focus handling) get closed deliberately rather
than by accident.

## Implementation status

Audited August 2026.

| Platform | State | Notes |
| --- | --- | --- |
| Dasher-Windows | Implemented | `SendInput` with `KEYEVENTF_UNICODE` (VK_BACK for deletes — one per code point, output-callback driven since Aug 2026); canvas-only topmost `WS_EX_NOACTIVATE` window with mini-bar and opacity; target-window tracking. `MainWindow.axaml.cs`. |
| Dasher-Apple (macOS) | Implemented | Accessibility-trusted CGEvent posting to the tracked frontmost app; floating non-activating window, "Sending to \<app\>" indicator. `DirectModeService.swift`, `MacContentView.swift`. |
| Dasher-Apple (iOS) | Different mechanism | Keyboard extension (`UITextDocumentProxy.insertText/deleteBackward`) — the OS-sanctioned form of direct entry. Onboarding covered by [RFC 0008](./0008-keyboard-onboarding.md). |
| Dasher-GTK | Implemented (X11) | `ydotool` injection with daemon probing + failure surfacing + UTF-8-safe deletes ([Dasher-GTK #51](https://github.com/dasher-project/Dasher-GTK/pull/51)); X11 window behaviour via `_NET_WM_WINDOW_TYPE_DOCK` (never focused by EWMH WMs, stays above, all desktops — v5's three GTK4-removed calls in one property, [#62](https://github.com/dasher-project/Dasher-GTK/pull/62)); opacity slider (Preferences → Output, persisted); editor + both bars hide with a floating mini-bar; layout menu (Right/Left/Bottom/Top/Keyboard). **Wayland:** no-focus/keep-above unavailable to regular apps — the mode works but the user must steer without clicking (see Detailed design, GTK section). |
| Dasher-Android | N/A (IME) | Standalone apps cannot inject input on Android; the IME service *is* direct entry there. |
| dasher-web | N/A | Browsers cannot inject input across applications. |
| DasherCore | N/A | Injection is entirely frontend-side; the engine only needs the output callback (`dasher_set_output_callback`, event types 0 insert / 1 delete). |

## Motivation

Direct entry is one of the main ways long-term Dasher users actually run the
program — v5 GTK had it via XTest ("direct mode"), and Windows users of v6 use
it daily. But it is also the feature most prone to *silent* failure, because it
depends on platform permission plumbing that the app cannot assume:

- A v6 first-impressions report (Linux, CachyOS, 2026-08): *"I prefer to type
  directly into a window. This is probably not implemented yet."* and *"I have
  no idea what the keyboard button does."* Root cause: GTK's availability check
  tested for the `ydotool` *binary*, while Arch installs the binary without
  enabling the `ydotoold` *daemon* — so the mode toggled, the pane collapsed,
  and nothing was typed, with no error anywhere. (Fixed in Dasher-GTK #51.)
- macOS requires Accessibility trust; Windows needs no permission but must not
  steal focus from the target window; GTK must not steal focus either — v5
  solved this with `gtk_window_set_accept_focus(false)` + keep-above + stick,
  all removed in GTK4.

Each frontend solved (or didn't solve) these problems independently. The
behavioural contract should be shared, like other cross-platform UX in RFCs
0008/0010, so that "enable keyboard mode" behaves recognisably everywhere and
fails loudly everywhere.

## Detailed design

### The contract (all platforms)

1. **Mode toggle.** One obvious control ("Keyboard" / "Direct Mode"), labelled
   or tooltiped with *what it does* even when unavailable. Toggling on:
   - hides the output/editor pane (canvas-only layout, plus a small control
     strip with at least: leave-mode, settings, pause),
   - switches output routing from the internal buffer to the injection path —
     including **deletes**, which must be forwarded as backspaces,
   - does **not** clear the engine context; the user keeps their sentence.
   Toggling off restores the normal editor layout.

2. **Window behaviour.** While the mode is on, the Dasher window must not
   disturb the target application:
   - stay above / floating,
   - **never take keyboard focus** on click or hover (the injected keystrokes
     go to the focused window — if clicking Dasher to steer steals focus,
     Dasher types into itself),
   - present on all workspaces/desktops where the platform allows it,
   - optional user-configurable opacity (Windows/Apple ship 0.2–1.0, default
     ~0.85) so the canvas doesn't cover the target app.

3. **Availability probing.** The enable control may only report "available"
   if the *whole injection path* works, not just that a helper binary exists:
   - macOS: `AXIsProcessTrusted` (offer the prompt variant).
   - GTK: probe `ydotool` end-to-end (a zero-length relative pointer move
     exercises socket + daemon + uinput without moving the pointer). Sandboxed
     Flatpak/AppImage builds report unavailable (`/dev/uinput` is unreachable).
   - Windows: always available.
   When unavailable, offer guided setup (Dasher-GTK's setup dialog with
   distro-specific install commands is the pattern; Apple uses the
   accessibility-gate screen).

4. **No silent failures.** Every injection call's outcome is checked. If
   injection fails mid-session (daemon died, permission revoked), the frontend
   must tell the user and leave the mode (or pause it), never keep swallowing
   output. Where possible, remember the last non-Dasher target window
   (Windows `GetForegroundWindow` on deactivate; macOS
   `NSWorkspace.didActivateApplicationNotification`) and re-aim at it.

5. **Delete semantics.** A delete event (callback event type 1) carries the
   deleted text; inject one backspace **per character** (code point), never
   per byte. (Dasher-GTK counted bytes until #51 — "é" deleted two
   characters.)

6. **Text semantics.** Newline injects Return/Enter, not a literal newline;
   tab injects Tab where the platform has a keycode. Unicode beyond the
   platform's keycode space uses the platform's unicode path
   (`KEYEVENTF_UNICODE`, CGEvent unicode string, `ydotool type`).

7. **Engine interface.** No engine changes are required. Frontends consume
   `dasher_set_output_callback` events; the engine's edit buffer keeps
   accumulating regardless (it is simply not displayed), so leaving the mode
   must not corrupt engine state.

### Platform specifics

- **Windows (shipped).** `SendInput`/`KEYEVENTF_UNICODE`;
  `WS_EX_NOACTIVATE | WS_EX_LAYERED` + `Topmost` + opacity + mini-bar
  (`KeyboardMiniBar`); focus restoration to the remembered target via
  `AttachThreadInput` + `SetForegroundWindow`.
- **macOS (shipped).** CGEvent unicode events posted to the tracked app's pid
  (fallback `cghidEventTap`); backspace keycode 51, Return 36; floating,
  non-activating, all-spaces window; accessibility-gate prompt.
- **GTK.** Injection via `ydotool` (`type` for strings, `key` for
  Backspace/Return/Tab), daemon-probed as above. Window behaviour is
  **resolved on X11** (shipped in [Dasher-GTK #62](https://github.com/dasher-project/Dasher-GTK/pull/62)):
  setting the window's EWMH type to `_NET_WM_WINDOW_TYPE_DOCK` makes
  EWMH-compliant window managers never give it keyboard focus, keep it above,
  and show it on all desktops — v5's three GTK4-removed calls in one property
  (a plain `WM_HINTS.input` toggle was tried first but GTK4 rewrites WM_HINTS
  whenever it manages focus, so it does not survive; the type hint does).
  Opacity follows via `_NET_WM_WINDOW_OPACITY` (0.2–1.0, persisted, live
  slider — Windows/Apple parity). **Wayland remains the open case:** regular
  apps cannot refuse focus or stay above (only layer-shell surfaces can, and
  that is compositor-specific). On Wayland the mode works but the user must
  steer without clicking the canvas (hover/gaze drivers). The pragmatic
  guidance until compositor support exists: X11 sessions get full parity,
  Wayland users are warned in the mode's setup copy.
- **Android / visionOS / web.** No standalone direct entry; Android's IME is
  the equivalent surface (onboarding: RFC 0008).

## Drawbacks

- Codifying window behaviour invites bikeshedding across three windowing
  systems; the GTK4/Wayland situation genuinely has no clean answer.
- The contract adds QA surface: each platform needs a "type into another app"
  manual pass (see Testing).
- Some clauses (opacity, mini-bar) are cosmetic; enforcing them uniformly may
  not be worth blocking a frontend that otherwise implements the mode.

## Alternatives considered

- **Leave it per-frontend.** Status quo; produced the GTK silent-failure gap
  this RFC grew out of, and inconsistent behaviour between platforms.
- **Implement direct entry in DasherCore.** Rejected: injection is inherently
  platform plumbing (uinput, CGEvent, SendInput) with no shared code to put in
  the engine.
- **Keyboard-extension/IME everywhere.** Only Android and iOS offer it; no
  desktop OS lets a normal app register as an IME for other apps.

## Prior art

- **Dasher v5 GTK direct mode** — XTest injection + hide editor + keep-above +
  `accept_focus(false)` + stick (`dasher_main.cpp` `toggle_direct_mode`); the
  behavioural template for this RFC.
- **Windows On-Screen Keyboard / Tablet input panel** — `WS_EX_NOACTIVATE`
  topmost translucent window; the pattern Dasher-Windows follows.
- **CharaChorder/Keyviz-style tools, ydotool/wtype** — Linux injection
  helpers; each requires the daemon/permissions probing described here.
- **RFC 0008** — the IME/keyboard-extension *onboarding* flows; 0015 covers
  the standalone-app injection mode and cross-references it.

## Testing

Per [RFC 0011](./0011-testing.md). Mixed automated + manual:

- **Automated (frontend):** pure logic that injection depends on is unit
  tested — GTK's UTF-8 code-point counting lives in
  `Dasher-GTK/tests/test_direct_mode_service.cpp`; Windows keeps a keyboard
  debug log (`%APPDATA%/Dasher/keyboard_debug.log`). Frontends that can
  self-inject (Windows) may assert `SendInput` return values.
- **Automated (probe):** where a probe is pure (macOS trust-state enum), test
  the state machine.
- **Manual verification required** per platform, since injection crosses
  process boundaries: enable mode → focus a native text app → write a
  sentence incl. accents/emoji → delete an accented character → confirm
  exactly one character is removed; kill the daemon/permission mid-session →
  confirm a visible error and clean exit from the mode. Record the pass in the
  PR that changes this behaviour.

## Unresolved questions

1. **GTK4/Wayland focus behaviour.** **Open.** X11 Xlib fallback vs
   documented limitation vs layer-shell — needs GTK maintainer (PapeCoding)
   input.
2. **Should the engine expose a "direct mode" flag** so the UI can ask the
   engine to suppress buffer-based features (speak-on-stop, copy-on-stop)
   while injecting? **Open.**
3. **Opacity/mini-bar uniformity.** Required, recommended, or optional?
   **Open.**
4. **Wayland text-injection protocol** (`zwp_text_input_v3` is for IMEs;
   `virtual-keyboard` protocol exists on some compositors) — viable alternative
   to ydotool on Wayland? **Open.**

## Resolution

- State: pending — open for discussion
- Decided by: —
- Date: —
- Decision: Not yet accepted. Windows and Apple implementations predate the
  RFC and already conform; GTK conformance is partial (Dasher-GTK #51 closes
  the probing/failure/delete clauses).
- Open sub-questions: all (see Unresolved questions).

## History

- _2026-08-21_ — _(initial proposal, growing out of the v6 first-impressions report and Dasher-GTK #51)_
- _2026-08-26_ — _GTK status updated to Implemented (X11) after [Dasher-GTK #62](https://github.com/dasher-project/Dasher-GTK/pull/62) shipped the dock-type window behaviour + opacity; Wayland remains the open case_
- _2026-08-24_ — _(Windows: deletions now forwarded from engine output events (one backspace per code point, event-2 clears resync without injecting), closing the gap reported in [Dasher-Windows #26](https://github.com/dasher-project/Dasher-Windows/issues/26))_
