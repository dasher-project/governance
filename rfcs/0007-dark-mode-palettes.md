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

DasherCore already has everything required to *render* a dark theme. Two
things were missing, both addressed by this RFC:

1. **A convention for pairing palettes** — the `appearance`/`companion`
   metadata and the eight dark companions (sections below).
2. **Appearance *state* owned by the engine boundary**, so a frontend can say
   "follow the system" or "force dark" and have DasherCore resolve the right
   palette — without each frontend reimplementing the mode toggle, the
   companion lookup, or the light/dark preference storage.

The appearance model lives at the **C API layer** (in `dasher_ctx`), not in
the DasherCore engine `Parameters` system. Appearance mode and palette
preferences are a *shell/canvas* concern (they mirror the OS appearance
setting), so they must not pollute the engine parameter schema, the settings
manifest, or the generic settings UI that every frontend renders. The model
persists via a small `appearance_settings.json` sidecar alongside
`dasher_settings.xml`.

A stateful model is required (rather than the originally-proposed stateless
"switch to my companion" call) because the stateless version has a
**persistence bug**: it wrote the auto-resolved palette to the persistent
`SP_COLOUR_ID` parameter, silently overwriting the user's explicit choice on
every appearance change, so the original choice was lost across restarts.
Storing the user's light/dark preferences as the source of truth and deriving
the active palette from them fixes this — the preference can never be
clobbered by an auto-switch.

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
Dark Green**. They carry no companion metadata; a user may select one directly
as their dark preference and it is honoured as-is — they are already
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

The model exposes an **appearance mode** (`SYSTEM` / `LIGHT` / `DARK`), a
transient **system appearance** input (what the OS reports, consulted only in
`SYSTEM` mode), and **two persisted palette preferences** (light and dark), so
a user may freely mix — e.g. Rainbow for light and TurboLUT Dark for dark.
The dark preference defaults to the light preference's companion.

```c
// Appearance mode (persisted). SYSTEM follows dasher_set_system_appearance;
// LIGHT/DARK are explicit overrides.
DASHER_API int  dasher_get_appearance_mode(dasher_ctx* ctx);            // 0=system,1=light,2=dark
DASHER_API void dasher_set_appearance_mode(dasher_ctx* ctx, int mode);

// Transient OS appearance input (not persisted). Frontends call this on an OS
// change. Consulted only when mode == SYSTEM.
DASHER_API int  dasher_get_system_appearance(dasher_ctx* ctx);          // 1=light,2=dark
DASHER_API void dasher_set_system_appearance(dasher_ctx* ctx, int appearance);

// User's preferred palette for each appearance (persisted). The palette picker
// should set the side matching the current effective appearance.
DASHER_API const char* dasher_get_light_palette(dasher_ctx* ctx);
DASHER_API const char* dasher_get_dark_palette(dasher_ctx* ctx);
DASHER_API void        dasher_set_light_palette(dasher_ctx* ctx, const char* name);
DASHER_API void        dasher_set_dark_palette(dasher_ctx* ctx, const char* name);

// Convenience for the picker: sets the preference for the current effective
// appearance, and defaults the other side to the chosen palette's companion
// (via dasher_find_companion_palette) if that side has not been customised.
DASHER_API void dasher_set_user_palette(dasher_ctx* ctx, const char* name);
```

The metadata helpers from the original proposal are retained — they are not
made redundant by the stateful model, since the dark preference still needs a
sensible default and the picker still wants to group palettes:

```c
DASHER_API int         dasher_get_palette_appearance(dasher_ctx* ctx, int index); // 0=unspec,1=light,2=dark
DASHER_API const char* dasher_find_companion_palette(dasher_ctx* ctx, const char* palette_name);
```

**Resolution.** Whenever mode, system appearance, or either preference
changes, DasherCore recomputes the active palette:

```
effective_appearance = (mode == SYSTEM) ? system_appearance : mode
active = (effective_appearance == LIGHT) ? light_palette : dark_palette
```

…and writes it to the existing `SP_COLOUR_ID` parameter, which is what the
canvas renders and what `dasher_get_current_palette` returns. `SP_COLOUR_ID`
is *derived*, not the source of truth: the persisted preferences are. The
repurposed `dasher_set_palette(ctx, name)` now sets the preference for the
current effective appearance (equivalent to `dasher_set_user_palette`), so
existing pickers stay correct within the model. Direct writes to
`SP_COLOUR_ID` via the generic parameter API bypass resolution and are
discouraged.

**Persistence.** `mode`, `light_palette`, and `dark_palette` are stored in
`<user_dir>/appearance_settings.json`, written on every change and reloaded
(and re-resolved) at `dasher_create`. Because the preferences — not the
transient active palette — are persisted, an auto-switch can never overwrite
the user's explicit choice across restarts.

### Frontend integration

1. Observe the OS appearance
   (`UITraitCollection.userInterfaceStyle` / `UISettings.ColorValues` /
   `Application.Current.RequestedTheme` / `Gtk.Settings.dark-theme` /
   `prefers-color-scheme` / `UiModeManager`).
2. On change, call `dasher_set_system_appearance(ctx, LIGHT or DARK)`. If
   `mode == SYSTEM`, DasherCore resolves and switches automatically.
3. Expose a **System / Light / Dark** control in the settings UI via
   `dasher_get/set_appearance_mode` — no per-frontend mode-toggle logic.
