# Issue 1 — No failure notifications (Teams shows success only, never failure)

> Backlog item 1 in `refdocs/guides/issues_backlog.md`. Plan: `refdocs/plans/2026-09-16-observability-and-error-handling.md`. Execution: `refdocs/execution/2026-09-16-observability-and-error-handling.md`.

> ## ⚠️ CORRECTION 2026-09-30: the core premise of this doc is wrong. Do not execute its plan as written.
>
> Re-parsing every flow's `definition.json` (walking each action's `runAfter`, not grepping) shows that **12 of 14 flows already have a failure alert**. It's a Teams "…process is FAILED!" post that runs after the final success post is `Failed/Skipped/TimedOut`. Any failure after the config lookup skips the success posts and so fires it (T1). The "0 matches" grep result recorded on 2026-09-16 was wrong. Why it came out wrong wasn't found, but the 12 flows plainly contain the pattern. Examples: Delete Student List's `Post_message_in_a_chat_or_channel_4`, and Add HC Supervisor's `Post_message_in_a_chat_or_channel_4`.
>
> **Flows that really lack an alert:** **Success Submit Email** (no Teams at all; now handled in [`2026-09-30-flow-01-success-submit-email.md`](2026-09-30-flow-01-success-submit-email.md)) and **Store Student List into SharePoint List** (its only non-success branch is a `Set_variable`, still to be reviewed).
>
> **What remains true and worth fixing, per flow:** (a) the existing alert says only "FAILED", not which step or why; (b) if the config `Get_item` fails, no alert can fire; (c) when the alert branch succeeds, the run may show as *Succeeded* in run history, hiding the failure (T3, to be checked in the sandbox). These are now handled flow by flow under D-08, starting with flows 1–3. The analysis below is kept for history; its "Structural fact" bullets are superseded.

## Status

⛔ **Superseded** (2026-09-30). See the correction above. The plan/execution pair `2026-09-16-observability-and-error-handling` must not be executed as written. Per-flow issue docs (`2026-09-30-flow-NN-*.md`) replace it.

## Reported symptom

From the original brief: *"All the processes while running when successfully show notifications in teams (running / processing/ success)."* And separately, reported as broken: *"email have to manual"* — staff resorting to manually sending emails instead of trusting the automation.

Read together, these describe the same gap from two angles: the *success* notification was explicitly requested and got built; nobody asked for a *failure* notification because the brief assumed "show notifications" implicitly covered both — but only the success case was ever implemented.

## Analysis

**Confidence note:** see `guides/methodology.md`. The two bullets below are **Tier 1 — structural fact**, read directly out of the JSON; nothing here is inferred. The "Consequence" paragraph after them is **Tier 3 — causal hypothesis**: it's the most plausible explanation for the reported symptoms, not something confirmed against an actual failed run's Teams silence or a real staff report of "I did the manual workaround because nothing showed up." If you can check these flows' run history from your personal account, that would move this from Tier 3 to confirmed — see Verification below.

**Structural fact, confirmed by direct inspection of all 14 flow `definition.json` files:**

- `grep -c '"Failed"'` runAfter-branch pattern across all 14 flows → **0 matches in every file.** No flow has any action configured to run on `Failed`, `Skipped`, or `TimedOut`.
- `grep -c 'PostMessageToConversation'` → present in 13 of 14 flows, always exactly once, always on the implicit default `runAfter: Succeeded` path.

**Consequence (hypothesis, not yet confirmed against a live run):** when any step in a flow fails — a throttled SharePoint call, a locked Excel file, the hard-coded drive-item ID going stale (issue 2), a malformed input from the PowerApp — the flow simply stops. No message anywhere. The only way anyone finds out is a downstream absence (an email that never arrived, a master-list entry that never got added), discovered hours or days later, by which point the instinct is to just do it manually rather than trust the flow to have partially worked.

## Review

**What already exists and must not break:**

