---
rfc: 0012
title: Typing rate (CPS / WPM) display
status: implemented
platforms: [apple, windows, gtk, android, core]
created: 2026-07-18
updated: 2026-08-01
---

# Typing rate (CPS / WPM) display

## Summary

Show the user's typing speed — **characters per second (CPS)** and **words per
minute (WPM)** — live, over a short rolling window so it is responsive but
stable. Always visible in **game mode**; **opt-in** during regular use via a
Settings toggle. Computed **engine-side** (DasherCore) and exposed through the
C API so every frontend displays the same number.

## Implementation status

Audited August 2026. The engine layer is done. DasherCore exposes
`dasher_get_wpm` and `dasher_get_cps` (WPM = CPS × 12).

| Platform | State | Notes |
| --- | --- | --- |
| Dasher-Apple (iOS, macOS) | Implemented | Live WPM, max, and average in the canvas overlay and in game mode; a Settings toggle (`showTypingRate`). CPS is not shown; only WPM. |
| dasher-web | Implemented | Own JS engine; live WPM, peak WPM, and accuracy. Does not consume the DasherCore C API. |
| Dasher-Windows | Not started | No WPM or CPS display. |
| Dasher-GTK | Not started | The bundled DasherCore predates `dasher_get_wpm`. |
| Dasher-Mobile (Android) | Not started | The bundled DasherCore fork predates this feature. |

## Motivation

- Typing rate is *the* headline Dasher outcome metric — valued by AAC/AT users,
  therapists, and researchers. Today it is invisible during normal use.
- Game mode already tracks per-sentence chars/sec internally (`CGameModule`:
  `m_uiTotalSyms / m_ulTotalTime`) — but only prints it in a log line at phrase
  end, never live.
- The metric should be consistent across all frontends (the project's stated
  cross-platform parity goal).

## Detailed design

### Metric definitions

- **CPS** = output characters **produced** per second over the rolling window.
  "Produced" = a character inserted into the output buffer (a text-output
  event). Deletions are **not** counted (they are editing, not production) —
  this is "characters typed" in the productive-throughput sense.
- **WPM** = `CPS × 12`. Standard convention: 1 word = 5 characters, 60 s/min →
  `CPS × 60 / 5 = CPS × 12`.
- **Gross** for v1 (all produced characters: letters, spaces, punctuation).
  Net WPM (error-adjusted) is a future option.

### Rolling window

- Window = the last **5 seconds** of output events (timestamped char counts).
- **Pause handling:** if no output occurs for **> 2 s**, the window freezes
  (keeps displaying the last rate) and a fresh window begins on the next
  character. Idle time never drags the rate toward zero while the user pauses
  intentionally.
- Updated each frame inside `dasher_frame` (which already receives `time_ms`).

### Data source — engine-side C API (recommended)

DasherCore owns the authoritative output character count (it emits the output
events and tracks the offset). Add a small typing-rate tracker that observes
output events + frame time, maintains the rolling window, and expose:

```c
// Characters produced / sec over the rolling window (0.0 if idle / no data yet).
DASHER_API double dasher_get_cps(dasher_ctx* ctx);
// CPS × 12 (one source of truth for the WPM formula).
DASHER_API double dasher_get_wpm(dasher_ctx* ctx);
```

Game mode reuses this for the **live** rate; the existing cumulative
`CGameModule` stats (total time / syms / nats shown at phrase end) remain
unchanged.

**Why engine-side:** cross-platform consistency (one implementation, one
number, one WPM formula); the engine already has the authoritative output
count and the frame clock; game-mode stats already live here as precedent.
Cost: a DasherCore addition + submodule bump.

### UI

- **Game mode (always on):** show `CPS` and `WPM` in / near the game target bar
  (next to the existing `correct / target` display). Throttle UI updates to
  ~2 Hz (not every frame) so the number doesn't churn.
- **Regular use (opt-in):** a new boolean setting `BP_SHOW_TYPING_RATE`
  (group: "Output", or a small "Statistics" group — per RFC 0006 IA). When on,
  a small CPS/WPM badge in the toolbar or a canvas corner. **Off by default**
  so it doesn't clutter the main writing view.
- Format e.g. `4.2 cps · 50 wpm`; labels localised per RFC 0003.

### Privacy

CPS/WPM are derived from **character count + time only** — never the typed
content. Safe to display locally. An aggregate (e.g. session-average WPM) could
be sent to PostHog later as a non-content property; out of scope for v1.

## Drawbacks

- Adds engine state + a small C API surface (vs a pure-frontend computation).
- The window (5 s) and pause threshold (2 s) are judgement calls — tunable.
- Gross WPM ignores accuracy; users comparing to "net WPM" tests may see higher
  numbers (Dasher's predictive output also has fewer deletes than typing tests).

## Alternatives considered

- **Frontend-side computation** (count output-callback chars + a stopwatch on
  each platform). Rejected as primary: N implementations, drift in the formula
  / window. Viable as a fast first cut if the engine change is delayed.
- **Reuse `CGameModule`'s cumulative stats only** (rate at phrase end, not
  live). Rejected: users want live feedback during writing.
- **True words (space-delimited) per minute.** Rejected: Dasher's predictive
  output + punctuation makes the 5-char standard more stable and comparable
  across alphabets / languages.

## Prior art

- Standard typing-test WPM (5-character-word convention).
- Dasher's own `CGameModule` cumulative chars/sec and nats/sec — the precedent
  this generalises to a live, everywhere-available metric.
- AAC/AT research, where cps and wpm are the primary throughput measures.

## Testing

Per [RFC 0011](./0011-testing.md):

- **Engine unit tests** (DasherCore `tests/`): drive a known sequence of output
  events + frame times; assert CPS/WPM within expected bounds, including the
  pause/freeze behaviour. Invariant: `wpm == cps × 12` (within float tolerance).
- **Frontend (manual):** type at a known cadence; confirm the displayed rate is
  plausible and updates live; confirm the game-mode display and the
  `BP_SHOW_TYPING_RATE` toggle (off-by-default, badge appears when on).

## Unresolved questions

1. **Window length / pause threshold** — 5 s / 2 s proposed. **Resolved
   (2026-08-01).** Shipped in the engine as a 5 s window with a 2 s pause freeze.
2. **Where the regular-use toggle lives** — "Output" group or a new "Statistics"
   group? **Resolved (2026-08-01).** Apple ships a Settings toggle
   (`showTypingRate`) in the Output/statistics area.
3. **Net vs gross WPM** — ship gross first? **Resolved (2026-08-01).** Yes; gross
   for v1, net (error-adjusted) is a future option.
4. **PostHog aggregate** — send session-average WPM as an analytics property?
   **Open.** Not sent today; privacy-safe, non-content.

## Resolution

- State: implemented
- Decided by: maintainers
- Date: 2026-08-01
- Decision: Engine API (`dasher_get_wpm`, `dasher_get_cps`) shipped. Apple (iOS,
  macOS) and web show live WPM. Windows, GTK, and Android pending.
- Open sub-questions: Q4 (session-average WPM as an analytics property).

## History

- 2026-07-18 — initial proposal.
