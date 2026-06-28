---
rfc: 0009
title: Crash reporting & engine diagnostics capture
status: proposed
platforms: [apple, windows, gtk, android, core]
created: 2026-06-28
updated: 2026-06-28
amendments:
  - number: 1
    title: "TestFlight crash reporting for Apple platforms"
    date: 2026-06-28
    issue: 13
---

# Crash reporting & engine diagnostics capture

## Summary

Define a single, cross-platform contract for capturing crashes and engine
diagnostics so that a crash report reaching PostHog (per [RFC 0001][1]) is
**useful** — it must contain the exception, a sanitised stack trace, and the
last few seconds of **engine diagnostic log lines** so a maintainer can
reconstruct what DasherCore was doing when it died. This RFC depends on the
DasherCore C API `dasher_set_log_callback` (added v0.1.3, RFC 0007-adjacent)
which made the engine's former `CFileLogger`/`CBasicLog`/`UserLog` systems
available to frontends as a stream of `(level, message)` events.

This RFC extends [RFC 0001][1] (which left crash detail as an unresolved
question) and is the authoritative spec for the `crash` event.

[1]: ./0001-analytics.md

## Motivation

- Dasher is a beta. Crashes matter. RFC 0001 specified *that* we capture crashes
  and the event name, but not *how* each platform hooks its uncaught-exception
  path, *what* goes in `stack_trace`, or how to capture engine-side context.
- Today the platforms are inconsistent: Windows wires
  `AppDomain.UnhandledException` → PostHog; Apple stubs it (no uncaught handler
  installed); GTK proposes signal handlers; Android has nothing. The result is
  that most crash reports we do get are thin (no engine state), and Android — a
  fast-growing install base — produces no crash data at all.
- The engine now exposes a single diagnostic channel (`dasher_set_log_callback`,
  `dasher.h`) carrying levelled log lines (0 debug / 1 info / 2 warn / 3 error).
  Capturing the **last N** of these into a ring buffer gives every crash report a
  "what was the engine doing" tail — invaluable for diagnosing assert-failures
  and bad-parameter crashes that originate in DasherCore rather than the
  frontend.

## Detailed design

### The crash report envelope

