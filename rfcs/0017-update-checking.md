---
rfc: 0017
title: Update distribution and in-app update checking (dual-track)
status: proposed
platforms: [apple, windows, gtk, android, web]
created: 2026-08-26
updated: 2026-08-26
---

# Update distribution and in-app update checking (dual-track)

## Summary

Dasher frontends ship through two kinds of channel, and update behaviour must
match the channel, not fight it:

1. **Managed channels** — platform stores (App Store / TestFlight, Google
   Play, possible future Flathub listing). The store owns discovery,
   download, installation and rollback. Dasher does **no** in-app update
   mechanics there beyond pointing users at the store page when a store
   policy requires it.
2. **Self-managed channels** — GitHub Releases (macOS today, Windows today,
   Android APKs today, GTK AppImage), Flatpak (GTK, user-managed via
   `flatpak update`), and future Linux store listings. Here Dasher itself is
   responsible for telling the user a newer version exists, because nothing
   else will — and for an AAC audience, "go check the releases page" is not
   an accessible update path.

Every frontend implements one shared behaviour for self-managed builds: a
**passive in-app update check** against the GitHub Releases API on launch
(at most weekly, opt-out in Settings → Privacy), showing a non-modal
notification with a link. No silent downloads, no self-installation.

## Implementation status

Not implemented anywhere. Dasher-Windows has a `UpdateChecker` service
(GitHub Releases API + in-app dialog) that is the natural starting point for
the shared behaviour; it is compiled out in `STORE` builds, which matches the
dual-track split.

| Platform | Current channel | In-app check |
| --- | --- | --- |
| Dasher-Apple (iOS) | TestFlight | None (TestFlight notifies) |
| Dasher-Apple (macOS) | GitHub Releases | None |
| Dasher-Windows | GitHub Releases; STORE variant planned | `UpdateChecker` (non-STORE builds only) |
| Dasher-GTK | GitHub Releases (Flatpak + AppImage artifacts) | None |
| Dasher-Android | GitHub Releases APKs; Play Store intended | None |
| dasher-web | Always "latest" by nature of the browser | N/A |

## Motivation

- **Nobody tells self-managed users.** Flatpak users get updates through
  `flatpak update`, but only if they run it. AppImage has no updater at all.
  Sideloaded Android APKs have no mechanism whatsoever. A user on v0.1.8
  whose restart-drift bug was fixed in v0.1.10 has no way to know.
- **Our users are the least able to go looking.** For many Dasher users,
  browsing to a GitHub releases page and choosing an artifact is itself a
  significant accessibility barrier. The update must come to them, in the
  app, as text they can act on with the input method they have.
- **Version display alone doesn't close the loop.** RFC 0016 put the version
  in Settings so users can *report* what they run; it does not tell them
  something newer exists.
- **Stores handle it — when we're on them.** iOS/TestFlight today; Play
  Store and possibly Flathub are intended destinations for Android and GTK.
  On those channels, in-app update UI is at best redundant and at worst a
  store-policy violation. So the behaviour must be channel-conditional, not
  universal.
- **Two approaches, explicitly:** this RFC names the split so each frontend
  builds once, behind a build flag / channel check, rather than bolting on
  store-conditional logic later.

## Detailed design

### Channel detection

- **Build-time flag** where the channel is fixed at compile time:
  - Android: `PLAY_STORE` product flavour vs the direct APK build.
  - Windows: the existing `STORE` preprocessor symbol.
  - GTK: a CMake option (`DASHER_CHANNEL=store` for a future Flathub
    listing; default `github`).
  - Apple: a build setting (App Store / TestFlight vs Developer ID
    notarised builds; `EXPANDED_CODE_SIGN_IDENTITY` or a Debug/Release
    distinction can gate it, as Sparkle-style apps already do).
- Flatpak is a **hybrid**: installed from a bundle but updated by the system
  package manager. Flatpak builds set `FLATPAK_ID`/`/.flatpak-info` (the
  keyboard-setup dialog already detects this). Flatpak builds show the
  notification only if `flatpak update` would not handle it — practically,
  Flatpak builds behave as **managed** (the notification says "update via
  your system's Flatpak tools" only if the remote is behind; we do not
  detect that, so Flatpak builds default to silent/managed).

### The check (self-managed builds only)

1. **On launch** (after the window is up, off the critical path — never
   block first paint), and at most once every 7 days (persisted timestamp).
2. **GET** `https://api.github.com/repos/dasher-project/<repo>/releases?per_page=1`
   (10-second timeout, fail silent). No auth token, no telemetry, no
   machine identifiers — the request contains nothing but the IP GitHub
   already sees.
3. Compare the release tag to the running app version (GTK: the git-describe
   string from RFC 0016's mechanism; Android: `BuildConfig.VERSION_NAME`;
   Windows: assembly version; Apple: bundle short version). Tag comparison
   is semver-numeric, ignoring leading `v`.
