---
rfc: 0003
title: Multilingual UI support across all frontends
status: proposed
platforms: [apple, windows, gtk, core]
created: 2026-06-17
updated: 2026-06-17
---

# Multilingual UI support across all frontends

## Summary

DasherCore already ships 33 locale files covering parameter labels, descriptions,
and enum values via a JSON runtime system (`dasher_set_locale`). However, every
frontend's own UI chrome (toolbar buttons, settings tabs, onboarding, dialogs)
is **hardcoded English** with no native localization wired up. This RFC
proposes a per-platform localization strategy for frontend strings so that
users get a fully localised experience — engine *and* UI — and aligns the
language picker so all 33 DasherCore locales are exposed everywhere.

## Motivation

### Current state (audited)

| Aspect | Dasher-Apple | Dasher-Windows | Dasher-GTK |
| --- | --- | --- | --- |
| **DasherCore i18n mechanism** | JSON runtime via C API | JSON runtime via C API (P/Invoke) | gettext `_()` in DasherCore — **domain never bound** |
| **Platform-native i18n used?** | No (`NSLocalizedString`/`.strings`/`.lproj` absent) | No (`.resx`/`.resw` absent) | No (`bindtextdomain`/`.po`/`.mo` absent) |
| **DasherCore locales shipped** | 33 `strings_*.json` | 33 `strings_*.json` | 1 `en_GB.po` (help text only, unused) |
| **Languages in UI picker** | 9 | 10 | 0 (no picker) |
| **What's localised?** | Parameter labels/descriptions only | Parameter labels/descriptions only | Nothing |

### Problems

1. **Only engine strings are localised.** Toolbar buttons, settings tab names,
   onboarding text, error messages, and dialog labels are all English literals
   in Swift / C# / C++ source. A user who selects French sees French parameter
   names inside an otherwise-English settings window.

2. **Language pickers are inconsistent.** Apple offers 9 locales, Windows
   offers 10 (different set), GTK offers none — despite all three shipping the
   same 33 DasherCore locale files.

3. **GTK has no translation infrastructure at all.** Its DasherCore branch
   uses the legacy gettext `_()` macro, but the gettext domain is never bound
   (`bindtextdomain` / `textdomain` are absent), so even engine strings render
   in English. The frontend itself has no `.po` files.

4. **RTL languages (Arabic, Persian, Urdu) need layout work.** These are in
   DasherCore's locale set but no frontend has RTL layout support.

5. **No community translation workflow.** There's no process for contributors
   to translate frontend strings or submit corrections to the LLM-generated
   DasherCore translations.

### Who feels the pain?

Dasher's user base is global — the engine supports writing in 100+ languages,
and the locale set covers major world languages. But a user who speaks only
Arabic or Hindi cannot navigate the settings UI in their language.

## Detailed design

### Principle: two layers, one locale

The user selects one language. Both layers localise from that single choice:

```
┌─────────────────────────────────────────────┐
│           Frontend UI strings               │  ← platform-native i18n
│  (toolbar, tabs, dialogs, onboarding)       │     (.xcstrings / .resx / gettext)
├─────────────────────────────────────────────┤
│         DasherCore strings                  │  ← dasher_set_locale()
│  (parameter labels, descriptions, enums)    │     (JSON runtime)
└─────────────────────────────────────────────┘
```

The frontend calls `dasher_set_locale(ctx, code)` **and** switches its own
native resource bundle to the same locale simultaneously.

### Canonical locale list

All frontends expose the **same 33 locales** as DasherCore. The list lives in a
single shared source so adding a DasherCore locale automatically propagates.

