---
rfc: 0021
title: Control-mode Select subtree
status: proposed          # draft | proposed | active | implemented | rejected | withdrawn
platforms: [core, windows, apple, gtk, android]   # platforms affected
created: 2026-11-01
updated: 2026-11-01
---

# Control-mode Select subtree

## Summary

Add a **Select** group to the control-mode node tree, mirroring the existing
Move and Delete groups' granularity (Char / Word / Sentence / Paragraph /
All, backward and forward). Selecting is an OS/target-application notion the
engine cannot execute, so the group is implemented as a **frontend-registered
custom action** on the existing `dasher_register_action` surface: the engine
grows the tree; each platform performs the selection natively.

## Implementation status

Not yet implemented.

## Motivation

Heide (v0.1.35 tester feedback), after the Control node was restored:

> "Since the Control Node is back, is it possible to add a "Select" section,
> and have the same options like the other nodes do, like: char, word,
> paragraph, etc."

The control tree today (`DasherCore/Data/control/control.xml`) offers Stop,
Pause, **Move**, **Delete**, Clear and **Speak** — Move already has exactly
this granularity, but it *moves the caret*; there is no way to **select**
text through Dasher at all. For an eye-gaze AAC user, selection is currently
impossible without a separate on-screen keyboard: she keeps a
TouchMousePointer running beside Dasher largely for this. Select composes
with the pieces that already exist — *Select word* (control node) → *Copy
selection* (her most-used toolbar button) is her copy-heavy workflow with no
third-party tool.

