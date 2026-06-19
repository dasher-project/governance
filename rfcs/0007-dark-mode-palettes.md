---
rfc: 0007
title: Dark mode support via appearance-aware colour palettes
status: proposed
platforms: [apple, windows, gtk, android, web, core]
created: 2026-06-19
updated: 2026-06-19
---

# Dark mode support via appearance-aware colour palettes

## Summary

Add first-class dark-mode support to Dasher by (a) annotating colour
palettes with an `appearance` (`light` | `dark`) and an optional
`companion` (the name of the opposite-appearance partner), and (b)
exposing three small C API functions so frontends can discover a
palette's appearance and flip to its companion when the OS switches
between light and dark. No new rendering path is introduced: dark
palettes are ordinary palettes that inherit a light palette via the
existing `parentName` mechanism and override only the UI chrome
colours (background, labels, outlines, info/warning boxes).

## Motivation

Every platform Dasher targets (Apple, Windows, Android, modern GTK,
the web) ships a system-wide light/dark appearance that users expect
applications to follow. Today DasherCore has **no concept of
appearance**:

- A search for `dark`, `appearance`, `userInterfaceStyle`,
  `traitCollection`, or `systemColor` in `DasherCore/src` returns
  nothing relevant.
- The only dark-ish palette shipped is `colour.blue.xml` ("Yellow on
  Blue"), which is a fixed aesthetic, not a system-driven dark mode.

As a result, each frontend that wants to respect the OS appearance has
to invent its own light→dark palette mapping, hardcode the pairs, and
hope they stay in sync. This is duplicated work across six frontends
and drifts easily.

The Dasher zooming canvas makes this more than a chrome concern:
node fills, label colours, and outlines all come from the active
palette, and a light palette rendered on a dark host window (or vice
versa) produces unreadable text and jarring borders. We need the
palette — not the frontend — to own the dark variant, so the canvas
stays legible in either appearance.

## Detailed design

### Guiding principle

DasherCore already has everything required to *render* a dark theme.
What is missing is a **convention for pairing palettes** and a **small
amount of discovery** so frontends don't each reinvent the mapping.
This RFC therefore adds metadata + three API calls, and explicitly
*avoids* an engine-level "appearance state" — appearance in Dasher is
expressed entirely as "which palette is active".

### Palette metadata (XML schema)

Two optional attributes are added to the modern `<colors>` palette
element (declared in `Data/colours/color.dtd`):

| Attribute | Values | Default | Meaning |
| --- | --- | --- | --- |
| `appearance` | `light` \| `dark` | unspecified | How this palette is classified, for frontend grouping and companion lookup |
| `companion` | a palette name | none | The opposite-appearance partner of this palette |

Example (a new file `colour.rainbow.dark.xml`):

```xml
<colors name="Rainbow Dark"
        parentName="Rainbow"
        appearance="dark"
        companion="Rainbow"
        backgroundColor="#1E1E1E"
        defaultLabelColor="#FFFFFF"
        defaultOutlineColor="#3A3A3A"
        crosshairColor="#CCCCCC"
        inputLineColor="#FF5555"
        inputPositionColor="#FFFFFF"
        infoTextColor="#FFFFFF"
        infoTextBackgroundColor="#000000"
        warningTextColor="#1E1E1E"
        warningTextBackgroundColor="#FFCC00"
        uiPreviewColors="#00FFFF,#B4EEB4,#9BCD9B,#FFD700">
</colors>
```

The dark palette inherits all of Rainbow's letter/group colours through
`parentName` (group colours already walk the parent chain in
`ColorPalette::GetNodeColor`/`GetGroupColor`) and overrides only the
~10 chrome colours plus the label/outline defaults. The letter fills —
the palette's visual identity — stay identical, which is the desired
behaviour: a user who chose "Rainbow" should see Rainbow's letters in
both appearances, only the canvas chrome flips.

### Bundled dark variants

The critical legibility fix is the **background colour**: every light palette
ships with a dark companion that overrides `backgroundColor` (plus the other
chrome drawn on the background). This RFC ships dark companions for all eight
light palettes:

| Light palette | Dark companion |
| --- | --- |
| Default | Default Dark |
| European/Asian (Original) | European/Asian (Original) Dark |
| European/Asian for Colourblind | European/Asian for Colourblind Dark |
| Rainbow | Rainbow Dark |
| Thai | Thai Dark |
| TurboLUT | TurboLUT Dark |
| Vowels | Vowels Dark |
| Vowels2 | Vowels2 Dark |

Three bundled palettes are already dark and need no companion (and at most
minimal tweaks later): **Yellow on Blue**, **Yellow on Black**, and **Blue on
Dark Green**. They carry no companion metadata; `dasher_set_appearance` returns
`-1` for them and leaves them unchanged, which is correct — they are already
appropriate for dark mode.

Each companion inherits its parent's node/group fills (the palette's visual
identity) and overrides only:

