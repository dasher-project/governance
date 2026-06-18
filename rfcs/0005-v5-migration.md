---
rfc: 0005
title: "Dasher v5 → v6 migration: settings, alphabets, and user data"
status: proposed
platforms: [apple, windows, gtk]
created: 2026-06-18
updated: 2026-06-18
---

# Dasher v5 → v6 migration: settings, alphabets, and user data

## Summary

When a user upgrades from Dasher v5 to v6, their preferences (speed,
alphabet, colours, input filter, control mode settings, language model
parameters), custom alphabet/colour/control XML files, and adaptive
training text should be automatically imported on first launch. Each
frontend detects v5 data in its platform-specific location, translates
the v5 parameter names to v6 equivalents, copies user-authored XML and
training files, and presents a brief "Your settings have been imported"
confirmation. The migration runs exactly once per user account.

## Motivation

Dasher v5 has been the stable release for over a decade. Users — many of
whom are people with disabilities who have invested significant effort
tuning their Dasher configuration — will lose years of personalisation
if v6 starts from defaults. Specifically:

- **Speed settings**: A user's `MaxBitRateTimes100` is highly personal
  (it reflects their physical input capability). Starting from the
  default of 80 (0.8) would feel broken to someone who had tuned it to
  700 (7.0) over years.
- **Custom alphabets**: Users like Steve Saling have authored custom
  alphabet XML with emojis, special symbols, and tailored training text.
  These cannot be reconstructed.
- **Adaptive training**: The language model's adaptive training file
  accumulates text the user has entered. Losing it resets the predictive
  quality to "factory English".
- **Colour palettes**: Users with visual impairments may have custom
  high-contrast palettes (e.g., `EurasianDarkMode`).
- **Control trees**: Custom control XML trees (speak/delete/move/stop)
  are tightly coupled to the user's workflow.

Without migration, v6 adoption will be painful for the most vulnerable
users — exactly the population Dasher exists to serve.

## Detailed design

### v5 data locations by platform

| Platform | System data (read-only) | User data (read-write) | Settings format |
|---|---|---|---|
| **Windows** | `C:\Program Files (x86)\Dasher\Dasher 5.00\system.rc\` | `%APPDATA%\dasher.rc\` | `settings.xml` (XML key-value) |
| **macOS** | `Dasher.app/Contents/Resources/` | `~/Library/Application Support/Dasher/` | `NSUserDefaults` plist (`uk.ac.cam.phy.inference.dasher.plist`) |
| **Linux/GTK** | `/usr/share/dasher/` (distro-dependent) | `~/.dasher/` | `settings.xml` (same as Windows) |

#### What `system.rc` and `dasher.rc` actually are

These are **directory names**, not files (confirmed from
`dasher/Src/Win32/Dasher.cpp:212-228`):

- **`system.rc\`** — appended to the application's install directory.
  Contains alphabet XML, colour XML, control XML, training text. This is
  the v5 equivalent of the app bundle's `Resources/` on macOS.
- **`dasher.rc\`** — appended to `%APPDATA%\`. Contains `settings.xml`
  and any user-modified XML/training files. This is the v5 equivalent of
  `~/Library/Application Support/Dasher/` on macOS.

On macOS and Linux, there is no `system.rc`/`dasher.rc` directory —
those platforms use the standard paths listed above. The README in the
`DasherSmoothSaling` repository references these Windows paths because
Steve Saling's configuration was created on Windows.

### v5 settings format

#### Windows/Linux (`settings.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE settings SYSTEM "settings.dtd">
<settings>
  <long name="MaxBitRateTimes100" value="700"/>
  <bool name="ControlMode" value="True"/>
  <bool name="TurboMode" value="True"/>
  <string name="AlphabetID" value="English with everything incl Emojis"/>
  <string name="ColourID" value="EurasianDarkMode"/>
  <string name="InputFilter" value="Normal Control"/>
  <string name="DasherFont" value="Alaska"/>
  ...
