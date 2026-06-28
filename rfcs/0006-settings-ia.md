---
rfc: 0006
title: Settings information architecture and progressive disclosure
status: proposed
platforms: [apple, windows, gtk, android, core]
created: 2026-06-18
updated: 2026-06-28
---

# Settings information architecture and progressive disclosure

## Summary

DasherCore exposes **108 parameters** across 5 groups. The `settings_manifest.json`
already tags every parameter with a `tier` — `common` (29), `advanced` (36), or
`expert` (43). Frontends use this **minimally**: the C API exposes a binary
`advanced` flag (collapsing the three tiers into two), and some Apple targets
(DasherVision, DasherKeyboard) group advanced-flagged params into a separate
"Advanced" section. But no frontend implements true progressive disclosure —
the three-tier system is not exposed, and users cannot choose a complexity
level. This RFC proposes activating the full tier system as a
progressive-disclosure mechanism: **Simple** (common only), **Advanced**
(+ advanced), **Pro** (all), with a user-facing toggle and sensible defaults.
It also addresses tab structure consistency, contextual filtering refinement,
and the critical need for end-user research to validate the tier assignments.

## Motivation

### The problem

108 parameters is overwhelming. A new user opening Settings sees dozens of
sliders, switches, and enums — many with opaque names like
`LP_DYNAMIC_BUTTON_LAG_MS` or `BP_TWO_PUSH_OUTER` that only make sense to a
Dasher expert. The design guide §7 acknowledges this:

> Users are overwhelmed by options; therefore, settings must have contextual
> hand-holding.

