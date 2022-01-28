# Governance WORKING DRAFT <!-- omit in toc -->

The official governance model for all the projects in the dasher project

- [Roles](#roles)
  - [Stewards](#stewards)
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

We have a identified a the following roles within the project. Each individual and organizations involved in the project acts within one of these roles.

## Stewards

The current steward of the project is [Ace Centre](http://acecentre.org.uk/). Ace Centre currently delegates two individuals to act as stewards on their behalf. Currently the stewards are [Gavin Henderson](https://acecentre.org.uk/about/staff/gavin-henderson) and [Will Wade](https://acecentre.org.uk/about/staff/will-wade).

The expectations of stewards are as follows:

- To make sure maintainers and contributors have the tools to be successful
- To apply for new funding
- To make make clear the needs of the end users
- To make sure that project development is always moving towards current aims and goals
- To facilitate discussions about the direction of the project
- To regularly update everyone involved with the project about its current progress
- All the expectations of maintainers also apply
- To make sure that major decisions follow the decision making process

## Maintainer

The expectations of maintainers are as follows:

- Triage bug and feature requests
- Engage with discussions on Slack
- Create a welcoming environment for new contributors
- Enforce the [Code Of Conduct](./code-of-conduct.md)

Here are a current list of codebases and their maintainers:

- [website](https://github.com/dasher-project/website)
  - [Will Wade](https://github.com/willwade)
  - [Gavin Henderson](https://github.com/gavinhenderson5)
- [dasher-web](https://github.com/dasher-project/dasher-web)
  - [Jim](https://github.com/sjjhsjjh)
  - [Jeremy Cope](https://github.com/jcope)
  - [Gavin Henderson](https://github.com/gavinhenderson5)
  - [Adam Spickard](https://github.com/aspickard)
- [dasher-captivewebview](https://github.com/dasher-project/dasher-captivewebview)
  - [Jim](https://github.com/sjjhsjjh)
- [dasher-electron](https://github.com/dasher-project/dasher-electron)
  - [Adam Spickard](https://github.com/aspickard)
  - [Gavin Henderson](https://github.com/gavinhenderson5)
- [dasher](https://github.com/dasher-project/dasher)
  - Unmaintained

## Contributor

A contributor is anyone who contributes to the project. Contributions are not limited to code changes. Joining in a discussion, opening an issue, giving feedback and writing docs are all considered as 'contributions'.

Everyone is welcome as a contributor.

There are no expectations, other than all contributions must abide by the [Code Of Conduct](./code-of-conduct.md).

# Funding

Dasher Project, requires a significant amount of engineering resources to add new features and improve the project. Unfortunately we can not always rely on the generosity of engineers donating their free time, or outside companies donating their engineering resource.

Ace Centre will apply for funding on behalf of the Dasher Project. All funding received will be paid to Ace Centre who will then invest funds directly back into the Dasher Project.

When spending the funding we will always allow existing maintainers and contributors the opportunity to get paid in exchange for their time completing pre agreed work. If no existing maintainers or contributors are available to complete the work we will look for outside contractors to complete the work using the funding.

When appropriate Ace Centre will use some of the money to cover the cost of future time invested in the Dasher Project. When this is done it will be explicit. We will prioritize new features and development over covering our costs.

All funding received and spent will be done in a public manner. There will be open discussions about funding and spending on our communication channels. However, we will explicitly maintain a spending log for each financial year in this repository. See below the spending/funding logs:

- [FY2022](./FY2022.md)

# Decision making

Each major decision starts as a Request for Comments (RFC). Everyone is invited to discuss the proposal, to work toward a shared understanding of the tradeoffs.

The decision making process only needs to be followed when making 'substantial' changes. Changes don't just apply to code but also architectural, product and process changes. If you are unaware if your change constitutes 'substantial' then feel free to open an RFC with minimal detail to ask before you commit to completing a full RFC.

The decision making model is closely based on [Rusts RFC model](https://github.com/rust-lang/rfcs).

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

Once you have created the RFC please share it as widely as you can on all communication channels.

## 3. Discussion

All discussion about the RFC should be kept to the issue thread. This will allow the conversation to be open to everyone and will serve as a good way to preserve the history of decisions we have taken.

## 4. Make changes to RFC following discussion

The creator of the RFC will make changes based on the feedback and discussion.

## 5. Reach a consensus

We will try and reach a general consensus on the RFC, whether it should be accepted or rejected. Ideally there will be a consensus with everyone engaging in the issue.

However, if there the only consensus required is that of the maintainers and stewards.

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
