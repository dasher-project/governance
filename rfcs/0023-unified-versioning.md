---
rfc: 0023
title: Unified versioning and cross-repo release process
status: active
platforms: [governance, core, apple, windows, gtk, android, web]
created: 2026-11-07
updated: 2026-11-08
---

# Unified versioning and cross-repo release process

## Plain-English summary

Dasher comes in several editions, for Windows, Apple devices, Linux, Android, and the web, and today each edition shows its own unrelated version number. This makes it hard for users and supporters to tell which edition is newest or whether a copy has the latest fixes. This proposal gives every edition the same leading number, so a version like 6.0 means the same generation everywhere, with each platform adding its own small fix number after it. It also automates the routine work behind releases: keeping the shared writing engine inside each edition up to date, checking that updates are compatible, and writing the notes that describe what changed. The plan is now agreed and most of it is already built; only the timing of the first shared 6.0 release is still to be decided.

## Summary

One product version across the Dasher v6 frontends, automation to keep every
frontend's DasherCore pin current, and a compatibility contract that makes
"can I bump the engine?" a build check instead of archaeology.

Seven mechanisms, each independently shippable:

1. **Aligned versioning**: all v6 frontends share MAJOR.MINOR (6.x),
   per-platform PATCH. The version names the feature generation and
   matches the design system ("Dasher v6.0"); the platform lives in the
   repo and `app_variant`, never in the version string.
2. **Engine-bump automation**: every frontend repo runs a scheduled workflow
   that opens a "bump DasherCore to vX" PR when its pin falls behind the
   newest engine tag. Merging a green PR becomes the whole update procedure.
3. **CAPI compatibility gate**: frontends declare the minimum
   `DASHER_CAPI_VERSION` they require; the build fails if the pinned engine's
   header is older. DasherCore releases list the CAPI level and which
   frontends are affected by behavioural changes.
4. **Engine version in telemetry**: every event carries `engine_version`
   (the running DasherCore version), so pin drift is visible in the field
   (PostHog version-adoption), not discovered by support archaeology.
5. **Ecosystem status file**: `ecosystem.json` in this repo, auto-updated
   on tags: latest release + engine pin per frontend. Machine-readable
   source for the website's status/matrix and for humans answering
   "who's behind?".
6. **Canonical shared artifacts**: `analytics-events.json`, design tokens,
   and the locales manifest live HERE and are vendored into frontends by
   sync workflows. This ends the five-diverging-copies pattern (the schema
   churn incidents of 2026-10-28/29 were exactly this failure).
7. **Inherited release notes**: frontend release automation appends the
   DasherCore changelog between the old and new pin. The section is
   generated rather than hand-written (the Android 0.1.22/0.1.23 notes
   were written by hand).

## Motivation (measured 2026-11-07)

| Repo | Latest release | Engine pin | Engine commits behind |
| --- | --- | --- | --- |
| DasherCore | v0.2.28 (latest tag) | — | — |
| Dasher-Android | v0.1.29 | c7899b65 (v0.2.24+4) | 7 |
| Dasher-GTK | v0.2.16 | b7117534 (v0.2.24) | 11 |
| Dasher-Windows | v0.1.45 | 34a2246e (current) | 0 |
| Dasher-Apple | v0.1.17-mac-beta | 34a2246e (current) | 0 |
| dasher-web | v0.2.8 | 296eb458 (v0.2.24+2) | 9 |

(Measured 2026-11-07 from GitHub via `scripts/gen-ecosystem-status.py`; the
live numbers live in `ecosystem.json`, regenerated weekly. An earlier draft
of this table used stale local clones and overstated Windows/Apple drift.)

- **The numbers lie to users.** GTK 0.2.16 sounds newer than Android 0.1.29
  but ships the same engine generation; both collide with *DasherCore*
  0.2.x. A user asked "is there a 1.26?" The scheme has already failed its
  most dependent user. Apple's `-mac-beta` suffix breaks version ordering.
- **Engine drift is silent.** Apple is 25 engine releases behind; the gap was
  found by writing this RFC's survey table, not by any dashboard. Every bump
  is a manual submodule PR per repo, queued only when a user hits an
  already-fixed bug (the 2026-10 Android saga was exactly this: the fix was
  in v0.2.7/8; no frontend had shipped it).
- **No compatibility contract.** `DASHER_CAPI_VERSION` + `struct_size` ABI
  versioning exist in the engine, but no frontend declares a required level,
  so "can I bump?" is answered by reading changelogs.