| Code | Endonym | RTL |
| --- | --- | --- |
| `af` | Afrikaans | |
| `ar` | العربية | ✓ |
| `bn` | বাংলা | |
| `cs` | Čeština | |
| `da` | Dansk | |
| `de` | Deutsch | |
| `el` | Ελληνικά | |
| `en` | English | |
| `es` | Español | |
| `fa` | فارسی | ✓ |
| `fi` | Suomi | |
| `fr` | Français | |
| `gu` | ગુજરાતી | |
| `hi` | हिन्दी | |
| `hu` | Magyar | |
| `it` | Italiano | |
| `kn` | ಕನ್ನಡ | |
| `ml` | മലയാളം | |
| `mr` | मराठी | |
| `nl` | Nederlands | |
| `pa` | ਪੰਜਾਬੀ | |
| `pl` | Polski | |
| `pt` | Português (Brasil) | |
| `pt-PT` | Português (Portugal) | |
| `ru` | Русский | |
| `sv` | Svenska | |
| `sw` | Kiswahili | |
| `ta` | தமிழ் | |
| `te` | తెలుగు | |
| `th` | ไทย | |
| `ur` | اردو | ✓ |
| `zh-CN` | 中文（简体） | |
| `zu` | isiZulu | |

The picker shows **endonyms** (native names), not English translations, sorted
alphabetically by endonym with English first.

#### Shared metadata

A small JSON file in DasherCore (e.g. `Strings/locales.json`) serves as the
canonical machine-readable list:

```json
[
  { "code": "en", "endonym": "English", "rtl": false },
  { "code": "ar", "endonym": "العربية", "rtl": true },
  ...
]
```

Each frontend reads this at build time (codegen) or runtime (bundled asset) so
the locale list stays in sync without manual updates.

### Per-platform frontend i18n

#### Apple (Dasher-Apple)

**Mechanism:** Apple-native **String Catalogs** (`.xcstrings`).

- Create `Localizable.xcstrings` in each target (DasherApp, DasherMac,
  DasherKeyboard, DasherVision).
- Use `String(localized:)` / `LocalizedStringKey` in SwiftUI views and
  `NSLocalizedString` in UIKit.
- Xcode auto-extracts strings from Swift source into the catalog.
- Ship `.lproj` folders for each locale, or use the single `.xcstrings` catalog
  (Xcode 15+ merges all languages into one file).
- **RTL:** Set `Environment(\.layoutDirection)` based on locale; SwiftUI handles
  mirroring automatically. UIKit needs `semanticContentAttribute`.

