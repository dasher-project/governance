# Governance <!-- omit in toc -->

The official governance model for all the projects in the dasher project

- [Roles](#roles)
  - [Project Lead](#project-lead)
  - [Maintainer](#maintainer)
  - [Contributor](#contributor)
- [Funding](#funding)
- [Decision making](#decision-making)
  - [1. Engage with the community](#1-engage-with-the-community)
  - [2. Create an RFC](#2-create-an-rfc)
  - [3. Discussion](#3-discussion)
  - [4. Make changes to RFC following discussion](#4-make-changes-to-rfc-following-discussion)
  - [5. Reach a consensus](#5-reach-a-consensus)
  - [6. Make changes](#6-make-changes)
- [Resources](#resources)

# Roles

We have identified the following roles within the project. Each individual and organizations involved in the project acts within one of these roles.

## Project Lead

The current project lead is [Will Wade](https://github.com/willwade). The Dasher Project is governed by its maintainers and contributors, with the project lead responsible for coordination and final decisions.

The expectations of the project lead are as follows:

- To make sure maintainers and contributors have the tools to be successful
- To apply for new funding
- To make clear the needs of the end users
- To make sure that project development is always moving towards current aims and goals
- To facilitate discussions about the direction of the project
- To regularly update everyone involved with the project about its current progress
- All the expectations of maintainers also apply
- To make sure that major decisions follow the decision making process

> **Historical note:** The Dasher Project was previously stewarded by [Ace Centre](http://acecentre.org.uk/), with Gavin Henderson and Will Wade acting as delegates. As of 2026, the project is led independently by Will Wade and the Dasher Project maintainer team.

## Maintainer

The expectations of maintainers are as follows:

- Triage bug and feature requests
- Engage with discussions on Slack
- Create a welcoming environment for new contributors
- Enforce the [Code Of Conduct](./code-of-conduct.md)
- Ensure all merged PRs have DCO sign-off (`Signed-off-by:`)

Dasher v6 is one **shared engine** ([DasherCore](https://github.com/dasher-project/DasherCore)) consumed by several **native frontends**. The current active codebases and their most active contributors are:

- [DasherCore](https://github.com/dasher-project/DasherCore) — shared C++ engine + C API
  - [prlw1](https://github.com/prlw1), [ipomoena](https://github.com/ipomoena), [willwade](https://github.com/willwade), [PapeCoding](https://github.com/PapeCoding), [gavinhenderson](https://github.com/gavinhenderson), [cagdasgerede](https://github.com/cagdasgerede)
- [Dasher-Apple](https://github.com/dasher-project/Dasher-Apple) — iOS / macOS / visionOS (SwiftUI)
  - [willwade](https://github.com/willwade)
- [Dasher-Windows](https://github.com/dasher-project/Dasher-Windows) — Windows (Avalonia / .NET)
  - [willwade](https://github.com/willwade)
- [Dasher-GTK](https://github.com/dasher-project/Dasher-GTK) — Linux + Win/macOS fallback (GTK4)
  - [PapeCoding](https://github.com/PapeCoding)
- [Dasher-Android](https://github.com/dasher-project/Dasher-Android) — Android (Kotlin / Jetpack Compose) + IME
  - [willwade](https://github.com/willwade)
- [website](https://github.com/dasher-project/website) — [dasher.at](https://dasher.at), docs + public feature status (Astro)
  - [willwade](https://github.com/willwade), [gavinhenderson](https://github.com/gavinhenderson), [cagdasgerede](https://github.com/cagdasgerede)
- [dasher-web](https://github.com/dasher-project/dasher-web) — in-browser WASM app
  - [sjjhsjjh](https://github.com/sjjhsjjh), [jcope](https://github.com/jcope), [willwade](https://github.com/willwade), [agutkin](https://github.com/agutkin), [gavinhenderson](https://github.com/gavinhenderson)

> Formal maintainer and `CODEOWNERS` assignments are being added per-repo (see each repo's `.github/CODEOWNERS`). The lists above show the most active contributors; the steward-confirmed maintainer roster should be finalised here as those land.

**Legacy / maintenance-only:**

- [dasher-captivewebview](https://github.com/dasher-project/dasher-captivewebview) — [Jim](https://github.com/sjjhsjjh)
- [dasher-electron](https://github.com/dasher-project/dasher-electron) — [Adam Spickard](https://github.com/aspickard), [Gavin Henderson](https://github.com/gavinhenderson)
- [dasher](https://github.com/dasher-project/dasher) — the original GPL C codebase — **unmaintained** (superseded by DasherCore + the native frontends above)

## Contributor

A contributor is anyone who contributes to the project. Contributions are not limited to code changes. Joining in a discussion, opening an issue, giving feedback and writing docs are all considered as 'contributions'.

Everyone is welcome as a contributor.

All contributions must abide by the [Code Of Conduct](./code-of-conduct.md). Code contributions must also be signed off under the [Developer Certificate of Origin (DCO)](https://developercertificate.org/) — see [CONTRIBUTING.md](./CONTRIBUTING.md#developer-certificate-of-origin-dco) for details.

# Funding

The Dasher Project requires a significant amount of engineering resources to add new features and improve the project. Unfortunately we can not always rely on the generosity of engineers donating their free time, or outside companies donating their engineering resource.

The project lead will apply for and manage funding on behalf of the Dasher Project.

When spending funding we will always allow existing maintainers and contributors the opportunity to get paid in exchange for their time completing pre-agreed work. If no existing maintainers or contributors are available to complete the work we will look for outside contractors to complete the work using the funding.

All funding received and spent will be done in a public manner. There will be open discussions about funding and spending on our communication channels. However, we will explicitly maintain a spending log for each financial year in this repository. See below the spending/funding logs:

- [FY2022](./FY2022.md)

# Decision making

Each major decision starts as a Request for Comments (RFC). Everyone is invited to discuss the proposal, to work toward a shared understanding of the tradeoffs.

The decision making process only needs to be followed when making 'substantial' changes. Changes don't just apply to code but also architectural, product and process changes. If you are unaware if your change constitutes 'substantial' then feel free to open an RFC with minimal detail to ask before you commit to completing a full RFC.

The decision making model is closely based on [Rust's RFC model](https://github.com/rust-lang/rfcs).

The purpose of this process is not to be absolute or be overly cumbersome. Its a simple, lightweight process to make sure everyone has their voice heard.

The decision making process is as follows:

## 1. Engage with the community

Before you create an RFC you should discuss the proposal with the community. This will inform your RFC and allow you to preempt any issues with your RFC that you can specifically address in your initial post.

## 2. Create an RFC

Once you have decided to create an RFC you start by creating a new Github Issue. RFCs should be created in the codebase that is most relevant to them. If they are relevant to many repositories then they should be placed in this repository.

You issue should be titled with the format `RFC - Brief Description`.

An RFC should include the following items:

- Summary of change
- Motivation
- Potential Drawbacks
- Alternatives
- Prior Art
- Unresolved questions

> 💡 A ready-made template and the live index of all RFCs live in the [`rfcs/`](./rfcs) directory of this repository: copy [`rfcs/0000-template.md`](./rfcs/0000-template.md) to get started, and see [`rfcs/README.md`](./rfcs/README.md) for the status of every RFC. For cross-platform UX or hardware interactions especially, an RFC should describe the approach on **each** platform so maintainers can align.

Once you have created the RFC please share it as widely as you can on all communication channels.

## 3. Discussion

All discussion about the RFC should be kept to the issue thread. This will allow the conversation to be open to everyone and will serve as a good way to preserve the history of decisions we have taken.

## 4. Make changes to RFC following discussion

The creator of the RFC will make changes based on the feedback and discussion.

## 5. Reach a consensus

We will try and reach a general consensus on the RFC, whether it should be accepted or rejected. Ideally there will be a consensus with everyone who has engaged with the RFC.

However, the only consensus required is that of the maintainers and stewards.

Once the consensus of accepted or rejected is met the RFC issue will be closed and then it should be given a label identifying the status of the RFC.

The consensus cannot be reached until 7 days have passed since the RFC was created.

## 6. Make changes

Once the decision has been made then the changes suggested should be made. If they are significant changes then they might make more sense to open issues referencing the RFC to be completed later.

# Resources

This governance document was created using the following resources.

- [NodeJS Governance](https://github.com/nodejs/node/blob/master/GOVERNANCE.md#collaborator-activities)
- [Open Source Guide](https://opensource.guide/leadership-and-governance/)
- [Red Hat](https://www.redhat.com/en/resources/guide-to-open-source-project-governance-models-overview)
- OSS Watch
  - [Meritocratic Governance Model](http://oss-watch.ac.uk/resources/meritocraticgovernancemodel)
  - [Benevolent Dictator Governance Model](http://oss-watch.ac.uk/resources/benevolentdictatorgovernancemodel)
- [Healthy Open Source](https://medium.com/the-node-js-collection/healthy-open-source-967fa8be7951)