4. If newer: show a **non-modal** notification (in-app banner or system
   notification) — never a modal dialog that could interrupt typing. The
   notification carries the release title and a link to the release page.
   Dismiss is persistent ("skip this version") plus a "remind me later"
   that re-arms after the next 7-day window.
5. **Setting**: "Check for updates" toggle in Settings → Privacy, default
   **on** for self-managed builds, absent entirely on managed builds. The
   Privacy placement matches RFC 0016's interim pattern (version info lives
   nearby) and keeps it discoverable without a dedicated section.
6. **What we do NOT do**: download the update, install it, or run
   installers. The link opens the release page in the platform browser /
   store. Rationale: self-installation is a security surface (code-signing
   validation, partial downloads, disk access) that stores already solve,
   and the AppImage side would need AppImageUpdate integration, which can
   be a future amendment once there is evidence users want it.

### Platform notes

- **macOS (GitHub Releases):** notification links to the release page.
  Sparkle-style self-update is explicitly out of scope for now (same
  rationale as 6 above). If adopted later, it must remain Developer-ID-build
  only.
- **Windows:** adopt the existing `UpdateChecker` service as-is for the
  behaviour above; the `STORE` symbol already excludes it. The current modal
  "Update Available" window becomes a non-modal toast per clause 4.
- **GTK:** AppImage builds get the check; Flatpak builds are managed (see
  above). For "what's the option on Linux" during v6 development: GitHub
  Releases is the channel; a future Flathub submission would flip the build
  to managed and remove the in-app check per the flag.
- **Android:** the Play Store flavour drops the check entirely (Play
  notifies). The direct-APK build gets it; the notification links to the
  release page where the new APK lives. If we later distribute only via
  Play, the flag disappears with the flavour.
- **iOS/TestFlight:** always managed; TestFlight already pushes
  notifications. Nothing to build. If a public App Store build arrives with
  a non-TestFlight beta channel, this RFC's managed track still applies.

### Telemetry

One opt-in analytics event (`update_prompt_shown`) on display, gated by the
existing RFC 0001 consent — so we can measure whether self-managed users are
being reached. No event contains the version list or any user identifier
beyond the existing anonymous id.

## Drawbacks

- Two code paths per frontend (flag-conditional). Mitigated by keeping the
  self-managed side to one HTTP call + one notification widget.
- GitHub API rate limits (60/hr unauthenticated) are fine for launch-time
  checks but could bite if we ever check more eagerly; the 7-day window
  keeps us far under.
- Some users on managed channels may still want proactive notification of
  new releases (store update lag). We accept the store's own cadence there;
  a "notify me about releases" that links to the store page is a possible
  future amendment.

## Alternatives considered

- **Sparkle / WinSparkle / in-app self-install:** heavier, security-bearing,
  and unnecessary while we are not the sole channel. Deferred (see clause 6).
- **Do nothing on self-managed channels:** the status quo; means our most
  engaged early users (who installed from GitHub) are stranded on old
  builds — the exact population giving us feedback in v6.
- **Web-page-only announcements:** not accessible enough for the audience;
  requires users to self-advocate.

## Prior art

- **Dasher-Windows' UpdateChecker** — the API-polling pattern already
  shipped; this RFC generalises it and softens its modal to a toast.
- **Firefox's** "release versus store" split on Windows/macOS.
- **Signal Desktop's** GitHub-releases check before their store builds.

## Testing

Per [RFC 0011](./0011-testing.md): manual verification primarily.
- Unit-test the version comparison (tag vs running version, `v`-stripping,
  semver ordering) — pure logic, lands in each frontend's test target.
- Manual: self-managed build against a repo with a newer tag → notification
  appears once, dismissal persists across restarts, "remind me later"
  re-arms after 7 days (simulate by clock override in a debug build).
- Manual: managed build (flag set) → no check made (verify with a proxy or
  log).

## Unresolved questions

1. **Notification surface** — in-app banner vs system notification vs both,
   per platform. **Open.**
2. **Flathub submission for GTK** — if/when it happens, does the Flatpak
   build keep a "new release" notification that opens the Flathub page
   (store pages lag artifacts by days)? **Open.**
3. **Android Play release track** — internal / closed / open / production
   affects whether the direct-APK channel retires. **Open.**
4. **Update the IME too?** The Android keyboard service is a separate
  surface — should it also notify, or only the main app? **Open** (leaning
   main-app-only; the IME has no room for banners).

## Resolution

- State: pending — open for discussion
- Decided by: —
- Date: —
- Decision: Not yet accepted. Dasher-Windows' UpdateChecker is the seed
  implementation; no other frontend has shipped the behaviour.
- Open sub-questions: all (see Unresolved questions).
