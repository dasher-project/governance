---
rfc: 0008
title: Keyboard extension / IME onboarding (Apple & Android)
status: proposed
platforms: [apple, android, core]
created: 2026-06-28
updated: 2026-06-28
---

# Keyboard extension / IME onboarding (Apple & Android)

## Summary

Dasher ships as both a standalone writing app **and** a system keyboard:
on Apple platforms an iOS custom keyboard extension (`NSExtensionPointIdentifier
com.apple.keyboard-service`), and on Android an Input Method Editor
(`InputMethodService`, `BIND_INPUT_METHOD`). Installing the app is not enough —
the user must explicitly **enable** the keyboard in OS settings and then **select**
it as the active input source. This is a multi-step system-settings dance that
first-time users routinely fail at, and it is the single largest source of
"the keyboard doesn't work" support requests.

This RFC specifies a shared, platform-specific **first-run onboarding flow** that
detects the keyboard's enablement state and walks the user through enabling it,
with deep-links into the exact system screens. It complements the generic
first-run onboarding in [RFC 0004](./0004-onboarding.md), which deliberately did
not cover the keyboard-enablement step.

## Motivation

- On Android, fewer than half of users who install an IME-based keyboard succeed
  in enabling it without guidance. The flow spans **Settings → System → Keyboard →
  On-screen keyboard → enable Dasher → "Back" → Default keyboard → pick Dasher**,
  optionally followed by **Privacy → Advanced input methods → grant input
  permission** (needed for clipboard / full-text access). Each step is a place to
  lose the user.
- On iOS, the flow is **Settings → General → Keyboard → Keyboards → Add New
  Keyboard → Dasher → (trust prompt "Allow Full Access")**. The "Full Access"
  prompt in particular scares users; without it the engine clipboard + speak
  callbacks are unavailable.
- The state is also **opaque**: the app cannot silently know whether the user
  completed the steps. Both platforms expose APIs to query it, but neither
  frontend currently does — there is no in-app guidance, no "you're nearly there",
  no re-prompt after the user returns from system settings.
- This is platform-specific plumbing that does not belong in DasherCore (the
  engine), but the **detection queries and the step model** are shared enough
  that a single RFC keeps Apple and Android aligned.

## Detailed design

### Shared model

A keyboard onboarding flow has three observable states plus a "needs permission"
sub-state:

| State | Meaning |
| --- | --- |
| `notEnabled` | The keyboard/IME is installed but not turned on in system settings. |
| `enabledNotDefault` | The keyboard/IME is enabled but not the currently selected input source. |
| `needsPermission` | Enabled, but the OS-level input/Full-Access permission is off (limits clipboard, speak, etc.). |
| `ready` | Enabled, selected, permission sufficient. |

Each frontend exposes:

1. A **detection** function returning the current state.
2. A **deep-link** to the exact system settings screen for the current state.
3. A **first-run prompt** + a **resume-on-return** check (re-detect when the app
   regains foreground after the user is sent to system settings).
4. A **manual re-trigger** from Settings (so users can re-run the flow later).

Detection must be **cheap and side-effect free** (called in `onResume` /
`scenePhase` becoming active).

### Android (IME)

**Detection.** `InputMethodManager` + `Settings.Secure`:

- **Enabled?** The IME's component name (`ComponentName(this, DasherImeService::class.java)`,
  flattened) appears in `Settings.Secure.getString(
  ENABLED_INPUT_METHODS)` — a colon-separated list of enabled IMEs.
- **Default?** On Android 11+, `imm.getEnabledInputMethodList()` plus the
  default-IME intent resolution. There is no fully public "current default IME"
  API before Android 14; the pragmatic check is whether Dasher's IME is enabled
  *and* the user has only one IME enabled, or whether the system's
  `Settings.Secure.DEFAULT_INPUT_METHOD` value equals the Dasher IME component.
  Fall back to "enabledNotDefault" if ambiguous.
- **Permission?** The input-method binding itself is the permission; the separate
  "input data access" prompt (Android 14+, `INPUT_METHOD_SERVICES_PRIVILEGED`)
  governs clipboard / commit-text visibility beyond the focused field. Query via
  the IME service's `isEnabledForInput` / shouldShow warnings when commiting.

**Deep-links.** Use the documented `Intent` actions:

| State | Intent |
| --- | --- |
| `notEnabled` | `android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS` (manage keyboards) |
| `enabledNotDefault` | `android.provider.Settings.ACTION_INPUT_METHOD_SELECTOR` (Android 11+ picker) or re-use `ACTION_INPUT_METHOD_SETTINGS` with guidance copy |
| `needsPermission` | `android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS` + inline guidance (there is no dedicated permission screen for IME input access pre-14) |

**Flow.**

1. On first run (flag in `SharedPreferences`: `onboarding_ime_shown`), show a
   modal: "Use Dasher as your keyboard" with a one-line explanation and a
   primary button **"Enable keyboard"** (deep-link to input-method settings) and
   a secondary **"Not now"**.
