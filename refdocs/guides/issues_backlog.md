# Issues Backlog — UTP CDO Internship Automation

> The working list. Pick **one** item at a time (per your instruction), get it fully spec'd into a plan/execution pair, execute it solo at the office laptop (I won't be present there), then come back for the next one.
>
> **Confidence note — read `guides/methodology.md` first.** "Confirmed" in the Evidence column means Tier 1 (read directly in the flow's exported JSON — a structural fact) or Tier 2 (verified against Microsoft's own docs — a platform fact), never Tier 3. Where an issue claims a specific structural fact *is the cause* of a specific reported symptom, that link itself is a **Tier 3 hypothesis** even when the structural fact underneath it is Tier 1-confirmed — none of these have been checked yet against an actual failed run's error message or a live reproduction. "Reported, not yet confirmed" means it's from your brief and still needs tracing to a specific flow/action.

Last updated: 2026-09-16

---

## Confirmed, root-caused, ready to spec

These have direct evidence in the flow exports. Each maps to a PRD Decision (`refdocs/changelog/DECISIONS.md`).

| # | Issue | Evidence | Affects | Status / maps to |
|---|---|---|---|---|
| 1 | ~~No failure notifications anywhere~~ **Corrected 2026-09-30:** 12 of 14 flows *do* post a Teams "FAILED" alert. The real gaps: **Success Submit Email** has no alert at all; **Store Student List** has none; and in the other 12 the alert doesn't say what failed, is blind if the config lookup fails, and may leave the run marked Succeeded | Re-parsed `runAfter` graphs of all 14 `definition.json` (the 2026-09-16 grep result was wrong) | Flow 1 (and flow 14) fully silent on failure; the other 12 partially. **Plus (observed 2026-09-30, flow 3): their failed runs show as "Succeeded" in run history** | 🔶 Reworked per flow under D-08. Flow 3: Try/Catch + Terminate pattern sandbox-tested ([doc](../issues/2026-09-30-flow-03-add-hc-supervisor.md)). Flow 1: fix built, sandbox test pending ([`../issues/2026-09-30-flow-01-success-submit-email.md`](../issues/2026-09-30-flow-01-success-submit-email.md)). Old doc [superseded](../issues/2026-09-16-01-no-failure-notifications.md) |
| 2 | **"Process ID reading Excel doesn't work"** — Excel master-list templates and their Office Scripts are referenced by a hard-coded SharePoint drive-item ID + script ID, bound to one specific file object | Confirmed in Host Company Info MasterList Checking (`file: 01QW2RL4GFFAT2NQYTXFEZ45YLOE4VKNIH`, `scriptId: ...01HL57H3NEOVQVGZ3N75FIXLGLMLEIQ7IG`); same reference *pattern* present in flows #2, #7, #12, #14 per `path` usage in `flow_inventory.md` | Every Excel-touching flow (5 of 14) | D-03 |
| 2a | **Refining #2:** I initially assumed the fix was "make the file reference resolve dynamically by path at runtime." Just confirmed via Microsoft's own docs/community threads: the Excel Online (Business) **`Run script` action's file parameter does not support dynamic/runtime selection** — it must be picked via Studio's file browser at design time, bound to that file. So a full dynamic rearchitecture isn't cleanly available on this connector. Revised fix direction: (a) keep D-03's in-place-edit rule as the primary defense, (b) add an early "file identity guard" step that checks the file is still the expected one and fails loudly with a clear Teams message instead of an opaque connector error, (c) write an exact recovery runbook for the day it does break anyway | Researched, not yet drafted into a plan | Same 5 flows | Will become an amended D-03 once spec'd |
| 2b | **Second candidate cause, from the original 2023–2024 admin guide:** any Excel file dropped to trigger the Issuance Letter flow must match an exact, undocumented-elsewhere format — `Course`/`Host Company` headers need exactly one trailing space, every other header none, table named exactly `Database` (guide p.25). A file off by one space or a wrong table name plausibly produces the same symptom as #2/#2a. **Whether "process ID reading Excel doesn't work" means a hard failure with no output, or a wrong/garbled output, points to a different one of #2a vs #2b** — needs the reporter to clarify which was observed | Confirmed via `refdocs/context-2023-2024-admin-user-guide.pdf`, detailed in `previous_system_guide_notes.md` | Acknowledgement Letter Email Process specifically | Will inform issue 2's plan doc once drafted |
| 6 | **Workflow-ordering footgun:** the Host Company / HC Supervisor MasterList Checking flows (#12, #13) operate on the *last output* of "Combine raw data" ("Get Raw Data" button), not live data. Running a MasterList check without first re-running Get Raw Data silently checks stale data | Confirmed via `refdocs/context-2023-2024-admin-user-guide.pdf` p.18 ("Make sure you had get latest 'Get Raw Data'!!!") | Flows #7, #12, #13 | Not yet mapped to a Decision — candidate for either an admin-guideline callout (M8) or a flow-level guard (check Get Raw Data's last-run timestamp before proceeding) |
| 3 | **Deprecated trigger** — "When a file is created in a folder (deprecated)" used by 2 flows | Confirmed via `grep 'deprecated'`: Acknowledgement Letter Email Process, Store Student List into SharePoint List | 2 flows — likely cause of reported "sharefolder" flakiness | D-06 |
| 4 | **Flow ownership on a departing account** — all 14 flows' connections authenticate as `kamalazreel.k@utp.edu.my`; total, not partial | Confirmed in every `manifest.json` | All 14 flows | D-02, Module M6 |
| 5 | **Outlook emails send from a personal mailbox**, not a shared/departmental one | Confirmed — Outlook connector owner is the same personal account as #4 | Every email-sending flow (7 of 14) | Module M6 |

## Reported in your brief, not yet traced to a specific cause

These are real (you reported them), but I haven't yet connected each one to a specific flow/action the way I have for the items above. Picking one of these means the first step is tracing it, not fixing it.

| # | Issue | What I know so far | What's still needed |
|---|---|---|---|
| 7 | **"Issue with the student share folder"** | Likely the same root cause as #3 (deprecated trigger on the student-list drop folder) — but could also be a separate SharePoint permissions/sync issue | Confirm with you: is this the file-drop-folder problem, or something else (e.g., students can't access a folder they're supposed to)? |
| 8 | **"System only works for students to fill in"** (implying other parts are degraded) | Could just be describing the downstream effect of #1 (no failure visibility) + #4/#5 (manual email fallback) — or could mean a specific button/flow is actually broken, not just silent | Needs you to name which specific admin button/flow currently fails outright vs. which ones you just don't trust |
| 9 | **"Old database" issue** | Not enough detail in the original brief to trace | Needs a concrete description: which database, what's wrong with it |
| 10 | **No admin guideline exists** | Confirmed absence — not a bug, a missing deliverable | Scoped as Module M8 / Phase P5, after the underlying flows are stable — writing a guideline for a system that's still breaking would go stale immediately |

## Data-integrity oddities found while reading the exports (need your confirmation, not necessarily bugs)

| # | Issue | Evidence | Why it matters |
|---|---|---|---|
| 11 | `UTPCSDCDO Success Submit Email` is the only flow export without a `[LIVE-CDO]` prefix | Confirmed naming difference | Might mean it's not currently published/live — if the "confirmation email after submit" isn't actually running, that's a real gap, not just a naming quirk |
| 12 | The zip named "Email for Student Report Duty Status" internally identifies itself as "Add Host Company into MasterList" | Confirmed by reading the flow's own `displayName` inside the package | Either a mis-export, or Power Automate genuinely has a duplicate/misnamed flow — don't edit this one until confirmed in Studio which flow it actually is | **RESOLVED 2026-10-02: mis-export.** Same flow id and definition as "Add Host Company into MasterList"; the real status flow still needs exporting.
| 13 | ~~"Standard approvals" step inside the Acknowledgement Letter flow — purpose unconfirmed~~ | **Resolved 2026-09-16** — confirmed via `refdocs/context-2023-2024-admin-user-guide.pdf`: a deliberate two-stage approval gate (raw file, then cleaned file), not a leftover | No longer blocks work on this flow — factored into its fix design already |

---

## How to use this list

1. Pick one row (any number).
2. I write (or finish) a plan + execution doc for it in `refdocs/plans/` and `refdocs/execution/`.
3. You execute it solo at the office laptop, following the execution doc exactly (no Claude there, so it has to be self-sufficient — Studio steps, exact field values, exact Verify checks).
4. Back here: report what happened, I update `STATUS.md` / `CHANGELOG.md` / this file, and we pick the next row.

**13 distinct issues total, 1 resolved (12 active).** Items **1–6** (and refinements 2a/2b of issue 2) are confirmed and ready to move straight to planning — issue 6 is the workflow-ordering footgun found in the original admin guide, see `previous_system_guide_notes.md`. Items **7–10** need a quick answer from you before they're plannable. Items **11–12** need a 30-second check in Studio (not a fix) before anyone touches those specific flows. Item **13** is resolved.
