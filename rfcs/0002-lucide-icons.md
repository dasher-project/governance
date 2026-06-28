---
rfc: 0002
title: Adopt Lucide as the cross-platform icon set
status: proposed
platforms: [apple, windows, gtk, android]
created: 2026-06-17
updated: 2026-06-28
---

# Adopt Lucide as the cross-platform icon set

## Summary

Standardise all Dasher v6 frontends on **[Lucide](https://lucide.dev/)** — an
ISC-licensed, community-maintained icon library of 1,400+ icons — as the single
source of UI iconography across Apple, Windows, and GTK. Each platform uses the
appropriate Lucide package: `lucide-icons-swift` (Apple SPM),
`Lucide.Avalonia` (Windows NuGet), and the Lucide TTF font (GTK/Pango).

## Motivation

Today, Dasher's frontends each use different icon sources (or none at all):

- **Apple** mixes SF Symbols and hand-rolled `systemImageNamed:` calls.
- **Windows** uses Avalonia's built-in `Geometry`/`PathIcon` data — some
  hand-authored, some from MaterialDesignIcons.
- **GTK** has no standardised icon set; buttons use GTK stock icons or text
  labels.

This creates three problems:

1. **Inconsistent visual identity** — the same action looks different on each
   platform, undermining cross-platform brand cohesion documented in the
   [design guide](https://github.com/dasher-project/dasher-design-guide).
2. **Maintenance burden** — icon updates, additions, and accessibility
   auditing must be repeated three times in three formats.
3. **Platform lock-in** — SF Symbols is Apple-only; Material Symbols is
   Android/web-oriented. Neither works across all three Dasher platforms.

Lucide solves all three: one library, one visual language, three native
packages, ISC licence.

## Detailed design

### Icon set

**Lucide** (<https://lucide.dev/>) — fork of Feather Icons, expanded to 1,400+
icons. ISC licence (permissive, GPL-compatible, no attribution required in
binary).

Properties:

- Uniform 24×24 grid, 2px stroke, rounded corners.
- Optimised for UI at 16–48px display sizes.
- Tree-shakeable in all three package formats (only referenced icons are
  bundled).

### Per-platform integration

#### Apple (Dasher-Apple)

**Package:** [`lucide-icons-swift`](https://github.com/JakubMazur/lucide-icons-swift)

- SPM dependency: `https://github.com/JakubMazur/lucide-icons-swift` (from
  `main` or a tagged release).
- Usage: `Image(lucide: "settings")` in SwiftUI; UIKit bridging available.
- Replaces: all `UIImage(systemName:)` / `Image(systemName:)` calls in toolbar,
  status bar, sidebar, settings, and onboarding views.
- SF Symbols may still be used as a fallback for icons not yet in Lucide, but
  new icons must use Lucide.

#### Windows (Dasher-Windows, Avalonia UI)

**Package:** [`Lucide.Avalonia`](https://github.com/lucide-icons/lucide-avalonia)

- NuGet dependency: `Lucide.Avalonia`.
- Usage: `<lucide:LucideImage Icon="Settings" />` in AXAML.
- Replaces: existing `PathIcon` / `StreamGeometry` definitions in
  `MainWindow.axaml`, `SettingsWindow.axaml`, and all toolbar/data templates.
- Fallback: Avalonia `MaterialIcon` types can remain temporarily where no Lucide
  equivalent exists; log missing icons for migration tracking.

#### GTK (Dasher-GTK, gtkmm)

**Package:** Lucide TTF font
([`lucide-static-font`](https://github.com/lucide-icons/lucide/tree/main/packages/lucide-static-font))

- Bundled asset: `lucide.ttf` in `resources/icons/`.
- Integration: Load as a `Pango::FontDescription`, then render icon glyphs via
  their Unicode codepoints (each Lucide icon maps to a private-use-area
  codepoint in the font).
- Usage: `Gtk::Image` with a `Pango` layout using the Lucide font + codepoint,
  or a small helper `makeIcon("settings", 24)` that returns a `Glib::RefPtr<Gdk::Pixbuf>`.
- Replaces: existing `Gtk::StockID` usage and `gtkmm` built-in icon lookups.

### Icon-to-action mapping

The design guide defines the canonical mapping:

| Action | Lucide name |
| --- | --- |
| New (reset) | `file-plus` |
| Open | `folder-open` |
| Save | `save` |
| Play | `play` |
| Pause | `pause` |
| Position | `flip-horizontal` |
| Prefs | `settings` |
| Copy | `copy` |
| Copy All | `clipboard-copy` |
| Paste | `clipboard-paste` |
| Quick Speak | `volume-2` |
| Control Mode | `mouse-pointer-click` |
| Game Mode | `gamepad-2` |
| Alphabet | `languages` |
| Speed | `gauge` |
| Learning | `brain-circuit` |

Additional icons may be added by frontend maintainers as needed; the design
guide is the SSOT for the canonical set.

### Sizing and theming

- Icon render size: **24px**, centred in the standard 48px touch target.
- Stroke colour:
  - **Default:** Deep Navy (`#00304E`).
  - **Active / hover:** Dasher Teal (`#35A7C4`).
  - **Disabled:** 40% opacity of default.
- No coloured icon fills — single-stroke monochrome only, consistent with
  Lucide's design language.

### Migration approach

Each frontend adopts Lucide independently (no flag day). Per-platform issues
track progress:

1. Add the dependency.
2. Introduce a helper/wrapper so icon names are type-checked.
3. Replace existing icons screen-by-screen.
4. Remove old icon assets and dependencies.

No DasherCore changes are required — this is a pure frontend concern.

## Drawbacks

- **Adds a third-party dependency** to each frontend. Lucide is actively
  maintained, but project-level vetting is still needed.
- **`lucide-icons-swift` is community-maintained** (not the official Lucide
  org). If it goes unmaintained, we may need to fork or find an alternative SPM
  package. Risk is low (the package is a thin wrapper around the SVG sources).
- **GTK TTF approach** is less ergonomic than native icon packages — a helper
  function is needed, and there's no compile-time icon-name checking.
- **Bundle size** increases slightly (the Lucide font is ~150 KB TTF; Swift
  package ships only referenced icons).

## Alternatives considered

### SF Symbols (Apple only)

Apple's native icon set. Excellent on Apple platforms, but:
- Not available on Windows or GTK.
- Apple could restrict its usage or change the library at any time.
- Creates a visual split: Apple looks like macOS, others look different.

### Material Symbols (Google)

- Cross-platform via fonts, but oriented toward Material Design's visual
  language, which doesn't match Dasher's teal/navy palette as cleanly.
- Stroke weight is variable (can be inconsistent at small sizes).
- Google-licenced (Apache 2.0) — slightly more complex than ISC.

### Tabler Icons

- Similar to Lucide (open source, stroke-based, MIT licence).
- More icons (~4,000 vs Lucide's 1,400+, though both are large).
- Less adoption / smaller community.
- No ready-made Avalonia package.

### Keep per-platform icons

Status quo. Rejected because it perpetuates the visual inconsistency and
maintenance burden described in Motivation.

## Prior art

- **VS Code** uses its own icon set (Codicons) for this same reason — visual
  consistency across Electron (Windows/macOS/Linux).
- **Element (Matrix client)** uses a shared icon set across its iOS, Android,
  and web frontends.
- **v5 Dasher** used platform-native icons everywhere, contributing to the
  "feels different on every platform" problem that the v6 design guide
  explicitly aims to fix.

## Unresolved questions

1. **`lucide-icons-swift` maintainership** — should we pin to a specific tagged
   release or track `main`? Should we consider forking preemptively?
2. **Accessibility labels** — should icon `aria-label` / accessibility
   identifier be derived from the Lucide icon name, or maintained separately?
3. **Dark mode** — Lucide icons are monochrome so theming is straightforward,
   but do we need separate "filled" variants for active states (e.g., solid
   play vs outline play)?
4. **visionOS** — does `lucide-icons-swift` render correctly in visionOS
   windows, or do we need SF Symbols as a visionOS-specific fallback?

## Resolution

_(To be filled in after community discussion.)_