2. The user is sent to system settings; the app goes to the background.
3. On `onResume`, re-detect. If `ready`, celebrate and dismiss. If still
   `notEnabled`/`enabledNotDefault`, show a persistent, dismissible banner
   ("Almost there — select Dasher as your keyboard") with a **"Open settings"**
   button.
4. A "Keyboard setup" entry in Settings → re-runs the flow.

The IME service itself does **not** run onboarding (it is the wrong process and
may not exist yet); the main app drives the flow and shares the persisted
onboarding flag via the app's `filesDir` (which, per RFC 0007 and the existing
shared-data pattern, is the same path the IME reads at its engine creation).

### Apple (iOS keyboard extension)

**Detection.**

- **Enabled?** `UIApplication.openSettingsURLString` does not expose keyboard
  state directly; the pragmatic approach is to attempt to detect via
  `UIInputViewController.hasFullAccess` (only valid inside the extension) plus a
  heartbeat: the extension writes a flag into the **App Group container**
  (`group.at.dasher.Dasher`) the first time it is loaded by the system (i.e. the
  user actually opened the keyboard picker). The main app reads that flag to know
  "the extension has been activated at least once."
- **Full Access?** `UIDevice` does not expose it; only the extension's
  `hasFullAccess` knows. The extension reports this through the App Group flag
  alongside the heartbeat.
- **Selected?** Best-effort: the heartbeat timestamp being recent is a proxy.

**Deep-link.** `UIApplication.shared.open(URL(string: UIApplication.openSettingsURLString)!)`
opens the app's settings; from there the user navigates to Keyboard. Apple
provides no more specific deep-link, so the modal must include **step-by-step
copy** ("Settings → General → Keyboard → Keyboards → Add New Keyboard → Dasher")
and, for Full Access, "tap Dasher → turn on Allow Full Access."

**Flow.**

1. First-run modal: "Install Dasher keyboard" with the step copy and an
   **"Open Settings"** button (`openSettingsURLString`).
2. On `scenePhase` becoming `.active`, re-read the App Group heartbeat. Update
   state, show a confirmation when the heartbeat indicates success.
3. The Full Access step has its own explanatory copy (why it's needed: clipboard,
   speak, training-file write-back) and a clear opt-out note (the keyboard works
   for basic entry without it).

### Copy and translation

All onboarding copy goes through the RFC 0003 i18n pipeline (engine
`strings_*.json` for any engine-side strings; platform-native catalogs for the
chrome). The "Allow Full Access" / "Input permission" explanations in particular
must be plain-language and localised — they are the scariest step.

### What does NOT belong here

- The **generic** first-run experience (welcome, input handshake, first-zoom
  tutorial) is RFC 0004. This RFC is only the keyboard-enablement sub-flow.
- **Switch / access-method setup** belongs to the input & access-methods RFC
  (0010), not here.
- **App-group / shared-storage layout** is defined by the existing shared-data
  pattern (the same `userDir` the engine reads); this RFC only depends on it.

## Drawbacks

- Adds platform-specific detection code that is **fragile across OS versions**
  (the Android default-IME query and the Apple Full Access detection are both
  partially heuristic). The detection must degrade gracefully (assume
  `enabledNotDefault` on uncertain queries, never block the user).
- The heartbeat pattern on iOS is a workaround for a missing API and could break
  if Apple changes App Group visibility for extensions.
- Onboarding modals are friction; users who installed the standalone app to use
  it *as an app* (not as a keyboard) will see a prompt that is not relevant to
  them. Mitigation: only show the keyboard onboarding if the keyboard target is
  bundled, and offer a "don't show again."

## Alternatives considered

- **Do nothing / rely on OS-level prompts.** Status quo. Confirmed poor
  conversion; this RFC exists because that is not good enough.
- **Fully automate via MDM / accessibility.** Not possible for a consumer app.
- **Bundle a system-prompt shim.** Neither platform allows an app to silently
  enable its own keyboard.

## Prior art

- **Gboard / SwiftKey** both ship a guided "Enable keyboard" first-run flow on
  Android with the exact deep-links above and a returning-user banner — the de
  facto user expectation.
- **Fleksy / Grammar Keyboard** on iOS use the step-copy + `openSettingsURLString`
  pattern.
- **Dasher v5** had no keyboard extension; this is a new concern for v6.

## Unresolved questions

1. **Default-IME detection on Android < 14.** What is the most reliable heuristic
   that doesn't require a privileged permission? Proposal: treat "enabled and
   only one IME enabled" as `ready`, else `enabledNotDefault`.
2. **Re-prompt cadence.** How often should the banner re-appear if the user
   dismisses it? Once per app launch? Once ever (until they re-open the flow from
   Settings)?
3. **Full Access messaging.** Is the AAC-specific framing ("needed so Dasher can
   speak what you write and remember your training") the right one, or does it
   over-promise?
4. **IME-engine sharing.** Should the onboarding flag live in the shared
  `userDir` (so the IME can also see it) or in the main app's private prefs?
5. **Does this warrant a small DasherCore C API** (e.g. a "mark keyboard
   onboarding complete" persisted flag) so all frontends share the SSOT, or is
   per-frontend persistence correct?

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _pending_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_
