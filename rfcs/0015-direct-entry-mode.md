---
rfc: 0015
title: Direct-entry mode (typing into other applications)
status: proposed
platforms: [apple, windows, gtk, android, core]
created: 2026-08-21
updated: 2026-09-13
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

7. **Engine interface.** Injection needs no engine changes. Frontends consume
   `dasher_set_output_callback` events; the engine's edit buffer keeps
   accumulating regardless (it is simply not displayed), so leaving the mode
   must not corrupt engine state.

8. **Context awareness** *(added 2026-09, see "Context awareness" below)*.
   Direct entry is a *conversation with the target field*, not a blank slate:
   - predictions continue from text already in the target field where the
     platform can read it (v5 could not do this on Windows),
   - switching target fields re-anchors the model rather than resetting to an
     empty context,
   - and editing actions (copy/paste/select-all) operate on the *target's*
     selection, not Dasher's internal buffer.

### Context awareness (target-field context)

**How v5 did it (researched, legacy `Src/Win32`)**: v5 never read the target
app's text. All Dasher output was inserted into an internal EDIT control (the
"shadow buffer") first, `SendInput`'d to the target second; the LM read its
context from that buffer (`GetContext` = `GetWindowText(edit)`). Clicking
re-anchored via `SetOffset(cursor)`; control-mode Copy/Paste/Cut/SelectAll
were `WM_COPY`/`WM_PASTE`/`EM_SETSEL` against the same buffer; a WinEvent
hook reset the buffer on target focus change (opt-in). So v5's "knows the
context" was *session* context: everything typed through Dasher into the
current target.

**The v6 upgrade** exceeds this in three tiers:

| Tier | Behaviour | Mechanism |
| --- | --- | --- |
| 1. Session context (v5 parity) | Predictions continue from everything typed through Dasher in this session | The engine's edit buffer already mirrors injected output (Dasher-Windows #45 verified byte parity). Frontend calls `dasher_set_offset` to re-anchor after external caret moves it knows about. |
| 2. Field context *(amended 2026-09-13, sentence-window)* | Switching target fields **re-reads** the new field and re-seeds; a caret move **within an already-focused field** re-seeds too | **Sentence-window seeding**: read the field's full text + caret via the platform's accessibility text API, then trim to the **sentence around the caret** (from the last sentence boundary — `.` `!` `?` `\n` `;` `:` — up to ~200 UTF-16 units back, whichever is closer). Seed via `dasher_seed_buffer(ctx, sentence, sentence_length)`. See "Sentence-window seeding" below for the design rationale — full-document seeding caused visible canvas resets in Outlook (Dasher-Windows #68). |
| 3. Pre-existing context | Predictions continue from text the user *didn't* type through Dasher — mid-sentence continuation, replying above quoted text | Same sentence-window `dasher_seed_buffer` at mode entry / focus change with the sentence around the caret. |

**Sentence-window seeding** *(amended 2026-09-13; supersedes the original
full-document tier-2/tier-3 mechanism)*

The original amendment seeded the engine with the FULL text of the target
field. This broke in Outlook (Dasher-Windows #68, user-report video): the
UIA provider fires `TextSelectionChanged` on every injected character and
returns **inconsistent full-document reads** (email signatures included or
omitted, formatting variations, read timing). The shadow-compare — the
mechanism that prevents re-seeding on echoes of our own injected output —
could never reliably match, so every keystroke triggered a full model
rebuild = a visible canvas reset. BlueMail showed the same failure at
lower severity ("stutters but usable"). v5 never had this problem because
it never re-read the target within a field.

The sentence-window model (Heide's suggestion, v5-aligned):

1. **Read the sentence, not the document.** The LM only needs local
   context for prediction — the current sentence (or last ~200 chars) is
   sufficient. Seeding with a small, stable window makes the
   shadow-compare reliable: during typing, the sentence and the engine
   buffer grow in lockstep (each typed character extends both
   identically), so echoes compare equal and are skipped. A genuine caret
   click at a different position changes the sentence window → mismatch →
   re-seed with the new sentence (the re-anchor the user wants).

2. **Symmetric trimming.** Both the target read AND the engine buffer are
   trimmed through the same sentence-window function before comparing.
   Without this, typing a sentence terminator (`.`) through Dasher broke
   the lockstep: the engine grew to include the period while the
   sentence window trimmed to empty (boundary). Symmetric trimming also
   handles the CRLF divergence (engine emits `\n`, Outlook inserts
   `\r\n`) naturally — the boundary lands the same place on both sides.

3. **Manual re-anchor.** A mini-bar button (crosshair icon) forces a
   fresh read + seed for edge cases where the caret-moved event doesn't
   fire (some apps' accessibility providers miss same-field clicks) or
   the user wants certainty about the current context.

4. **Surrogate safety.** The 200-unit lookback cap can land mid-UTF-16-
   surrogate-pair; both the window start AND end are guarded against
   splitting a pair (start slides forward past a low surrogate, end steps
   back from a lone high surrogate).

**Cross-platform note**: all platforms with accessibility-text APIs are
susceptible to the same full-document read inconsistency — GTK's
`AtkText`/`atspi` and Apple's `AXUIElement` return the full accessible
text of complex editors (Mail, Pages, browser-based editors), and the
same signature/formatting/timing variations apply. Android's IME
`SurroundingText` API already returns a windowed subset rather than the
full text, confirming this as the correct approach. **All frontends
implementing clause 8 (or RFC 0019 clause 6) should use sentence-window
seeding, not full-document seeding.**

**Failure modes**: accessibility reads can be slow (read on a background
thread; timeout ~200 ms), unsupported in some apps (browsers' canvas editors,
games), or blocked (elevated target processes from a non-elevated Dasher).
Degrade gracefully: no read → Tier 1 session context; read failed for a new
target → seed empty (v5 behaviour), never a dead mode.

**Engine-side contract** (`dasher.h`):

- `dasher_set_offset(ctx, offset)` — re-anchor the model at a buffer
  position; the LM context becomes the buffer text before the offset.
- `dasher_seed_buffer(ctx, text, caret_offset)` — replace the buffer,
  emit event 2 (buffer cleared) first so output subscribers resync **without
  injecting** (backspacing a full field into the document would destroy the
  user's text — the same reasoning as Dasher-Windows #45), then rebuild the
  model anchored at `caret_offset`. Rate stats reset.

**Editing actions** (clipboard bridge): Copy lives in control mode — a
control node whose action invokes the existing `dasher_set_clipboard_callback`
(the engine already has `SupportsClipboard()` plumbing from v5). Paste /
Cut / Select-All must be **frontend** actions (they act on the target's
selection, which the engine cannot touch): injected as Ctrl+V/X/A (or the
platform equivalent) aimed at the tracked target window, surfaced on the
mini-bar. This mirrors v5, which implemented them in the frontend for exactly
this reason.

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

## Test matrix

| Clause | Platform | Automated test | Manual scenario |
|---|---|---|---|
| 1: keyboard mode toggles | GTK | — | toggle Layout → Keyboard |
| 2: text injection | GTK | `DirectModeService` (worker thread) | type into notes app |
| 2: text injection | Android | — (IME path) | type into any app |
| 4: deletions forwarded | GTK/Windows | engine tests (output events) | backspace in direct mode |
| 6: caret triggers | Windows | — (manual only) | click in Outlook/Notepad |
| 6: caret triggers | GTK | `TargetContextWatcher` atspi (26 cases) | click in target (needs a11y session) |
| 7: clipboard bridge | GTK/Windows | — | Sel/Copy/Paste from mini-bar |
| 8: context awareness (tier 1-3) | Windows | — (manual only) | switch fields in Outlook |
| 8: sentence-window trimming | all | `TargetContextDecision` unit tests | — |

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
- _2026-09-01_ — _Context-awareness amendment (contract clause 8 + "Context awareness" section): tiered session/field/pre-existing context via new `dasher_set_offset` + `dasher_seed_buffer` CAPI, clipboard bridge for control mode and mini-bar. Grows out of the v5-context research in [Dasher-Windows #50](https://github.com/dasher-project/Dasher-Windows/issues/50)._
- _2026-09-08_ - _Clause 8 trigger amendment (with RFC 0019): caret moves within an already-focused target field are context triggers alongside focus changes; platform caret-moved/selection-changed events listed; stale events dropped at seed time (tracked target must still be foreground)._
- _2026-09-13_ - _Sentence-window amendment: tier-2/tier-3 context seeding now trims to the sentence around the caret (~200 UTF-16 units, symmetric trimming for the shadow-compare) instead of seeding the full document. Full-document reads from Outlook's UIA provider returned inconsistent results (signatures, formatting, timing) — the shadow-compare could never match and every keystroke triggered a visible canvas reset. Manual re-anchor button recommended on the mini-bar. All platforms should adopt sentence-window seeding (Dasher-Windows #68)._
