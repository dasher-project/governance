---
rfc: 0000
title: <short, descriptive title>
status: proposed          # draft | proposed | active | implemented | rejected | withdrawn
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

## Testing

Per [RFC 0011](./0011-testing.md): say whether the change is testable
automatically, by manual verification, or both, and where the tests live.

- Is this change testable automatically, by manual verification, or both?
- For automated tests: which repo(s) and path(s) hold them? (See the repo map
  in [RFC 0011](./0011-testing.md).) Shared invariants ideally land in
  DasherCore's `tests/`; frontend-specific behaviour lands in the frontend's
  test target.
- For privacy, data-egress, security, or correctness claims made elsewhere in
  this RFC: name the test that asserts the claim (e.g. a scrubber test, a
  "no-typed-text-in-payload" schema test).
- If there are no automated tests, say why and how a reviewer verifies the
  change (e.g. a manual run-through, a screenshot, a UX step).

"Manual verification only" is a legitimate answer; the point is that the choice
is written down. A missing test plan does not block an RFC from going `active`,
but reviewers are expected to ask about it.

## Unresolved questions

What do you want input on before this is finalised?

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _accepted / rejected_
- Decided by: _maintainers + stewards_
- Date: _YYYY-MM-DD_
- Decision: _short rationale_

## History

A short, dated log of revisions after the RFC is first proposed (one line per
change + PR link). The body above always reflects the **current** design; this
section is just for traceability — see
[rfcs/README.md → Keeping RFCs current](./README.md#keeping-rfcs-current).
Avoid appending "Amendment N" sections that supersede body text; edit the body
in place or rewrite it instead.

- _YYYY-MM-DD_ — _(initial proposal)_
