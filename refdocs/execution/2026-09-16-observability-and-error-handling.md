# Execution — Observability & Error Handling (P2)

> ⛔ **SUPERSEDED 2026-09-30. Do not execute at the office laptop.** Following it would add a second failure alert to the 12 flows that already have one. The replacement is per-flow issue docs with sandbox-verified "Office steps" (D-08). Flow 1's is `refdocs/issues/2026-09-30-flow-01-success-submit-email.md`, which also drops the per-student Teams success message proposed in Task 2a below.

> Plan: `refdocs/plans/2026-09-16-observability-and-error-handling.md`. Tasks run top to bottom. This is a single office-laptop session — budget for all 14 flows in one sitting per D-02, and don't leave a flow half-fixed at the end of the day (mark it ⛔ Blocked in STATUS.md instead, naming exactly what's left).

## Before starting

- [ ] At the office admin laptop, signed into `kamalazreel.k@utp.edu.my` (still the connection owner as of this session — see D-02, M6 hasn't run yet)
- [ ] `refdocs/guides/flow_inventory.md` open for reference — it has each flow's existing Teams action and connectors
- [ ] For each of the 14 flows: export a fresh `.zip` backup from Studio into `flows/` *before* touching it, overwriting this repo's copy, and `git status` confirms the diff is visible (this is the D-07 rollback mechanism — do this even though the flow hasn't changed yet, to guarantee the pre-fix state is captured with today's date)
- [x] ~~A scratch note listing each flow's existing Teams action's exact channel/chat target~~ — **resolved during planning, not needed live:** every flow's Teams recipient is `@{outputs('Get_item')?['body/TeamsNotification1']}` (13 of 14 flows) or `@{outputs('Get_item')?['body/TeamsNotification2']}` (Combine raw data only), read from the shared config item (`id: 1`) that `Get_item` already fetches early in each flow. Full detail: `refdocs/issues/2026-09-16-01-no-failure-notifications.md`. Reuse this expression directly in each task below — don't re-derive it per flow. **Exception: Success Submit Email has neither a Teams connector nor a `Get_item` action at all** — see Task 2a, it needs both added before it can get a failure branch.

## Task 1 — Pilot: Delete Student List from SharePoint List

The smallest flow (2 connectors: SharePoint, Teams) — used to confirm the wrap-in-`Scope` technique works before repeating it 13 more times.

1. Open the flow in Studio. If its actions are a flat top-level sequence (not already inside one `Scope`), select all actions and use "Add a Scope" to wrap them.
2. Add a failure-path `Post message in a chat or channel` action, `runAfter` the new/existing `Scope` configured for `Failed`, `Skipped`, `TimedOut`. Set `location` to `Chat with Flow bot` and `recipient` to `@{outputs('Get_item')?['body/TeamsNotification1']}` — the exact same expression the flow's existing success post already uses (confirmed per-flow in `refdocs/issues/2026-09-16-01-no-failure-notifications.md`; don't re-fetch, reuse `Get_item`'s output). Message text: `❌ [flow display name] failed. Check run history.`
3. **Verify:** Run the flow in test mode with a deliberately invalid input (e.g., point the SharePoint list lookup at a list/site that doesn't exist) and confirm the Teams failure message actually posts, with the run history link recorded here once done. Then run it again with valid input and confirm the *existing* success message still posts unchanged.

## Task 2a — Special case: Success Submit Email (needs new setup, not just a failure branch)

⚠️ **This flow is different from every other one in this doc.** Confirmed via its `manifest.json`: it has only SharePoint and Outlook connectors — **no Teams connector reference at all**, and no `Get_item` action reading the Control Template config item. It currently has *zero* Teams visibility (not even a success message), unlike the other 13. Do this one after Task 1's pilot confirms the `Scope` technique, but budget extra time for it — it's a bigger lift:

1. Add a Teams connection to the flow (Studio will prompt to create/select a connection the first time you add a Teams action to a flow that doesn't have one).
2. Add a `Get_item` action near the start of the flow (SharePoint `Get item`, same site, same table `be7f2b53-cc4e-42b1-a043-a7d6a849ba42`, `id: 1`) — matching every other flow's pattern, to fetch the Control Template record.
3. Add a **success**-path `Post message in a chat or channel` action (this flow never had one — you're adding the baseline, not just the failure half), `runAfter` the main body `Succeeded`, recipient `@{outputs('Get_item')?['body/TeamsNotification1']}`, a success message matching the style of the other 13 flows' existing success messages (check one, e.g. Delete Student List, for the exact wording convention).
4. Then follow Task 1's steps 1–2 to add the **failure**-path post, using the same `Get_item` output.
5. **Verify:** both a forced-failure run (failure message arrives) and a normal run (new success message arrives, and the flow's actual SharePoint/Outlook side effects are unaffected).

## Task 2b — Simple flows (no Excel): Add HC Supervisor into MasterList*, Add Host Company into MasterList*, Email To Inform Student Updates, Email for Report Duty Reminder

(*these two do touch Excel Online but not via a hard-coded-ID pattern per the inventory — grouped here for session pacing, not because they're Excel-free.)

Repeat Task 1's steps 1–2 for each, using each flow's own `Get_item` → `TeamsNotification1` recipient expression. **Verify** per flow: same forced-failure + Teams-message-arrives check, plus a regression check that the flow's actual side effect (the SharePoint write, or the email) still happens correctly on the success path.

## Task 3 — Bulk/status email flows: Bulk Email To Start Registration, Email for Student Report Duty Status

Same steps. These send to multiple recipients — for the forced-failure test, use a test mode run against a single test record if Studio allows it, not a live run against the real student list, to avoid sending real emails during testing.

## Task 4 — Excel-heavy flows with hard-coded IDs: Combine raw data, Clear Raw Database, HC Supervisor Info MasterList Checking, Host Company Info MasterList Checking

Same steps, with two additions:
- **"Combine raw data" is the one exception to the recipient expression** — its `Get_item` output field is `TeamsNotification2`, not `TeamsNotification1`. Use `@{outputs('Get_item')?['body/TeamsNotification2']}` for this flow only, matching its own existing success post.
- Since these flows are also P3's target (D-03/issue 2), **do not** change anything about how they reference their Excel files in this session — only add the failure branch around the existing logic. Note in the Verify step whether the forced failure was easy or hard to trigger cleanly (useful input for P3's design, since these are the flows most likely to fail from the hard-coded-ID issue in real operation).

## Task 5 — Deprecated-trigger flows: Acknowledgement Letter Email Process, Store Student List into SharePoint List

Same steps, applied only to the flow's *action* body — **do not touch the trigger** in this session (that's D-06 / P3). Because these two also have the most connectors (Word Online, Standard approvals in the Acknowledgement Letter flow), take extra care that the new `Scope` wrap doesn't disturb the approval step's configuration; re-check the approval step's assigned approver(s) after wrapping.

## Task 6 — Regression pass

- [ ] For all 14 flows, one final Studio test run each on the success path, confirming both the flow's normal side effect *and* the (unchanged) success Teams message still work exactly as before this session started.
- [ ] `guides/flow_inventory.md` "Confirmed gaps" updated — remove "no failure-path Teams notification anywhere" and add a "Confirmed fixed 2026-XX-XX" note (fill in the actual session date).

## Task 7 — Final backup

- [ ] Export a fresh `.zip` from Studio for all 14 flows into `flows/`, overwriting this repo's copies.
- [ ] `git add flows/ refdocs/` and confirm the diff includes all 14 updated `.zip` files plus the inventory/STATUS updates below.

---

## Wrap-up (do not skip)

- [ ] `refdocs/STATUS.md` — P2 row moved to ✅ Done (only if every task's Verify actually passed — if any flow was skipped or only partially done, mark it 🔶 or ⛔ and name exactly which flow and why)
- [ ] `refdocs/changelog/CHANGELOG.md` — session entry added, with a per-flow Verified line, not one blanket line for all 14
- [ ] `refdocs/changelog/DECISIONS.md` — no new ADR expected from this session (P2 executes D-06/D-03's *observability* prerequisite, doesn't introduce new architectural calls), but note here if one came up
- [ ] This doc updated to match what actually happened, including the actual session date replacing every `2026-XX-XX` placeholder above
