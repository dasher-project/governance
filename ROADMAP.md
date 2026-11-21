# Dasher v6 — Roadmap

> **Draft for the steering group's first meeting** (the NLnet MoU's advisory
> group). Mark it up, reorder it, argue with it — that's what it's for.
> Last updated: 2026-11-21.

One page: **what we're building, in what order, landing in which release.**
Three sources joined: the [NLnet plan](mou/2026-04-069-plan.md) (€50,000, 11
tasks — what we promised), the [RFCs](rfcs/README.md) (what's agreed and how
far it's built), and the [UX sprint](https://github.com/dasher-project/dasher-design-guide)
(what users tell us).

Start with **Where we are** and **The release train**. In each theme:
⭐ = suggested first priority; empty checkbox = not done; *Target* line gives
the rough date and the release it ships in.

---

## Where we are (November 2026)

The engine is healthy: DasherCore v0.2.28 plus five frontends share one C
API, and most of the 23 RFCs are implemented. What defines the next phase:

1. **UX is the gap, not engineering.** Onboarding (RFC 0004), settings tiers
   (RFC 0006) and the access screen (RFC 0010) all wait on user research —
   the stalled UX sprint. And the frontends still look like separate products
   rather than one Dasher (theme 2).
2. **The NLnet grant has started** (€50,000, milestone-paid). This roadmap
   decides what gets picked up first.
3. **No steering rhythm yet.** The monthly advisory group and the two-monthly
   public report both start with the first meeting.

---

## The release train

We can be more ambitious than a queue because the work runs in **parallel
lanes** with different owners:

| Lane | Who | Time | Carries |
| --- | --- | --- | --- |
| Engine + Windows + web | Kirsty (KM) | **full-time** | DasherCore + **Dasher-Windows (her main target)** + dasher-web — releases, prediction interface, switch + eye-gaze engine side. *No Mac: she cannot build Dasher-Apple.* GTK possible in theory but not her focus. |
| Apple + Android | Will (WW) | own coding time — **unfunded** | keeps those frontends up to date; bigger SwiftUI/Kotlin lifts may need a short contractor run (decision 7) |
| Users & research | Will (WW) | 1 day/week on grant time | research programme, user docs, community — the funded day |
| GTK | Owen Kent | part-time, AI-assisted | GTK frontend — already contributing; claimable under NLnet via milestones (on the MoU contributor list) |
| UX research | Bala | volunteer; funding to confirm | sprint lead: method, recruitment, consent, synthesis |
| Language models | Keith (KV) | part-time | prediction models (NLnet task 5) |
| Volunteers | UX squads | 8–10 weeks | interviews, card-sorts, prototyping |

The lanes are independent — engineering doesn't wait on research except
where a checkbox says so. Dates below assume all five lanes run.

> ⏰ This train lands every grant milestone inside the MoU's 12 months (to
> Oct 2027) without an extension — but the buffer is thin. The Commons Fund
> programme itself ends June 2027; if anything slips a quarter, start the
> extension conversation with NLnet immediately.

| Release | Rough date | Theme | What's in it | NLnet tasks |
| --- | --- | --- | --- | --- |
| **v6.1 — "alignment cut"** | Dec 2026–Jan 2027 | 11 | One engine pin, one version, feature matrix + CI, first simultaneous tagged release | 8a–c |
| **v6.2 — "first five minutes"** | Mar–Apr 2027 | 1, 2, 3, 5 | Design system v2, unified chrome, onboarding, settings tiers (+ emoji as a point release when the crash fix lands) | 1, 3, 5d |
| **v6.3 — "learning mode"** | Jun 2027 | 4 | Learning mode — built and proven on dasher-web from Feb; integrated into every native frontend at this minor | 2 |
| **v6.4 — "every access method"** | Q3 2027 | 6, 7, 8 | Switch access, eye-gaze, calibration profiles, access screen — the heaviest release; split into two minors if it slips | 4, 6 |
| **v6.5 — "voice"** | Q4 2027–2028 | 10 | Speech/TTS unification — Q4 2027 if rescoped small, 2028 if it grows | 7 |

**Prediction (theme 9) is deliberately not a named release.** The engine work
ships when it's ready and surfaces through point releases; whether it earns a
minor of its own gets decided once we see what the pluggable interface makes
possible.