- **Frontends don't report what they run.** Telemetry carries `app_version`
  but not the engine version; a personal `0.1.33-…` build appeared in
  PostHog and its engine was unknowable.
- **Shared artifacts are hand-copied** per repo and diverge (two churn
  incidents in one week).

## Detailed design

### 1. Aligned versioning

- **Format**: `vMAJOR.MINOR.PATCH` everywhere; prereleases as
  `vMAJOR.MINOR.PATCH-rc.N`. No platform suffixes, no `-beta` tails.
- MAJOR.MINOR is shared by all v6 frontends and names the generation:
  6.0 is the first aligned cut (design system "Dasher v6.0"). PATCH is
  per-platform and independent (Android may be 6.0.3 while GTK is 6.0.1).
- **Release trains**: minors are cut on a coordinated schedule (target:
  monthly). Frontends board the train when ready; PATCHes ship whenever.
  App Store review latency never blocks other platforms.
- **Version source of truth**: git tags, via `git describe --match 'v*'`
  (Android and GTK already do this; Windows/Apple adopt the same). A
  checked-in fallback constant is maintained by each repo's release script,
  never by hand.
- **Migration**: at the next coordinated cut every frontend tags 6.0.0.
  Existing 0.x tags remain (history is immutable); update checkers compare
  within-repo so the jump is safe. Users see one clear number.
- DasherCore keeps 0.2.x: it is a component version, surfaced via
  `engine_version`, never presented as the product version.

### 2. Engine-bump automation

Per frontend repo, `.github/workflows/engine-bump.yml`:

- **Weekly schedule + workflow_dispatch.** Compares the newest `v*` tag in
  DasherCore against the submodule pin (git describe of the submodule).
  If behind: branch, `git submodule update --remote` (or checkout the tag),
  push, open a PR titled `chore: bump DasherCore to vX.Y.Z` with the engine
  changelog (commits between pin and tag) in the body.
- Uses only the repo's own `GITHUB_TOKEN` (same-repo PRs); no org app, no
  PAT, no Renovate dependency. Adding Renovate later is compatible.
- The submodule path is a single env var, so the file is identical across
  repos (`third_party/DasherCore`, `DasherCore`, `wasm-build/dashercore-src`).
- Merge policy: green CI = merge. Frontend-specific adaptation work rides
  the PR as additional commits before merge.

### 3. CAPI compatibility gate

- DasherCore (done): `DASHER_CAPI_VERSION` (currently 3) +
  runtime `dasher_capi_version()`.
- Each frontend declares `REQUIRED_DASHER_CAPI_VERSION` in one place;
  the build (Gradle/CMake/msbuild) parses the pinned `dasher.h`'s
  `#define DASHER_CAPI_VERSION` and fails the build if lower. A runtime
  assert at engine-create is belt-and-braces.
- DasherCore release checklist gains one line: state the CAPI level and name
  frontends affected by observable behaviour changes.

### 4. Engine version in telemetry

- DasherCore gains `dasher_get_engine_version()` returning the compiled-in
  version (`project(VERSION)` + optional git describe suffix).
- Every frontend adds `engine_version` to its analytics default properties
  (RFC 0001 properties block). It prefers the runtime call and falls back
  to the build-time submodule describe (frontends bundle the engine, so
  the pin IS the running version today).
- The PostHog version-adoption tile then shows engine drift per platform.

### 5. Ecosystem status file

`ecosystem.json` in governance:

```json
{
  "updated": "2026-11-07T…",
  "engine": { "latest": "v0.2.26", "capi_version": 3 },
  "frontends": {
    "dasher-android": { "latest": "v0.1.29", "engine_pin": "v0.2.24-4-gc7899b65", "behind": 2 },
    "dasher-gtk":     { "latest": "v0.2.16", "engine_pin": "v0.2.24", "behind": 2 },
    "dasher-windows": { "latest": "v0.1.27", "engine_pin": "v0.2.19-2-ga71c2dea", "behind": 7 },
    "dasher-apple":   { "latest": "v0.1.8-mac-beta", "engine_pin": "v0.2.1-1-g8bb4ed98", "behind": 25 },
    "dasher-web":     { "latest": "v0.2.8", "engine_pin": "v0.2.24-2-g296eb458", "behind": 2 }
  }
}
```

A scheduled Action regenerates it (gh API: latest tags + submodule pins) and
commits/PRs the diff. The website renders a status table from it; the
feature matrix can migrate to the same source over time.

### 6. Canonical shared artifacts

- `governance/analytics-events.json` becomes canonical; frontend copies are
  generated. Sync workflow (same shape as the bump bot) opens a PR in each
  frontend when the canonical file changes.
