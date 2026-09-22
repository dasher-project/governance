---
rfc: 0020
title: Emoji in the tree — a settings-gated emoji group for every alphabet
status: proposed
platforms: [android, gtk, windows, apple, web, core]
created: 2026-09-22
updated: 2026-09-22
---

# Emoji in the tree — a settings-gated emoji group for every alphabet

## Summary

Emoji are available **inside the Dasher node tree for every language**, not
through a mode switch. A settings-gated engine extension appends emoji groups
to whatever alphabet is loaded (the control-mode precedent: a root-level
extra with a reserved probability slice), so emoji are committed and learned
by the language model **in context** — "thanks 👍" — in the user's own
language, with no corpus changes and no alphabet switching.

Two supporting changes: the trainer gains **longest-match** symbol lookup so
multi-codepoint emoji (skin-tone modifiers, ZWJ family sequences) become
trainable; and a **preferred skin tone** setting pre-selects which tone
variant ships in the tree, alongside tone nodes that personalise through PPM
adaptation.

Supersedes the option-2 decision in
[Dasher-Android #61](https://github.com/dasher-project/Dasher-Android/issues/61)
(toolbar toggle switching to a standalone emoji alphabet), which shipped in
v0.1.21 and was withdrawn after real-use feedback: the standalone tree had a
degenerate mass distribution (a space-separated corpus trained the space
symbol to 50% of all mass), multi-codepoint nodes were permanently
untrainable, and selection crashed on Android 13.

## Implementation status

Not yet implemented. v0.1.21's option-2 design is the withdrawn first
attempt.

| Platform | State | Notes |
| --- | --- | --- |
| DasherCore | Not started | Extension merge, `BP_EMOJI_GROUP`, mass slice, longest-match trainer |
| Dasher-Android | Withdrawn (v0.1.21) | Toggle buttons to be removed; settings pickers to come |
| Dasher-GTK / Windows / Apple / web | Not started | Pick up the setting once core lands; no per-frontend data work |

## Motivation

Real-use feedback on the v0.1.21 emoji alphabet (Heide, Galaxy Tab S9 +
Android 13 emulator reports):

- **Crash**: selecting an emoji crashed the app on Android 13 (native crash;
  invisible to the Kotlin exception reporter — PostHog shows nothing).
- **Degenerate tree**: the emoji-only corpus was space-separated, and the
  trainer converts every character to a symbol lookup — the space symbol
  received 50% of trained mass ("a lot of spaces in the canvas"), most emoji
  became unaimable slivers, and the one flower with 9 corpus hits was the
  only comfortably selectable node.
- **Second-class multi-codepoint nodes**: `AlphabetMap::SymbolStream::next`
  reads exactly one unicode character per lookup (by design, 2002-era:
  "we do not support multi-unicode-character symbols"); 31 of 308 nodes
  (VS16 carriers, ZWJ families) could never receive training mass.
- **Mode-switch UX**: users expect a popup picker (Gboard model); a full
  alphabet switch restarts the zoom position mid-sentence. Zooming emoji was
  received positively once discovered ("that's pretty cool") — the tree is
  the right place, the switch was the problem.

The structural answer: emoji live in the same tree as the user's language,
at a reserved slice of root mass, learned in context through the adaptive
language model. No corpus sprinkling is required for v1 — uniform priors
inside the group, then adaptation lifts what the user actually types.

## Design

### Clause 1 — Emoji extension, load-time merge

When enabled, `CAlphIO` appends the emoji extension groups (a shared data
asset, restructured from the withdrawn `alphabet.emoji.xml`: groups +
nodes, no `<alphabet>` wrapper) to **every** loaded alphabet, as a
root-level group. The merged symbols are real alphabet symbols: committable
through `textCharAction`, present in the alphabet map, and learnable by the
PPM. One asset serves all languages.

### Clause 2 — Settings gate, default on

`BP_EMOJI_GROUP` (bool, default **true**), registered in
`settings_manifest.json` so every frontend's settings UI and persistence
come for free. The reserved root mass slice follows the control-mode
precedent (`CNodeCreationManager::AddExtras`, `NORMALIZATION / 20`).

### Clause 3 — Common at depth 2, full set at depth 3

The extension contains ~100 common emoji (faces, gestures, hearts —
messaging-first) directly in its group, and a "More…" subgroup with the
full curated set (~300), grouped topically. Two zoom levels to common
emoji, three to the long tail. No popup, no mode switch.

### Clause 4 — Longest-match trainer

`SymbolStream::next` probes multi-character map keys longest-first before
the single-character fallback, making VS16 and ZWJ nodes trainable. The
`alphabet.emoji_corpus_tokens_are_nodes` engine test relaxes from
"single-codepoint tokens only" to "whole-node tokens".

### Clause 5 — Skin tones: nodes + preference

All five Fitzpatrick variants of the most common gestures ship as nodes;
PPM adaptation personalises (the tone the user types rises in mass). A
string setting `SP_EMOJI_SKIN_TONE` (default `"none"`) pre-selects the
preferred variant at merge time, for users who want it fixed rather than
learned. Both mechanisms coexist; either may be retired later based on
usage.

### Clause 6 — Toolbar toggles withdrawn

The 😀/Abc toggle buttons (Dasher-Android #65/#67) are removed in the
release that ships the extension. The standalone `Emoji` alphabet
(DasherCore #96) is **kept** for now — harmless, and an emoji-only session
remains possible — but its corpus is not prioritised.

### Clause 7 — Crash fix gates release

The Android 13 selection crash is reproduced (API 33 emulator), root-caused
from the tombstone, fixed, and regression-tested before any part of this
RFC ships. PostHog's blindness to native crashes is a known gap; the fix
should land with the release that carries the extension.

## Testing

Per [RFC 0011](./0011-testing.md):

- **Automated (engine)**: extension present/absent per `BP_EMOJI_GROUP`;
  merged symbols commit whole (multi-codepoint atomicity tests already
  exist from #96); root mass slice bounded; tone preference filters
  variants; merge works across three alphabets (English, German, Arabic —
  RTL); longest-match trains a VS16 node above default mass; existing
  alphabet/regression suites stay green.
- **Automated (frontend)**: Android settings pickers expose the two new
  parameters (manifest-driven UI, existing pattern).
- **Manual**: select emoji in-context mid-sentence on Android 13 emulator +
  Samsung hardware; verify no crash; verify tone preference; verify
  low-memory mode with the enlarged symbol table.

## Test matrix

| Clause | Platform | Automated test | Manual scenario |
|---|---|---|---|
| 1: load-time merge | core | emoji extension present on 3 alphabets | — |
| 2: settings gate | core | extension absent when `BP_EMOJI_GROUP=false` | toggle in Settings |
| 2: settings gate | android | picker exposes parameter | Settings → Language |
| 3: depth-2 common / depth-3 full | core | group/node counts after merge | zoom: common in 2, "More…" in 3 |
| 4: longest-match | core | VS16 token trains above default | — |
| 5: tone nodes + preference | core | variant filtered per `SP_EMOJI_SKIN_TONE` | pick tone, verify tree |
| 6: toggles removed | android | — | no 😀 button in app or IME |
| 7: no crash on select | android | — (manual repro first) | select emoji on API 33 emulator + Samsung |

## Unresolved questions

1. **Open.** Cold-start ranking: uniform priors mean emoji start modest
   until adaptation lifts them — acceptable? (Alternative: sprinkle a
   shared emoji-frequency table at merge time.)
2. **Open.** Memory: the extension adds ~300 symbols to every alphabet's
   PPM table — verify against Android `setLowMemoryMode(true)`.
3. **Open.** Should the extension carry an image-label fallback (RFC 0014)
   for platforms without a colour-emoji font?

## Resolution

_(pending — open for discussion)_