The mini-bar's one-shot Select All button was removed at the same tester's
request (dasher-project/Dasher-Windows#80); "All" returns inside this
subtree, so nothing is lost permanently.

## Detailed design

### Engine (DasherCore)

1. **`control.xml` grows the subtree**, structurally identical to Move /
   Delete (same ref-chaining so the group stays reachable after an action):

   ```xml
   <node name="CTL_SELECT" label="Select" color="-1">
     <alph/>
     <node name="CTL_SELECT_BACKWARD" label="&lt;=" color="-1">
       <node label="All"   color="-1"><select forward="no" dist="all"/>…</node>
       <node label="Para." color="-1"><select forward="no" dist="paragraph"/>…</node>
       <node label="Word"  color="-1"><select forward="no" dist="word"/>…</node>
       <node label="Char"  color="-1"><select forward="no" dist="char"/>…</node>
     </node>
     <node name="CTL_SELECT_FORWARD" label="=&gt;" color="-1"> …char/word/paragraph/all… </node>
   </node>
   ```

2. **Execution rides the existing custom-action surface.** `select` is *not*
   a built-in `ControlAction` — selection has no engine-side semantics. The
   frontend registers a handler before `dasher_set_screen_size()` (the
   documented timing constraint, DasherCore `docs/CUSTOM_ACTIONS.md`):

   ```c
   dasher_register_action(ctx, "select", my_select_callback, user_data);
   // callback receives: name="select",
   //   attrs: forward="yes|no", dist="char|word|sentence|paragraph|all"
   ```

3. **Capability gating — the one engine change that matters.** `control.xml`
   is shared by every frontend: an unregistered `select` element must not
   render as a dead node on platforms that have not implemented it (zooming
   into a node that silently does nothing is worse than not having it).
   **Parsing must skip a node whose actions include no registered handler.**
   If current parsing already drops unknown element names, this is free; if
   it renders them, skipping is the deliverable engine change (plus a test:
   tree with handler → Select present; without → absent).

4. **Granularity in v1: Char, Word, Paragraph, All.** "Sentence" has no
   native selection keystroke on any platform. Options are (a) a
   frontend-measured heuristic (read the target text, extend to the sentence
   boundary — fragile across apps, and direct mode deliberately does not
   trust full-text reads) or (b) omit Sentence from Select v1 and revisit if
   users ask. **This RFC proposes (b).** Move/Delete keep Sentence — they
   operate engine-side where sentence distance is well-defined.

### Platform mappings

Selection must be **native OS selection** so everything downstream (the
target's own Copy toolbar, our toolbar Copy/Cut, keyboard Delete, screen
readers) acts on it without further work.

| dist | Windows direct (keystrokes) | Windows editor | Android (InputConnection) | GTK | Apple |
|---|---|---|---|---|---|
| char | `Shift+←` / `Shift+→` | `TextBox.Select` | `setSelection` ± measured char | XTest `Shift+←/→` | `Shift+←/→` via AX |
| word | `Ctrl+Shift+←` / `→` | measured word bounds | measured word bounds | `Ctrl+Shift+←/→` | `Shift+Opt+←/→` |
| paragraph | `Ctrl+Shift+↑` / `↓` | measured ¶ bounds | measured ¶ bounds | `Ctrl+Shift+↑/↓` | `Shift+Cmd+↑/↓` |
| all | `Ctrl+A` | `TextBox.SelectAll` | select all op | `Ctrl+A` | `Cmd+A` |

- **Windows direct mode** reuses the existing `SendInput` chord machinery
  (`SendCtrlChord`, the v0.1.35 editing keys' injection path), with
  `_pickerSessionActive`-class guards and `EnsureForeground` exactly like
  the strip's editing keys.
- **Windows editor mode** is trivial and doubles as the reference
  implementation of "measured" selection (distances from the pane text —
  the same `SentenceWindow`-style measurement the re-anchor uses).
- **Forward/backward** with a selection already active = extend/shrink from
  the active end (native `Shift+arrow` semantics do this for free in
  keystroke platforms; Android/editor measure from the current selection
  end).

### Composition with existing pieces

- **Delete after Select**: the target's Delete key deletes the OS selection;
  the resulting text divergence is a genuine re-seed handled by RFC 0015's
  shadow-compare. The engine's *control-mode Delete* group remains
  buffer-based and independent — no coupling.
- **Copy/Cut**: the toolbar's *Copy selection* / *Cut selection in target
  app* operate on the OS selection — Select is their missing first half.
- **Move vs Re-anchor**: Move (engine caret) and the mini-bar Re-anchor
  (context re-seed) overlap conceptually; out of scope here, noted for a
  future UX pass.

### Edge cases

- **Targets without selection keystrokes** (elevated windows, consoles):
  selection silently fails, as it does for every keystroke we inject today;
  no new failure class.
- **Read-only fields**: selection is harmless (copy-only) — same as native.
- **IME composition active**: defer the action until composition ends
  (editor mode's existing `_imeSeedPending` pattern).
- **RTL locales** (ar/fa/ur): arrow *direction* flips visually but
  `Ctrl+Shift+←` still selects a word leftward — semantics are unchanged;
  no special casing.
- **Keyboard extensions** (Apple DasherKeyboard, Android IME): selection
  targets the host app's field — same paths as the direct-mode mappings.

## Testing

- **Engine (automatic)**: control-tree parse tests in the
  `test_control_actions.cpp` pattern — Select nodes present when a handler
  is registered, absent when not; attributes (`forward`, `dist`) surface to
  the callback verbatim.
- **Windows editor mode (automatic)**: measured distances are pure
  functions (the `SentenceWindow`/`EditorKeyActions` pattern) — unit-tested
  over caret/selection/word/paragraph fixtures including CRLF and surrogate
  pairs.
- **Windows direct mode (manual)**: keystroke mapping verified by hand in
  the target matrix (Outlook, Word, Notepad, a browser field) — the same
  manual matrix the editing keys shipped with. New `ui_action` telemetry:
  `select` with dist carried in the existing action-name vocabulary
  (schema addition at implementation time).

## Rollout

1. Engine: parse-skip for unregistered actions + the subtree + tests.
2. Windows: register the handler, editor-mode (measured) + direct-mode
   (keystroke) mappings, telemetry.
3. Other platforms: register + map natively per the table above, each
   behind their own PR; until they do, the subtree simply does not appear.