Migration steps:
1. Add `Localizable.xcstrings` to the Xcode project.
2. Wrap all hardcoded English string literals with `String(localized:)`.
3. Extract the initial English catalog via Xcode → Build → auto-extract.
4. Generate placeholder translations for the remaining 32 locales (reuse
   DasherCore's LLM pipeline or import from `strings_*.json` where keys overlap).
5. Replace the 9-locale hardcoded picker with a data-driven list from
   `locales.json`.

#### Windows (Dasher-Windows)

**Mechanism:** Avalonia **`.resx`** resource files + `CultureInfo` switching.

- Create `Resources.resx` (neutral/English) and `Resources.{locale}.resx` for
  each locale under `src/Dasher.Windows/Resources/`.
- Use `x:Static` markup extension in AXAML: `<TextBlock Text="{x:Static res:Resources.PlayButton}" />`.
- In code-behind: `Resources.PlayButton` (auto-generated `Resources.Designer.cs`).
- Switch culture at runtime: `Thread.CurrentThread.CurrentUICulture = new CultureInfo(code)`.
- Avalonia's `ResourceInclude` loads the correct satellite assembly automatically.
- **RTL:** Avalonia supports `FlowDirection="RightToLeft"` on any control.

Migration steps:
1. Add `.resx` files to the project with MSBuild resgen task.
2. Extract all hardcoded strings from AXAML and C# source into `Resources.resx`.
3. Create per-locale `.resx` files (LLM-assisted initial translations).
4. Replace the 10-locale hardcoded `Dictionary<string, string>` with a
   data-driven list from `locales.json`.
5. Wire `FlowDirection` binding for RTL locales.

#### GTK (Dasher-GTK)

**Mechanism:** **gettext** — the standard on the GNOME/Linux platform.

DasherCore's `_()` macro is already active in this build. The frontend needs to:

1. **Bind the text domain** at startup:
   ```cpp
   #include <libintl.h>
   #include <locale.h>

   setlocale(LC_ALL, "");
   bindtextdomain("dasher-gtk", LOCALEDIR);
   bind_textdomain_codeset("dasher-gtk", "UTF-8");
   textdomain("dasher-gtk");
   ```
2. **Create `.po`/`.pot` files** under a new `po/` directory:
   - `POTFILES.in` — list of source files with translatable strings.
   - `dasher-gtk.pot` — template generated by `xgettext`.
   - `dasher-gtk.{locale}.po` — per-locale translations.
   - `LINGUAS` — list of available locale codes.
3. **Wrap all frontend strings** in `_()`:
   - `set_title(_("Dasher v6"))` instead of `set_title("Dasher v6")`.
   - All `Gtk::Label`, `Gtk::Button`, menu items, tooltips.
4. **CMake integration** to compile `.po` → `.mo` at build time and install to
   `$(localedir)/{locale}/LC_MESSAGES/dasher-gtk.mo`.
5. **Add a locale picker** in Preferences (currently absent) that calls
   `setlocale(LC_ALL, code)` and refreshes the UI, plus `dasher_set_locale()`
   for engine strings.
   - **Note:** GTK frontend does NOT currently use the C API. To localise
     DasherCore parameter strings, it either needs to (a) adopt the C API
     (`dasher_set_locale`), or (b) properly bind DasherCore's own gettext
     domain (`bindtextdomain("dasher", ...)`) so the `_()` calls in DasherCore
     resolve to translations. Option (b) requires DasherCore to ship `.po` files,
     which it currently doesn't — the JSON system replaced them. **Option (a)
     is recommended.**
6. **RTL:** GtkWindow respects `GtkWidget::default-text-direction`. Set
   `Gtk::TextDirection::RTL` for RTL locales.

### Locale picker UX

All frontends present the language picker in the same location within the
settings UI (Output tab, under a "Language" subgroup), showing endonyms.
On change:

1. Call `dasher_set_locale(ctx, code)` (engine layer).
2. Switch the platform-native resource culture (frontend layer).
3. Refresh/rebuild the settings UI so all visible text updates.
4. Persist the choice in the app's preferences store.
5. On next launch, detect system locale and default to it (if supported).

### RTL support

For `ar`, `fa`, `ur`:

- **Layout mirroring:** Toolbar, status bar, and sidebar mirror horizontally.
- **Canvas position:** The canvas "position" setting (Left/Right/Top/Bottom)
  should respect the layout direction — a right-handed Arabic user expects the
  canvas on the right side by default.
- **Text alignment:** All labels, buttons, and text fields use natural
  alignment for the script.
- **Canvas glyphs:** The Dasher canvas itself is not affected — text composition
  direction is determined by the alphabet model, not the UI locale. An Arabic
  alphabet model already produces RTL text output inside the canvas.

### Translation workflow

#### Initial translations

DasherCore's 33 locale files were generated via Google LLM (July 2025). For
frontend strings, we can:

1. Extract all UI strings into the platform-native catalog (`.xcstrings` /
   `.resx` / `.pot`).
2. Run the same LLM pipeline to produce initial translations for all 32
   non-English locales.
3. Mark machine-translated entries as `fuzzy` (gettext) or `state: translated
   (needs review)` (`.xcstrings`) so human reviewers know to verify.

#### Community contributions

- **Apple:** `.xcstrings` is diff-friendly; translators submit PRs with updated
  JSON.
- **Windows:** `.resx` is XML; translators submit PRs per locale.
- **GTK:** Standard `.po` workflow; translators use Poedit/Weblate/GitHub PRs.
- **DasherCore:** JSON `strings_{locale}.json`; same PR workflow.

A `TRANSLATORS.md` file in each repo documents how to contribute.

#### Shared string bank

Many UI strings are identical across platforms (e.g. "Play", "Pause", "Copy",
"Settings"). To reduce duplication:

- Maintain a **shared English string bank** in the design guide
  (`design-guide/strings.md`) that lists canonical UI strings with IDs.
- Each platform maps its native resource key to the same ID.
- Translators can work from a single English source and apply to their
  platform's format.

This is optional / aspirational — the priority is getting the per-platform
infrastructure in place first.

## Drawbacks

- **Initial effort is significant.** Wrapping every UI string in each frontend,
  generating 32 locale files, and testing RTL is substantial work.
- **Machine translation quality.** LLM-generated translations for 33 languages
  will have errors. Some languages (Zulu, Swahili, smaller Indic languages) may
  need expert review that's hard to source.
- **Ongoing maintenance.** Every new UI string needs translations in 32
  languages. Without a translation platform (Weblate, Crowdin), this falls on
  contributors to keep up.
- **Apple String Catalogs require Xcode 15+.** Older toolchains won't support
  `.xcstrings` (minor concern — current builds use recent Xcode).
- **GTK gettext adoption adds build complexity** (CMake gettext macros,
  `.mo` install paths).

## Alternatives considered

### Single cross-platform translation format (e.g. all gettext)

Could standardise all three frontends on gettext `.po` files, then convert to
native formats at build time. Rejected because:

- Apple strongly favours `.xcstrings` for tooling integration (Xcode
  auto-extraction, App Store localisation review).
- Windows/.NET favours `.resx` for designer support and MSBuild integration.
- Forcing gettext on platforms that have better native tooling creates friction.

### Web-based translation platform (Weblate / Crowdin / Pontoon)

Host all translations in a platform that exports to each format. This is a good
**future** option but adds hosting cost and a dependency. For now, GitHub PRs
with native formats are sufficient for a small community. Can revisit once
translation volume grows.

### English-only with system locale for engine only

Keep frontend UI in English, only localise DasherCore parameters. Rejected
because this creates a jarring half-localised experience (French parameter
names in an English settings window).

### Don't expose all 33 locales in the picker

Only show locales that have complete frontend translations. Rejected because
DasherCore already has all 33 — showing them costs nothing, and partial
translation (engine localised, some UI localised) is still better than none.
Frontends fall back to English per-string, so incomplete translations degrade
gracefully.

## Prior art

- **Dasher v5** shipped platform-native localisation: macOS had `.strings`/`.lproj`
  in many languages; Windows had `.resx`; GTK used gettext with community `.po`
  files. The v6 rewrite lost this by using hardcoded strings.
- **GIMP / Inkscape / GNOME apps** — all use gettext + `.po` with large community
  translation teams.
- **Signal** — uses a shared translation bank (`.json`) that generates
  platform-specific resource files via a build script.

## Unresolved questions

1. **GTK C API adoption** — Should GTK switch to the C API (`dasher_set_locale`)
   for engine strings, or should DasherCore re-generate gettext `.po` files
   alongside the JSON files? The C API route is recommended but requires GTK to
   call through `dasher.h` instead of linking C++ classes directly.

2. **Translation quality bar** — Do we ship machine translations immediately
   (marked fuzzy), or wait for human review per language? What's the threshold
   for "good enough" to appear in a release?

3. **Locale vs. alphabet model** — The UI locale (interface language) and the
   Dasher alphabet model (text output language) are independent. Should changing
   the UI locale auto-suggest a matching alphabet model? (e.g., selecting French
   suggests the French alphabet.) Or keep them fully decoupled?

4. **Plural forms** — Some languages (Arabic, Russian, Polish) have complex
   plural rules. Do any frontend strings need plural-aware translation? Most UI
   strings are labels ("Play", "Copy") not count-based ("3 files"), so this may
   be a non-issue, but onboarding/error messages could need it.

5. **Keyboard extension (iOS)** — The DasherKeyboard target has its own UI.
   Does it share the same `.xcstrings` as the main app, or need a separate catalog?

## Resolution

_(To be filled in after community discussion.)_
