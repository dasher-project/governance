---
rfc: 0016
title: Report the app version in Settings (Privacy tab for now)
status: active
platforms: [apple, windows, gtk, android, web]
created: 2026-08-22
updated: 2026-08-22
---

# Report the app version in Settings (Privacy tab for now)

## Summary

Every Dasher v6 frontend displays its **application version** in its settings
UI so a user can say exactly which build they are running. Until a dedicated
About section exists (see RFC 0006), the version line lives at the bottom of
the existing **Privacy** tab — the tab every frontend already ships for the
analytics opt-in.

## Implementation status

| Platform | State | Notes |
| --- | --- | --- |
| Dasher-GTK | Implemented | `Preferences → Privacy`, `DASHER_GTK_VERSION` compile definition (same source analytics already uses). |
| Dasher-Android | Implemented | `Settings → Privacy`, `BuildConfig.VERSION_NAME` (same source analytics already uses). |
| Dasher-Windows | Implemented | `Settings → Privacy`, bottom line; `UpdateChecker.GetCurrentVersion()` — the same source analytics and update checks already use. |
| Dasher-Apple | Issue filed | Version exists in analytics; needs the Settings row (macOS/iOS/visionOS). |
| dasher-web | Issue filed | Needs the row in its settings surface. |

## Motivation

User reports arrive without build information. In August 2026 a Windows user
emailed feedback about "the new build"; correlating her two reports with the
release list required guessing between v0.1.14 and v0.1.15 (the answer changed
the diagnosis — the versions were functionally identical, which ruled out a
regression). Every support conversation starts better with "what version are
you on?" answerable from the app itself, and users on packaged installs
(Flatpak, AppImage, store builds, self-builds) frequently do not know.

The version is also the natural anchor for the rest of the support story:
crash reports already carry `app_version` (RFC 0001/0009), and the
update-check UI knows a version. This RFC makes the same value visible to the
human.

## Detailed design

- **Content:** one plain, non-interactive line at the bottom of the Privacy
  tab, e.g. `Dasher 0.2.2` (GTK), `Dasher 0.1.0` (Android). The frontend's
  user-facing name plus its version string — nothing else.
- **Source of truth:** the same version identifier the frontend already
  reports elsewhere, so the UI can never disagree with analytics or crash
  reports:
  - GTK: `DASHER_GTK_VERSION` compile definition (set in CMake, consumed by
    `CrashReporter.cpp`).
  - Android: `BuildConfig.VERSION_NAME` (consumed by `AnalyticsService`).
  - Windows: the assembly/package version used by the updater.
  - Apple: `CFBundleShortVersionString` / the value the analytics layer sends.
- **Placement for now:** bottom of the Privacy tab — it exists on every
  frontend already (analytics opt-in), needs no new navigation, and the
  version is arguably relevant there ("what did I consent to, on what
  build?"). This is explicitly **interim**: when RFC 0006's About section
  lands, the line moves there and this RFC's placement clause is retired (edit
  in place per the RFC-editing rules).
- **Not in scope:** engine (DasherCore) version display. Frontends pin
  different submodule commits between releases; surfacing that usefully needs
  an engine-side version API (see Unresolved questions).

## Drawbacks

- Privacy is not the semantically obvious home for a version line; it's a
  pragmatic squat until About exists.
- One more thing every frontend must remember to keep wired (mitigated: the
  value comes from the existing analytics version constant, so it updates
  itself with the release process).

## Alternatives considered

- **Dedicated About section now.** Better end state, but it's RFC 0006
  territory (settings IA) and shouldn't block the immediate support need.
- **Window title / menu only.** Not discoverable on mobile/keyboard
  extensions, and window chrome is absent in IME contexts.
- **Nowhere — rely on the store/package manager.** Fails exactly when we need
  it: Flatpak/AppImage side-by-side installs, self-builds, APKs shared
  directly with testers.

## Prior art

- Every browser's `settings → About` line; used as the canonical first
  question of web support for decades.
- Android system settings "App info" (not reachable enough from inside an
  app's own support flow).
- v5 showed version in its about dialogue — parity restoration, not a new
  concept for Dasher.

## Testing

Per [RFC 0011](./0011-testing.md): manual verification only. Each frontend's
PR confirms visually that (a) the shown string equals the version the
frontend reports in its analytics events (GTK/Android implementations assert
this by construction — both read the same constant), and (b) the line appears
on the Privacy tab. No automated test: the value is a build constant and the
assertion would restate the code.

## Unresolved questions

1. **Engine (DasherCore) version alongside the app version.** Useful for
   support ("jumbling" reports needed the submodule pin to diagnose) but
   requires a `dasher_get_version()` C API + per-release tagging discipline
   in every frontend's bump commits. **Open** — propose alongside RFC 0006's
   About section.
2. **Build metadata** (commit, channel) beyond the plain version. **Open** —
   lean no for now; release builds are the support surface.

## Resolution

- State: accepted
- Decided by: project lead (Will Wade)
- Date: 2026-08-22
- Decision: Small, non-controversial support fix; accepted directly with
  implementation landing immediately on GTK and Android and issues filed for
  the remaining frontends. Placement in Privacy is explicitly interim pending
  RFC 0006's About section.
- Open sub-questions: 1, 2 (engine version display; build metadata).

## History

- _2026-08-22_ — _(initial proposal; accepted directly, GTK and Android implemented immediately, issues filed for the remaining frontends)_
- _2026-08-24_ — _(Windows implemented — version line at the bottom of Settings → Privacy, closing [Dasher-Windows #29](https://github.com/dasher-project/Dasher-Windows/issues/29))_
