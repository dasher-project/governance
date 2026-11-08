---
rfc: 0004
title: First-run onboarding experience (incl. keyboard/IME enablement)
status: proposed
platforms: [apple, windows, gtk, android, core]
created: 2026-06-17
updated: 2026-11-08
---

# First-run onboarding experience (incl. keyboard/IME enablement)

## Plain-English summary

Dasher is a free tool that lets people who cannot use a keyboard write, by
zooming in on text they point to with a mouse, their eyes, or a switch. It is
powerful but hard to start using: new users often feel lost or even queasy the
first time they open it, and many give up. On Apple and Android devices,
Dasher can also stand in as the keyboard for the whole device, but turning
that on is a maze of settings screens that defeats many people. This
proposal suggests a short guided introduction when someone first opens the
app: learn the basics, and if relevant, switch on the Dasher keyboard with
help. It draws on expert help and user testing before anything is built,
because we do not yet know what works best. It would help new users, and the
caregivers who set Dasher up for them. This is still at the ideas stage.

## Summary

Dasher has a notoriously steep learning curve. New users frequently describe
the initial experience as "sea-sickness inducing" (per the design guide §1).
No v6 frontend implements any onboarding; all three launch directly into the
live editor. The design guide §8 defines an aspirational scaffolded flow
(welcome → input handshake → first zoom challenge → progress dashboard), and
DasherCore has a functional Game Mode engine (`CGameModule`) and a disabled
Demo Filter (`CDemoFilter`). However, `CDemoFilter` has since been removed
from DasherCore (commit `f79eb6a9`, Jun 2026; it had been disabled since 2007
due to segfaults and was never re-enabled). This RFC frames the onboarding
problem, documents what exists, identifies the design questions that need
UX expert input, and proposes a phased implementation plan.

