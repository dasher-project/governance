---
rfc: 0019
title: The editor contract — v5-parity editing for the output pane
status: proposed
platforms: [apple, windows, gtk, android, core]
created: 2026-09-08
updated: 2026-09-08
---

# The editor contract — v5-parity editing for the output pane

## Summary

Every Dasher v6 frontend's output pane/editor must behave like v5's editor: the
pane is **editable**, user edits are synchronised back into the engine's edit
buffer so predictions follow what the user typed or pasted themselves, placing
the caret (clicking in the text) **re-anchors the model** at that position, and
a **New** action starts a fresh session by clearing the buffer *and* dropping
the model's context. All of this runs on engine APIs that already ship
(`dasher_seed_buffer`, `dasher_set_offset`, the UTF-16/codepoint offset
converters, `dasher_reset_output_text`, `dasher_reset`); the contract is
frontend wiring, not new core work.

## Implementation status

Not yet implemented. Audited September 2026 — both v6 frontends regressed
against v5:

| Platform | State | Notes |
| --- | --- | --- |
| Dasher-Windows | Not started (read-only pane) | `MessageArea` is `IsReadOnly`; `dasher_set_offset` has no frontend callers. Reported by a long-term v5 user after v0.1.26: "clicked at the end of the word, the canvas didn't move to that word like it did in 5." |
| Dasher-GTK | Not started (editable but unsynced) | `Gtk::TextView` accepts user input, but nothing syncs edits back; the next engine update `set_text` silently clobbers user-typed text. No `set_offset`/`seed_buffer` calls exist in `src/`. |
| Dasher-Apple | Not audited | iOS editor + macOS pane need the same audit. |
| Dasher-Android | Not audited | IME context (RFC 0008) has its own buffer rules; the editor-contract clauses may map differently. |
| DasherCore | Complete | Every API this contract needs shipped with the RFC 0015 context work (v0.2.21/v0.2.22) and is covered by engine tests. |

## Motivation

v5 shipped a real editor on both desktop frontends:

- **Win32** (`Src/Win32/Widgets/Edit.cpp:482-492`): `CEdit::OnLButtonUp` read
  the caret via `EM_GETSEL` and called `SetOffset(iStart)` — click a word, the
  canvas re-targets there, predictions continue from the click. The box was
  fully editable.
- **GTK** (`Src/Gtk2/GtkDasherControl.cpp:210-230` and `dasher_editor.cpp`):
  `set_offset`, `set_buffer(0)` (**New** — clear + drop context), control-node
  `ctrl_move`/`ctrl_delete`, `clear_all_context`.

v6 regressed in two different ways (see Implementation status), and no PR or
issue exists on either frontend to restore the behaviour. Direct-entry users
rarely notice (the pane is hidden); editor-mode users notice immediately,
because caret-click re-anchoring is v5 muscle memory.

The engine side is done: RFC 0015's context-awareness work shipped exactly the
primitives an editor needs. This RFC writes down the shared behaviour so each
frontend wires the same contract against the same APIs, rather than inventing
its own sync rules.

## Detailed design

### The contract

1. **Editable pane.** The output pane accepts user input: typing with a
   physical keyboard, paste, and caret/selection manipulation. Frontends may
   disable their widget's undo stack (engine-buffer sync is the source of
   truth; v5 had no undo parity).

2. **User edits synchronise to the engine.** Edits the user makes in the pane
   must reach the engine's edit buffer so the language model's context follows
   them:
   - call `dasher_seed_buffer(ctx, text, caret_byte_offset)`, converting the
     widget's caret index with `dasher_byte_offset_from_utf16` (UTF-16
     widgets) or `dasher_byte_offset_from_codepoints` as appropriate;
   - debouncing is allowed and recommended (e.g. 300 ms after the last edit);
     the **caret must never be lost** — pure caret moves (selection change,
     text unchanged) use `dasher_set_offset` immediately, without debounce;
   - IME composition: defer seeding until composition commit.

3. **Caret placement re-anchors the model.** Clicking in the pane (or moving
   the caret by any means) re-anchors predictions at the caret — v5's
   `SetOffset(iStart)` behaviour. Pure caret move → `dasher_set_offset`;
   caret move plus pending text change → one `dasher_seed_buffer` covering
   both.

4. **Engine-origin updates must not loop or jump the caret.** Engine output
   arrives via the output callback / buffer-change events and rewrites the
   pane; the frontend must distinguish engine-origin updates from user edits
   (origin flag or last-pushed-text comparison) so the sync in clause 2 does
   not feed back. Programmatic rewrites must **restore the caret** to the
   equivalent position (insert at/before caret advances it; delete before
   caret pulls it back), never strand it at position 0/end.

5. **New = full reset.** A **New** action (toolbar and direct-mode mini-bar)
   clears the buffer **and** drops the model context: `dasher_reset(ctx)`.
   `dasher_reset_output_text` alone is *not* New — the model would resume
   mid-sentence (GTK's `DasherBridge::reset()` documents this exact v5
   distinction from `SetBuffer(0)`). Clearing via the buffer-cleared event
   (output event 2) must not inject backspaces.