Every crash report is a single PostHog `crash` event with this shape (extends
RFC 0001's table):

| Field | Source | Notes |
| --- | --- | --- |
| `platform` | frontend | `apple` / `windows` / `gtk` / `android` |
| `app_variant` | frontend | e.g. `dasher-android`, `dasher-apple-ios` |
| `app_version` | build | semver |
| `os_version` | OS | e.g. `Android 15`, `iOS 26.5`, `Windows 11 22631` |
| `locale` | engine | `dasher_get_locale` (already sent with analytics) |
| `exception_type` | uncaught handler | e.g. `java.lang.IllegalStateException`, `EXC_BAD_ACCESS`, `System.NullReferenceException` |
| `stack_trace` | uncaught handler | **PII-scrubbed** (see below) |
| `engine_log_tail` | log ring buffer | last N `(level, message)` lines from `dasher_set_log_callback` |
| `signal_or_reason` | handler | e.g. `SIGSEGV`, `Aborting: DASHER_ASSERT` |

The `engine_log_tail` is the new, unifying piece: every frontend keeps a small
in-process ring buffer of the most recent engine log lines (recommended size:
**64 lines, capped at 8 KB total**) and appends it to the crash event.

### Per-platform crash hooks

| Platform | Hook | Notes |
| --- | --- | --- |
| **Android** | `Thread.setDefaultUncaughtExceptionHandler` (JVM) **+** a native `sigaction(SIGSEGV/SIGABRT/SIGILL)` shim for JNI/engine crashes | The JVM handler catches Kotlin/Java throws; the signal shim catches crashes inside `libdasher.so`. Pipe the latter via a `sigwait`-or-`abort` trampoline that writes a minidump line + the ring buffer to a crash file before re-raising. |
| **Apple** | `signal(SIGABRT/...)` + `NSExceptionExceptionHandler` (NSSetUncaughtExceptionHandler) | Capture `callStackSymbols`; write to App Group container; flush on next launch (a crashing process can't safely do network). |
| **Windows (.NET)** | `AppDomain.CurrentDomain.UnhandledException` + `TaskScheduler.UnobservedTaskException` | Already implemented in Dasher-Windows; align fields to this envelope. |
| **GTK** | `signal(SIGSEGV/SIGABRT)` + `std::set_terminate` | async-signal-safe path writes the buffer to disk; flush on next launch. |

**Crash-time discipline.** Inside an uncaught handler you must **not** do work
that can itself crash (no heap allocation, no network, no PostHog SDK calls in
the crashing thread). The handler writes a small **crash file** to the app's
private storage containing the envelope; on the **next launch**, the app
detects the crash file, sends the `crash` event via the normal PostHog SDK
path, and deletes it.

### Engine log ring buffer (shared pattern)

Each frontend, at engine creation, registers a log callback that:

1. Routes lines to the platform log (Android `Log` / Apple `os_log` / Windows
   `Debug`+`engine.log` / GTK `g_log`) — **already done** in Dasher-Android
   (→ logcat, `DasherEngine.installEngineCallbacks`) and Dasher-Windows.
2. Appends `(level, message, monotonic_ms)` to a fixed-capacity ring buffer.
3. The crash handler snapshots the ring buffer into the crash file.

Levels are filtered per RFC 0007's `dasher_set_log_callback(ctx, cb, user, min_level)`
argument. For the ring buffer, capture at `min_level = 1` (info) by default —
debug (0) is too noisy to keep around for a crash, but info+warnings+errors
reconstruct the sequence. A **diagnostic mode** (Settings → Privacy →
"Send verbose logs with crash reports") lowers this to 0 for users who opt in to
helping diagnose a specific issue.

### PII scrubbing

Crash reports can leak via stack traces (file paths containing usernames —
`/Users/jane/…`, `C:\Users\bob\…`, `/data/data/at.dasher.android/…` is fine) and
via the engine log tail if a log line ever included user text. The schema
guarantees (RFC 0001) that **typed text, clipboard, canvas contents, training
text** are never collected, and the engine's `Message()` callback (the only
current log emitter in `CAPI.cpp`) routes user-facing strings but not raw typed
text. Even so, scrubbers **must** run before the envelope is written:

- Home-directory path segments → `<user>` (`/Users/<user>/`, `C:\Users\<user>\`,
  `/home/<user>/`).
- Email-shaped strings → `<email>`.
- Truncate `stack_trace` to 16 KB and `engine_log_tail` to 8 KB.
- Hard cap the whole envelope at 32 KB; truncate the tail first if exceeded.

A scrub unit test must cover each platform's path format.

### When to send

- **Opt-in gate.** No crash event is sent unless the user has opted in to
  analytics (RFC 0001). If the user has *not* opted in, the crash file is still
  written (cheap, local) but **never transmitted**; it is deleted after 7 days or
  on opt-out.
- **First launch after crash.** Detect the crash file, send, delete. If the send
  fails (offline), retry on subsequent launches up to 3 times, then discard.

## Drawbacks

- **Signal handlers and uncaught-exception handlers are inherently risky** to
  run inside a crashing process. The "write a tiny file and re-raise" pattern
  minimises this but is not free; a handler that itself crashes can wedge the
  app. Mitigation: keep the handler path trivial and crash-tested.
- **Native (JNI/.so) crashes on Android** are the hardest case; a JVM
  `UncaughtExceptionHandler` will not see a SIGSEGV in `libdasher.so`. The
  signal shim is extra complexity and must be re-tested per NDK/AGP version.
- **Verbose logs → crash size.** Allowing `min_level = 0` (debug) bloats the
  envelope; opt-in only and hard cap is essential.
- **Privacy optics.** Sending *any* log tail with a crash may worry users even
  with scrubbing. The privacy policy and the Settings copy must be explicit.

## Alternatives considered

- **Crash-only SDK (Sentry / Crashlytics / Bugsnag).** Removes the per-platform
  handler work; gives better native stack symbolication. Cost: another network
  dependency, another vendor, possibly a different retention posture. RFC 0001's
  "alternatives" section already considered this; this RFC keeps the PostHog-only
  model but a future RFC could revisit a dedicated crash tool for native stacks.
- **No engine log tail** (stack trace only). Rejected: the assert failures and
  bad-parameter paths inside DasherCore are exactly the crashes that need engine
  context to diagnose.
- **Stream all logs to PostHog continuously** (not just on crash). Rejected:
  violates RFC 0001's "no canvas/typed-text" promise and inflates ingest; the
  ring-buffer-then-send-on-crash model is the right trade.

## Amendment 1: TestFlight crash reporting for Apple platforms

Apple platforms have a native crash-reporting channel — **TestFlight crash
reporting** (via App Store Connect) — that is complementary to PostHog and
requires zero code integration.

### Dual-channel model

| Channel | Scope | Strengths | Limitations |
| --- | --- | --- | --- |
| **TestFlight** | Beta builds only | Apple-symbolicated native stacks (better for DasherCore C++ frames); automatic; privacy-respected via iOS analytics toggle | Not available for App Store production releases; Apple-only; no cross-platform correlation |
| **PostHog** | Beta + production | Cross-platform parity (same project as Windows/Android/GTK); unified with analytics events; RFC 0009 engine log tail | Requires SDK handler installation; stack symbolication is the frontend's responsibility |

Both channels may be active simultaneously — they do not conflict. TestFlight
collects at the OS level; PostHog collects at the SDK level.

### Recommendation

- **Beta builds (TestFlight):** Both channels active. TestFlight is the primary
  crash-reporting surface for beta testers (better native symbolication);
  PostHog provides the cross-platform event correlation and the engine log tail.
- **App Store releases (production):** PostHog is the primary (and only
  programmatic) channel. TestFlight crash data is not available for production
  builds. Users may still share Apple's native diagnostic logs via Settings →
  Privacy → Analytics & Improvements, but that is OS-level and outside this RFC.

### What this means for the PostHog path on Apple

The PostHog `crash` event envelope (`exception_type`, `stack_trace`,
`engine_log_tail`, per this RFC) applies to the PostHog path only. TestFlight
uses Apple's native crash-reporting format (unsymbolicated binary addresses +
OS metadata) and is not constrained by this RFC's envelope shape.

Dasher-Apple should still install the `NSSetUncaughtExceptionHandler` + signal
handler described in the **Per-platform crash hooks** table above, so that
PostHog receives structured crash data from both beta and production builds.
TestFlight operates independently at the OS level.

## Prior art

- **posthog-ios / posthog-dotnet / posthog-android** all have
  `captureException`/automatic-capture modes; this RFC aligns the envelope and
  adds the engine tail they don't have.
- **Firefox/Sentry** capture a "breadcrumb" tail — the engine log ring buffer is
  the same idea.
- **Dasher-Windows** already implements `AppDomain.UnhandledException` +
  `engine.log`; this RFC generalises that pattern.
- **TestFlight crash reporting** (Apple) is the platform-native equivalent —
  available for beta builds with zero code, providing Apple-symbolicated stacks
  that complement PostHog's structured envelope (see Amendment 1).

## Unresolved questions

1. **Ring buffer process boundary (Android).** The IME runs in the same package
   but the user's crash might be in the IME process. Should the IME also write a
   crash file, or only the main app? (Proposal: both, different filename suffix.)
2. **Symbolication.** Do we ship (or host) dSYM/PDB/.map files to symbolicate
   native stacks, or accept unsymbolicated frames in v1?
3. **Verbose-log opt-in surface.** Is "Send verbose logs with crash reports" the
   right Settings copy and placement (Settings → Privacy, per RFC 0006 IA)?
4. **Retention of crash files pre-opt-in.** 7 days is proposed; is that right
   given some users take longer to decide on the analytics opt-in?

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _pending_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_
