# Dasher pre-release test checklist

Walk through this before tagging a release. Check items as you verify them;
reset all checkboxes for the next release. File anything that fails as a
GitHub issue with the checklist item referenced.

**Budget**: the full checklist is ~2 hours across all platforms. For quick
releases, walk the **core** items (marked ⭐) — about 25 items covering the
regression-prone paths. Rotate through the rest on major releases.

Organised by feature area, not RFC number — testers don't think in RFCs.
Each section links to the governing RFC for the full spec.

Legend: ✅ previously verified · ⚠️ known gap or platform-specific issue ·
(empty) not yet tested this cycle

---

## Editor — output pane (RFC 0019)

*Applies to: GTK, Android (main app), Windows (text mode)*

- [ ] ⭐ Type "the quick brown fox" in the output pane; predictions follow
- [ ] Click mid-word; canvas re-targets at the click position
- [ ] ⭐ Press New (toolbar); pane empties; predictions restart from scratch (NOT mid-sentence)
- [ ] Open a .txt file; content appears AND predictions continue from its end
- [ ] Save the file; content matches (no truncation, no CRLF corruption)
- [ ] Type CJK with the physical keyboard (Japanese/Chinese IME); predictions follow after commit (not mid-composition)
- [ ] Type/paste a paragraph; no visible canvas reset on each keystroke
- [ ] Paste a large block (>100KB); app doesn't freeze

## Editor — direct mode / keyboard mode (RFC 0015)

*Applies to: GTK (keyboard mode), Windows (direct mode). Android IME has its own section below.*

