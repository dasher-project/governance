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

## RFC statuses

| Status | Meaning |
| --- | --- |
| `proposed` | Drafted, under discussion |
| `active` | Accepted, ready to implement |
| `implemented` | The change has landed |
| `rejected` | Not accepted |
| `withdrawn` | Author withdrew the proposal |

## Index

| # | Title | Status | Platforms |
| --- | --- | --- | --- |
| _0000_ | _(`0000-template.md` — not a real RFC)_ | — | — |
| [0001](./0001-analytics.md) | Privacy-preserving analytics and crash reporting | proposed | apple, windows, gtk |
| [0002](./0002-lucide-icons.md) | Adopt Lucide as the cross-platform icon set | proposed | apple, windows, gtk |
| [0003](./0003-multilingual-ui.md) | Multilingual UI support across all frontends | proposed | apple, windows, gtk, core |
| [0004](./0004-onboarding.md) | First-run onboarding experience | proposed | apple, windows, gtk, core |
