---
rfc: 0019
title: The editor contract — v5-parity editing for the output pane
status: withdrawn
platforms: [apple, windows, gtk, android, core]
created: 2026-09-08
updated: 2026-11-08
---

# The editor contract — v5-parity editing for the output pane

> **Withdrawn 2026-11-08 and folded into
> [RFC 0015](./0015-direct-entry-mode.md)** ("The editor contract" chapter).
> Direct entry and the editor were one context contract seen from two
> surfaces, sharing every engine primitive and amending each other in both
> directions, so they now live in one document. The clauses, engine
> interface, platform notes, test rows, and open questions all moved.
>
> Nothing was lost: the contract is implemented on all four native
> frontends (Windows #56/#64, GTK #86/#87, Apple #54, Android #40), and the
> engine primitives shipped with RFC 0015's context-awareness work.

## History

- 2026-09-08 — initial proposal, growing out of editor-parity work after
  v0.1.26 user feedback; engine primitives shipped with RFC 0015's
  context-awareness amendment (DasherCore v0.2.21/v0.2.22).
- 2026-11-08 — plain-English summary and readability pass (final state
  before the fold).
- 2026-11-08 — withdrawn and folded into RFC 0015 as "The editor contract"
  chapter.