</settings>
```

Three element types: `<long>`, `<bool>`, `<string>`, each with
`name` (the v5 `regName`) and `value` attributes.

#### macOS (NSUserDefaults plist)

Binary plist at
`~/Library/Preferences/uk.ac.cam.phy.inference.dasher.plist`.
Keys are the same `regName` strings. Values are stored as native
plist types (`NSNumber` for bool/long, `NSString` for string). Since v6
has a different bundle ID (`at.dasher.Dasher.macOS`), v6 cannot use
`NSUserDefaults` to read v5 values directly — it must read the plist
file from disk via `NSDictionary(contentsOfFile:)`.

**Platform-specific keys** in the v5 plist (not in `settings.xml`):
`AppStyle`, `EditFont`, `EditFontSize`, `EditHeight`, `EditWidth`,
`FileEncodingFormat`, `FullScreen`, `MirrorLayout`, `PopupEnable`,
`PopupFont`, `PopupFullScreen`, `PopupInfront`, `ScreenHeight`,
`ScreenHeightH`, `ScreenWidth`, `ScreenWidthH`, `TimeStampNewFiles`,
`ToolbarID`, `ViewStatusbar`, `ViewToolbar`, `WindowState`, `XPosition`,
`YPosition`, `ConfirmUnsavedFiles`. These are UI/layout settings specific
to the v5 Cocoa app and have no v6 equivalent — they are silently
ignored during migration.

### Parameter mapping

v5 and v6 share the same `regName`/`storageName` for all surviving
parameters. The migration maps v5 `regName` → v6
`dasher_find_parameter_key("ENUM_NAME")`.

#### Direct 1:1 mappings (no transformation needed)

These parameters have identical `regName` strings and compatible value
semantics. They are read from v5 storage and applied directly via
`dasher_set_bool_parameter`, `dasher_set_long_parameter`, or
`dasher_set_string_parameter`.

**Bool (23 parameters):**

| v5 regName | v6 enum | Notes |
|---|---|---|
| `DrawMouseLine` | `BP_DRAW_MOUSE_LINE` | |
| `DrawMouse` | `BP_DRAW_MOUSE` | |
| `CurveMouseLine` | `BP_CURVE_MOUSE_LINE` | |
| `StartOnLeft` | `BP_START_MOUSE` | |
| `StartOnSpace` | `BP_START_SPACE` | |
| `ControlMode` | `BP_CONTROL_MODE` | |
| `PaletteChange` | `BP_PALETTE_CHANGE` | Default changed (true→false) but migrated value should win |
| `TurboMode` | `BP_TURBO_MODE` | |
| `ExactDynamics` | `BP_EXACT_DYNAMICS` | |
| `Autocalibrate` | `BP_AUTOCALIBRATE` | |
| `RemapXtreme` | `BP_REMAP_XTREME` | |
| `AutoSpeedControl` | `BP_AUTO_SPEEDCONTROL` | |
| `LMAdaptive` | `BP_LM_ADAPTIVE` | |
| `NonlinearY` | `BP_NONLINEAR_Y` | |
| `PauseOutside` | `BP_STOP_OUTSIDE` | regName changed from `PauseOutside` to `StopOutside` in v6 — **map by enum, not regName** |
| `BackoffButton` | `BP_BACKOFF_BUTTON` | |
| `TwoButtonReverse` | `BP_TWOBUTTON_REVERSE` | |
| `TwoButtonInvertDouble` | `BP_2B_INVERT_DOUBLE` | |
| `SlowStart` | `BP_SLOW_START` | |
| `CopyOnStop` | `BP_COPY_ALL_ON_STOP` | regName changed — **map by enum** |
| `SpeakOnStop` | `BP_SPEAK_ALL_ON_STOP` | regName changed — **map by enum** |
| `SpeakWords` | `BP_SPEAK_WORDS` | |
| `SlowControlBox` | `BP_SLOW_CONTROL_BOX` | |

**Long (50+ parameters):** All surviving `LP_*` parameters with
unchanged `regName` and compatible semantics. Notable examples:

| v5 regName | v6 enum | Notes |
|---|---|---|
| `MaxBitRateTimes100` | `LP_MAX_BITRATE` | The most important migration value |
| `UniformTimes1000` | `LP_UNIFORM` | |
| `LMAlpha` | `LP_LM_ALPHA` | |
| `LMBeta` | `LP_LM_BETA` | |
| `LMMaxOrder` | `LP_LM_MAX_ORDER` | |
| `Zoomsteps` | `LP_ZOOMSTEPS` | |
| `NodeBudget` | `LP_NODE_BUDGET` | |
| `DasherFontSize` | `LP_DASHER_FONTSIZE` | **See transformation below** |
| `ScreenOrientation` | `LP_ORIENTATION` | |
| `LineWidth` | `LP_LINE_WIDTH` | |
| `MarginWidth` | `LP_MARGIN_WIDTH` | |
| `TargetOffset` | `LP_TARGET_OFFSET` | |

**String (7 parameters):**

| v5 regName | v6 enum | Notes |
|---|---|---|
| `AlphabetID` | `SP_ALPHABET_ID` | |
| `ColourID` | `SP_COLOUR_ID` | Empty string in v5 → leave as v6 default |
| `DasherFont` | `SP_DASHER_FONT` | Font may not exist on v6 system — see "Fonts" |
| `GameTextFile` | `SP_GAME_TEXT_FILE` | |
| `InputFilter` | `SP_INPUT_FILTER` | |
| `InputDevice` | `SP_INPUT_DEVICE` | Case difference: v5 "Mouse Input" vs v6 "Mouse input" |
| `Alphabet1`–`Alphabet4` | `SP_ALPHABET_1`–`SP_ALPHABET_4` | Recently-used alphabet history |

#### Transformations required

**1. `DasherFontSize` (v5 index → v6 points)**

v5 used a small integer index (0=small, 2=medium, 4=large). v6 uses
absolute point size (8–72). Mapping:

| v5 value | v6 value | Meaning |
|---|---|---|
| 0 | 14 | Small |
| 1 | 18 | Medium-small |
| 2 | 22 | Medium (v5 default) |
| 3 | 28 | Medium-large |
| 4 | 36 | Large |
| ≥5 | min(v5 × 8, 72) | Clamp |

**2. Start mode booleans → enum**

v5 had separate booleans `StartOnMousePosition` and `CircleStart`. v6
consolidated these into `LP_START_MODE`:

| v5 state | v6 `LP_START_MODE` value |
|---|---|
| `CircleStart=True` | `circle_start` (2) |
| `StartOnMousePosition=True` | `mouse_pos_start` (1) |
| Both false | `none` (0) |

**3. Button assignments (6 strings → 1)**

v5 stored `Button0`–`Button4`, `Button10` as separate string params. v6
uses a single `SP_BUTTON_MAPPINGS` (`ButtonMap`). Migration packs them
into the v6 format (exact serialization TBD by DasherCore).

**4. `ColourID` empty string**

v5 stored `""` for default colour. v6 uses `"Default"`. Map empty →
`"Default"`.

**5. Removed parameters (silently dropped)**

These v5 parameters have no v6 equivalent and are silently ignored:

- `BP_MOUSEPOS_MODE` → migrated as `LP_START_MODE` (see above)
- `BP_CIRCLE_START` → migrated as `LP_START_MODE` (see above)
- `BP_SOCKET_DEBUG`, `BP_GLOBAL_KEYBOARD` — dropped
- `LP_YSCALE` — dropped
- `SP_CONTROL_BOX_ID` — ControlManager now uses `control.xml`
- `SP_SOCKET_INPUT_X_LABEL`, `SP_SOCKET_INPUT_Y_LABEL` — dropped
- `SP_JOYSTICK_DEVICE` → replaced by `SP_JOYSTICK_XAXIS` + `SP_JOYSTICK_YAXIS`
- All platform-only UI settings (window position, edit font, etc.)

### Unsupported but tracked features

Some v5 settings cannot be migrated because v6 does not yet implement
the feature. These should be surfaced in Settings > Migration as
"planned for a future update" so users know they haven't been
permanently removed.

In practice, v5's settings UI was very limited — most users only
changed a handful of values (alphabet, speed, colour, control mode).
The settings XML contains many values but most were never exposed in
the v5 preferences panel and remain at their defaults. The main
categories of genuinely-missing functionality are:

| v5 feature | Status in v6 | Migration action | Future plan |
|---|---|---|---|
| Custom control trees (`control.*.xml`) | Same DTD — fully compatible | Copy as-is | N/A (already works) |
| Socket/network input | Not implemented | Skip | Future RFC for network input |
| Joystick device path | Replaced by axis-based config | Skip | Implement when joystick support is added |
| Window position / fullscreen | OS-managed in v6 | Skip | N/A (different paradigm) |
| Custom edit/output fonts | Only Dasher canvas font is configurable | Import `DasherFont` only | Add output font selection later |
| Game mode help settings | Game mode exists but help drawing differs | Import what we can | Align game mode features in future |
| Button scan time / menu boxes | Button modes exist but scan UI differs | Import what we can | Verify button mode parity |

The migration report should list these as "Not yet available" rather
than silently dropping them. This transparency builds trust with
long-time users who may be looking for specific functionality.

### Custom user data migration

#### What to copy

From the v5 user data directory, copy these file patterns:

| Pattern | Destination | Purpose |
|---|---|---|
| `alphabet.*.xml` | v6 user data dir | Custom alphabet definitions |
| `colour.*.xml` | v6 user data dir | Custom colour palettes |
| `control.*.xml` | v6 user data dir | Custom control trees (same DTD, fully compatible) |
| `training_*.txt` | v6 user data dir | Adaptive training text |

#### v5 user data directory locations

| Platform | v5 path | v6 path |
|---|---|---|
| Windows | `%APPDATA%\dasher.rc\` | `%APPDATA%\Dasher\` (TBD) |
| macOS | `~/Library/Application Support/Dasher/` | Same (no change needed) |
| Linux | `~/.dasher/` | `~/.local/share/Dasher/` (TBD, XDG compliant) |

#### Colour XML compatibility

v5 colour XML uses `<colours>` root with `<palette>` / `<colour>` tags.
DasherCore v6's `CColorIO::Parse` supports both the legacy `<colours>`
spelling and the new `<colors>` spelling. No transformation needed.

#### Control XML compatibility

v5 and v6 control XML use the **same DTD** (verified: `control.dtd` is
byte-identical between versions). The same elements are supported:
`<node>`, `<stop/>`, `<pause/>`, `<move>`, `<delete>`, `<speak/>`,
`<copy/>`, `<ref>`, `<root/>`, `<alph/>`. v6's ControlManager is a
rewrite of v5's CControlBoxIO, but the XML format was preserved for
backward compatibility. v6 adds the ability to register custom actions
via `dasher_register_action()`, but all v5 action elements parse
correctly.

**v5 control XML files should be migrated as-is.** No transformation
needed. The only caveat: any v5 files with stray syntax errors (e.g.,
Steve Saling's file has a leftover `-->` on the last line) should be
cleaned up or tolerated by the parser.

#### Fonts

If `DasherFont` references a font that was bundled with v5 (e.g.,
"Alaska", "CG Omega"), v6 should check if the font exists on the
system. If not, fall back to the v6 default font and log a warning.
Custom `.ttf` files in the v5 user data directory should be offered
for installation but NOT auto-installed (security/permission concerns).

### Migration flow

The migration is **opt-in, not automatic**. On first launch, if v5 data
is detected, the user sees a prompt offering to import. If they decline,
they can re-run the migration later from Settings.

```
On first launch of v6:

  1. Check: has migration already been offered?
     - Read UserDefaults "dasher.v5_migration_offered"
     - If true → skip detection entirely

  2. Detect: is v5 data present?
     - macOS: Does ~/Library/Preferences/uk.ac.cam.phy.inference.dasher.plist exist?
     - Windows: Does %APPDATA%\dasher.rc\settings.xml exist?
     - Linux: Does ~/.dasher/settings.xml exist?
     - If no v5 data found → set "dasher.v5_migration_offered" = true, skip

  3. Show migration prompt:
     ┌──────────────────────────────────────────────┐
     │  Dasher 5 settings found                      │
     │                                                │
     │  We found your Dasher 5 configuration          │
     │  (alphabet, colours, speed, and custom         │
     │  files). Would you like to import these        │
     │  settings into Dasher 6?                       │
     │                                                │
     │  Summary of what was found:                    │
     │    • Alphabet: "English with everything..."    │
     │    • Speed: 7.0x                               │
     │    • 2 custom alphabet files                   │
     │    • 1 custom colour palette                   │
     │    • Control mode: enabled                     │
     │                                                │
     │  Some Dasher 5 features are not yet            │
     │  available in Dasher 6 (see Settings >         │
     │  Migration for details).                       │
     │                                                │
     │     [Import settings]    [Not now]             │
     └──────────────────────────────────────────────┘

  4a. If "Import settings":
     a. Read all v5 parameter values
     b. Transform and apply each mapped parameter via dasher_set_*_parameter()
     c. Copy custom user data (alphabet/colour/control/training files)
     d. Set "dasher.v5_migration_completed" = true
     e. Set "dasher.v5_migration_offered" = true
     f. Show success banner: "Your settings have been imported."
        + list any items needing attention (e.g., "Custom font 'Alaska'
          was not found — install it separately or choose a new font.")

  4b. If "Not now":
     a. Set "dasher.v5_migration_offered" = true
     b. Continue with v6 defaults
     c. Migration remains available in Settings > Migration

  5. In all cases, call dasher_save_settings() to persist.
```

### Settings > Migration panel

A dedicated section in Settings allows users to:

1. **Re-run migration**: If the user declined initially, they can
   trigger it here at any time. Shows the same detection summary.
2. **View migration report**: After migration, shows what was imported
   and what was skipped, with explanations for skipped items.
3. **See unsupported v5 features**: A list of v5 settings that have no
   v6 equivalent yet, flagged as "coming in a future update." This sets
   expectations and helps users understand what's different.

```
Settings > Migration

  ── Dasher 5 Import ──────────────────────────

  Status: Not imported (Dasher 5 data detected)

  Found:
    • Alphabet: "English with everything incl Emojis"
    • Colour palette: "EurasianDarkMode"
    • Speed: 7.0x (MaxBitRateTimes100 = 700)
    • Control mode: enabled
    • Turbo mode: enabled
    • 2 custom XML files

  [Import from Dasher 5]

  ── Unsupported in Dasher 6 ──────────────────

  These Dasher 5 settings will not be imported because
  Dasher 6 does not yet support them:

  • Custom control trees (control XML)
    → Planned: Dasher 6 has a new control system; custom
      trees need to be recreated.
  • Custom fonts (Alaska, CG Omega)
    → Install fonts separately, then select in Settings.
  • Window position / full screen
    → Managed by the OS window manager in Dasher 6.
```

### Timing

Migration must run **before** `dasher_set_screen_size()` (which triggers
`Realize()` and starts the engine). The flow is:

1. `dasher_create()` — engine created but not realised
2. **Migration runs here** — reads v5 data, calls `dasher_set_*_parameter()`
3. `dasher_set_screen_size()` — engine realises with migrated settings
4. UI renders with the user's familiar configuration

### Per-platform implementation notes

#### Apple (Dasher-Apple)

**Scope: macOS only.** iOS and visionOS are excluded:
- **iOS**: v5 iOS used a different bundle ID (`org.uk.acecentre.dasher`)
  and stored data in the app sandbox. Sandboxed apps cannot read another
  app's container, so migration from a v5 iOS install is not possible
  without user-initiated file sharing.
- **visionOS**: No v5 predecessor exists.

The migration code lives in `DasherShared/` and runs only on macOS.

- Read `~/Library/Preferences/uk.ac.cam.phy.inference.dasher.plist`
  via `NSDictionary(contentsOfFile:)`.
- Copy files from `~/Library/Application Support/Dasher/` (same path
  in v6 — no directory change needed).

The migration is triggered from the app's `init()` before the engine is
created, or from a dedicated `MigrationService` called during launch.

#### Windows (Dasher-Windows)

**Scope: Windows (confirmed).**

- Read `%APPDATA%\dasher.rc\settings.xml` (XML parsing).
- Copy files from `%APPDATA%\dasher.rc\` to the v6 user data directory.
- Also check `C:\Program Files (x86)\Dasher\Dasher 5.00\system.rc\` for
  custom alphabet/colour files that the user may have installed into the
  system directory (as documented in Steve Saling's README). These should
  be copied to the v6 user data directory, not the install directory.

#### GTK (Dasher-GTK)

**Scope: Deferred — needs investigation.**

Linux/GTK paths and settings format have not yet been verified against
the v5 GTK source code. The expected paths are:
- Settings: `~/.dasher/settings.xml` (same XML format as Windows)
- User data: `~/.dasher/`

However, v6 GTK does not yet exist, so this section will be completed
when a GTK frontend is under development. The XML format is identical to
Windows, so the migration logic can be shared once paths are confirmed.

### Steve Saling case study

Steve Saling's configuration (from `DasherSmoothSaling/`) illustrates a
real-world migration:

| v5 setting | v5 value | v6 action |
|---|---|---|
| `AlphabetID` | `English with everything incl Emojis` | Set SP_ALPHABET_ID — alphabet XML must be imported |
| `ColourID` | `EurasianDarkMode` | Set SP_COLOUR_ID — colour XML must be imported |
| `ControlBoxID` | `!Spk-Del-Mov-Stp` | Set BP_CONTROL_MODE = true — control XML copied as-is |
| `DasherFont` | `Alaska` | Set SP_DASHER_FONT — font TTF must be installed separately |
| `MaxBitRateTimes100` | `700` | Set LP_MAX_BITRATE = 700 (7.0x speed) |
| `ControlMode` | `True` | Set BP_CONTROL_MODE = true |
| `CopyOnStop` | `True` | Set BP_COPY_ALL_ON_STOP = true |
| `TurboMode` | `True` | Set BP_TURBO_MODE = true |
| `CircleStart` | `True` | Set LP_START_MODE = circle_start |
| `DasherFontSize` | `4` | Set LP_DASHER_FONTSIZE = 36 (large) |

Custom files to import:
- `alphabet.englishSS.xml` → v6 user data dir
- `colour.euroasian4.xml` → v6 user data dir
- `control.Spk-Del-Mov-Stp.xml` → v6 user data dir (compatible, minor cleanup of stray `-->`)
- `Fonts/*.ttf` → user must install manually (or we bundle Alaska/CG Omega)

## Drawbacks

- **Complexity**: 100+ parameter mappings, platform-specific file paths,
  and edge cases (font size transformation, start mode consolidation)
  make this a substantial implementation effort.
- **Incomplete migration**: Some platform-specific settings (window
  position, socket input, joystick device paths) cannot be migrated
  because v6 doesn't implement those features yet. The migration report
  mitigates this by being transparent about what was skipped and why.
  Control XML, alphabets, and colour palettes are fully compatible.
- **Font dependency**: Users with custom fonts (Alaska, CG Omega) will
  see a font fallback unless they install the TTFs separately. We could
  bundle common v5 fonts, but licensing is unclear.
- **Opt-in friction**: Users who click "Not now" and then later want
  their old settings need to find the Settings > Migration panel. This
  is discoverable but adds a step.

## Alternatives considered

### A. No migration

Start everyone from defaults. Simple, but unacceptable for users who
have spent years tuning their configuration. Would severely harm v6
adoption among the existing user base.

### B. Manual export/import

Provide a "Export settings" button in v5 and an "Import settings" button
in v6. Users would need to run both versions. This requires users to
have v5 still installed and functional, and adds friction. Many users
will upgrade (or have v5 upgraded for them) without knowing about this
step.

### C. Cloud sync

Store settings in the cloud and sync between v5 and v6. Overkill for a
text-entry tool, requires infrastructure, and raises privacy concerns
(especially for an AAC tool used by people with disabilities).

### D. Settings file format compatibility

Make v6 read `settings.xml` directly (for Windows/Linux) or the v5
plist (for macOS). This avoids a migration step but couples v6 to v5's
storage format indefinitely. The one-shot migration approach is cleaner
because it allows v6 to evolve its storage independently.

## Prior art

- **macOS app migrations**: Many macOS apps perform one-shot migrations
  from predecessor plist domains when the bundle ID changes (e.g.,
  1Password, TextExpander). The pattern is: check for old plist, import,
  mark as done.
- **Windows app migrations**: Office, Visual Studio, and Adobe Creative
  Cloud all detect previous versions and offer to import settings.
- **Dasher v4 → v5**: Historical context suggests v4 to v5 did NOT have
  an automated migration (users had to reconfigure). This was a common
  complaint.
- **Browser migrations**: Firefox, Chrome, and Safari all detect each
  other and offer to import bookmarks/history on first launch — a very
  similar UX pattern.

## Unresolved questions

1. **Where does v6 store user data on Windows?** The RFC proposes
   `%APPDATA%\Dasher\` but this should be confirmed. Windows convention
   is `%LOCALAPPDATA%\Dasher\` for per-machine data.

2. **Should we bundle common v5 fonts?** Steve Saling uses "Alaska" and
   "CG Omega". If these are freely redistributable, bundling them would
   make the migration seamless. Licensing needs checking.

3. **Should the migration be re-runnable?** The RFC proposes an opt-in
   migration with a Settings > Migration panel for re-import. Should
   there be a limit on re-runs?

4. **GTK/Linux paths**: Need to verify `~/.dasher/` is still correct and
   determine where v6 GTK should store user data (XDG `~/.local/share/Dasher/`?).
   Deferred until GTK frontend exists.

5. **v5 colour index semantics**: v6 may have changed colour index
   assignments. If a user's custom colour XML assigns specific indices
   (e.g., index 10 = green for letters), do these still map correctly
   in v6's rendering engine?

6. **Adaptive training privacy**: The training file contains text the
   user has typed. Migrating it is essential for prediction quality but
   means copying potentially sensitive text. Should we warn the user?

## Resolution

_(To be filled in after community discussion.)_
