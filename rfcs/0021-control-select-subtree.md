---
rfc: 0021
title: Control-mode Select subtree
status: proposed          # draft | proposed | active | implemented | rejected | withdrawn
platforms: [core, windows, apple, gtk, android, web]   # platforms affected
created: 2026-11-01
updated: 2026-11-01
---

# Control-mode Select subtree

## Summary

Add a **Select** group to the control-mode node tree, mirroring the existing
Move and Delete groups' granularity — **Char / Word / Paragraph / All**,
backward and forward (Sentence is deferred; see Unresolved questions).
Selecting is an OS/target-application notion the engine cannot execute, so
the group is implemented as a **frontend-registered custom action** on the
existing `dasher_register_action` surface: the engine grows the tree; each
platform performs the selection natively, and platforms that have not
registered a handler never see the nodes at all.

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
   Delete. One complete leaf, to show the ref-chaining that keeps the group
   reachable after an action (the pattern `CTL_MOVE` uses):

   ```xml
   <node name="CTL_SELECT" label="Select" color="-1">
     <alph/>
     <node name="CTL_SELECT_BACKWARD" label="&lt;=" color="-1">
       <!-- ... All / Para. / Word leaves, each like this: -->
       <node label="Char" color="-1">
         <select forward="no" dist="char"/>
         <alph/>
         <ref name="CTL_SELECT_BACKWARD"/>
         <ref name="CTL_SELECT_FORWARD"/>
       </node>
     </node>
     <node name="CTL_SELECT_FORWARD" label="=&gt;" color="-1">
       <!-- ... Char / Word / Para. / All leaves, same shape -->
     </node>
   </node>
   ```

   v1 `dist` values: `char | word | paragraph | all` (no `sentence` — see
   Unresolved questions).

2. **Execution rides the existing custom-action surface.** `select` is *not*
   a built-in `ControlAction` — selection has no engine-side semantics. The
   frontend registers a handler **before** `dasher_set_screen_size()` (the
   documented timing constraint, DasherCore `docs/CUSTOM_ACTIONS.md`):

   ```c
   dasher_register_action(ctx, "select", my_select_callback, user_data);
   // callback receives: name="select",
   //   attr keys/values: forward="yes|no", dist="char|word|paragraph|all"
   ```

   Contract details implementers must respect: the attribute arrays are
   valid **only during the callback** (copy what you need); the callback
   fires from `CContNode::Do()` on the thread that runs `dasher_frame()`;
   and the engine validates **no** attributes for custom actions — a typo'd
   `dist` fails silently at runtime, never at parse time (true of all
   custom actions today; noted here so the Windows implementation logs
   unexpected values).