Since November 2026 this RFC also covers **keyboard and IME enablement** on
Apple and Android, folded in from RFC 0008 (withdrawn; see the "Keyboard and
IME enablement" chapter). Installing the app is not enough to use Dasher as
the system keyboard: the user must enable it in OS settings and select it as
the active input source. That multi-step settings dance is the first-run
journey's most common failure point and the single largest source of "the
keyboard doesn't work" support requests.

## Implementation status

Audited August 2026. Not implemented.

No frontend ships a first-run onboarding flow. The only first-launch prompts
today are the analytics opt-in (Apple, Windows) and the v5 migration prompt
(Apple macOS, Windows). visionOS shows a one-time "pinch and look" gesture hint;
that is a single gesture tip, not an onboarding flow.

Game Mode exists on all platforms and is the closest thing to guided practice,
but the user invokes it at any time. It is never triggered on first launch.

Keyboard and IME enablement (folded in from RFC 0008) is likewise not
implemented. Dasher-Apple ships the iOS keyboard extension, but the host app
never mentions it: no enablement guide, no Full Access check, no deep link
into system settings. Dasher-Mobile ships the Android IME, but there is no
in-app flow to guide the user to enable or select it.

This RFC still needs UX research before it can move out of `proposed` (see
"Design questions needing UX expert input").

The dasher-web playground ships an always-available game-mode practice overlay
(August 2026 "RFC rounds" work). That is practice material, not a first-run
onboarding flow.

## Motivation

### The core problem

Dasher's zooming text-entry paradigm is unlike any other input method. A new
user opening the app for the first time sees a canvas of letters zooming toward
a cursor point, with no explanation of how to control it, what the goal is, or
how to adjust speed. The result is predictable: high abandonment.

The design guide identifies this explicitly:

> The primary reason new users abandon Dasher is the initial learning curve,
> often described as "sea-sickness inducing."

### Current state (audited)

| | Dasher-Apple | Dasher-Windows | Dasher-GTK |
| --- | --- | --- | --- |
| **Onboarding flow** | None | None | None |
| **First-launch detection** | None | Analytics opt-in only | None |
| **First experience** | Live editor canvas immediately | Editor + analytics opt-in modal | Editor window ("Dasher v6") |
| **Calibration in onboarding** | No (Settings only) | No (Settings only) | No (no calibration UI) |
| **Input mode selection** | Toolbar / Settings | Settings | Footer controls |
| **Speed tuning** | Status bar (on-demand) | Status bar (on-demand) | Footer bar |
| **Gamified practice** | Yes (Game Mode toggle) | Yes (Game Mode) | Yes (Play button + `CScreenGameModule`) |

**Game Mode** is the closest thing to onboarding that exists. All three
frontends can enter it via a toolbar/footer button, and DasherCore's
`CGameModule` provides target text, progress feedback, and a directional arrow.
But it's user-invoked at any time, never triggered on first launch, and not
part of any guided sequence.

**CDemoFilter** ("Demo Mode (no input)") was an automated cursor driver that
could show users how Dasher works without requiring them to control it. It is
no longer in DasherCore: removed in commit `f79eb6a9` (Jun 2026) after
being disabled since 2007 due to segfaults. The three `LP_DEMO_*` parameters
that drove it were removed at the same time. Whether onboarding needs a passive
"watch how it works" step at all, and if so what serves it best, is a UX
research question, not a foregone conclusion (see "DasherCore changes
needed" below).

### What the design guide proposes (§8)

The design guide defines a four-stage flow:

```
[Welcome to Dasher] → [Input Device Handshake] → [First Zoom Challenge] → [Progress Dashboard]
```

With specific beginner-mode canvas behaviours:

1. **Sibling Box Suppression:** show sibling boxes but hide their children to
   reduce visual load.
2. **Color Harmonization:** group siblings in muted monochromatic hues.
3. **Dynamic Pink Path Correction:** a correction arrow that guides the user
   toward the correct letter, fading as they approach, with auto-slow when they
   drift off-path.
4. **Stats & Milestones:** WPM, accuracy, and unlock badges (e.g. "Smooth
   Steerer") at the end of a training sequence.

This is a strong vision, but none of it has been validated with users or
implemented. Several questions need UX research before building.

## Design questions needing UX expert input

This RFC deliberately does not prescribe all the answers. The following
questions require UX research, user testing, or expert consultation:

### Q1. How many steps before the user is "in"?

The design guide proposes 4 stages. But accessibility users with different
motor abilities may need more or fewer steps. Key sub-questions:

- Should the welcome screen explain *what Dasher is* before showing the canvas?
- Is a device handshake necessary on first run, or should we default to the
  most common input (mouse/touch) and let users change it later?
- Should the user be typing real words during onboarding, or practicing with a
  guided target (Game Mode)?
- Can onboarding be interrupted and resumed, or must it complete in one session?

### Q2. Speed calibration: automatic or guided?

Dasher's speed (`LP_MAX_BITRATE`) determines how fast the canvas zooms. Too fast
= overwhelming; too slow = boring. Currently it's a manual slider with no
guidance.

Options:
- **Guided calibration:** Show a short phrase, ask the user to type it, measure
  completion time, auto-set speed. (Similar to typing-test calibration.)
- **Progressive speed:** Start slow, gradually increase as the user demonstrates
  control. (Requires engine support: a ramp-up parameter?)
- **Auto-speed control:** DasherCore already has `BP_AUTO_SPEEDCONTROL`. Should
  onboarding enable it by default and disable it once the user is proficient?

UX question: does asking users to "type this phrase" during onboarding create
*more* anxiety (performance pressure) or less (clear goal)?

### Q3. What happens with different input methods?

A mouse user, an eye-tracker user, and a switch user have fundamentally
different onboarding needs:

- **Mouse/touch:** Point and hold. Intuitive for most users.
- **Eye gaze:** No clicking (dwell-based). Needs explanation that *looking* is
  *selecting*. Many users don't realise their eye movements are being tracked
  as input.
- **Switch:** Timed scanning. Completely different mental model from pointing.
- **Tilt/joystick:** Physical movement maps to cursor. Needs calibration.

Should onboarding detect the active input method and adapt? Or show a generic
"how Dasher works" animation first, then input-specific practice?

### Q4. Sibling suppression and path correction: effective or patronising?

The design guide proposes hiding child nodes and showing a pink correction
arrow. But:

- Does hiding nodes confuse users who then see a "different" Dasher than the one
  they'll actually use?
- Does the pink arrow feel helpful or condescending?
- At what point do training wheels come off? After N successful characters?
  After explicit user request? Never (make it a toggle)?

This needs A/B testing with real users.

### Q5. Gamification: motivating or childish?

The design guide proposes badges ("Smooth Steerer") and WPM/accuracy stats. For
an assistive technology used by adults with disabilities, this could feel
patronising. On the other hand, gamification is proven to help skill acquisition.

UX question: should gamification be opt-in, age-dependent, or always present?
What's the right tone (celebratory but not childish)?

### Q6. Onboarding vs. always-available tutorial

Should onboarding be strictly first-run, or should it be accessible at any time
from a "Learn Dasher" / "Practice" entry point? Arguments for both:

- **First-run only:** Less clutter for returning users.
- **Always available:** Users may want to revisit; assistive tech users may have
  cognitive disabilities and benefit from repetition; caregivers setting up the
  app for someone else may need to preview it.

### Q7. RTL and language considerations

If onboarding includes text instructions (likely), it depends on RFC 0003
(multilingual UI). Onboarding text should be in the user's language. The pink
path correction arrow direction must respect the writing direction of the
alphabet being practiced.

## Detailed design (proposed, pending UX validation)

### Phase 0: Research (before building)

1. **Engage a UX consultant** to validate the design guide §8 proposals.
2. **User testing** with 3-5 first-time Dasher users per input method
   (mouse, eye gaze, switch) to observe where they get stuck.
3. **Review competitor onboarding:** how do Tobii Communicator, Grid 3,
   Proloquo2Go, and other AAC tools handle first-run?
4. **Audit the UX background decks** (`dasher-design-guide/ux-background/`) with
   the consultant.

### Phase 1: First-run detection + welcome screen (all platforms)

The simplest increment that helps:

1. **Detect first launch** via a persisted flag (`UserDefaults` / registry /
   `Glib::KeyFile`).
2. **Show a welcome screen** explaining what Dasher is (1-2 paragraphs + a short
   animation or static illustration of the zooming concept).
3. **Offer two paths:** "Start typing" (skip to editor) and "Learn the basics"
   (go to guided practice).
4. **Set sensible defaults:** Auto-speed control ON, beginner canvas mode ON
   (sibling suppression), moderate starting speed.

This gives users a choice without forcing a long tutorial. The welcome screen
text needs to be localised (RFC 0003).

### Phase 2: Guided practice sequence (Game Mode integration)

Wire the existing `CGameModule` into a structured practice sequence:

1. **Step 1 ("Find the letter H"):** Single target letter. Canvas zooms slowly.
   Pink arrow guides. Sibling children suppressed.
2. **Step 2 ("Type 'HI'"):** Two letters. Slightly faster.
3. **Step 3 ("Type 'HELLO'"):** Full word. Full speed (with auto-speed control).
4. **Step 4 (Progress dashboard):** Show WPM, accuracy, time. Offer "Practice
   more" or "Start typing."

Each step should be skippable. Progress is saved so users can resume.

This sequence is not input-method-specific in Phase 2. It uses whatever
input method is currently active. Phase 3 adds per-method adaptation.

### Phase 3: Input-method-aware onboarding

If UX research (Q3) determines that per-method guidance is needed:

- **Eye gaze:** Add a screen explaining "Your eyes control the cursor. Look at a
  letter and hold your gaze to select it." Include a dwell-practice step.
- **Switch:** Add a screen explaining scanning. "Press your switch when the
  highlight reaches the letter you want." Include a scanning-practice step.
- **Tilt/Joystick:** Offer calibration (already exists on Apple via
  `TiltCalibrationView`; needs adding on Windows/GTK).

### Phase 4: Refinement

- A/B test sibling suppression (Q4).
- Test gamification tone (Q5).
- Add "Practice" / "Learn Dasher" entry point in settings (Q6).
- Ensure RTL support for the practice sequences (Q7).

### DasherCore changes needed

> **Research-led caveat.** The table below inventories what exists today and
> what *might* be required. It is not a build spec. The onboarding design,
> including whether Game Mode is the right practice vehicle at all, and whether
> any passive demonstration (the old `CDemoFilter` concept) is even needed, is
> an output of the UX research (RFC 0004's reason for being). The research
> may well propose a mechanism that replaces or bypasses several rows here.

| Feature | Status | What might be needed (pending research) |
| --- | --- | --- |
| `CGameModule` (target text, progress, arrow) | Functional | *Hypothesis:* a guided game-mode sequence is the practice vehicle. To validate: expose target text / progress via C API for prototype dashboards. Research may propose something different. |
| Passive "watch how it works" demo | **Removed** (`CDemoFilter` deleted in `f79eb6a9`; disabled since 2007) | Only if research shows a passive step helps. Options: a pre-recorded video clip (no engine work), or a fresh auto-driver built to the current codebase. The old filter is **not** to be resurrected. |
| Sibling suppression | Not implemented | New boolean parameter (e.g. `BP_BEGINNER_MODE`) that hides child nodes (if research validates a beginner mode). |
| Path correction arrow | Partial (GameModule has a help arrow) | Generalise only if the chosen design needs it outside Game Mode. |
| Auto-speed ramp | `BP_AUTO_SPEEDCONTROL` exists | Evaluate whether it's sufficient for onboarding or needs a dedicated ramp parameter. |
| Progress metrics (WPM, accuracy) | Not exposed | New C API calls (only if the validated design includes a dashboard). |

### Per-platform implementation

#### Apple

- `OnboardingView.swift`: SwiftUI view with `TabView` for multi-step flow.
- `@AppStorage("hasOnboarded")` for first-launch detection.
- Reuse `TiltCalibrationView` and `SwitchCaptureView` within the flow.
- Game Mode practice via `DasherViewModel.enterGameMode()`.

#### Windows

- `OnboardingWindow.axaml`: Avalonia window with `Carousel` for multi-step.
- `AnalyticsService.HasPrompted` pattern extended to `Settings.HasOnboarded`.
- Game Mode practice via existing Game Mode infrastructure.

#### GTK

- `OnboardingWindow.cpp`: `Gtk::Assistant` (GTK's built-in wizard widget) or
  a custom `Gtk::Box` with page transitions.
- First-launch flag via `Glib::KeyFile` or `GSettings`.
- Game Mode practice via `DasherController` / `CScreenGameModule`.

## Keyboard and IME enablement (Apple and Android)

Folded in from RFC 0008 (withdrawn 2026-11-08) so the whole first-run story
lives in one place. Dasher ships as both a standalone writing app and a
system keyboard: on Apple an iOS custom keyboard extension
(`NSExtensionPointIdentifier com.apple.keyboard-service`), on Android an
Input Method Editor (`InputMethodService`, `BIND_INPUT_METHOD`). Installing
the app is not enough. The user must explicitly **enable** the keyboard in
OS settings and then **select** it as the active input source.

### Why this is part of onboarding

- On Android, fewer than half of users who install an IME-based keyboard
  succeed in enabling it without guidance. The flow spans **Settings →
  System → Keyboard → On-screen keyboard → enable Dasher → "Back" → Default
  keyboard → pick Dasher**, optionally followed by **Privacy → Advanced
  input methods → grant input permission** (needed for clipboard and
  full-text access). Each step is a place to lose the user.
- On iOS, the flow is **Settings → General → Keyboard → Keyboards → Add New
  Keyboard → Dasher → (trust prompt "Allow Full Access")**. The "Full
  Access" prompt in particular scares users; without it the engine
  clipboard and speak callbacks are unavailable.
- The state is opaque: the app cannot silently know whether the user
  completed the steps. Both platforms expose APIs to query it, but neither
  frontend does today. There is no in-app guidance, no "you're nearly
  there", no re-prompt after the user returns from system settings.
- This is platform-specific plumbing that does not belong in DasherCore
  (the engine), but the detection queries and the step model are shared
  enough that one chapter keeps Apple and Android aligned.

### Shared state model

A keyboard onboarding flow has three observable states plus a "needs
permission" sub-state:

| State | Meaning |
| --- | --- |
| `notEnabled` | The keyboard/IME is installed but not turned on in system settings. |
| `enabledNotDefault` | The keyboard/IME is enabled but not the currently selected input source. |
| `needsPermission` | Enabled, but the OS-level input/Full-Access permission is off (limits clipboard, speak, etc.). |
| `ready` | Enabled, selected, permission sufficient. |

Each frontend exposes:

1. A **detection** function returning the current state.
2. A **deep-link** to the exact system settings screen for the current state.
3. A **first-run prompt** plus a **resume-on-return** check (re-detect when
   the app regains foreground after the user is sent to system settings).
4. A **manual re-trigger** from Settings (so users can re-run the flow later).

Detection must be **cheap and side-effect free** (called in `onResume` /
`scenePhase` becoming active).

### Android (IME)

**Detection.** `InputMethodManager` + `Settings.Secure`:

- **Enabled?** The IME's component name (`ComponentName(this, DasherImeService::class.java)`,
  flattened) appears in `Settings.Secure.getString(
  ENABLED_INPUT_METHODS)`, a colon-separated list of enabled IMEs.
- **Default?** On Android 11+, `imm.getEnabledInputMethodList()` plus the
  default-IME intent resolution. There is no fully public "current default
  IME" API before Android 14. The pragmatic check is whether Dasher's IME
  is enabled *and* the user has only one IME enabled, or whether the
  system's `Settings.Secure.DEFAULT_INPUT_METHOD` value equals the Dasher
  IME component. Fall back to "enabledNotDefault" if ambiguous.
- **Permission?** The input-method binding itself is the permission; the
  separate "input data access" prompt (Android 14+,
  `INPUT_METHOD_SERVICES_PRIVILEGED`) governs clipboard and commit-text
  visibility beyond the focused field. Query via the IME service's
  `isEnabledForInput` / shouldShow warnings when commiting.

**Deep-links.** Use the documented `Intent` actions:

| State | Intent |
| --- | --- |
| `notEnabled` | `android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS` (manage keyboards) |
| `enabledNotDefault` | `android.provider.Settings.ACTION_INPUT_METHOD_SELECTOR` (Android 11+ picker) or re-use `ACTION_INPUT_METHOD_SETTINGS` with guidance copy |
| `needsPermission` | `android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS` + inline guidance (there is no dedicated permission screen for IME input access pre-14) |

**Flow.**

1. On first run (flag in `SharedPreferences`: `onboarding_ime_shown`), show
   a modal: "Use Dasher as your keyboard" with a one-line explanation and a
   primary button **"Enable keyboard"** (deep-link to input-method
   settings) and a secondary **"Not now"**.
2. The user is sent to system settings; the app goes to the background.
3. On `onResume`, re-detect. If `ready`, celebrate and dismiss. If still
   `notEnabled`/`enabledNotDefault`, show a persistent, dismissible banner
   ("Almost there: select Dasher as your keyboard") with an **"Open
   settings"** button.
4. A "Keyboard setup" entry in Settings re-runs the flow.

The IME service itself does **not** run onboarding (it is the wrong process
and may not exist yet). The main app drives the flow and shares the
persisted onboarding flag via the app's `filesDir` (which, per RFC 0007 and
the existing shared-data pattern, is the same path the IME reads at its
engine creation).

### Apple (iOS keyboard extension)

**Detection.**

- **Enabled?** `UIApplication.openSettingsURLString` does not expose
  keyboard state directly. The pragmatic approach is to attempt to detect
  via `UIInputViewController.hasFullAccess` (only valid inside the
  extension) plus a heartbeat: the extension writes a flag into the **App
  Group container** (`group.at.dasher.Dasher`) the first time it is loaded
  by the system (i.e. the user actually opened the keyboard picker). The
  main app reads that flag to know "the extension has been activated at
  least once."
- **Full Access?** `UIDevice` does not expose it; only the extension's
  `hasFullAccess` knows. The extension reports this through the App Group
  flag alongside the heartbeat.
- **Selected?** Best-effort: the heartbeat timestamp being recent is a
  proxy.

**Deep-link.** `UIApplication.shared.open(URL(string: UIApplication.openSettingsURLString)!)`
opens the app's settings; from there the user navigates to Keyboard. Apple
provides no more specific deep-link, so the modal must include **step-by-step
copy** ("Settings → General → Keyboard → Keyboards → Add New Keyboard →
Dasher") and, for Full Access, "tap Dasher → turn on Allow Full Access."

**Flow.**

1. First-run modal: "Install Dasher keyboard" with the step copy and an
   **"Open Settings"** button (`openSettingsURLString`).
2. On `scenePhase` becoming `.active`, re-read the App Group heartbeat.
   Update state, show a confirmation when the heartbeat indicates success.
3. The Full Access step has its own explanatory copy (why it's needed:
   clipboard, speak, training-file write-back) and a clear opt-out note
   (the keyboard works for basic entry without it).

### Copy and translation

All onboarding copy goes through the RFC 0003 i18n pipeline (engine
`strings_*.json` for any engine-side strings; platform-native catalogs for
the chrome). The "Allow Full Access" / "Input permission" explanations in
particular must be plain-language and localised: they are the scariest
step.

### Scope boundaries

- The **generic** first-run experience (welcome, input handshake,
  first-zoom tutorial) is the rest of this RFC; this chapter is only the
  keyboard-enablement sub-flow.
- **Switch / access-method setup** belongs to
  [RFC 0010](./0010-input-access-methods.md), not here.
- **App-group / shared-storage layout** is defined by the existing
  shared-data pattern (the same `userDir` the engine reads); this chapter
  only depends on it.

## Drawbacks

- **Large effort.** A proper onboarding flow is one of the biggest features for
  v6. It touches all three frontends and requires DasherCore changes.
- **UX research is a prerequisite.** Building onboarding without validation risks
  creating something that doesn't actually reduce abandonment.
- **Maintenance burden.** Onboarding text, illustrations, and animations need
  localisation (RFC 0003) and updates as the product evolves.
- **Risk of over-engineering.** A simple "welcome + practice mode" might be 80%
  as effective as a full guided sequence. Need to avoid gold-plating.
- **Lock-in risk if we pre-commit to a mechanism.** Reimplementing something like
  `CDemoFilter`, or assuming the current Game Mode is the practice vehicle, would
  bake in today's assumptions. The point of the UX research is that it may propose
  a better mechanism; the engineering choice should follow the evidence, not lead
  it.
- **Keyboard detection is fragile across OS versions** (the Android
  default-IME query and the Apple Full Access detection are both partially
  heuristic). The detection must degrade gracefully (assume
  `enabledNotDefault` on uncertain queries, never block the user). The iOS
  heartbeat pattern is a workaround for a missing API and could break if
  Apple changes App Group visibility for extensions.
- **Keyboard onboarding modals are friction** for users who installed the
  standalone app to use it *as an app*, not as a keyboard. Mitigation: only
  show the keyboard onboarding if the keyboard target is bundled, and offer
  a "don't show again."

## Alternatives considered

### No onboarding (status quo)

Ship without onboarding. Rejected: the learning curve is the #1 reason users
abandon Dasher, and competitors (Grid 3, Tobii) all have guided setup.

### Video tutorial only

Ship a "How to use Dasher" video on the welcome screen, no interactive practice.
Simpler to build but passive: users learn Dasher by doing, not watching.

### Adaptive onboarding (AI-driven)

Track user behaviour and dynamically adjust difficulty, hints, and speed.
Interesting but over-engineered for v6's first pass. Can revisit post-launch.

### Web-based tutorial

Host a tutorial on the website that users complete before installing. Rejected
because the tutorial needs to work with the user's actual input device and the
real Dasher canvas. A web simulation wouldn't reflect their setup.

### Rely on OS-level prompts for keyboard enablement

Status quo for the keyboard/IME chapter. Confirmed poor conversion; the
chapter exists because that is not good enough. (Fully automating via MDM or
accessibility is not possible for a consumer app, and neither platform
allows an app to silently enable its own keyboard.)

## Prior art

- **Grid 3 (Smartbox):** First-run wizard with input method selection, 
  calibration, and a guided "find the word" exercise.
- **Tobii Communicator:** Eye gaze calibration wizard with progressive practice.
- **Proloquo2Go:** Crescendo vocabulary onboarding with "add first words" guided
  setup.
- **SwiftKey / Gboard:** Glide typing tutorial that appears on first use: a
  short "try typing HELLO" prompt. Both also ship a guided "Enable keyboard"
  first-run flow on Android with the exact deep-links in the keyboard/IME
  chapter, plus a returning-user banner: the de facto user expectation.
- **Fleksy / Grammar Keyboard** on iOS use the step-copy +
  `openSettingsURLString` pattern from the keyboard/IME chapter.
- **v5 Dasher:** Had no onboarding, and no keyboard extension. Users were
  dropped into the editor. The design guide §8 was written specifically to
  address this gap; the keyboard is a new concern for v6.

## Unresolved questions

1. **UX expert engagement:** Who do we engage, and what's the budget? **Open.**
2. **Is a passive demonstration step needed at all?** **Open.** A research
   output, not an engineering decision.
3. **Beginner mode persistence:** first-run-only or a persistent setting?
   **Open.**
4. **Cross-platform consistency:** identical across platforms, or per-platform
   conventions? **Open.**
5. **Measurement:** how do we measure whether onboarding reduces abandonment?
   **Open.** Analytics ([RFC 0001](./0001-analytics.md)) could track completion
   rate, time-to-first-word, and retention by path.
6. **Default-IME detection on Android < 14** (keyboard/IME chapter): most
   reliable unprivileged heuristic still to be chosen. **Open.**
7. **Re-prompt cadence** (keyboard/IME chapter): how often to re-offer the
   keyboard setup if declined. **Open.**
8. **Full Access messaging** (keyboard/IME chapter): copy to be finalised.
   **Open.**
9. **IME-engine sharing:** should the keyboard onboarding flag live in the
   shared `userDir` or in the main app's private prefs? **Open.**
10. **Does keyboard onboarding warrant a small DasherCore C API** ("mark
    keyboard onboarding complete") so all frontends share the SSOT, or is
    per-frontend persistence correct? **Open.**

## Resolution

- State: pending (open for discussion)
- Decided by: —
- Date: —
- Decision: Not yet accepted. The UX research ("Design questions needing UX
  expert input") is a prerequisite, and no frontend ships onboarding yet.
- Open sub-questions: all (see Unresolved questions).

## History

- 2026-11-08 — plain-English summary added, prose simplified for readability, implementation status re-synced against the frontend repos.
- 2026-11-08 — RFC 0008 (keyboard extension / IME onboarding) folded in as
  the "Keyboard and IME enablement" chapter; its open questions moved here
  (items 6-10), and 0008 is now a redirect stub marked withdrawn. The two
  were merged before either was implemented, so no shipped behaviour
  changed.
