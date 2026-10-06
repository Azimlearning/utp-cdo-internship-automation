# Plan — Observability & Error Handling (P2)

> ⛔ **SUPERSEDED 2026-09-30. Do not execute.** Its premise ("no flow has a failure branch") was wrong: 12 of 14 flows already post a Teams FAILED alert. See the correction at the top of `refdocs/issues/2026-09-16-01-no-failure-notifications.md`. Work now happens per flow under D-08 (sandbox first), in `refdocs/issues/2026-09-30-flow-NN-*.md`.

> Phase P2 of `refdocs/cdo-internship-automation-PRD.md` §6. Execution doc: `refdocs/execution/2026-09-16-observability-and-error-handling.md`.
> A plan says **what and why**. The execution doc says **how and in what order**.

## Why this exists

The brief reports "email has to be manual" and general distrust that automation is running. Direct inspection of all 14 flows confirms the mechanism: 13 of the 14 flows post to Teams exactly once, on the success path only (`grep`-verified: zero `Failed`-branch actions in any of the 14 `definition.json` files); the 14th, Success Submit Email, has no Teams post at all — see "What's already covered" below. When any step fails — an Excel file locked, a throttled connector, the hard-coded drive-item ID from D-03 going stale — the flow simply stops. Nobody is told. Staff only notice because an email never arrived, hours or days later, and by then the only recourse is doing it by hand.

This is the highest-leverage fix available: it doesn't require the deprecated-trigger replacement or the Excel-ID rearchitecture to already be done, and it's a prerequisite for diagnosing everything else — once every flow reports its own failures, the *next* office-laptop session (P3) can see exactly what's actually breaking instead of guessing from symptoms.

## What's already covered (no work needed)

- **Teams connector is already wired into 13 of the 14 flows**, authenticated and working (`PostMessageToConversation` / "Post message in a chat or channel" actions confirmed present). For those 13, this plan does not add a new connector or a new Teams channel — it adds a second, failure-path message next to the existing success-path one. **Exception: Success Submit Email has no Teams connector and no `Get_item` action at all** — it needs both added as part of this plan (Task 2a in the execution doc), not just a failure branch. This is the one flow where "what's already covered" doesn't apply.
- **New-vs-partial-match detection logic** (Module M2) is unaffected by this plan and is not being touched.

## Scope

**In:**
- Add a `Configure run after` branch (on Failed, Skipped, TimedOut) to the outermost scope/action-group of each of the 14 flows, posting a distinct "❌ [Flow name] failed at [step]" message to the same Teams channel/chat the success message already uses.
- Where a flow has no single outermost scope (several were built as a flat sequence of top-level actions rather than one wrapping `Scope`), wrap the flow's body in a `Scope` action first, so there's one place to attach the failure handler instead of one per top-level action.
- Confirm, for each flow, which Teams channel/chat the existing success post targets, and match the failure post to the same destination — don't introduce a new channel as a side effect.
- Test each flow's failure path by deliberately forcing a failure (e.g., temporarily pointing a lookup at a nonexistent item) and confirming the Teams message actually arrives.

**Out (and why):**
- **Fixing the deprecated trigger or the hard-coded Excel IDs** — that's P3 (D-06, D-03). This plan only makes failures *visible*; it doesn't fix their root causes. Bundling both into one office-laptop session would make the session too large to finish and review carefully in one sitting (D-02).
- **Retry logic** — Power Automate supports automatic retries per action, but adding retries changes behavior (a flaky step now succeeds silently on attempt 2) in a way that should be a deliberate, separate decision per action, not a blanket addition here. Flag candidates during P2 execution; decide retries in a follow-up, don't default to adding them.
- **The ownership migration (M6)** — out of scope here; P4.

## Approach