Alongside, not tied to a release: UX research (theme 14, Dec 2026–Feb 2027),
study design + ethics (H1 2027) and the study itself (Q3 2027), developer
experience (theme 12, continuous), docs (theme 13, with v6.2/v6.3) and
videos (Q3 2027).

**Suggested first three milestones to claim:** UX research findings published
(task 1a, €1,200) · switch-access RFC accepted (task 6a, €1,000) ·
feature-matrix research report (task 8a, €1,000).

---

## 1. Design system & brand

*Target: v2 round Jan–Feb 2027 · feeds the v6.2 unified chrome.*

v1 is published and adopted — but the honest state is that it has never had
a dedicated human design pass. **v2 is that pass**: colours, type scale,
spacing and component patterns reviewed with actual design judgement,
informed by the theme-2 UI audit.

**v1 (done):**

- [x] Design guide + DESIGN.md tokens published
- [x] Lucide icons adopted — Apple & Windows only (divergence tracked in theme 2)
- [x] Dark mode palettes (RFC 0007 — GTK/Android window chrome remains)
- [x] watchOS scoped in governance + RFC 0010 (Nov 2026): companion to the iPhone app, touch + Digital Crown, no standalone ambitions

**v2 (the human round):**

- [ ] Review tokens, typography and spacing with design judgement, not just lint passes
- [ ] Component patterns per form factor, feeding theme 2's maps
- [ ] Validate v2 against the UI audit findings + WCAG contrast checks
- [ ] Re-lint DESIGN.md and re-adopt across frontends as they pick up the unified chrome

