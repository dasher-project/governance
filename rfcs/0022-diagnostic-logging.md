---
rfc: 0022
title: Diagnostic logging
status: proposed
platforms: [windows, apple, gtk, android]   # platforms affected
created: 2026-11-02
updated: 2026-11-02
---

# Diagnostic logging

## Summary

A shared diagnostic-logging system so tester-reported logs are parseable
across platforms: standardised file names, a common line format, a
two-level verbosity model (lifecycle always / verbose gated by an
"Advanced logging" setting), version-scoped rotation so each release
starts clean, size caps, and an in-app "Clear logs" affordance. The
November 2026 field lesson: a tester's 40 MB `keyboard_debug.log`
spanning every build ever shipped was unparseable for remote debugging.

## Implementation status

| Platform | State | Notes |
|---|---|---|
| windows | implemented (PR #82) | LogManager + advanced toggle + rotation + clear |
| apple | implemented (Dasher-Apple PR #57: LogManager with version-scoped rotation, 10 MB caps, Advanced-logging toggle, [KB] format; PR #66 adds the Export logs affordance — share sheet on iOS/visionOS, Finder reveal on macOS) | |
| gtk | not started | |
| android | not started | |

## Motivation

Every platform has some form of diagnostic logging, but the formats,
file names, verbosity rules, and lifecycle management are ad-hoc. When
a tester reports a bug, the maintainer needs to know:

- **Which build** produced the log (rotation on version change)
- **What the log means** (a shared format, not per-platform guesswork)
- **That it's readable** (10 MB of unparseable traces is worse than
  10 KB of lifecycle events)
- **That they can get it** (testers can't navigate %APPDATA% or
  adb logcat by hand — an in-app export/clear affordance)

Heide's v0.1.36 report: a 40 MB `keyboard_debug.log` accumulated across
every build since diagnostics were introduced, mixing pre- and post-fix
behaviour, making it impossible to tell whether a fix worked without
manual timestamp archaeology. The paragraph-fix investigation (PR #79)
required isolating the "latest session" by finding gaps in the log —
a heuristic that breaks when sessions overlap.

## Detailed design

### Log files

| File | Content | Platform equivalent |
|---|---|---|
| `keyboard_debug.log` | Direct-mode injection, UIA reads, context seeds, SendInput traces | Windows: `%APPDATA%\Dasher\`; Android: app-internal dir; GTK: `~/.local/share/dasher/`; Apple: `~/Library/Application Support/Dasher/` |
| `eyegaze.log` | Eye-tracker lifecycle + verbose per-sample lines | same base dir |

### Line format

```
[KB] HH:MM:SS.mmm <message>
```

- `HH:MM:SS.mmm` — wall-clock local time with millisecond precision
- `<message>` — free text; see the indentation convention below

Additional writers may use category prefixes inside the message
(`[UIA]`, `[Win32]`, `[tracker]`, `[Ctx]`).

### The indentation convention (verbosity gating)

Every diagnostic log line is either **lifecycle** or **verbose**:

- **Lifecycle** (always written): engine created, tracker connected/
  disconnected, errors, context-seed decisions (skip/seed), mode
  changes, version transitions. These are the minimum for remote
  debugging and are written regardless of the toggle.
- **Verbose** (only when "Advanced logging" is ON): per-keystroke
  SendInput traces, per-sample eye-tracker lines, UIA read internals,
  per-frame timing diagnostics. These generate megabytes during active
  use.

The convention: **verbose lines are indented with a two-space prefix**;
lifecycle lines start at column 0. This makes the gate a one-line check
per writer method, and makes the log visually scannable (dense indented
blocks = verbose sections).

```
[KB] 17:01:28.381 EngineOutput insert: " "
[KB] 17:01:28.386   SendInput(' '): cbSize=40 sent=2   ← verbose (indented)
[KB] 17:01:29.037 Context seed (caret moved): sentence unchanged      ← lifecycle
```

### The "Advanced logging" toggle

A single setting in each platform's Settings UI, replacing any
per-subsystem logging toggles. Help text warns: *"Detailed diagnostic
logging for bug reports. Basic connection events are always logged.
May generate large log files."*

The toggle controls ALL verbose logging (keyboard traces, eye-tracker
per-sample, UIA internals) — one switch, not per-subsystem.

### Rotation on version change

At startup, **before any log writes**:

1. Read the last-version marker (`last_version.txt` in the log dir).
2. If the app version has changed: rename each live log to
   `{name}.v{old-version}.log` (the previous session's diagnostics,
   scoped to the build that produced them).
3. Start a fresh log for the current build.
4. Write the current version to the marker.

**Version identity**: use the informational/marketing version (the one
users see), not the assembly version — AssemblyVersion is often `0.0.0`
or `1.0.0` in dev builds, which would make every local run "the same
version" and never rotate.

### Size caps and truncation

- **Cap**: 10 MB per log file.
- **Truncation**: at the NEXT startup (never mid-write — that would
  corrupt a line), truncate to the last 1000 lines. This runs BEFORE
  rotation so an oversized live log doesn't become an oversized archive.
- **Archives**: subject to the same cap (a pre-existing 40 MB archive
  from before this RFC is truncated on first run).
- **Retention**: keep at most 2 archives per log name; older archives
  are deleted.

### In-app management

A "Clear logs" button in Settings showing the total log size (live +
archives). Deletes all managed logs and resets the size display.
Testers can't be expected to navigate `%APPDATA%\Dasher` or run
`adb shell` by hand.

### Per-platform mapping

| Concern | Windows | Android | GTK | Apple |
|---|---|---|---|---|
| Log dir | `%APPDATA%\Dasher\` | app-internal (`getFilesDir()`) | `~/.local/share/dasher/` | `~/Library/Application Support/Dasher/` |
| Verbose gate | `msg.StartsWith("  ")` check in each Log method | same convention (indent verbose lines) | same | same |
| Rotation | `LogManager.Initialize()` at App startup | Application `onCreate` | `main()` init | `applicationDidFinishLaunching` |
| Toggle in | Settings → Input | Settings → Privacy | Preferences → Diagnostics | Settings → Privacy |
| Clear button | Settings → Input (with size display) | Settings → Privacy | Preferences | Settings |

## Drawbacks

- The two-space indent convention is a social contract, not a type
  system — a new writer that doesn't follow it leaks verbose lines past
  the gate. Mitigated by code review and the convention being cheap
  to apply.
- Wall-clock timestamps are not monotonic (NTP adjustments). For
  intra-line deltas this is fine; for cross-process correlation,
  monotonic clocks would be needed (not worth the complexity).
- The 10 MB cap is per-file, not per-session: a very long session with
  advanced logging on could exceed it and get truncated mid-diagnostic
  at the next startup.

## Alternatives considered

- **Structured logging (JSON lines)**: more parseable but harder to
  read by hand in a text editor, and testers sometimes read their own
  logs to describe what they saw. Free-text with the timestamp/indent
  convention is the right balance.
- **Per-subsystem toggles** (keyboard verbose, eyegaze verbose
  separately): rejected — one switch is simpler for testers and the
  advanced-logging use case (full detail for a bug report) always wants
  everything.
- **Log rotation by time (daily/weekly)**: rejected — version-scoped
  rotation is strictly better for the "which build produced this"
  question, and time-based rotation would split a single session
  across files.

## Prior art

- RFC 0009 (crash reporting): the engine-log ring buffer for crash
  reports is a separate, in-memory concern; this RFC covers the
  on-disk diagnostic files that testers send.
- Android's `logcat` verbosity levels (V/D/I/W/E): the
  lifecycle/verbose split is a deliberate simplification to two levels
  — the field lesson is that testers don't distinguish five levels.

## Unresolved questions

- Should the engine (DasherCore) also write to these files via the
  log callback, or is the engine log ring buffer (RFC 0009) sufficient?
  Current: engine logs go to the ring buffer for crash reports; the
  frontend diagnostic files capture the frontend-side interaction.
- Should there be an in-app "Export logs" (zip the dir) alongside
  Clear? Heide's zip upload worked; automating it would be better.

## Testing

- **Windows (automatic)**: the LogManager class is testable (rotation,
  truncation, archive pruning are pure file operations). The verbosity
  gate can be asserted by inspecting the log after operations with the
  toggle on/off.
- **Cross-platform (manual)**: verify each platform's log format matches
  (timestamp, indent convention) by comparing a sample from each.