Power Automate's standard pattern for this: every action (or the wrapping `Scope`) gets `runAfter` configured for `Failed`, `Skipped`, and `TimedOut` in addition to the default `Succeeded`, targeting a `Post message in a chat or channel` action that composes a message naming the flow and, where derivable, the specific action that failed (`@{workflow()['name']}`, `@{result('<ScopeName>')[0]['name']}` for the failing action inside a scope).

Two shapes exist across the 14 flows and need slightly different treatment:
1. **Flows already built around a single named `Scope`** (e.g., "Combine raw data" has one `Scope` wrapping its file-handling actions) — attach the failure branch to that existing scope.
2. **Flows built as a flat top-level action sequence** (most of the rest) — wrap the whole action list in a new outer `Scope` first, then attach the failure branch to it. This is a structural change to the flow, not just an addition, so it needs care: moving existing actions inside a new `Scope` in Power Automate Studio's UI (drag-select → "Add a Scope") preserves their configuration and connections; it does not require rebuilding them.

## Risks & unknowns

| Risk / unknown | Confidence | Mitigation |
|---|---|---|
| Wrapping flat action sequences in a new `Scope` preserves all existing action configuration | Medium — this is standard, documented Power Automate Studio behavior, but not yet tested against these specific 14 flows | Do one flow first (smallest one — "Delete Student List from SharePoint List", 2 connectors, no Excel) as a pilot in the office-laptop session; confirm it still runs identically before doing the other 13 |
| Which Teams channel/chat each flow's existing success message targets | **Resolved** — confirmed by reading all 14 `definition.json` files directly: it's not a channel, it's a 1:1 "Chat with Flow bot" to whoever's in a shared SharePoint config item's (`id: 1`, table `be7f2b53-cc4e-42b1-a043-a7d6a849ba42`) `TeamsNotification1` field (`TeamsNotification2` for "Combine raw data"), fetched early via a `Get_item` action. Full analysis: `refdocs/issues/2026-09-16-01-no-failure-notifications.md` | The failure branch reuses `Get_item`'s existing output (`@{outputs('Get_item')?['body/TeamsNotification1']}`) rather than re-fetching or guessing a target — see the execution doc's per-task detail |
| Forcing a deliberate failure won't have side effects on real data | Medium — depends per flow; a forced failure on "Store Student List into SharePoint List" could partially write data before failing | Pilot the forced-failure test on read-only or low-risk flows first; for write-heavy flows, force the failure on the *first* action in the chain so nothing downstream runs |
| Whether Power Automate's `runAfter` UI behaves identically when re-imported from this project's `.zip` vs. edited live in Studio | Low — not yet tested; this plan assumes editing happens live in Studio, not by hand-editing `definition.json` and reimporting | Confirmed approach: edit live in Studio during the office-laptop session, export a fresh `.zip` afterward for this repo — not the reverse |
| Success Submit Email needs a new Teams connection + new `Get_item` action added, not just a failure branch — materially more work than the other 13 flows | High confidence this is needed (confirmed no Teams connector in its `manifest.json`); low confidence on how long adding a first-time connection takes in Studio | Budget extra time for this one flow specifically; if the office-laptop session runs short, this is the flow to defer to a follow-up rather than leaving one of the "quick" flows half-done |

## Definition of done

This phase is done when every line below is true and has been *observed*, not assumed:

- [ ] All 14 flows have a failure-path action that posts to Teams, confirmed by reading each flow's `definition.json` after re-export
- [ ] Every one of the 14 flows was deliberately forced to fail at least once in Studio, and the Teams failure message was seen to arrive, with a screenshot or run-history link recorded in the execution doc's Verify step for that flow
- [ ] The existing success-path Teams messages still fire correctly (regression-checked, not assumed unaffected) for all 14 flows
- [ ] `guides/flow_inventory.md` "Confirmed gaps" section is updated to move "no failure-path Teams notification anywhere" from a gap to a resolved item, with the date
- [ ] A fresh `.zip` backup of all 14 post-fix flows exists in `flows/` and is committed
