# RFCs

This directory holds the Dasher Project's **Requests for Comments** — the
lightweight design-review process for substantial changes, described in the
[governance README → Decision making](../README.md#decision-making).

The process is closely based on [Rust's RFC model](https://github.com/rust-lang/rfcs).

## How to propose an RFC

1. Discuss the idea with the community first (Slack / an issue).
2. Copy [`0000-template.md`](./0000-template.md) to a new file
   `NNNN-short-name.md` (pick the next free number — `0001`, `0002`, …).
3. Fill it in. For cross-platform UX/hardware changes, describe the approach on
   **each** platform so other maintainers can align.
4. Open a pull request against this repository (or the most relevant repo, if
   the RFC is single-repo). Share it widely on our comms channels.
5. Discussion happens on the PR. The author revises in place.
6. After **at least 7 days**, maintainers + stewards reach consensus and the RFC
   is marked `active` (accepted) or `rejected`.

> **Testing (per [RFC 0011](./0011-testing.md)).** Every RFC includes a short
> `Testing` section stating whether the change is testable automatically, by
> manual verification, or both — and where the tests live. "Manual verification
> only" is valid. This is **expected, not a hard gate**: a thin or missing test
> plan does not block `active`, but reviewers will ask about it. Privacy,
> data-egress, and correctness claims should name the test that asserts them.

## RFC statuses

| Status | Meaning |
| --- | --- |
| `draft` | Early work-in-progress; not yet ready for formal consensus |
| `proposed` | Drafted, under discussion |
| `active` | Accepted, ready to implement |
| `implemented` | The change has landed |
| `rejected` | Not accepted |
| `withdrawn` | Author withdrew the proposal |

## Keeping RFCs current

An RFC body should always describe the **current** design — not a history of
changes. When a design evolves:

- **Edit the body in place** so it reads as one coherent spec.
- Append a short, dated entry to a `## History` section at the end (what
  changed + a link to the PR).
- **Avoid appending "Amendment N" sections** that supersede earlier body text.
  A reader should never have to reconcile "the base says X, but amendment 3 says
  not X". If a change is large, **rewriting the RFC** (same number, new body) is
  preferred over stacking amendments.

This keeps RFCs readable for someone arriving fresh.

## Index

The `Status` column is the RFC's lifecycle state (see above). Most RFCs now carry
an `## Implementation status` section that records, platform by platform, what is
actually built. Read that section for the real picture — `implemented` often
means "landed on some platforms, not all."

| # | Title | Status | Platforms |
| --- | --- | --- | --- |
| _0000_ | _(`0000-template.md` — not a real RFC)_ | — | — |
| [0001](./0001-analytics.md) | Privacy-preserving analytics and crash reporting | implemented | apple, windows, gtk, android |
| [0002](./0002-lucide-icons.md) | Adopt Lucide as the cross-platform icon set | implemented | apple, windows, gtk, android |
| [0003](./0003-multilingual-ui.md) | Multilingual UI support across all frontends | active | apple, windows, gtk, android, core |
| [0004](./0004-onboarding.md) | First-run onboarding experience | proposed | apple, windows, gtk, android, core |
| [0005](./0005-v5-migration.md) | Dasher v5 → v6 migration: settings, alphabets, and user data | implemented | apple, windows, gtk, core |
| [0006](./0006-settings-ia.md) | Settings information architecture and progressive disclosure | implemented | apple, windows, gtk, android, core |
| [0007](./0007-dark-mode-palettes.md) | Dark mode support via appearance-aware colour palettes | implemented | apple, windows, gtk, android, web, core |
| [0008](./0008-keyboard-onboarding.md) | Keyboard extension / IME onboarding (Apple & Android) | proposed | apple, android, core |
| [0009](./0009-crash-reporting.md) | Crash reporting & engine diagnostics capture | implemented | apple, windows, gtk, android, core |
| [0010](./0010-input-access-methods.md) | Input & access methods (steering/selection/dwell/switch/eye-gaze/joystick) | active | apple, windows, gtk, android, core |
| [0011](./0011-testing.md) | Testing expectations for RFCs | active | apple, windows, gtk, android, web, core |
| [0012](./0012-typing-rate.md) | Typing rate (CPS / WPM) display | implemented | apple, windows, gtk, android, core |
| [0013](./0013-custom-rendering.md) | Node-tree rendering API (custom rendering) | active | apple, windows, gtk, android, web, core |
| [0014](./0014-image-labels.md) | Image labels for alphabet symbols | implemented | apple, windows, gtk, android, web, core |