4. The palette picker sets preferences via `dasher_set_user_palette` (or the
   explicit `set_light_palette` / `set_dark_palette` if it offers separate
   pickers), and can use `dasher_get_palette_appearance` to group the list.

### Edge cases

- **No companion / unset preference.** If the resolved preference is empty or
  unknown, DasherCore falls back to the engine's default palette rather than
  failing; the user's other preference is untouched.
- **Already-dark palettes.** Yellow on Blue / Yellow on Black / Blue on Dark
  Green carry no companion. If a user sets one as their dark preference, that
  is honoured directly.
- **Low-memory mode / keyboard extensions.** No impact; resolution is a couple
  of string comparisons and a parameter set, with no extra allocation on the
  frame path.
- **Dangling companions.** `dasher_find_companion_palette` only returns names
  that resolve to a known palette; a `companion` pointing at a missing palette
  is treated as "no companion".
- **Mixed inheritance.** A dark palette may itself be a parent of further
  palettes; the existing `RelinkParents` cycle detection already guards this.

## Drawbacks

- **Adds two XML attributes and a new C API group.** The metadata
  (`appearance`/`companion`), the eight dark companions, and the
  mode/preference/resolution API are non-zero ABI and data surface that must be
  documented and kept stable.
- **State at the C API layer, not in the engine parameter system.** This is
  deliberate (appearance is a shell concern) but means the model persists via a
  sidecar file rather than `dasher_settings.xml`, and is not exposed through
  the generic parameter-introspection API. Frontends that auto-build settings
  from the parameter schema will not see appearance controls there — they use
  the dedicated `dasher_get/set_appearance_*` functions.
- **Authoring burden.** A genuinely good dark variant of each palette requires
  hand-tuning chrome colours. This RFC ships chrome-only dark companions for
  all eight light palettes using a shared, consistent dark palette; per-palette
  contrast tuning (e.g. where an individual letter fill is too dark on
  `#1E1E1E`) is follow-up work captured in the unresolved questions. Algorithmic
  inversion was deliberately rejected (see Alternatives).
- **Legacy palettes can't self-classify.** Because `ParseLegacy` does not read
  the new attributes, a legacy light palette reports `appearance = unspecified`.
  This is acceptable (the bidirectional lookup still pairs it), but frontends
  that want every palette classified will see "unspecified" until palettes are
  migrated to the modern format.

## Alternatives considered

### A. Frontends hardcode light→dark name pairs

Each platform keeps its own map and calls `dasher_set_palette`. Smallest
possible engine change, but duplicates the mapping six times and drifts whenever
a palette is added or renamed. Rejected as the maintainable-cost failure mode.

### B. Stateless "switch to my companion" API (original v1 of this RFC)

A single `dasher_set_appearance(ctx, light|dark)` that flips to the current
palette's companion. **Rejected after review** because it (1) provides no
System/Light/Dark mode, forcing every frontend to reinvent the mode toggle; (2)
locks the user into 1:1 pairings (Rainbow light ⟺ Rainbow Dark, no mixing); and
(3) has a **persistence bug** — it wrote the auto-resolved palette to the
persistent `SP_COLOUR_ID`, overwriting the user's explicit choice across
restarts. The stateful mode + dual-preference model in this RFC fixes all three.

### C. Appearance as a DasherCore engine parameter

Track mode/preferences inside the engine `Parameters` system so they appear in
the schema and `dasher_settings.xml`. Rejected because appearance is a
shell/canvas concern: surfacing it in the generic parameter schema would force
it into every frontend's auto-generated settings UI and bloat the settings
manifest/localization. The C-API-layer model with a sidecar keeps the engine
untouched while still centralizing the logic so frontends don't reimplement it.

### D. Algorithmic palette inversion

Compute a dark variant at load time by inverting luminance and flipping label
colours. Rejected: results are usually ugly (e.g. pastel fills invert to muddy
darks), contrast ratios are uncontrolled, and it defeats the purpose of authored
palettes. The parent-inheritance mechanism already gives us clean hand-tuned
overrides with very little XML.

### E. Migrate all palettes to the modern format and annotate all of them

Would let every palette self-report `appearance`, removing the "unspecified"
caveat. Worth doing incrementally, but blocked on hand-authoring each modern
file and not required for this RFC to deliver value — the bidirectional
companion lookup covers legacy palettes in the meantime.

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
   `"<Name> Dark"` suffix (as shipped), or a separate `appearance`-keyed
   namespace? A suffix is simpler for the bidirectional companion lookup.
2. **Default mode for fresh installs** — `SYSTEM` (follow the OS, proposed) vs
   `LIGHT` (preserve historical Dasher behaviour). With `SYSTEM` and a default
   `system_appearance = LIGHT`, out-of-the-box rendering is unchanged until a
   frontend reports otherwise; confirming `SYSTEM` as the default is the open
   question.
3. **Settings UI shape** — a single palette list with appearance badges plus a
   System/Light/Dark mode control, or separate Light/Dark palette pickers (which
   the dual-preference model already supports)? This may warrant a follow-up to
   RFC 0006 (settings IA).
4. **Per-alphabet dark overrides** — some alphabets (e.g. Thai, with its own
   colour sequences) may need darker-specific group colours. Should we allow a
   dark palette to override `nodeLabelColorSequence` per group, or is flipping
   the default label colour always enough?

## Resolution

_(To be filled in after community discussion.)_