- [ ] ⭐ Enter keyboard/direct mode; type into a notes app; text appears in the target
- [ ] ⭐ Press Enter; canvas does NOT reset (Windows Outlook regression, #58)
- [ ] Use Select All from the mini-bar; target's text is selected
- [ ] Use Copy from the mini-bar; clipboard contains the selection
- [ ] Use Paste from the mini-bar; clipboard content appears in the target
- [ ] Use New from the mini-bar; engine resets (predictions restart)
- [ ] Use Re-anchor from the mini-bar; predictions re-read the target context
- [ ] Exit keyboard mode; main window comes back visible and focused (not buried)
- [ ] Open Settings from the mini-bar; dialog appears ABOVE the keyboard overlay
- [ ] Click mid-sentence in the target; predictions re-anchor there
- [ ] Switch between two fields with different content; predictions reflect the focused field, not the previous one (GTK: requires session a11y; see GTK README)

## Training data (RFC 0005 + engine #84/#88)

*Applies to: all platforms*

- [ ] ⭐ Type several sentences; force-stop the app; relaunch; learned words still predict
- [ ] Settings → Language → Training: size shows > 0 after typing
- [ ] Export training data; file contains what you typed
- [ ] Import a .txt file; predictions adapt immediately AND after restart
- [ ] Import the same file twice; text is NOT duplicated
- [ ] Reset training data; predictions return to built-in defaults (after restart)
- [ ] Reset training data; type afterwards; learning starts fresh

## Alphabet selection (engine #88)

*Applies to: all platforms*

- [ ] ⭐ Switch alphabet; predictions use the new alphabet immediately
- [ ] Switch to a non-Latin alphabet (e.g. Arabic, CJK); predictions work
- [ ] Old settings with a broken alphabet (e.g. "Default") auto-heal on launch

## Input & access methods (RFC 0010)

*Platform-dependent — see RFC 0010's compatibility matrix*

### Mouse/touch steering (all platforms)
- [ ] ⭐ Mouse/touch steering works; canvas zooms toward the pointer
- [ ] Speed setting changes are immediate and proportional

### One-switch / two-switch (platform-dependent)
- [ ] One-switch mode: press advances the highlight; release selects
- [ ] Two-switch mode: switch 1 advances, switch 2 selects

### Dwell click (GTK, Windows)
- [ ] Dwell mode: hovering triggers a click after the configured delay
- [ ] Dwell doesn't fire while the pointer is moving

### Eye-gaze (RFC 0010 — proposals still open)
- [ ] Eye-gaze tracking works with a supported tracker (Windows: Tobii etc.)
- [ ] Calibration settings persist across sessions
- [ ] Auto-speed adjusts based on gaze stability
- [ ] ⚠️ Eye-gaze is the least-tested access method across all platforms

### Joystick (GTK, Android)
- [ ] Joystick/gamepad steering works (left/right/up/down zooms accordingly)
- [ ] Joystick button selects

## Keyboard mode — Android IME (RFC 0015 + #48-#50)

*Android only*

- [ ] Enable the Dasher keyboard in system settings; it appears in the picker
- [ ] ⭐ Focus a text field; IME shows; type; text appears in the target app
- [ ] ⭐ Editing toolbar: ⌫ deletes the character before the cursor
- [ ] Editing toolbar: ← → moves the cursor in the target app
- [ ] Editing toolbar: Select All selects the target's text
- [ ] Editing toolbar: Copy puts the selection on the clipboard
- [ ] Editing toolbar: Paste inserts clipboard content
- [ ] Editing toolbar appears in BOTH docked and floating modes
- [ ] Float button: floating window appears
- [ ] Floating window: drag by the handle; follows finger in BOTH directions (Samsung regression #46)
- [ ] Floating window: resize with the ⟷ handle; canvas adapts
- [ ] Dock button: returns to docked; editing toolbar reappears; type works
- [ ] Dock height: reasonable on tablet (~35%) vs phone (~42%)
- [ ] ⭐ After visiting the main app, return to any app and type; IME still works (#53)
- [ ] ⭐ Settings changed in the main app (speed, alphabet) take effect in the IME on next show (#54)

## Cross-app output (the static listener class — #53/#56)

*The recurring #53/#56 bug class: main app and IME listener cross-talk*

- [ ] Open main app; type; close main app; open IME; type — IME output works
- [ ] Open IME; type; close IME; open main app; type — main app output works
- [ ] Copy from the engine's control node; clipboard has the text (both surfaces)
- [ ] Speak from the engine's control node; TTS speaks the text (where available)
- [ ] Pause/other control actions fire correctly
- [ ] Engine messages (warnings) appear on the correct surface

## Appearance (RFC 0007)

*Applies to: all platforms*

- [ ] ⭐ Dark mode: canvas uses dark palette; text readable; no white flashes
- [ ] Light mode: canvas uses light palette
- [ ] System mode: follows OS setting
- [ ] Switch between modes; palette changes immediately (no restart needed)
- [ ] Colour palette picker: switching palettes changes colours immediately

## Startup (RFC 0018)

*Applies to: all platforms*

- [ ] ⭐ First launch (fresh install): loading indicator visible; no black/frozen window
- [ ] Subsequent launches: no flash of loading state (warm start < 3s on reference hardware)
- [ ] Engine creation failure: error message shown, not a dead window

## Settings (RFC 0006)

*Applies to: all platforms*

- [ ] Settings panel opens; every section shows at least one control
- [ ] Speed slider: changes take effect immediately
- [ ] Alphabet picker: full list; current alphabet highlighted
- [ ] ⭐ Settings persist across app restart
- [ ] Settings changed in the main app take effect in the IME (Android)

## Typing rate (RFC 0012)

- [ ] CPS/WPM readout updates while typing
- [ ] Reset button zeroes the readout

## Version & update check (RFC 0016 + 0017)

- [ ] Version shown in Settings → Privacy (or equivalent location)
- [ ] Version matches the tagged release
- [ ] Update check (self-managed builds only): new release notification appears (non-modal)

## Crash reporting (RFC 0009)

- [ ] Opt-in prompt appears on first launch (or equivalent)
- [ ] Opt-out is respected (no events after declining)
- [ ] Crash reports arrive in PostHog with readable stack traces
- [ ] Engine log tail included in crash reports

## Analytics (RFC 0001)

- [ ] ⭐ Opt-in: events appear in PostHog (app_launched, alphabet_selected)
- [ ] Opt-out: no events
- [ ] No typed text, clipboard content, or personal info in any event

---

## Control-node actions (engine ControlManager)

*The engine's control mode provides speak/copy with full granularity (all/page/paragraph/sentence/line/word). Test that frontends expose it.*

- [ ] Control node: Copy what=all — entire buffer to clipboard
- [ ] Control node: Copy what=sentence — current sentence to clipboard
- [ ] Control node: Speak what=all — TTS reads entire buffer
- [ ] Control node: Speak what=word — TTS reads last word
- [ ] Control node: Stop — halts current TTS
- [ ] Control node: Pause — pauses the engine

## Input filter modes (engine)

*All filters exist in DasherCore; test that frontends expose them and they behave correctly.*

- [ ] One-dimensional mode: single-axis steering works (head-tracker style)
- [ ] Compass mode: N/S/E/W button navigation selects
- [ ] Stylus mode: pen/stylus input works
- [ ] Stop-outside: zooming stops when pointer leaves the canvas
- [ ] Slow start: speed ramps up gradually at session start
- [ ] Circle start: dwell in the start circle to begin zooming
- [ ] Auto-copy on stop: buffer copied to clipboard when session pauses/stops

## Known gaps

Prioritised for RFC drafting. **Windows is the primary platform** for access
methods (eye-gaze is impractical on mobile).

### Elevate (core AAC gaps)
- **Eye-gaze** (RFC 0010 proposals open) — Windows: tracker matrix, calibration
  workflow, accuracy, auto-speed stability. The primary access method for the
  target audience and the least-tested code path.
- **Switch access profiles** (RFC 0010 Q2) — scanning mode, timing, switch
  hardware on Windows/GTK. Core AAC.
- **Voice/speech output** — speak-on-space, speak control nodes, per-platform
  TTS. Core AAC (users who can't see the screen rely on it).

### Keep (lower priority)
- **Onboarding** (RFC 0004, still `proposed`) — needs UX validation first
- **Keyboard extension onboarding** (RFC 0008) — Apple/Android IME enablement
- **v5 migration completeness** (RFC 0005) — Windows is the gap
- **Multi-alphabet workflows** — switching mid-session, per-alphabet training
- **Game mode** — real but not on Heide's critical path

### Coverage gaps (tests that should exist but don't)
- **Windows editor-contract automation** — clause 2 (edits sync) has no test;
  Android and GTK both do
- **Android IME crash reporting** — the IME process may be unguarded (RFC 0009
  open question #1)

### Verified present in v6 DasherCore (was incorrectly listed as gaps)
All of these exist in the engine — the gap is frontend exposure and testing,
not missing functionality:
- Speak/copy control actions with full granularity (all/page/paragraph/
  sentence/line/word) — `ControlManager.cpp`
- Socket input → replaced by `dasher_mouse_move(ctx, x, y)` CAPI
- OneDimensionalFilter, CompassMode, StylusFilter, TwoPushDynamicFilter,
  AlternatingDirectMode — all in `src/DasherCore/`
- Stop-outside (`BP_STOP_OUTSIDE`), Slow start (`BP_SLOW_START`), Circle
  start (`LP_CIRCLE_PERCENT`), Auto-copy on stop (`BP_COPY_ALL_ON_STOP`)

### Explicitly deprioritised
- Screen reader compatibility of Dasher's own UI — not a priority
- Data portability beyond training-text export/import — not a priority
- Undo/redo — deferred by design (RFC 0019 OQ 2)
