---
rfc: 0000
title: <short, descriptive title>
status: proposed          # proposed | active | implemented | rejected | withdrawn
platforms: [apple, windows, gtk, android, web, core]   # platforms affected
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# <title>

## Summary

One paragraph explaining the change. What does it do, and at a high level, how?

## Motivation

What problem does this solve? Who feels the pain? Link any issues, user
feedback, or platform-parity gaps from the [feature matrix](https://dasher.at/status/).

## Detailed design

This is the core of the RFC. Describe the proposed change in enough detail that
a maintainer on **another** platform could implement their side of it.

For UX or hardware interactions, cover:

- The behaviour from the user's point of view.
- The DasherCore callback / parameter / API surface used (see [DasherCore's C API](https://github.com/dasher-project/DasherCore/blob/main/docs/C_API.md)).
- How the UI surface looks on **each** affected platform (Apple / Windows / GTK / Web …) and any platform-specific mapping.
- Edge cases: what happens when the hardware isn't present, low-memory modes, keyboard extensions, etc.

## Drawbacks

Why might we _not_ want to do this? What's the cost?

## Alternatives considered

What other approaches did you consider, and why is this one better?

## Prior art

Other apps, previous Dasher versions, or other projects that have solved this.

## Unresolved questions

What do you want input on before this is finalised?

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _accepted / rejected_
- Decided by: _maintainers + stewards_
- Date: _YYYY-MM-DD_
- Decision: _short rationale_