6. **Direct-entry caret moves re-seed** *(this amends RFC 0015 clause 8)*.
   A caret move **within an already-focused target field** is a context
   trigger equal to a focus change: Windows subscribes to UI Automation
   `TextSelectionChanged`; GTK uses AtkText `caret-moved`/`text-changed`;
   Apple uses `NSAccessibilitySelectedTextChanged`/`AXSelectedTextRange`.
   Stale events must be dropped at seed time (the target-must-be-foreground
   guard that RFC 0015's Windows review established).

7. **Failure modes.** Very long documents may seed a trailing window of text
   (cap chosen per frontend, documented); if the engine is unavailable the
   pane degrades to a plain editor for the session, never a dead pane.

### Engine interface (all shipped)

| Call | Use |
| --- | --- |
| `dasher_seed_buffer(ctx, text, caret_offset)` | user edits + caret (debounced); target-field re-seed |
| `dasher_set_offset(ctx, offset)` | pure caret re-anchor |
| `dasher_byte_offset_from_utf16` / `_from_codepoints` | widget caret → engine bytes |
| `dasher_get_output_text(ctx)` | pane content on (re)load |
| `dasher_reset_output_text(ctx)` | clear buffer, keep model position |
| `dasher_reset(ctx)` | **New**: buffer + context + rate window |

### Platform notes

- **Windows** — Avalonia `TextBox`: `IsReadOnly=false`, `UndoLimit=0`;
  `CaretIndex` for caret; loop-guard flag around engine-origin `Text` sets
  with explicit caret restore.
- **GTK** — `Gtk::TextView`: connect `GtkTextBuffer` insert/delete/notify::cursor-position; guard around `set_text` pushes from
  `OnBufferChange`; **today's behaviour silently destroys user input and
  should be treated as a bug while this RFC is pending.**
- **Apple** — audit `DasherEdit` paths per platform (macOS pane, iOS
  keyboard-extension buffer rules differ).
- **Android** — the IME already owns the target buffer; clauses 1–5 may
  reduce to New + reset semantics. Audit before implementing.

## Drawbacks

- Sync complexity: the loop-guard and caret-preservation logic (clause 4) is
  the genuinely fiddly part; a naive implementation oscillates or fights the
  user's caret.
- Seeding on every debounced edit rebuilds model context; acceptable at
  realistic document sizes, capped for extreme ones.
- Editor undo is sacrificed in v1 (engine sync is the undo surface of record).

## Alternatives considered

- **Read-only pane + caret-click only** (the minimal reading of the user
  report): cheap, but abandons paste/type-then-predict, which v5 had and the
  engine already supports; rejected.
- **Per-frontend ad-hoc behaviour**: the status quo that produced two
  divergent regressions; rejected.
- **New engine edit-op API** (incremental insert/delete instead of re-seed):
  unnecessary today — `seed_buffer` is fast enough at realistic sizes and
  already tested; revisit only if profiling the 100k-char cap says otherwise.

## Prior art

- Dasher v5 Win32 `CEdit` (click→`SetOffset`, editable, forward-keyboard
  modes) and v5 GTK `dasher_editor` (bidirectional buffer, control-node
  editing).
- The RFC 0015 context-awareness tiering (session/field/pre-existing) — this
  contract extends its trigger set rather than replacing it.

## Testing

Per [RFC 0011](./0011-testing.md):

- **Automated (engine invariants, DasherCore `tests/`)**: seed-on-edit
  equivalence (`seed_buffer` then `get_offset` == caret bytes); `dasher_reset`
  vs `dasher_reset_output_text` context-drop difference. Much of this already
  exists via the RFC 0015 test work; extend where the reset distinction is
  unpinned.
- **Automated (frontend)**: Windows engine-integration tests extend
  `EngineCApiTests`; UI-loop behaviour is manual.
- **Manual verification required** (the v5 behaviours): click-mid-word
  re-anchor; type/paste into pane then predict; engine↔pane no-loop hammering;
  New resets to root predictions; direct-entry caret moves re-seed; IME
  composition (CJK); regression pass over RFC 0015 focus-switch seeding.

## Unresolved questions

1. **Open.** Long-document cap: seed trailing N chars — what N? (Proposal:
   100 000 UTF-16 units, per-frontend override.)
2. **Open.** Editor undo: is `UndoLimit=0` acceptable long-term, or should a
   later amendment specify an undo-aware sync?
3. **Open.** Android/Apple mapping of clauses 1–5 (audit needed before
   implementation claims).
4. **Open.** Control-node editing parity (`ctrl_move`/`ctrl_delete`) — in
   scope for a future amendment once Control Mode resurfaces in the settings
   IA.

## Resolution

_(pending — open for discussion)_

## History

- _2026-09-08 — (initial proposal) Grows out of the editor-parity work
  following v0.1.26 user feedback; engine primitives shipped with RFC 0015's
  context-awareness amendment (DasherCore v0.2.21/v0.2.22). Includes the
  RFC 0015 clause-8 caret-trigger amendment in the same PR._
