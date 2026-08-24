---
rfc: 0001
title: Privacy-preserving analytics and crash reporting
status: implemented
platforms: [apple, windows, gtk, android]
created: 2026-06-17
updated: 2026-08-20
---

# Privacy-preserving analytics and crash reporting

## Summary

Add opt-in, anonymised analytics and crash reporting to the Dasher v6
frontends (Apple, Windows, GTK) using a self-hosted PostHog instance. The
goal is to understand how many people use Dasher, on which platforms, with
which input methods and languages — and to get visibility into crashes —
without ever collecting what users type. Collection is strictly opt-in via
a first-run prompt, the event schema is published openly in the repo, and
no personally identifiable information is sent.

## Implementation status

Audited August 2026 (re-audited 2026-08-20 against the live PostHog project).
Implemented on Apple, Windows, Android, and GTK; not started on web.

| Platform | State | Notes |
| --- | --- | --- |
| Dasher-Apple (iOS, macOS) | Implemented | PostHog SDK wired in; opt-in prompt; seven-event schema; Settings toggle and reset-ID control. |
| Dasher-Apple (visionOS) | Partial | The SDK is linked, but the opt-in prompt is not shown, so reports do not leave the device until the user opts in elsewhere. |
| Dasher-Windows | Implemented | PostHog SDK; opt-in dialog; published schema. |
| Dasher-GTK | Implemented | Custom libcurl transport + offline queue + first-run consent ([Dasher-GTK #24](https://github.com/dasher-project/Dasher-GTK/pull/24), [#32](https://github.com/dasher-project/Dasher-GTK/pull/32)); crash capture per RFC 0009. Not yet in a tagged release, so no GTK events appear in PostHog. |
| Dasher-Mobile (Android) | Implemented | PostHog SDK; opt-in prompt; published schema; crash reporting via captureException. |
| dasher-web | Not started | No analytics code. |

### 2026-08-20 live audit findings and fixes

An audit of the live PostHog project found and fixed three deviations:

1. **Location data was being collected (Apple and Android).** PostHog Cloud
   enriches every event with `$geoip_*` properties — city, postal code, and
   latitude/longitude — derived from the client IP. This happens even with the
   project's *anonymize IPs* setting enabled, and violates this RFC's
   "no location data" promise. Fixed by sending `$geoip_disable: true` on
   every event (the only Cloud-level control). Historical events already
   enriched retain location properties until retention expires.
2. **Windows events had no `$os`.** The dotnet SDK sends no OS context, so
   OS breakdowns in PostHog only showed Apple/Android data. Fixed by setting
   `$os` explicitly on Windows. Android's SDK-supplied `$os` is the coarse
   string "Android"; version granularity lives in `os_version` on all
   platforms.
3. **Apple was auto-collecting lifecycle events** (`Application Opened`,
   `Application Backgrounded`, `Application Installed`) not present in the
   published schema, violating "if it's not in the schema, it's not
   collected". Fixed by disabling `captureApplicationLifecycleEvents`.

**Hosting note:** the live instance is **PostHog Cloud EU**
(`eu.i.posthog.com`), not the self-hosted deployment this RFC originally
resolved on. Maintainers should either amend the resolution to accept Cloud
EU or stand up the self-hosted instance and migrate the frontends' host
configuration.

The self-hosted PostHog instance and the open event schema are the agreed
direction. `input_method_changed` is now emitted by Dasher-Windows and
Dasher-Android (confirmed in live data, August 2026); Apple and GTK still
do not emit it.

## Motivation

Dasher v5 and below had **no telemetry whatsoever**. We do not know:

- How many people use Dasher (daily/monthly active users).
- Which platforms they are on.
- Which input methods (eye-gaze, switch, touch, joystick) are actually used.
- Which languages/alphabets are most popular.
- Why Dasher crashes for users when it does.

This blind spot makes it hard to prioritise development, justify funding
applications ("Dasher has N active users on platform X"), and fix crashes
that users experience but never report.

Dasher is free, open-source, and used by a vulnerable population (people
with disabilities, often in clinical or educational settings). Any analytics
must respect that context. This RFC proposes a privacy-first approach that
gives the project useful data without compromising user trust.

## Detailed design

### Provider: self-hosted PostHog

PostHog is open-source (MIT-licensed for the core product), self-hostable,
and provides:

- **Event analytics** (DAU/MAU, funnels, trends)
- **Crash reporting** (exception tracking with stack traces)
- **Feature flags** (gradual rollouts without app store releases)
- **Session replay** (DISABLED by default — not appropriate for an
  assistive text-entry tool)

The PostHog instance would be self-hosted on infrastructure controlled by
the Dasher Project (not PostHog Cloud), so raw data never leaves the
project's control.

### SDK integration per platform

| Platform | SDK | Notes |
| --- | --- | --- |
| Apple (iOS/macOS/visionOS) | [`posthog-ios`](https://github.com/PostHog/posthog-ios) (Swift) | Single SDK covers all Apple platforms via SPM |
| Windows (Avalonia/.NET) | [`posthog-dotnet`](https://github.com/PostHog/posthog-dotnet) | NuGet package |
| GTK (C++/gtkmm) | HTTP ingest API via libcurl | No official C++ SDK; ~100-line wrapper around `POST /capture` |

### Opt-in flow

1. **First launch** after update (or fresh install): a simple dialog
   explains what data is collected, with a link to the full privacy
   policy and the open event schema.
2. User taps **"Help improve Dasher"** (opt-in) or **"Not now"** (opt-out).
3. The choice is stored locally and respected permanently unless changed
   in Settings.
4. **No analytics events are sent before the user makes a choice.**
5. The setting is accessible in Settings > Privacy at any time.

### Event schema (published openly)

All events are defined in a JSON or YAML schema file committed to the repo
(`analytics-events.json` or similar). The schema is the single source of
truth — if it's not in the schema, it's not collected.

**Proposed events (v1):**

| Event | Properties | Trigger | PII? |
| --- | --- | --- | --- |
| `app_launched` | platform, os_version, app_version, locale | App starts (after opt-in) | No |
| `input_method_changed` | method (pointer/touch/switch/joystick/tilt) | User selects input method | No |
| `alphabet_selected` | alphabet_id (e.g. "English.English") | User picks alphabet | No |
| `settings_viewed` | tab_name (customization/input/language/output) | User opens settings | No |
| `crash` | platform, os_version, app_version, stack_trace | Uncaught exception | No (stack traces may contain file paths but not user text) |

**Explicitly NOT collected:**

- Typed text or symbols (ever)
- Clipboard contents
- Dasher canvas contents / node positions
- User name, email, or account info
- IP address (scrubbed at ingest)
- Training text contents
- Game mode target text

### Anonymous identity

- A random UUID is generated locally on first launch (after opt-in) and
  stored in app preferences. This is the `distinct_id` sent to PostHog.
- The UUID is not derived from any hardware identifier, account, or PII.
- It cannot be correlated back to a person.
- Users can reset it in Settings > Privacy ("Reset analytics ID").

### Offline behaviour

- Events are queued locally (SQLite or plist) when offline.
- Sent in batch on next launch.
- Queue is capped at 500 events; oldest dropped if exceeded.
- No UX impact — all network happens on a background thread/process.

### Privacy policy

A short, plain-language privacy page will be added to the website
(`/privacy/`) and linked from:

- The opt-in dialog in-app
- The App Store privacy nutrition label (Apple)
- Settings > Privacy on every platform

### Platform-specific notes

**Apple:**
- App Store requires a Privacy Nutrition Label declaring all data
  collected. Since collection is opt-in, the label can state "Data is not
  collected from the app" with a note that optional analytics are
  available.
- The `posthog-ios` SDK handles background sending, batching, and offline
  queueing.
- iOS keyboard extension: **no analytics from the keyboard extension**
  (too memory-constrained, too privacy-sensitive). Only the main app.

**Windows:**
- `posthog-dotnet` provides automatic crash capture via
  `AppDomain.UnhandledException`.
- Avalonia's crash reporting hooks integrate cleanly.

**GTK:**
- No SDK available; a thin C++ wrapper using libcurl to POST events to
  the PostHog ingest endpoint (`/capture`).
- Crash capture via signal handlers (`SIGSEGV`, `SIGABRT`) or
  `std::terminate` handler.
- The wrapper will be a single file (`AnalyticsClient.{h,cpp}`) that can
  be reused.

## Drawbacks

- **Adds a network dependency** to what was previously a fully offline
  tool. Some users and institutions (especially clinical settings) may
  object to any network activity, even opt-in.
- **Maintenance burden** of a self-hosted PostHog instance (server,
  updates, storage costs).
- **GTK C++ wrapper** is custom code that must be maintained without an
  official SDK.
- **Risk of community backlash** if the opt-in flow is perceived as
  manipulative or the data collection is not transparent enough. (cf.
  Audacity, who faced significant pushback for adding telemetry.)
- **GDPR / UK GDPR compliance** requires a legitimate basis for
  processing. Opt-in consent covers this, but a privacy policy and data
  retention policy must be maintained.

## Alternatives considered

### A. Crash reporting only (Sentry)

Use Sentry (or similar) for crash reporting, skip usage analytics.
- **Pros:** Lower privacy footprint, Sentry has good C++/.NET/Swift SDKs,
  free tier sufficient.
- **Cons:** Doesn't solve the "we don't know how many users we have"
  problem. Still adds a network dependency.
- **Verdict:** Worth considering as a fallback if the analytics portion
  is rejected. Could be a phase 1.

### B. Download counts only

Use GitHub release downloads, App Store Connect analytics, and Linux
package manager stats.
- **Pros:** Zero code changes, zero privacy concerns.
- **Cons:** Misses macOS (not in MAS), sideloaded installs, Linux builds
  not from package managers. No crash visibility. No feature usage data.

### C. Privacy-preserving ping

A minimal "I launched Dasher" HTTP request with just platform + version,
no SDK.
- **Pros:** ~20 lines per frontend, near-zero privacy footprint.
- **Cons:** No crash reporting, no feature usage, still needs a server
  to receive pings.

### D. Platform-native telemetry

Rely on OS-level telemetry (Windows Diagnostic Data, macOS analytics).
- **Pros:** No code changes.
- **Cons:** Not under our control, inconsistent across platforms, users
  may have disabled it globally, provides no crash visibility for Dasher
  specifically.

## Prior art

- **Firefox** collects opt-out telemetry but anonymises aggressively.
  Publishes a [data collection policy](https://www.mozilla.org/en-US/privacy/firefox/).
- **VS Code** has opt-in telemetry with three levels (off, crash only,
  full). [Documentation](https://code.visualstudio.com/docs/supporting/faq#_how-to-disable-telemetry-reporting).
- **Homebrew** uses anonymous analytics via a simple ping system.
  [Details](https://docs.brew.sh/Analytics).
- **Audacity** faced significant community backlash when adding
  telemetry without sufficient transparency — a cautionary tale.
- **Dasher v5**: no telemetry at all. This is the baseline we are
  improving on.

## Unresolved questions

1. **Who hosts the PostHog instance?** **Resolved (2026-08-01).** A self-hosted
   PostHog instance is live; Apple (iOS, macOS) and Windows ship against it.
2. **Data retention period?** **Open.** Proposed 13 months (the PostHog default).
   Confirm against the configured value on the live instance.
3. **Should crash reporting be opt-in separately from usage analytics?**
   **Resolved (2026-08-01).** No. Crashes use the same opt-in, specified in
   [RFC 0009](./0009-crash-reporting.md).
4. **Do we need a consent flow per platform, or is a single project-wide privacy
   policy sufficient?** **Resolved (2026-08-01).** One published event schema,
   with a per-platform opt-in prompt (Apple and Windows ship it).
5. **Should the event schema live in DasherCore (shared) or in each frontend
   repo?** **Resolved (2026-08-01).** Per-frontend. Apple and Windows each ship
   their own `analytics-events.json`.

## Resolution

- State: implemented
- Decided by: maintainers
- Date: 2026-08-01
- Decision: Opt-in PostHog analytics shipped on Dasher-Apple (iOS, macOS) and
  Dasher-Windows. GTK, Android, and web have not started. Crashes fold into the
  same opt-in via [RFC 0009](./0009-crash-reporting.md).
- Open sub-questions: Q2 (confirm the configured retention period).