- Design tokens (`DESIGN.md` front matter → platform constants) and the
  locales manifest follow the same pattern as they stabilise.

### 7. Inherited release notes

Frontend release automation computes `git log --oneline OLD_PIN..NEW_PIN`
over the DasherCore submodule and appends it under an "Engine changes"
heading (full log link included). Android's release workflow adopts this
first; others copy the step.

### Version-mechanism readiness (audited 2026-11-07, re-synced 2026-11-08)

| Frontend | Version source | Ready for 6.0.0? |
| --- | --- | --- |
| Android | `git describe --match 'v*'` (gradle) | ✅ tag and go |
| GTK | `git describe` + metainfo contract (`tag-release.sh`) | ✅ tag and go (metainfo entry same day) |
| Windows | tag-driven versioning scripts (adopted with #108) | ✅ ready |
| Apple | tag-driven versioning (adopted with #75; `-mac-beta` retired) | ✅ ready |
| web | npm/package version | ⚠️ align at the train |

Windows and Apple previously carried hand-set project versions and could
drift silently (Apple sat at 0.1.17-mac-beta, 17 PATCHes behind the version
scheme's own scheme). Both now derive version from tags: Windows via the
#108 release scripts, Apple via #75, which retired the `-mac-beta` suffix.
Web aligns at the train.

### 2026-11-08 Amendment: dasher-shared-resources joins the plan

The original automation covered only the DasherCore submodule. **dasher-shared-resources**
(the RFC 0003 canonical UI string catalogue, consumed by Android, GTK, Windows,
Apple) had the identical invisible-drift problem. Worse: it had never been
tagged, so drift could not even be measured. Survey at amendment time:
Android 29 commits behind, GTK 26, Apple 16, Windows 1.

- **Tagged from v0.1.0** (2026-11-08). Translation rounds keep their PR flow;
  a tag lands per accepted round.
- **Item 2 generalises**: `engine-bump.yml` becomes `shared-deps-bump.yml`, a
  matrix over all shared submodules (`DasherCore`, `shared-resources`): same
  weekly tag-compare, changelog-in-PR, green-CI-merge contract per component.
- **Item 5 generalises**: `ecosystem.json` records a `shared_resources_pin`
  (and drift) per frontend alongside the engine pin.
- dasher-web consumes no submodule (strings via fetch at build), so it is exempt.

## Resolution

- **State**: accepted
- **Decided by**: maintainers
- **Date**: 2026-11-08
- **Decision**: The seven mechanisms are the plan of record; items 2–7 are
  implemented or in flight across the repos. The 6.0.0 aligned cut
  (item 1) is GO: the first train leaves when each frontend is ready —
  GTK cut 6.0.0 on 2026-11-08; others board as their pins and notes land
  (no coupling to store review latency).

## Rollout

| Step | Item | Repos | Status |
| --- | --- | --- | --- |
| 1 | 6.0.0 aligned cut | all | **GTK v6.0.0 tagged 2026-11-08** (engine v0.2.28, tag-scheme guard live); Android/Windows/Apple/web board the train as ready |
| 2 | engine-bump / shared-deps automation | all frontends | landed: Android #84 (generalised to shared-deps), GTK #100 + #102, web (engine-bump workflow), Windows #108 |
| 3 | CAPI gate | all + core | landed: Windows #108 and Apple #75, both with tag-driven versioning; Apple retired the `-mac-beta` suffix |
| 4 | engine_version telemetry | all + core | landed: DasherCore `dasher_get_engine_version`, Android #83, GTK #99, Windows #108, Apple #73 |
| 5 | ecosystem.json | governance | live in governance, regenerated 2026-11-07, shared-resources pins recorded |
| 6 | schema sync (vendored artifacts) | governance + frontends | landed: Android #85, GTK #101, Windows #108 |
| 7 | inherited release notes | android | landed: Android #86 |

## Alternatives considered

- **Renovate for submodule bumps**: good, but depends on the GitHub App
  being installed org-wide; the per-repo Action has no dependency. Adopt
  Renovate additionally if/when the org enables it.
- **One monorepo**: solves syncing by construction but rewrites every
  frontend's CI, packaging, and review flow; the automation above gets the
  same effect with none of the migration cost. Revisit if drift persists.
- **Lockstep versions (identical PATCH across platforms)**: rejected
  because it couples platforms to each platform's slowest store review.
  Aligned MAJOR.MINOR is the contract users actually perceive.

## History

- 2026-11-08 — plain-English summary added, prose simplified for readability, implementation status re-synced against the frontend repos.