3. **Capability gating — the one engine change.** Current behaviour
   (verified, `ControlManager.cpp` parsing): an XML element whose name is
   not in the registry is **silently ignored, but the containing node is
   kept**. Shipping the subtree ungated would therefore produce exactly the
   dead node this RFC must not create ("zooming into a node that silently
   does nothing"). The engine change is a **node-level skip**, specified
   precisely:

   - Skip a node **iff it contains an unregistered action element AND
     retains no other actions** after that element is dropped. Structural
     group nodes (`CTL_SELECT`, the direction groups) carry no actions and
     are never skipped by this rule — they are handled by the next clause.
   - **Cascade-prune emptied ancestors**: if skipping a node's children
     leaves an ancestor with no action-bearing descendants and no actions of
     its own, the ancestor is skipped too (Select → "⇐" → dead end must not
     render).
   - **Compound nodes** (the house style mixes actions per node — see
     `CTL_CLEAR`, or `speak`+`move` in the Speak subtree): drop the
     unregistered action element, keep the node if any action remains, skip
     it if none does. A future `<speak what="word"/><select dist="word"/>`
     node therefore degrades to a working speak-only node.
   - **Refs**: a `<ref>` to a named node that was skipped is itself skipped
     (dangling refs must not render). Test plan includes this case.
   - Re-registration or un-registration takes effect at the next control-box
     rebuild (toggling `BP_CONTROL_MODE` off and on), matching the existing
     timing constraint.

4. **Directional semantics (extend/shrink).** "Backward/forward" means
   **from the last-known active end of the existing selection**, where the
   frontend tracks the active end as "the end it last extended, or the
   anchor on cold start (no prior selection: anchor = caret, selection is
   empty)". Keystroke platforms get extend/shrink free from `Shift+arrow`
   semantics; Android/editor-mode frontends implement the state machine
   explicitly (their selection APIs expose start/end but no active end).
   The active-end state is per-session frontend state; it resets when the
   frontend observes a selection it did not create (user clicked/dragged).

### Platform mappings

Selection must be **native OS selection** so everything downstream (the
target's own Copy toolbar, our toolbar Copy/Cut, keyboard Delete, screen
readers) acts on it without further work.

| dist | Windows direct (keystrokes) | Windows editor | Android IME (direct) | GTK | Apple |
|---|---|---|---|---|---|
| char | `Shift+←` / `Shift+→` | `TextBox.Select` (measured) | `setSelection(caret, caret±1)` from the shadowed `onUpdateSelection` caret | XTest `Shift+←/→` | `Shift+←/→` |
| word | `Ctrl+Shift+←` / `→` | measured word bounds | **deferred** (needs word bounds = a full-text read) | `Ctrl+Shift+←/→` | `Shift+Opt+←/→` |
| paragraph | `Ctrl+Shift+↑` / `↓` ⚠ | measured ¶ bounds | **deferred** (same) | `Ctrl+Shift+↑/↓` (GtkTextView-class targets) | `Shift+Opt+↑` / `Shift+Opt+↓` |
| all | `Ctrl+A` | `TextBox.SelectAll` | `performContextMenuAction(android.R.id.selectAll)` (app-dependent) | `Ctrl+A` | `Cmd+A` |

Honesty notes per platform, because the mappings are NOT uniform:

- **Windows ⚠**: `Ctrl+Shift+↑/↓` is paragraph-accurate in Word/Outlook but
  behaves as line-or-paragraph depending on the control class (plain edit
  controls, browsers). Same failure envelope as every keystroke we inject;
  documented rather than papered over.
- **Apple**: paragraph is `Shift+Opt+↑/↓`. (`Shift+Cmd+↑/↓` selects to
  **document start/end** — the obvious-looking mapping is a data-loss bug
  when followed by Cut; called out so nobody "fixes" it later.)
- **Android (direct mode)**: `InputConnection` takes absolute offsets an IME
  does not inherently have. v1 implements **char** (caret±1 via the
  `onUpdateSelection` shadow — one offset, no text read) and **all** (via
  `performContextMenuAction(selectAll)`, app-dependent). **Word/paragraph
  are deferred**: they need word/paragraph bounds, i.e. the same
  full-text-read class RFC 0015's direct mode deliberately distrusts.
  Android **editor mode** (our own pane) implements the full set from
  measured text, like the Windows editor.
- **GTK**: XTest keystrokes work under X11; **Wayland has no XTest** (same
  open item as RFC 0015's clipboard notes) — Wayland GTK degrades to
  editor-mode-only until a portal path exists.
- **Web** (`dasher-web`): shares control.xml and the gating change; its
  editor pane can implement the full measured set via the Selection API.
  Direct-mode selection of the host page is out of scope (browser
  extension territory).

### Composition with existing pieces

- **Delete after Select**: the target's Delete key deletes the OS selection;
  the resulting text divergence is a genuine re-seed handled by RFC 0015's
  shadow-compare. The engine's *control-mode Delete* group remains
  buffer-based and independent — no coupling.
- **Copy/Cut**: the toolbar's *Copy selection* / *Cut selection in target
  app* operate on the OS selection — Select is their missing first half.
- **Dasher-Windows #79 settle window**: the caret events our selection
  keystrokes provoke land in the existing caret-moved debounce; a selection
  that does not change text cannot trip a re-seed (the shadow-compare is
  text-only), and the paragraph-settle guard covers the Enter case. The
  Windows implementation re-verifies this with the #79 log signatures.
- **Move vs Re-anchor**: Move (engine caret) and the mini-bar Re-anchor
  (context re-seed) overlap conceptually; out of scope, noted for a future
  UX pass.

### Edge cases

- **Targets without selection keystrokes** (elevated windows, consoles):
  selection silently fails, as it does for every keystroke we inject today;
  no new failure class.
- **Read-only fields**: selection is harmless (copy-only) — same as native.
- **IME composition active**: defer the action until composition ends
  (editor mode's existing `_imeSeedPending` pattern).
- **Game mode**: control nodes are not reachable in game mode today;
  nothing to specify.
- **RTL locales** (ar/fa/ur): arrow *direction* flips visually but
  `Ctrl+Shift+←` still selects a word leftward — semantics are unchanged;
  no special casing.
- **Keyboard extensions** (Apple DasherKeyboard, Android IME): selection
  targets the host app's field — same paths as the direct-mode mappings.

### Telemetry

A control-tree select emits from **no existing surface** (the `ui_action`
schema's `surface` enum is main_toolbar/status_bar/ime_toolbar). The
implementation PR extends the schema additively: new `surface` value
`control_tree`, new `action` value `select`, and the granularity carried as
`state: "dist=char,forward=yes"`-style encoding (the schema's existing
free-text `state` field). Schema amendment at implementation time, per the
RFC 0001 process.

## Drawbacks

- The engine ships tree structure for an action it cannot execute or
  verify — the gating rule is the only thing standing between every
  platform and dead nodes. The rule's precision (above) is the price of
  sharing control.xml.
- Keystroke-based selection is inherently app-dependent (the Windows ⚠ and
  Android app-dependent selectAll rows); we accept envelope parity with
  the existing editing keys rather than chasing per-app perfection.
- Another ten nodes deepen the control subtree; users who never select pay
  a small navigation cost (mitigated: the group is one zoom level deep,
  same as Move/Delete).

## Alternatives considered

- **Per-platform `control.xml` overrides** (the parser already supports
  user-dir control XML): each frontend ships only its own tree — no gating
  change needed. Rejected for v1: five divergent trees to maintain, and
  the gating fix is small and benefits any future custom action.
- **Toolbar Select buttons** (like the removed Select All): rejected — the
  strip is crowded (the v0.1.35 editing keys filled it), granularity needs
  a menu, and the control tree is where Move/Delete already live; Heide's
  request explicitly pointed there.
- **Built-in engine `SelectAction`** with a new C-API callback: rejected —
  no engine-side semantics exist to hang it on; the custom-action surface
  is exactly the documented extension point.

## Prior art

- Dasher v5's control mode (Move/Delete/Speak; no Select).
- iOS VoiceOver rotor + selection commands; Windows Speech Access
  ("select that"); macOS VoiceOver — all demonstrate granularity-based
  selection as an accessibility primitive, all implemented natively per OS.
  This RFC's split (shared semantics, native execution) mirrors their
  architecture deliberately.

## Unresolved questions

- **Sentence granularity**: rejected for v1 because no platform has a
  native select-to-sentence keystroke and a frontend-measured heuristic
  needs exactly the full-text reads direct mode distrusts. Revisit if
  editor-mode-only sentence selection (measured, our own pane — safe)
  would serve the workflows users actually describe.
- **Selection-state feedback**: after "Select word", an eye-gaze user has
  no acknowledgement that anything happened (in direct mode the engine
  cannot even know it worked). Candidates: a status-bar flash, a canvas
  toast, or Copy-selection button state. Needs design input from testers;
  not a blocker for the engine/Windows v1 behind the control tree.
- **Wayland GTK**: no XTest; portal-based selection does not exist. The
  GTK implementation may land editor-mode-only; tracked here rather than
  silently in the platform table.

## Testing

- **Engine (automatic)**: control-tree parse tests in the
  `test_control_actions.cpp` pattern — Select nodes present when a handler
  is registered, absent when not; **compound nodes degrade** (speak+select
  node keeps speak); **emptied ancestors pruned**; **refs to skipped nodes
  skipped**; attributes (`forward`, `dist`) surface to the callback
  verbatim.
- **Windows editor mode (automatic)**: measured distances and the
  active-end state machine are pure functions (the
  `SentenceWindow`/`EditorKeyActions` pattern) — unit-tested over
  caret/selection/word/paragraph fixtures including CRLF and surrogate
  pairs.
- **Windows direct mode (manual)**: keystroke mapping verified by hand in
  the target matrix (Outlook, Word, Notepad, a browser field) — the same
  manual matrix the editing keys shipped with, with the Word-vs-plain-edit
  paragraph difference explicitly checked.

## Rollout

1. Engine: the node-level skip rule + the subtree + parse tests.
2. Windows: register the handler, editor-mode (measured) + direct-mode
   (keystroke) mappings, active-end state machine, telemetry schema
   amendment.
3. Other platforms: register + map natively per the table above, each
   behind their own PR; until they do, the subtree simply does not appear
   (Android v1 ships char + all + editor-mode full set; GTK may land
   editor-mode-only pending Wayland).
