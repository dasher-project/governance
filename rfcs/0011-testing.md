---
rfc: 0011
title: Testing expectations for RFCs
status: proposed
platforms: [apple, windows, gtk, android, web, core]
created: 2026-06-28
updated: 2026-06-28
---

# Testing expectations for RFCs

## Summary

Every RFC should say, in the document itself, **whether the change is testable,
what kind of test covers it, and where those tests live**. "Manual verification
only — no automated tests" is an acceptable answer, but it must be a deliberate
one, not a silent gap. This RFC adds a `Testing` section to the template and
records where tests live in each of our repos, so a contributor implementing an
RFC on one frontend knows both what to write and where to put it.

This is guidance, **not a merge gate**: a missing or thin test plan does not
block an RFC from going `active`. Reviewers are expected to ask about it; the
author is expected to answer.

## Motivation

A contributor landing an RFC on, say, Dasher-Android today has to hunt to find
out:

- whether tests are expected at all,
- which framework that repo uses,
- where the test sources live, and
- what is already covered by the shared engine vs. what the frontend must cover.

The result is the uneven coverage we have today:

| Repo | Framework | Test sources | State |
| --- | --- | --- | --- |
| DasherCore | doctest (C++) | [`tests/`](https://github.com/dasher-project/DasherCore/tree/main/tests) (~32 files, incl. C-API tests) | Mature; the strongest layer |
| Dasher-Windows | xUnit + Microsoft.NET.Test.Sdk | `tests/Dasher.Windows.Tests/` | Active; e.g. `PiiScrubberTests`, `EngineLogRingBufferTests` for RFC 0009 |
| Dasher-Apple | XCTest | `tests/` dirs exist | `project.yml` declares `testTargets: []` — files present but not wired into a build target |
| Dasher-Android | JUnit 4 + AndroidX test (Espresso) | (none yet — `app/src/test`, `app/src/androidTest` not created) | Deps in the version catalog; no test sources |
| dasher-web | (none yet) | — | No test tooling wired up |
| Dasher-GTK | (none yet) | — | TBD |

Dasher-Windows implementing `PiiScrubberTests` and `EngineLogRingBufferTests`
for RFC 0009 is the model this RFC wants to generalise: the RFC promised the
crash scrubber strips PII, and a test in the implementing repo proves it. Today
that happened because the author chose to; this RFC makes "where's the test?"
an explicit question every author answers up front.

## Detailed design

### The template

[`0000-template.md`](./0000-template.md) gains a `Testing` section with the
following prompt (filled in by the author):

> - Is this change testable automatically, by manual verification, or both?
> - For automated tests: which repo(s) and path(s) hold them? (See the repo map
>   in [RFC 0011](./0011-testing.md).) Shared invariants ideally land in
>   DasherCore's `tests/`; frontend-specific behaviour lands in the frontend's
>   test target.
> - For privacy, data-egress, security, or correctness claims made elsewhere in
>   this RFC: name the test that asserts the claim (e.g. a scrubber test, a
>   "no-typed-text-in-payload" schema test).
> - If there are no automated tests, say why and how a reviewer verifies the
>   change (e.g. a manual run-through, a screenshot, a UX step).

"Manual verification only" is a legitimate answer — especially for UX-driven
RFCs like onboarding (0004/0008) or the access-method IA (0010), where the real
validation is with users. The point is that the choice is written down.

### Where tests live (per repo)

A contributor implementing an RFC on a given frontend should put its tests in
that frontend's test target. Invariants that are true for **every** frontend
(the C-API contract, the analytics event schema, the crash-scrubbing rules if
they're ever shared) belong in **DasherCore** so a single test guards all four
frontends.

- **DasherCore** — `tests/` (doctest; run via CMake `ctest`). This is the home
  for cross-frontend invariants. The C-API tests here are the contract every
  frontend relies on.
- **Dasher-Windows** — `tests/Dasher.Windows.Tests/` (xUnit). Run via
  `dotnet test`.
- **Dasher-Apple** — XCTest test targets (the existing `tests/` dirs need to be
  wired into `project.yml`'s `testTargets`; until then, add the file and flag
  the wiring in the PR).
- **Dasher-Android** — `app/src/test/` for JVM unit tests (JUnit 4) and
  `app/src/androidTest/` for instrumented tests (AndroidX test / Espresso). Both
  are already in the version catalog; the directories just need creating.
- **dasher-web** — TBD (no test runner wired up yet; pick one when the repo gets
  its first test).
- **Dasher-GTK** — TBD.

### Privacy, data-egress, and correctness specifically

These are the cases where a missing test is most likely to cause real harm
(Dasher is used by a vulnerable population, often in clinical/educational
settings). When an RFC makes a promise of the form "X is never collected," "X
is scrubbed before leaving the device," or "the output equals …", the author
should name the test that breaks if the promise is violated. Examples from
already-accepted RFCs:

- **RFC 0001 (analytics)** — a test that no captured event payload contains
  typed text / clipboard / canvas contents.
- **RFC 0009 (crash reporting)** — a scrubber test proving home-directory paths
  and emails are stripped from the stack trace and engine log tail (Dasher-Windows's
  `PiiScrubberTests` is the reference implementation; each frontend that
  implements 0009 should add an equivalent).

This is phrased as expectation, not a gate. A reviewer who sees a privacy claim
with no test will (and should) ask.

## Drawbacks

- Adds a small amount of process to every RFC. Mitigated by allowing "manual
  verification only" as a valid answer.
- "Expected, not gated" depends on reviewer discipline; if reviewers stop
  asking, the section rots. The README will say so plainly.
- The repo map will go stale as frontends add test infrastructure; it lives here
  on purpose so updating it is a one-line PR, not a code change.

## Alternatives considered

- **Hard gate (block `active` without a test plan).** Rejected — too heavy for
  docs/UX RFCs and would slow the project down. Kept as reviewer expectation.
- **Per-repo CONTRIBUTING files instead of a central RFC.** Rejected — the
  question is cross-cutting and belongs where contributors already look (the RFC
  they're implementing).
- **A formal tier system (required / recommended / manual / n/a).** Considered
  and dropped — it reads as bureaucracy to a new contributor. The single prompt
  in the template achieves the same outcome with less jargon.

## Prior art

- **Rust** marks each RFC's "testing" expectations inline; the Rust team treats
  test coverage as part of stabilisation.
- **PostHog's own SDKs** ship a shared test suite for the ingestion schema —
  analogous to DasherCore owning the cross-frontend invariant tests.

## Unresolved questions

1. Should DasherCore grow a small shared test harness for the analytics event
   schema and the crash scrubber, so every frontend runs the same assertions
   against the same fixture set?
2. Do we want CI to **report** test coverage per repo (a status check) even
   though it isn't a gate?
3. When Apple wires `testTargets` in `project.yml`, does that count as a
   prerequisite for this RFC or a follow-up?

## Resolution

_(Filled in once a decision is reached — do not fill in when proposing.)_

- Status: _pending_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_
