# Contributing to the Dasher Project

Thanks for your interest in contributing! This guide covers **how** changes get
made across the Dasher Project. The short version: be kind (see the
[Code of Conduct](./code-of-conduct.md)), sign your work (DCO), and open an RFC
for anything substantial.

Dasher v6 is **one shared engine** ([DasherCore](https://github.com/dasher-project/DasherCore),
C++ with a flat C API) consumed by several **native frontends**. Most code
contributions belong in a specific repo, not this one:

| Repo | What lives here |
| --- | --- |
| [DasherCore](https://github.com/dasher-project/DasherCore) | The shared engine + the `dasher_*` C API that every frontend calls |
| [Dasher-Apple](https://github.com/dasher-project/Dasher-Apple) | iOS / macOS / visionOS (SwiftUI) |
| [Dasher-Windows](https://github.com/dasher-project/Dasher-Windows) | Windows (Avalonia / .NET) |
| [Dasher-GTK](https://github.com/dasher-project/Dasher-GTK) | Linux + Win/macOS fallback (GTK4) |
| [Dasher-Android](https://github.com/dasher-project/Dasher-Android) | Android (Kotlin / Jetpack Compose) + IME |
| [dasher-web](https://github.com/dasher-project/dasher-web) | In-browser WASM app |
| [website](https://github.com/dasher-project/website) | [dasher.at](https://dasher.at), docs, public feature status |
| **governance** (this repo) | Roles, decision-making process, RFCs, funding logs |

## Developer Certificate of Origin (DCO)

Every commit must be signed off under the
[Developer Certificate of Origin](https://developercertificate.org/). This
attests that you wrote the change or have the right to contribute it.

The easy way: use `git commit -s` (or configure `git config format.signoff true`
in your clone), which appends a `Signed-off-by: Your Name <you@example.com>`
line matching your commit identity. Maintainers will block PRs that are missing
it. If you forget, `git commit --amend -s --no-edit` fixes the last commit.

## Branches, commits, PRs

- Work on a **feature branch**, not `main`. Descriptive name, e.g.
  `feat/android-crash-reporting` or `rfcs/add-android-platform`.
- Keep commits focused; write a clear message (most repos follow
  [Conventional Commits](https://www.conventionalcommits.org/) —
  `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
- Open a PR against `main`. CI runs a DCO check and (per repo) a build gate.
- Mark PRs that need cross-platform alignment with the relevant RFC link.

## When to open an RFC

Any **substantial** change — architectural, cross-platform UX, a new platform,
a privacy/security-relevant feature, or a process change — goes through the
[Decision making](./README.md#decision-making) process and starts as an RFC in
[`rfcs/`](./rfcs). The bar is "would another maintainer want a say?" — when in
doubt, open a short draft RFC and ask.

Each RFC declares which **platforms** it affects in its frontmatter. When you
add a feature to a platform that an existing RFC covers, update that RFC's
`platforms:` line and the table in [`rfcs/README.md`](./rfcs/README.md).

## Adding or updating a platform

If you are bringing a new frontend onto a shared feature (or bringing a new
frontend up at all):

1. Read the relevant RFCs end-to-end — they describe the cross-platform contract.
2. Consume DasherCore **only through its C API** (`dasher.h`); do not link engine
   classes directly. This keeps the engine free to evolve.
3. Add your platform to the affected RFCs' `platforms:` matrices and the
   `rfcs/README.md` index.
4. Where a platform genuinely cannot match the contract (e.g. no eye-gaze API,
   memory-constrained keyboard extension), call it out in the RFC's
   platform-specific notes rather than silently diverging.

## Questions

- Discussion: the Dasher Slack (see the website for the current invite).
- Process bugs / improvements to *this* repo: open an issue or PR here.