But the only "hand-holding" implemented today is contextual subgroup filtering
(hiding parameters for input modes that aren't active) plus a basic binary
advanced/non-advanced split in some targets. There is no three-tier progressive
disclosure or user-facing complexity toggle.

### What exists today

| Layer | Mechanism | Used? |
| --- | --- | --- |
| `settings_manifest.json` `tier` field | `common` / `advanced` / `expert` (3 levels) | **Read but collapsed** — C API exposes binary `advanced` only |
| C API `int advanced` (`dasher.h:181`) | Binary (0 = not advanced, 1 = advanced) | **Yes, minimally** — Vision/Keyboard group advanced params into separate section; App/Mac/Windows read into struct but don't filter by it |
| Contextual subgroup filtering | Hide params for inactive input modes | **Yes** — all frontends |
| `dependsOn` field (3 params) | Show param only if dependency is enabled | **Not used by any frontend** |

### Current frontend state

| | Apple | Windows | GTK |
| --- | --- | --- | --- |
| Tabs/sections | 7 (Customization, Input, Language, Output, Speech, Game Mode, Privacy) | Same 7, dynamic from manifest | 3 hand-built pages (Mode, Help, Input Mapping) — **does not render from manifest** |
| Tier filtering | Minimal — Vision/Keyboard: advanced params grouped into "Advanced" section. App/Mac: field read but not used for visibility. | Minimal — `Advanced` field read into struct, not used for filtering | None |
| Subgroup filtering | Yes (15 input modes) | Yes (14 input modes) | No |
| Simple/Advanced toggle | None | None | None |
| Settings rendered from manifest | Yes (dynamic) | Yes (dynamic) | **No** (hand-built) |

### Parameter distribution by tier

| Group | common | advanced | expert | Total |
| --- | --- | --- | --- | --- |
| Input | 23 | 26 | 16 | 65 |
| Customization | 5 | 5 | 8 | 18 |
| Language | 0 | 2 | 12 | 14 |
| Output | 1 | 3 | 3 | 7 |
| Game Mode | 0 | 0 | 4 | 4 |
| **Total** | **29** | **36** | **43** | **108** |

Key observation: **Language and Game Mode have zero common-tier parameters.**
A Simple-mode user would see no Language or Game Mode settings at all — which
may be correct (those are inherently advanced) or may indicate the tier
assignments need adjustment.

## Detailed design

### Three visibility modes

The user picks a complexity level in Settings. This controls which parameters
are visible:

```
┌──────────────────────────────────────────────────┐
│  Settings                          [Simple ▾]    │
│                                                  │
│  ┌─ Simple ──────────────────────────────────┐   │
│  │  29 common params only                    │   │
│  │  Speed, colour, font size, input mode,    │   │
│  │  alphabet, speech on/off, etc.            │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌─ Advanced ────────────────────────────────┐   │
│  │  65 params (common + advanced)            │   │
│  │  Adds: smoothing, calibration, LM order,  │   │
│  │  auto-speed, colour tuning, etc.          │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌─ Pro ─────────────────────────────────────┐   │
│  │  108 params (all)                         │   │
│  │  Adds: socket config, debug logging,      │   │
│  │  button timing constants, etc.            │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

#### Default: Simple

New users start in Simple mode. This shows ~29 parameters — enough to choose an
input method, set speed, pick colours/fonts, select alphabet, and toggle
speech. The design guide's "live mini-canvas preview" helps them see effects
immediately.

#### Discoverability of Advanced/Pro

- A banner or footer in Simple mode: *"Showing essential settings. [Show
  advanced settings]"* — tappable link, not a hidden menu.
- The toggle is persistent (saved per-user), not per-session.
- Switching to Pro shows a brief confirmation: *"Pro mode shows all 108
  parameters. You can switch back anytime."*

#### Relationship to contextual filtering

Tier filtering and subgroup filtering **compose** — a parameter is visible only
if *both* its tier is enabled AND its subgroup matches the active input mode.
So a Simple-mode user with Click Mode active sees only common-tier Click Mode
params; a Pro-mode user sees all Click Mode params.

### Tab structure (all platforms)

Align all frontends to the manifest's group structure. The 5 canonical groups
become tabs, plus two frontend-added tabs:

| Tab | Source | Content |
| --- | --- | --- |
| Customization | manifest group | Appearance, Layout, Mouse Line, Themes |
| Input | manifest group | Control + active-filter subgroups |
| Language | manifest group | Learning, History, Advanced |
| Output | manifest group | Speed, Speech, Clipboard, Display, Logging |
| Game Mode | manifest group | Help |
| Speech | frontend-added | TTS engine selection, voice picker (not in manifest) |
| Privacy | frontend-added | Analytics opt-in, data controls (not in manifest) |

**In Simple mode**, tabs with zero common-tier parameters (Language, Game Mode)
are hidden entirely. Speech and Privacy remain always visible.

**GTK must adopt dynamic rendering** from the manifest — the current hand-built
3-page PreferencesWindow is a dead end.

### `dependsOn` activation

Three parameters already declare `dependsOn` in the manifest
(`BP_CURVE_MOUSE_LINE`, `BP_SLOW_CONTROL_BOX`, `LP_SLOW_START_TIME`). Frontends
should honour this: grey out or hide a parameter if its dependency is disabled.
Currently none do.

### Per-platform implementation

#### DasherCore (minor API change)

The `tier` field exists in `settings_manifest.json` (three levels) but is
currently collapsed to a binary `bool advancedSetting` in `Parameters.h` and
exposed via the C API as `int advanced` (`dasher.h:181`). This loses the
distinction between `common` and `advanced` — both map to `advanced == 0`,
while only `expert` maps to `advanced == 1` (or similar — the exact mapping
needs verification). To expose the three-tier system cleanly:

- **Option A (no API change):** Frontends read `tier` from the manifest JSON
  directly at build time (codegen a tier map).
- **Option B (minor C API addition):** Add `tier` to the existing
  `dasher_get_parameter_info()` response struct, or add a standalone
  `dasher_get_parameter_tier(ctx, param_key)` returning `"common"`,
  `"advanced"`, or `"expert"`.

Option B is recommended — it keeps the manifest as the sole SSOT and avoids
frontends hardcoding tier data.

#### Apple

- Add a `tier` case to `DasherBridge.ParameterGroup` or a parallel filter.
- In `DasherSettingsView.parameters(for:)`, filter by tier in addition to
  subgroup:
  ```swift
  let visibleParams = allParams.filter { param in
      param.group == group &&
      activeSubgroups[group]?.contains(param.subgroup) ?? true &&
      isTierVisible(param.tier, currentTier: settingsMode)
  }
  ```
- Add a segmented control or menu in the settings header: Simple | Advanced | Pro.
- Persist choice in `@AppStorage("settingsMode")`.

#### Windows

- `ParameterDisplayInfo` already has an `Advanced` int field (read from C API) —
  extend the C API to expose the full tier and carry it as 0=common, 1=advanced,
  2=expert.
- Add a ComboBox or ToggleButton in `SettingsPanel` header.
- Filter in `LoadParameterGroups()` by tier before rendering widgets.

#### GTK

- Must first adopt dynamic manifest rendering (currently hand-built).
- Then add the same tier filter + mode toggle.

### End-user research (critical path)

This RFC proposes the *mechanism* (progressive disclosure via existing tiers),
but the *tier assignments* — which of the 108 parameters are "common" vs
"advanced" vs "expert" — **must be validated with real end users** before
building. The current assignments were tagged by developers, not users. This
is the most important part of this RFC and should not be skipped or deferred.

#### Q1. Are the current tier assignments correct?

The manifest was tagged by a developer, not validated with users. A parameter
like `BP_AUTO_SPEEDCONTROL` (auto speed adjustment) is marked `common` — is
that right? Is `LP_LM_ALPHA` (PPM smoothing) correctly `expert`?

**Approach:** Card-sort study with 5-10 Dasher users (mixed experience levels).
Ask them to sort parameter labels into "essential," "useful sometimes," and
"rarely/never." Compare to current tier assignments.

#### Q2. Is "Simple" too simple?

29 parameters may still overwhelm some users — or it may be too restrictive.
AAC users with cognitive disabilities may need fewer options still.

**Approach:** Observe first-time users in Simple mode. Can they accomplish
core tasks (change speed, switch alphabet, enable speech)?

#### Q3. Should mode switching be in-line or modal?

A segmented control in the settings header is low-friction. A separate "mode"
page is heavier. Which feels more natural to users?

#### Q4. Should Pro mode require confirmation?

If a user accidentally enables Pro, they see 108 parameters. Should there be a
speed bump ("Pro mode is for advanced users — continue?"), or is that
patronising?

### Relationship to other RFCs

| RFC | Relationship |
| --- | --- |
| **0004 (Onboarding)** | Onboarding sets sensible defaults; Settings is where users discover more. A user who completes onboarding in Simple mode should never need to leave Simple unless they want to. |
| **0005 (Migration)** | After v5→v6 migration, the user lands in Simple mode. Migrated settings are preserved regardless of visibility — a param hidden in Simple still has its migrated value. |
| **0003 (Multilingual)** | Settings UI strings must be localised. The mode labels ("Simple" / "Advanced" / "Pro") need translation. |

### Design guide updates needed

1. **Fix DESIGN.md staleness:** The Settings Modal section lists tabs as
   "Customization, Punctuation, Volume, Locks, Accessibility" — these are
   legacy v5 names. Update to match the manifest groups.

2. **Fix README.md §7 Input count:** Says "Input (63 params)" — actual is 65.

3. **Document the tier system:** Add the Simple/Advanced/Pro concept to the
   design guide, including the default mode, the discoverability pattern, and
   the composition with contextual filtering.

4. **Reference Jen's UX work:** The PowerPoint decks in `ux-background/`
   (`Dasher - settings + onboarding.pptx`) contain UX research on settings
   organisation that should inform the tier assignments.

## Drawbacks

- **Tier assignments are subjective.** What's "common" to a developer may be
  "expert" to a user. The card-sort study is essential but takes time.
- **Maintenance overhead.** Every new parameter needs a tier assignment. This
  should be enforced in CI (the manifest validator should reject params without
  a `tier`).
- **GTK is further behind.** It needs dynamic manifest rendering before it can
  participate in tier filtering at all.
- **Risk of hiding important params.** If a user needs an `expert`-tier
  parameter, they must know to switch to Pro mode. Discoverability of the mode
  toggle is critical.
- **Language tab vanishes in Simple mode.** Zero `common`-tier Language params
  means Simple users can't change alphabet or language model settings. This
  may be the wrong default — alphabet selection feels like a "common" task.

## Alternatives considered

### Search-based settings (no tiers)

Instead of progressive disclosure, offer a search bar that filters parameters
by name/description. Good as a *supplement* but not a replacement — new users
don't know what to search for.

### Guided settings wizard

A question-based flow: "Do you use a mouse or eye tracker?" → "Do you need
speech output?" → configure accordingly. Powerful but high-effort to build and
maintain. Could be a future enhancement on top of the tier system.

### Adaptive complexity (AI-driven)

Track which parameters a user changes and auto-promote/demote their visibility.
Interesting but over-engineered for v6's first pass.

### Status quo (contextual filtering only)

Keep showing all tiers. Rejected — the design guide explicitly says users are
overwhelmed, and the tier field already exists and is unused.

## Prior art

- **macOS System Settings:** Has "Show all" / "Show basic" in some panes.
- **iOS Settings:** Hides developer/EAP options entirely until unlocked.
- **VS Code:** Three-tier settings (User, Workspace, Folder) with a search-first
  UI that also exposes a JSON view for power users.
- **Grid 3 (Smartbox):** Quick vs Advanced settings toggle — widely praised by
  AAC professionals for reducing cognitive load on end users.
- **v5 Dasher:** Had a flat preferences dialog with legacy tab names
  (Punctuation, Volume, Locks, Accessibility). No tiering. This is what
  DESIGN.md still references.

## Unresolved questions

1. **Tier audit** — Who runs the card-sort study, and when? Can we crowdsource
   tier validation from the community (e.g. a survey on the website)?
2. **Alphabet selection in Simple mode** — Should we promote the alphabet
   picker to `common` tier so Language tab appears in Simple? Or move alphabet
   selection to the status bar (where it already lives on some platforms)?
3. **Pro mode confirmation** — Speed bump or not? (Q4 above)
4. **GTK timeline** — Dynamic manifest rendering is a prerequisite. When does
   GTK adopt it?
5. **Search** — Should we add a settings search bar alongside (not instead of)
   the tier system?

## Resolution

_(To be filled in after community discussion and end-user research.)_