**Links:** rides NLnet tasks 1–3 (spec/design work) · RFCs [0002](rfcs/0002-lucide-icons.md), [0007](rfcs/0007-dark-mode-palettes.md) · [design guide](https://github.com/dasher-project/dasher-design-guide) · Owners: KM + Bala

---

## 2. One interface on every platform

*Target: audit Dec 2026 · chrome lands in v6.2 (Q2 2027).*

A user moving phone → iPad → desktop should recognise Dasher instantly.
Today they can't: Apple and Android look like different products, both carry
more buttons than v5, and nothing catches UI drift (the feature matrix tracks
capabilities, not consistency).

- [ ] ⭐ UI audit: side-by-side screenshots of every frontend's main screen + button count vs v5, published in the design guide
- [ ] Chrome diet: canonical button set per form factor (phone / tablet & iPad / desktop); every button earns its place, the rest move to settings or progressive disclosure (theme 5)
- [ ] Icon story settled: Lucide everywhere (RFC 0002) or explicitly bless per-platform sets — today it's half-and-half
- [ ] Per-form-factor component maps in the design guide
- [ ] Extend `dasher-shared-resources` beyond strings — layout patterns, assets
- [ ] UI-alignment short run, decided: Will unpaid vs a SwiftUI/Kotlin contractor claimable under NLnet — **human-coded either way, no AI agents for this run**
- [ ] Implement per frontend: Apple + Android first (most visible divergence — Will unfunded, or the contractor run), Windows (KM), GTK (Owen), web (KM)
- [ ] UI-consistency checks in the release test checklist + feature matrix

**Links:** no dedicated NLnet task — rides tasks 1–3 and 8; steering group to
decide if it needs milestones of its own · RFCs [0002](rfcs/0002-lucide-icons.md), [0006](rfcs/0006-settings-ia.md) · Owners: WW + KM + Owen

---

## 3. Onboarding & first-run experience

*Target: research Dec 2026–Feb 2027 · ships in v6.2 (Mar–Apr 2027).*

The biggest adoption barrier: today a first-time user gets no welcome, no
explanation, no practice. Design exists (RFC 0004, `proposed`); its open
questions need the research first. Squad A owns this.

- [ ] ⭐ UX research: first-touch studies and interviews (Squad A) — *unblocks themes 3, 4 and 5*
- [ ] Settle RFC 0004 (incl. keyboard/IME enablement, folded in from RFC 0008)
- [ ] Start-up guide + first-run flow prototyped in dasher-web
- [ ] First-run experience shipped across desktop and mobile frontends

**Links:** NLnet task 1 (€4,000) · RFC [0004](rfcs/0004-onboarding.md) · Owners: KM + UX

---

## 4. Learning / practice mode

*Target: design Jan–Feb 2027 · built on the web Feb–Apr · v6.3 native integration Jun 2027.*

Building speed takes practice; today's game mode is unspecified and uneven.
Deliberately on hold until the research shapes it — likely called "learning",
parts may ship as a web app. Spec it after the research, not before.

- [ ] ⭐ UX research: what makes practice rewarding, not frustrating (Squad C, with Squad A)
- [ ] Learning-mode design + progression model in the design guide
- [ ] Built and proven on dasher-web, where iteration is fastest
- [ ] Progression tuned with genuine new users
- [ ] Integrated into every native frontend — *this integration is what makes it the v6.3 minor*

**Links:** NLnet task 2 (€3,500) · new RFC or a chapter of 0004 · Owners: KM + UX

---

## 5. Settings experience

*Target: card-sort Dec 2026–Jan 2027 · tiers ship in v6.2 (Mar–Apr 2027).*

100+ settings: expert power, newcomer burial. The IA is agreed and
implemented (RFC 0006); progressive disclosure (Simple/Advanced/Pro) waits on
the card-sort study. Squad B owns this.

- [ ] ⭐ Card-sort study with users (Squad B) — *unblocks the tiers*
- [ ] Progressive-disclosure tiers designed and implemented in dasher-web
- [ ] Inline explanations for the options that matter most
- [ ] Settings consistent across desktop and mobile
- [ ] Settings carry over between learning mode and normal use

**Links:** NLnet task 3 (€3,000) · RFC [0006](rfcs/0006-settings-ia.md) · Owners: KM + UX

---

## 6. Input foundations — the canonical access model

*Target: engine docs table Dec 2026 · dwell and smaller methods across v6.2–v6.4.*

Same setting, same meaning, every platform: RFC 0010's agreed model of nine
selection methods × seven steering methods + compatibility matrix. Agreed
August 2026; verified only on Apple and Windows so far.

- [ ] Publish the selection-method → `SP_INPUT_FILTER` mapping in `DasherCore/docs`
- [ ] Adopt canonical names + matrix on GTK, Android and web
- [ ] Dwell: app-level radial indicator + configurable duration (RFC 0010 proposal)
- [ ] Access settings sub-screen in the RFC 0006 shape everywhere — *blocked on the access-screen research (theme 14)*
- [ ] Joystick/gamepad: Apple capture (listed, not implemented), GTK via SDL, Android decision
- [ ] Tilt: keep iOS + Android aligned
- [ ] Hand tracking: visionOS Phase 3, when scheduled

**Links:** foundation for NLnet tasks 4 and 6 · RFC [0010](rfcs/0010-input-access-methods.md) · Owners: KM + WW

---

## 7. Eye-gaze input

*Target: starts Dec 2026, in parallel with the design work — engine + Windows, no design dependency · ships in v6.4 (Q3 2027).*

Eye-gaze users are among Dasher's fastest writers; the community has asked
for it to work *really* well. Windows leads (WinRT + UDP); Apple has hover +
iPadOS 18 Eye Tracking; GTK TBD; Android explicitly not planned;
mouse-presenting trackers work everywhere already. This is engine-side work
in Kirsty's lane — it doesn't queue behind the UX research or design-system
v2.

- [ ] ⭐ End-to-end evaluation: smoothing, zoom dynamics under continuous gaze, dwell behaviour, latency budgets
- [ ] Tracker abstraction standardised: platform-native, mouse-presenting, network gaze (UDP :5555, Windows protocol as wire format)
- [ ] Calibration/profile workflow: survives restarts, moves between machines
- [ ] Smoothing, zoom-dynamics, latency improvements in DasherCore input filters
- [ ] Per-platform validation with representative hardware + published default profiles
- [ ] GTK and macOS: decide follow-or-not once Windows lands

**Links:** NLnet task 4 (€4,000) · RFC [0010](rfcs/0010-input-access-methods.md) · Owners: KM + WW

---

## 8. Switch access

*Target: spikes Dec 2026 · RFC Jan–Feb · build Q1–Q2 in parallel with the UX-driven work · ships in v6.4 (Q3 2027).*

For some users one switch is the only reliable movement. Today: Android
nothing, Windows selection methods but no capture UI, GTK keyboard-only.
Blocking question (RFC 0010 Q2): OS switch systems (Android Switch Access,
Apple Switch Control) or in-app capture — investigate before choosing
(decided 2026-11-08). Together with eye-gaze (theme 7) this is the heaviest
lift in the train; if v6.4 slips, split it — switch first, eye-gaze after.

- [ ] ⭐ Per-platform spikes: OS switch systems vs in-app capture *(resolves RFC 0010 Q2)*
- [ ] Switch-access RFC accepted (closes governance#43): scanning modes, timing/debouncing, hardware, loadable profiles
- [ ] `SwitchProfile` implemented: physical inputs → `dasher_key_event`, `access.json` sidecar
- [ ] Native switch operation in DasherCore + desktop frontends
- [ ] OS accessibility-framework interop: platform switch events drive Dasher without bespoke config
- [ ] Loadable profiles + hardware notes + user documentation

**Links:** NLnet task 6 (€5,500) · RFC [0010](rfcs/0010-input-access-methods.md) · Owners: KM + WW

---

## 9. Language model & prediction engine

*Target: interface Q1 · offline models H1 · online H2 · surfaces as point releases; emoji as an early point release.*

Prediction is Dasher's fuel. The grant promises a pluggable engine:
offline-first, better models where they help. Largest NLnet task; not started.

- [ ] ⭐ Pluggable language-model interface specified and implemented in DasherCore
- [ ] Offline default model bundled; download + caching per platform (works with no network)
- [ ] Online/remote models behind the same interface where beneficial, with graceful fallback
- [ ] Emoji in the tree (RFC 0020, `proposed`): settings-gated group per alphabet — *crash fix gates the release*
- [ ] Recommended default LM settings identified through the user study (theme 14)

**Links:** NLnet task 5 (€7,000) · RFCs [0020](rfcs/0020-emoji-in-tree.md), 0010 · Owners: KM + Keith Vertanen + WW

---

## 10. Speech / text-to-speech (TTS)

*Target: rescope by Jan 2027 · v6.5 Q4 2027 if small, 2028 if it grows.*

Speech is the voice of the product for users who can't look at the screen
while typing. **Underway, not on hold anymore**: Dasher-GTK v6.0.2 (Nov 2026)
rebuilt speech on rust-tts-wrapper 1.16.2 / Sherpa-ONNX 2 — one provider →
model → voice settings surface, user pronunciation exceptions, in-process
audio, per-utterance interruption. Apple was already there; Android is the
remaining gap and the natural next step. The RFC below is what turns shipped
practice into the agreed spec.

- [ ] Voice/speech RFC accepted (closes governance#42): when speech fires, interruption, voice selection, rate/volume/pitch ownership, direct-mode behaviour — *GTK v6.0.2's shipped behaviour is the draft evidence*
- [ ] Per-platform TTS unified behind one settings surface — ✓ GTK (v6.0.2), ✓ Apple; Android pending
- [ ] Speak-on-space + speak control-node options in settings, documented in direct mode

**Links:** NLnet task 7 (€4,000, scope under review) · no RFC yet · Owners: WW + open

---

## 11. Platforms, parity & releases

*Target: v6.1 cut Dec 2026–Jan 2027 · IME and stabilisation through v6.2–v6.4.*

Fragmentation is the failure mode this project exists to fix. Parity must be
visible and measured, not assumed.

- [ ] ⭐ Decide the v6.1 alignment-cut timing (RFC 0023 — the roadmap suggests Jan 2027)
- [ ] Feature-matrix parity mechanism researched and agreed (linked to dasher.at/status)
- [ ] Versioning + feature matrix enforced by CI across all frontends, against the test checklist
- [ ] First simultaneous tagged release with release notes (v6.1)
- [ ] On-screen keyboard / IME integration (OS text output): Windows (KM, NLnet) · iOS + Android (Will unfunded, or the contractor run — decision 7)
- [ ] iOS + Android stabilisation: long-standing crashers fixed, verified against the checklist (Will unfunded, or the contractor run)
- [ ] Close the small loops: GTK v5 migration decision (RFC 0005 Q4), update-checking loose ends (RFC 0017)

**Links:** NLnet task 8 (€6,000) · RFCs [0023](rfcs/0023-unified-versioning.md), [0017](rfcs/0017-update-checking.md), [0005](rfcs/0005-v5-migration.md) · Owners: KM + WW + open

---

## 12. Developer experience & SDK

*Target: continuous · docs overhaul by Q3 2027.*

v6 succeeds if developers outside the core team — including commercial AT
makers — can build with it.

- [ ] Developer docs overhaul: architecture guide, per-platform builds, contribution paths
- [ ] Worked examples: embedding Dasher, alternative frontends
- [ ] Published experiments beyond the C API (e.g. the 3D work via higher-level bindings)
- [ ] Clone-to-running templates and tooling for new contributors

**Links:** NLnet task 9 (€5,500) · Owners: KM + WW

---

## 13. User documentation & training videos

*Target: guides with v6.2/v6.3 · videos Q3 2027.*

The people who most need Dasher are least served by developer docs. Produced
*with* the UX team once the flows settle.

- [ ] User guides in markdown on the project website (install, access methods, prediction, onboarding)
- [ ] End-user training videos: getting started, switch access, speech output
- [ ] Developer-facing videos: per-platform builds

**Links:** NLnet task 10 (€3,000) · Owners: UX + WW + open

---

## 14. Research & evidence

*Target: sprint restart Dec 2026 · study run Q3 2027, report Q4.*

The UX sprint is the single biggest unblock in this roadmap (it feeds themes
3, 4, 5, 6) — planned, staffed with volunteers, stalled since summer. The
empirical study measures the finished experience.

**Researcher-led or developer-led?** An honest open question, held by KM: a
developer can run a usability test, so is a dedicated researcher worth it?
The plan's answer is to **pair and let evidence settle it**: Bala leads
method, recruitment, consent and synthesis; KM pairs on prototyping and
signs off each round, so engineering judgement meets user evidence from day
one. What tips it toward needing the researcher: three RFCs are blocked on
exactly this research, the project's history says our hunches get overturned
by users, and the population — eye-gaze, switch, AAC users — is specialist
to recruit and interpret. First research round decides; steering group can
overturn sooner.

- [ ] ⭐ Restart and run the UX sprint (8–10 weeks, squads A/B/C)
- [ ] KM paired on prototyping + synthesis; signs off each research round
- [ ] Publish findings, personas and ranked problems per squad — *anonymised, openly licensed in the design guide: this is what makes the research a payable NLnet milestone*
- [ ] Study design, participant materials and ethics approval (text-entry-rate evaluation)
- [ ] Run the study with existing and novice users across access methods
- [ ] Public report: text-entry-rate results + recommended default settings

**Links:** NLnet task 11 (€4,500) + the vehicle for tasks 1–3 · Owners: WW (programme, 1 day/week), Bala (research lead), KM + WW (study)

---

## 15. Project health (unfunded — still ours)

*Target: steering group Dec 2026 · reports two-monthly from Jan 2027.*

- [ ] ⭐ Steering group: first meeting, monthly cadence, review this roadmap + MoU plan
- [ ] Public progress report every two months + status page current (grant obligation)
- [ ] Privacy policy: confirm analytics retention (proposed 13 months), close RFC 0001 Q2
- [ ] Performance budgets: cold-start, frame rate on low-end devices, memory ceilings per platform
- [ ] Request NLnet's free accessibility audit for the frontends (grantee support service — evidence for themes 6–8)
- [ ] Confirm Bala as the named UX researcher in the MoU team list and agree the funding split

---

## NLnet cross-reference

| NLnet task | Theme | Budget | Owner | Status |
| --- | --- | --- | --- | --- |
| 1. Onboarding & first-run | 3 | €4,000 | KM, UX | waiting on UX research |
| 2. Learning mode | 4 | €3,500 | KM, UX | on hold pending research |
| 3. Settings experience | 5 | €3,000 | KM, UX | waiting on card-sort |
| 4. Eye-gaze performance | 7 | €4,000 | KM, WW | not started |
| 5. Prediction engine | 9 | €7,000 | KM, KV, WW | not started |
| 6. Switch access | 8 | €5,500 | KM, WW | design question open |
| 7. Voice & speech | 10 | €4,000 | WW | scope under review |
| 8. Parity & releases | 11 | €6,000 | KM, WW | partly done (RFC 0023) |
| 9. Developer experience | 12 | €5,500 | KM, WW | not started |
| 10. Docs & videos | 13 | €3,000 | UX, WW | not started |
| 11. Text-entry-rate study | 14 | €4,500 | KM, WW | not started |

Full milestone breakdown: [`mou/2026-04-069-plan.md`](mou/2026-04-069-plan.md)
(on the `nlnet-2026-04-069-mou` branch until that PR merges).

### How NLnet pays: publicly verifiable milestones

NLnet funds **milestones anyone can verify are complete, in public** — a PR
is just the commonest form. UX qualifies exactly like code, provided it
lands as a public artifact.

| ✅ Funded (verifiable) | ❌ Not funded |
| --- | --- |
| Findings, personas, card-sorts published in `dasher-design-guide` | Coordinating volunteers (community management) |
| Wireframes, prototypes, linkable web demos | Raw user recordings — publish anonymised findings |
| RFCs accepted through the normal process | Hosting, ops, promotion |
| Implementations verified against the test checklist | Participant travel/hardware *as milestones* — pre-agree with NLnet, invoice through them (MoU clause 12) |
| Study report + recommended defaults | Sprint all-hands as an event |

Everything open-licensed (software MIT — done; design guide MIT covers
docs). Programme ends June 2027; claim milestones while the MoU holds.
NLnet also gives grantees free support services — accessibility audits (HAN
University), security audits, mentoring — worth requesting (theme 15).

### Stretching the grant: not every target needs NLnet money

Will can code — he just can't claim NLnet money for it. So **targets stay
targets, with dates, whether or not they're funded.** Three sources of
effort:

- **NLnet milestones** — claimable € per the plan; pays KM, KV, Bala and
  Will's user-focused day.
- **Self-funded code** — Will's own time, agentic coding included: same
  roadmap, same review, no invoice. NLnet's generative-AI policy (v1.1)
  still applies regardless of funding: commit-level provenance marks for
  generated code, and no purely AI-generated outputs as milestone
  deliverables.
- **Volunteer time** — the UX squads, and anyone else who wants in.

The lever this creates: a milestone completed unfunded **frees its amount**
to be reassigned — more research hours, more KM time — or simply left
unclaimed (the plan is modifiable with NLnet; decision 6). Biggest
self-fundable chunks: the **Apple and Android builds themselves** (KM has no
Mac, so they ride on Will's unfunded time or a contractor) and
keyboard/IME + stabilisation (task 8d+e, €3,000).

---

## Decisions for the steering group

1. **Priorities.** UX research first (this document's suggestion) — or sequence differently?
2. **One interface, how far?** How hard to push unification; how far to cut buttons toward v5 simplicity; does theme 2 need its own milestones?
3. **The v6.1 alignment cut.** The roadmap suggests Dec 2026–Jan 2027 — agree or move?
4. **Speech scope.** Keep task 7 small (unify settings) or grow it (VoiceGarden)?
5. **UX: researcher-led or developer-led?** Bala leads with KM pairing (this document's suggestion) — or developer-led with a smaller research budget? Decide on the evidence after the first research round, not before.
6. **Rebalance the NLnet plan to match capacity.** KM is full-time (more than the plan assumed), WW's grant time is user-focused only, Bala is the TBD researcher. Amounts attach to milestones, not people — reassigning owners is administrative, agreed with NLnet. Also decide: which code milestones run **unfunded** on Will's own/agentic time, and whether their amounts redirect to research or KM.
7. **Apple and Android capacity.** KM has no Mac, so Dasher-Apple (and largely Android) ride on Will's unfunded time. A short, **human-coded** UI-alignment run — a SwiftUI/Kotlin contractor claimable under NLnet, no AI agents for this work — could take the load. Decide scope, budget, and whether Owen's AI-assisted GTK model extends elsewhere.
8. **GTK v5 migration.** Close it (distro packages handle upgrades, and Owen now carries GTK) or spec it?
9. **Sustainability.** MoU standing brief: what happens after this grant?

---

## Sources

- [NLnet MoU + project plan](mou/README.md) (grant 2026-04-069)
- [RFC index](rfcs/README.md) — status synced 2026-11-08
- RFC overlap & gap review (2026-11-08) — findings folded into the RFCs (PR #60)
- [UX research sprint](https://github.com/dasher-project/dasher-design-guide/tree/main/research)
- [Feature status matrix](https://dasher.at/status/) — shipped capabilities per platform
- [NLnet guide for applicants](https://nlnet.nl/commonsfund/guideforapplicants/) — funding rules
