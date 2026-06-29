---
rfc: 0009
title: Crash reporting & engine diagnostics capture
status: proposed
platforms: [apple, windows, gtk, android, core]
created: 2026-06-28
updated: 2026-06-29
---

# Crash reporting & engine diagnostics capture

## Summary

When Dasher crashes, send a useful report to PostHog (under RFC 0001's opt-in
analytics): the exception type, a scrubbed stack trace, and the last few
seconds of **engine diagnostic logs** so a maintainer can see what DasherCore
was doing when it died. Reports are sent as a PostHog **`$exception`** (Error
Tracking) on the **next launch**, from a small crash file written at crash
time — never from the crashing process itself.

This extends RFC 0001, which left crash detail open. Reference implementation:
**Dasher-Windows**; macOS implemented; iOS/visionOS (production), GTK, and
Android pending.

## The contract

### Event: PostHog `$exception` via `captureException`

Every frontend sends crashes through `PostHog.captureException(...)`, producing
a PostHog **`$exception`** event in the **Error Tracking** product (grouping,
trends, fingerprinting). Do **not** send a custom `capture("crash", …)` event —
it will not appear in Error Tracking.

| Property | Source | Notes |
| --- | --- | --- |
| `exception_type` | handler / reconstructed | e.g. `System.NullReferenceException`, `NSGenericException`, `UncleanShutdown` |
| `stack_trace` | handler / saved | PII-scrubbed; the **saved** stack (PostHog won't have the original at send time) |
| `engine_log_tail` | log ring buffer | last N `(level, message)` lines from `dasher_set_log_callback` |
| `source` | handler | capture hook, e.g. `AppDomain.UnhandledException`, `NSSetUncaughtExceptionHandler`, `unclean_shutdown` |
| `platform`, `app_variant`, `app_version`, `os_version` | SDK defaults | attached automatically by `captureException` |

`distinctId`: `captureException` resolves it from SDK storage, so call
`PostHog.identify(distinctId)` after setup so crashes attribute to the same
anonymous ID as analytics events.

### Deferred send (never call the SDK from a crashing process)

At crash time, write a small **crash file** synchronously (no heap allocation,
no network). On the **next launch**: read it, reconstruct a throwable (Windows:
`SavedCrashException`; macOS: an `NSError` built from the saved type/reason),
call `captureException`, then delete the file.

**Crash file format** (shared shape, pioneered by Windows):

```
exception_type=<full type name>
source=<capture hook>

<stack trace>

--- engine log ---
<engine_log_tail>
```

A different on-disk encoding is acceptable (macOS uses JSON) provided the
resulting `$exception` carries the same properties.

### Engine log ring buffer

Each frontend registers `dasher_set_log_callback` at engine creation and
appends each line to a fixed-capacity ring buffer (recommended **64 lines /
8 KB**), mirrored to an `engine.log` file so it survives a hard crash. Capture
at `min_level = 1` (info) by default; a future "verbose logs" opt-in may lower
this to 0.

### Opt-in gate & retention

No crash is sent unless the user opted into analytics (RFC 0001). The crash
file is still written if not opted in, but is never transmitted; it is
discarded after **7 days**. On send failure (offline), retry up to **3**
launches, then discard.

### PII scrubbing (before anything leaves the device)

- Home-directory segments → `<user>` (`/Users/<user>/`, `C:\Users\<user>\`,
  `/home/<user>/`).
- Email-shaped strings → `<email>`.
- Truncate `stack_trace` → 16 KB and `engine_log_tail` → 8 KB; hard-cap the
  envelope at 32 KB (truncate the tail first).

The engine never places typed text, clipboard, or canvas contents in log lines
(RFC 0001); scrubbers are defence-in-depth.

## Per-platform implementation

| Platform | Hook | Status |
| --- | --- | --- |
| **Windows** | `AppDomain.UnhandledException` + `TaskScheduler.UnobservedTaskException` → crash file → next-launch `CaptureException(SavedCrashException)` | ✅ Done (Dasher-Windows #17) — **reference** |
| **macOS** | `NSSetUncaughtExceptionHandler` + an **alive-marker** unclean-shutdown detector → crash file → next-launch `captureException(NSError)`. Sole channel (non-App-Store app, no TestFlight). | ✅ Done (Dasher-Apple #20) |
| **iOS / visionOS** | **TestFlight** for beta; production build installs the PostHog `$exception` path (same as macOS) | ⏳ Pending |
| **GTK** | `signal(SIGSEGV/SIGABRT)` + `std::set_terminate` → crash file → next launch | ⏳ Pending |
| **Android** | `Thread.setDefaultUncaughtExceptionHandler` (JVM) + a native `sigaction` shim for `libdasher.so` crashes | ⏳ Pending |

**Why macOS uses an alive-marker instead of raw signal handlers.** Swift signal
handlers cannot safely do capture work (async-signal-safety), so macOS writes
an `alive.marker` at launch (cleared on a clean quit); its presence at the next
launch means an unclean shutdown, reported as
`exception_type = UncleanShutdown` with the engine tail. This catches
`fatalError`/SIGSEGV that `NSSetUncaughtExceptionHandler` misses. (Raising an
`NSException` from pure Swift is unreliable and does not reach the handler.)

## Engine side (DasherCore)

DasherCore v0.1.6 makes the engine a first-party participant:

- **Boundary exception capture.** Every `extern "C"` entry point in `CAPI.cpp`
  catches `std::exception` + `...`, routes the failure through
  `dasher_set_log_callback` at level 3 (error), and returns — it never
  propagates across the boundary (generalises CONTRIBUTING Rule 4;
  [DasherCore#34](https://github.com/dasher-project/DasherCore/issues/34),
  fixed in #35). The per-frame hot path (`dasher_frame`, `dasher_mouse_*`,
  `dasher_key_event`) is wrapped (#38). So a boundary exception always appears
  in `engine_log_tail`.
- **Engine error state.** A caught exception sets an internal `engineError`
  flag, exposed via `int dasher_has_engine_error(dasher_ctx*)`. Once set, the
  hot path no-ops. **Frontend contract:** on `dasher_has_engine_error()` → stop
  calling frame, surface a message, then `dasher_destroy` + `dasher_create` (or
  ask the user to relaunch). `dasher_reset` does **not** clear it; only engine
  recreation does.
- **What this does NOT catch:** SEGV/SIGBUS (signals — owned by the per-platform
  handlers/unclean-marker), stack overflow, `DASHER_ASSERT` under `NDEBUG` (a
  no-op in release), and exceptions from destructors (`std::terminate`).

## Apple: TestFlight + PostHog (dual channel)

| Channel | Scope | Best for |
| --- | --- | --- |
| **TestFlight** | Beta builds | Apple-symbolicated native stacks (DasherCore C++ frames); automatic |
| **PostHog `$exception`** | Beta + production | Cross-platform parity; engine log tail; unified with analytics |

Both may be active simultaneously. **macOS** has no TestFlight (direct download)
— PostHog is the sole channel there. iOS/visionOS betas lean on TestFlight;
**production** iOS/visionOS uses the PostHog path.

## Out of scope (stated honestly)

- **Native stack symbolication in PostHog.** `captureException` carries the
  *captured* stack only (managed / Swift / Obj-C frames). It does **not**
  symbolicate native SIGSEGV/SIGABRT frames. For those, rely on OS crash logs
  (macOS `.ips`, the Windows crash dialog) shared manually by the user, or a
  future dedicated crash SDK.
- **A second vendor (Sentry / Crashlytics / Bugsnag).** Rejected for v6's
  PostHog-only, single-vendor, open-source model.

## Drawbacks

- Uncaught-exception / signal handlers are inherently risky inside a crashing
  process — hence the "write a tiny file and re-raise" discipline.
- Native (`libdasher.so` / JNI) crashes on Android are the hardest case; the
  signal shim is extra complexity.
- Collecting *any* log tail with a crash has privacy optics — the privacy
  policy and Settings copy must be explicit.

## Alternatives considered

- **Sentry / Crashlytics / Bugsnag** — better native symbolication, but a
  second vendor; rejected for the PostHog-only model.
- **No engine log tail** (stack trace only) — rejected; engine-side faults are
  exactly the crashes that need engine context.
- **Stream all logs to PostHog continuously** — rejected; violates RFC 0001's
  no-typed-text promise and inflates ingest.

## Prior art

- PostHog SDKs' `captureException` / automatic capture; this RFC adds the engine
  tail they lack.
- Firefox / Sentry "breadcrumbs" — the engine log ring buffer is the same idea.
- Dasher-Windows (#17) is the reference implementation.

## Testing

Per [RFC 0011](./0011-testing.md). Defence-in-depth claims should name a test:

- **PII scrubbing** — a unit test per platform asserting home-dir/email redaction
  and size caps (macOS: `CrashReporter.Scrubber`; Windows: equivalent).
- **Crash-file round-trip** — write → parse → reconstructed throwable (Windows
  `FlushPendingCrash`; macOS `sendPendingCrashIfNeeded`).
- **Engine side** — DasherCore `tests/` covers boundary capture and
  `dasher_has_engine_error` (v0.1.6).
- **End-to-end** — manual: trigger a crash (debug hook or `kill -ABRT`), relaunch,
  confirm a `$exception` lands in PostHog Error Tracking. Verified on macOS.

## Unresolved questions

1. **Android IME process boundary** — should the IME also write a crash file, or
   only the main app? (Proposal: both, suffixed filenames.)
2. **Verbose-log opt-in** — copy and placement of "Send verbose logs with crash
   reports" (Settings → Privacy, per RFC 0006).
3. **Native symbolication** — accept unsymbolicated native frames in v1 (rely on
   user-shared `.ips` / dialogs), or revisit a crash SDK later?
4. **Crash-file format convergence** — switch macOS from JSON to the shared text
   format, or accept both?

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _pending_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_

## History

Rewritten 2026-06-29 as a single coherent spec (was a base + stacked
amendments, which had become hard to read). It folds in:

- TestFlight dual-channel for Apple ([PR #14](https://github.com/dasher-project/governance/pull/14)).
- Engine-side exception capture / `dasher_has_engine_error` ([PR #15](https://github.com/dasher-project/governance/pull/15)).
- PostHog Error Tracking (`$exception`) + crash-file format (originally PR #16,
  closed into this rewrite).

Implementation references: DasherCore v0.1.6 (#38, issue #34/#35),
Dasher-Windows #17, Dasher-Apple #20.