- `backgroundColor` — the primary fix, flipped to a dark neutral (`#1E1E1E`);
- `defaultLabelColor` / `defaultOutlineColor` — flipped to white / a subtle
  dark outline so any labels or outlines drawn on the background are legible;
- the chrome that sits on the background — crosshair, input line/position,
  root/control node, selection, circle markers, start boxes, two-push guides,
  info/warning text and backgrounds, game guide.

The dark companions define no `<groupColorInfo>` of their own, so every node
colour lookup falls through to the parent. To support this, `ColorPalette::
GetUIPreviewColors()` now inherits the parent's preview colours when a palette
has none of its own, so the picker shows the parent's representative colours
for a dark companion (e.g. "Default Dark" shows Default's swatches).

### Legacy palettes

The shipped palettes (`colour.xml`, `colour.rainbow.xml`, etc.) use the
legacy `<colours><palette><colour r g b>` format, which is parsed by
`CColorIO::ParseLegacy` and does not carry appearance metadata. Rather
than require every legacy palette to be rewritten, **companion lookup is
bidirectional**: if palette *A* declares `companion="B"`, then *B*'s
effective companion is *A*, even when *B* is a legacy palette with no
metadata of its own. This means annotating only the dark side is
sufficient to link a pair.

### C API surface

Three functions are added to `dasher.h` (alongside the existing
`dasher_get_palette_*` / `dasher_set_palette` group):

```c
// Classify a palette's appearance.
// Returns: 0 = unspecified, 1 = light, 2 = dark, -1 = index out of range.
DASHER_API int dasher_get_palette_appearance(dasher_ctx* ctx, int index);

// Find the companion (opposite-appearance) palette for the given name.
// Lookup is bidirectional (see RFC). Returns the companion name, valid
// until the next API call, or NULL if the palette has no companion.
DASHER_API const char* dasher_find_companion_palette(dasher_ctx* ctx,
                                                     const char* palette_name);

// Switch to the current palette's companion for the requested appearance.
// appearance: 1 = light, 2 = dark.
// Returns 0 on success, -1 if the current palette has no companion.
DASHER_API int dasher_set_appearance(dasher_ctx* ctx, int appearance);
```

No new engine parameter or rendering code is introduced. Switching is
implemented as a lookup + the existing `dasher_set_palette`.

### Frontend integration

On every platform the pattern is identical:

1. Observe the OS appearance (e.g. `UITraitCollection.userInterfaceStyle`
   on Apple, `UISettings.ColorValues` / `Application.Current.RequestedTheme`
   on Windows, `Gtk.Settings.dark-theme` on GTK, `prefers-color-scheme`
   on web, `NightMode` / `UiModeManager` on Android).
2. On change, call `dasher_set_appearance(ctx, LIGHT or DARK)`.
3. If it returns `-1` (no companion), leave the current palette alone —
   the user picked a palette with no dark variant, and that choice is
   respected.

The settings UI can additionally use `dasher_get_palette_appearance`
to group palettes into "Light", "Dark", and "Other" sections, and
`dasher_find_companion_palette` to show a "matches system appearance"
badge.

### Edge cases

- **No companion available.** `dasher_set_appearance` returns `-1` and
  the frontend keeps the active palette. This honours an explicit user
  choice (e.g. "Yellow on Blue") over the OS preference.
- **Low-memory mode.** No change; palettes are already loaded in this
  mode and the new functions are pure lookups.
- **Keyboard extensions / small surfaces.** No impact; switching is a
  string-parameter set and triggers no extra allocation.
- **Cycles / dangling companions.** `dasher_find_companion_palette`
  only returns names that resolve to a known palette; a `companion`
  pointing at a missing palette is treated as "no companion".
- **Mixed inheritance.** A dark palette may itself be a parent of
  further palettes; the existing `RelinkParents` cycle detection
  already guards this.

## Drawbacks

- **Adds two XML attributes and three C API functions.** Small surface,
  but non-zero ABI/schema growth that must be documented and kept
  stable.
- **Authoring burden.** A genuinely good dark variant of each palette
  requires hand-tuning chrome colours. This RFC ships chrome-only dark
  companions for all eight light palettes using a shared, consistent dark
  palette; per-palette contrast tuning (e.g. where an individual letter fill
  is too dark on `#1E1E1E`) is follow-up work captured in the unresolved
  questions. Algorithmic inversion was deliberately rejected (see Alternatives).
- **Legacy palettes can't self-classify.** Because `ParseLegacy` does
  not read the new attributes, a legacy light palette reports
  `appearance = unspecified`. This is acceptable (the bidirectional
  lookup still pairs it), but frontends that want every palette
  classified will see "unspecified" until palettes are migrated to the
  modern format.

## Alternatives considered

### A. Frontends hardcode light→dark name pairs

Each platform keeps its own map and calls the existing
`dasher_set_palette`. Smallest possible engine change, but duplicates
the mapping six times and drifts whenever a palette is added or
renamed. Rejected as the maintainable-cost failure mode.

### B. Engine-level appearance state

Add an "appearance" parameter to DasherCore that the engine tracks and
uses to pick colours itself (e.g. auto-inverting palettes). Rejected
because it duplicates the palette mechanism — appearance in Dasher *is*
"which palette is active" — and because auto-inversion produces poor
results for hand-tuned palettes.

### C. Algorithmic palette inversion

Compute a dark variant at load time by inverting luminance and flipping
label colours. Rejected: results are usually ugly (e.g. pastel fills
invert to muddy darks), contrast ratios are uncontrolled, and it
defeats the purpose of authored palettes. The parent-inheritance
mechanism already gives us clean hand-tuned overrides with very little
XML.

### D. Migrate all palettes to the modern format and annotate all of them

Would let every palette self-report `appearance`, removing the
"unspecified" caveat. Worth doing incrementally, but blocked on
hand-authoring each modern file and not required for this RFC to
deliver value — the bidirectional companion lookup covers legacy
palettes in the meantime.

## Prior art

- **Apple / Windows / Android / GTK / Web** all define system
  appearance as an observable preference that apps follow by swapping
  asset/theme variants, not by recolouring algorithmically. This RFC
  mirrors that: appearance is resolved to a named variant.
- **v5 Dasher** had no dark mode; the long-standing "Yellow on Blue"
  palette is the closest existing precedent and demonstrates that a
  dark canvas is fully renderable today.
- The existing `parentName` inheritance in `CColorIO` / `ColorPalette`
  is itself prior art for the override-only authoring model.

## Unresolved questions

1. **Naming convention** for dark variants — should we standardise on a
   `"<Name> Dark"` suffix (as in the Rainbow Dark example), or a
   separate `appearance`-keyed namespace? A suffix is simpler for the
   bidirectional companion lookup.
2. **Settings UI grouping** — do frontends want a single ordered list
   with appearance badges, or separate "Light"/"Dark" pickers? This
   may warrant a follow-up to RFC 0006 (settings IA).
3. **Per-alphabet dark overrides** — some alphabets (e.g. Thai, with
   its own colour sequences) may need darker-specific group colours.
   Should we allow a dark palette to override `nodeLabelColorSequence`
   per group, or is flipping the default label colour always enough?
4. **Auto-switch by default vs. opt-in** — should a fresh install
   follow the system appearance automatically (and pick a sensible
   default palette's companion), or require the user to enable
   "match system"? Proposed default: follow system, falling back to
   the chosen palette when no companion exists.

## Resolution

_(To be filled in after community discussion.)_