- 13 of 14 flows already have a working success-path Teams post. The fix adds a second, failure-path post next to it — it does not touch or re-architect the success path. **The 14th, Success Submit Email, has no Teams post and no `Get_item` action at all** (confirmed: its `manifest.json` lists only SharePoint and Outlook connectors) — it needs a baseline success post *and* the failure post added, not just the failure half. Treated as its own task (2a) in the execution doc rather than folded into the "simple flows" group.
- **The Teams recipient is not hard-coded per flow.** Every flow's Teams post is preceded by a `Get_item` action (SharePoint, `GetItem` operation) that is one of the flow's *first* actions (`runAfter: {}` — no dependencies), fetching a **single fixed config list item, `id: 1`**, from table `be7f2b53-cc4e-42b1-a043-a7d6a849ba42` on the CDO site. The Teams post's recipient is `@{outputs('Get_item')?['body/TeamsNotification1']}` — a field on that config item. One flow ("Combine raw data") reads `TeamsNotification2` instead of `TeamsNotification1` from the same config item — worth confirming whether that's intentional (a second notification target for a different purpose) or a copy-paste inconsistency, but it doesn't block this fix either way; the failure branch for that flow should read whichever field its own success branch already reads.
- This is a better foundation than the original plan assumed. The plan's Risk table flagged "which Teams channel/chat does each flow target" as an unconfirmed unknown requiring a per-flow read before writing the failure branch — **that's now resolved**: it's not a channel, it's a 1:1 "Chat with Flow bot" to whoever's listed in the shared config item's `TeamsNotification1` (or `2`) field, and since `Get_item` already ran early in the flow for the success path, the failure branch can reuse its output directly instead of re-fetching it.

**What this changes about the fix design:**

- Because `Get_item` runs *before* the flow's main logic (not interleaved with it), the realistic failure scenarios are almost all *downstream* of it — meaning the failure branch can safely assume `Get_item`'s output is available, without needing a hard-coded fallback recipient for the common case.
- The one edge case worth guarding: if `Get_item` *itself* is what fails (the config item was deleted, or the SharePoint connection is broken tenant-wide), no Teams post can fire at all — dynamic or hard-coded — because the failure is upstream of having a recipient. This can't be solved by this fix; it's a fundamental limit of "notify via the same system that just failed." Noting it rather than solving it (see Verification below for how we'll at least detect this class of failure differently).

## Fix design

Per flow:
1. If the flow's actions aren't already wrapped in one `Scope`, wrap them in a new outer `Scope` (Studio: select all actions → "Add a Scope"). This gives one place to attach a failure handler instead of one per action.
2. Add a `Post message in a chat or channel` action, `runAfter` the `Scope` configured for `Failed`, `Skipped`, `TimedOut`, with:
   - `location`: `Chat with Flow bot` (matching the existing success post)
   - `recipient`: the **same expression the flow's existing success post already uses** — `@{outputs('Get_item')?['body/TeamsNotification1']}` (or `TeamsNotification2` for Combine raw data) — reusing `Get_item`'s output, not re-fetching it
   - `message`: `❌ [flow display name] failed. Check run history.` — simple and specific enough to locate the run, not diagnostic prose that goes stale
3. Leave the trigger and the `Get_item` action outside the wrapped `Scope`, so a failure in the flow's core logic doesn't prevent the failure message's own inputs from being available.

This is unchanged in shape from the original plan — the correction is entirely in *which expression* the failure post uses for its recipient, now confirmed rather than assumed.

## Plan / execution links

- Plan (why/scope/risk/DoD): [`../plans/2026-09-16-observability-and-error-handling.md`](../plans/2026-09-16-observability-and-error-handling.md)
- Execution (task-by-task Studio steps): [`../execution/2026-09-16-observability-and-error-handling.md`](../execution/2026-09-16-observability-and-error-handling.md) — updated to specify the exact recipient expression per task instead of "same channel as existing success message"

## Verification

- **Before the office-laptop session, if accessible from the personal account:** check each flow's Run history in Power Automate (usually viewable with read access, not just edit access). Look for past failed runs and their actual error messages — this would confirm (or correct) the Tier 3 hypothesis above cheaply, without needing live access to reproduce anything.
- Per flow: force a failure, confirm the ❌ message actually arrives in the Flow-bot chat with the correct recipient (whoever's in the config item's `TeamsNotification1`/`2` field), confirm the existing ✅ success message still fires unchanged on a normal run.
- System-wide, once all 14 are done: confirm the shared config item (`id: 1`) is documented in `guides/env_setup.md` as a dependency every flow relies on — if that item or its `TeamsNotification1`/`2` columns are ever changed, every flow's notifications (success *and* failure) break at once. This is a smaller, less severe version of the same "shared fixed identity" fragility as issue 2 (D-03) and worth flagging in the admin guideline (Module M8) later: don't delete or restructure that config list item.
