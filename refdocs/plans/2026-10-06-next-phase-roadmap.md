# Plan: finish the rollout, secure the system, then improve it

> **Date:** 2026-10-06. **Owner:** Fakhrul (intern). **For:** Fakhrul and the CDO supervisor.
> **Status:** proposal. Phases A–D follow the existing PRD. Phases E–G add the improvement work and need the scope change in **D-11** confirmed by the supervisor before they start.
> **Detail lives elsewhere:** rollout steps in `../execution/2026-10-02-real-system-rollout.md`, per-flow status in `../updates/FLOW-TRACKER.md`, manual items in `../updates/MANUAL-TODO.md`.

## 1. Summary

Do the work in three stages, in this order:

1. **Stabilize** (Phases A–B): put the sandbox-tested fixes on the real system, wave by wave. Nothing in the live system has changed yet.
2. **Secure** (Phases C–D): move all 14 flows off Kamal's account, then run the semester rollover on the fixed system. If Kamal's account is disabled, every flow stops, so this is the biggest single risk.
3. **Improve** (Phases E–G): make the flows harder to break, give CDO staff an admin page in the PowerApp, and add a few small flows where they clearly help.

The improvements are worth doing. Most of the problems found in testing are design problems that error alerts alone cannot prevent: duplicate rows on a re-run, no "are you sure?" before deleting everything, a stray file in a folder breaking a check, a failed file sitting in a drop folder with nobody told. But building them before the fixes are live, or on an account that is about to disappear, would mean doing the work twice.

## 2. Where things stand (2026-10-06)

| Area | State |
|---|---|
| Error alerts (Try/Catch + Terminate) | Built and sandbox-tested on flows 1, 3–10, 12, 13, 14. Flows 3, 4, 12, 13, 14 also tested against real Excel Online. **None applied live.** Packages ready in `build/office/` |
| Deprecated trigger (flows 2, 14) | Replacement tested in the sandbox; flow 14's `{Identifier}` Excel read proven. Flow 2's approvals/letters can only be tested at the office |
| Flow 11 (Get Status) | Blocked: the export is a copy of flow 4. Needs a fresh export |
| PowerApp (SIIP Report Duty Form, IPBAS) | Visible to you as run-only; no export or edit access yet |
| Ownership | All 14 flows on `kamalazreel.k@utp.edu.my`. Not started |
| Admin runbook | Draft (`../guides/admin_runbook.md`); final only after the rollover dry run |
| Hard-coded Excel file / Office Script ids (issue 2) | Researched: the Excel `Run script` action cannot pick its file at run time, so the plan is an identity guard plus a recovery runbook, not a full fix. Not built |
| Rollover date | Unknown (PRD Open Question #1) |

## 3. Rules for the improvement work

These apply to Phases E–G and come from what this project has learned so far.

1. **CDO staff must be able to maintain it without you.** Stay with Power Apps, Power Automate, SharePoint lists and Excel. No custom code unless D-04's test is met. Every new piece goes into the admin runbook.
2. **Standard connectors only, unless licensing is confirmed.** SharePoint, Outlook, Teams, Excel Online and Approvals work with the normal Microsoft 365 licence. Premium connectors (HTTP, Dataverse, custom connectors) need extra licences. `ASSUMED:` CDO has no premium Power Platform licence; check before designing anything that needs one.
3. **Every change goes through the sandbox first** (D-08/D-09), then the office laptop with a backup (rule 5). Improvements change behaviour, so each one also needs a success-path test, not only a failure test.
4. **No improvement work during a rollover window.** Freeze changes from the rollover dry run (Phase D) until the live rollover has finished.
5. **One change at a time per flow, re-exported and committed** each time, so any regression can be traced and undone.
6. **Fix the design, not just the symptom.** Each item in the backlog (§6) names the observed finding it removes.

## 4. Phases

### Phase A: First office visit (this week, Wed or Thu)

**Goal:** prove the rollout procedure on the safest flows and collect what is blocking later phases.

- Before starting: connections not on *Reconnect*; "before" screenshots of each flow's runs; someone watching the Teams alerts; quiet period agreed.
- **Wave 1, flow 9 (pilot):** backup → probe → read the failed run and the Teams alert → prod package → success test with your own address → re-export → `compare_prod.py`. **Press the real PowerApp button during the probe** and write down what the app shows when a flow fails. Nobody has seen this yet, and it shapes Phase F.
- **Wave 2, flow 1:** same procedure, one test registration in quiet hours.
- If time allows: **wave 3** (probe + fix only for flows 8, 10, 5, 6; their first real run is the success test) and **wave 4** (flows 3, 4 with `testdata/` rows).
- **Collect:** a fresh export of flow 11; exports of the PowerApps (`.msapp` or a package), or at least co-owner/edit access to them; the answers in MANUAL-TODO B and section E (shared mailbox, new owner account, rollover date).
- **Exit:** flows 9 and 1 live and verified; the PowerApp's reaction to a failed flow recorded; flow 11 exported or a date for it.

### Phase B: Finish the rollout (next 1–2 office visits)

- Waves 4–6: flows 3, 4, then 7, 12, 13, then 14 (procedure and cleanup list in the execution doc).
- Flow 2 last, with its own mini-plan (trigger swap + subfolder guard + approvals/letters; letters and emails to you only).
- Flow 11: analyse the new export, add the same Try/Catch fix, sandbox-test, then roll out like the others.
- Class R flows (5, 6, 8, 10): stay "awaiting first real run" in STATUS until their first genuine run is read.
- **Exit:** every flow's FAILED alert proven on the real system; `compare_prod.py` IDENTICAL for each; FLOW-TRACKER shows all flows applied.

### Phase C: Ownership migration (PRD P4, one dedicated visit)

**Why before improvements:** connections, the Teams sender and the Outlook sender all hang off Kamal's account. Anything built before this would have to be reconnected again afterwards.

- **Decide (with CDO/IT):** the new owner, ideally a shared or service account that does not leave with a person (PRD Open Question #6); the shared CDO mailbox for outgoing emails; at least two human co-owners on every flow and the PowerApp.
- Write the plan/execution pair first (rule 2): connection-by-connection list per flow, the order, and a rollback.
- **Exit:** every flow runs under the new connections with Kamal removed; a forced failure (probe) still alerts; emails come from the shared mailbox.

### Phase D: Rollover dry run and the live rollover (PRD P5–P6)

- Dry run the semester rollover (M5) on the fixed, migrated system, with a staff member following the admin runbook unaided. Fill every `[to fill: …]` in the runbook.
- **Change freeze** from the dry run until the live rollover has finished.
- Live rollover, watched through the Teams alerts.
- **Exit:** the rollover completes with no silent failure; the runbook is marked final.

> Phases A–D are the original PRD. Phases E–G below are new and depend on **D-11** being confirmed.

### Phase E: Make the flows harder to break (robustness)

Small, flow-by-flow changes that remove the failure modes seen in testing (backlog §6, items R1–R9). Each is designed in the sandbox, shipped like a fix (probe not needed, but backup, success test and compare are), and documented in the runbook.

**Start with:** R1 (run log), R2 (plain-language alerts) and R3 (no duplicates on re-run). They are the most visible to staff and are needed by the admin page in Phase F.

### Phase F: PowerApp admin / control page

**Needs:** edit access to the PowerApp (Phase A collects it), and R1 (the run log) from Phase E.

A separate screen in the existing admin app, only for CDO admins (backlog items A1–A7):

- **System status:** per flow, last run time, result and the error in plain words, read from the run log list. Red/amber/green at a glance.
- **Safe buttons:** every destructive action ("Clear Raw Data", "Delete All Student", "Send email to all students", "Add into MasterList") behind a confirmation screen saying what will happen and how many records it touches, then a "running…" state until the flow returns.
- **Control Template editor** with validation (email format, semester format, Teams recipients present) instead of editing the list directly.
- **Semester rollover checklist:** the runbook steps in order, each with its button, status and "done" tick, so the order cannot be skipped.
- **Pre-flight checks** before a run: e.g. "the check folder holds exactly one file", "the template tables are empty", "Get Raw Data ran after the last change".

How it will be tested: a copy of the app imported into your own environment, pointed at the sandbox lists (same idea as D-08). This needs the app export from Phase A.

### Phase G: Student-facing PowerApp and new flows (only where they clearly help)

- **Student form (U1–U3):** field validation with clear messages (email, student ID format), a confirmation screen, "your submission was received" state. Only what fixes a real data problem seen in the lists; no redesign for its own sake.
- **New flows (N1–N4):** a daily health check that posts to Teams if something looks wrong; a "send this failed item again" flow called from the admin page; a rollover assistant that runs the rollover steps in order with checks between them; a weekly summary for the PIC.

Each new flow gets the same Try/Catch wrapper, a run-log entry, sandbox tests and a runbook page.

## 5. Order and dependencies at a glance

```
A (visit 1) ─► B (visits 2–3) ─► C (ownership) ─► D (rollover, freeze)
                    │                                   │
                    └─ E1–E3 can be designed in the     └─► E (rest) ─► F (admin page) ─► G
                       sandbox during B–C, shipped
                       after C
```

You can design and sandbox-test Phase E items from home at any time. Only shipping them needs the office, and it should wait until after Phase C so they are built on the new connections.

## 6. Improvement backlog

Effort: S = under a day, M = a few days, L = a week or more (including sandbox tests and docs).

### Robustness (Phase E)

| # | Improvement | Fixes (observed finding) | Approach | Effort |
|---|---|---|---|---|
| R1 | **Run log list** | Staff cannot see what ran or failed without opening Power Automate | New SharePoint list `CDO Flow Run Log` (flow, start, end, result, failed step, error, run link, who started it). Every flow writes one row at start and updates it at the end, inside the existing Try/Catch | M |
| R2 | **Plain-language alerts** | FAILED alerts show technical step names | Map the common errors (bad email, file locked, table not found, connection expired) to a sentence and a "what to do" line in the Teams post, as in runbook §6 | S |
| R3 | **No duplicates on re-run** | Flows 3, 4, 5 add duplicates when run twice; flow 14 duplicates students when files arrive together | Check-before-create (look the record up first); for flow 14, trigger concurrency set to 1 so files are processed one at a time | M |
| R4 | **Input validation before work starts** | Flows 1 and 9 fail on one bad address; flow 10 leaves a half-sent batch when one address is bad; flows 2, 12, 13, 14 need exact column/table names | Validate emails and required columns first; skip and report bad rows instead of failing halfway | M |
| R5 | **One-file guard for the check flows** | Flows 12, 13 process every file in the folder; a stray file breaks the run and emails the PIC twice | Stop with a clear alert if the folder does not hold exactly one file | S |
| R6 | **Failed drop files moved aside** | Flow 14 (and 2) leave a failed file in the drop folder; nobody knows | Move it to a `Failed` subfolder and name it in the alert | S |
| R7 | **Excel identity guard** (issue 2) | Replacing a template silently breaks the flows that use it | First step checks the template's id still exists and has the expected tables; if not, an alert saying "the template was replaced; see runbook §x" | M |
| R8 | **Wait for completion, not fixed delays** | Flows 7, 12, 13 wait a fixed time | Replace the fixed `Delay` with a check loop where the connector allows it | M |
| R9 | **Shared error-handling block** | The same Try/Catch is copied into every flow | A child flow "Notify CDO" called from every flow's Catch. **Check first:** child flows must live in a solution, which needs Dataverse in the environment | M |

### Admin page (Phase F)

| # | Improvement | Fixes | Effort |
|---|---|---|---|
| A1 | System status screen (from R1) | Staff cannot tell whether things worked | M |
| A2 | Confirmation screens on destructive buttons, with record counts | "Clear Raw Data" / "Delete All Student" have no "are you sure?" (runbook §2) | S |
| A3 | Running / done / failed state on every button | Unknown how the app reacts when a flow fails (Phase A finds out) | M |
| A4 | Control Template editor with validation | Wrong PIC email or semester in the one settings record breaks every flow | M |
| A5 | Rollover checklist screen | The rollover order matters and is easy to get wrong | M |
| A6 | Pre-flight checks before risky runs | One-file rule, empty templates, Get Raw Data first | M |
| A7 | Admin-only access | Admin functions should not be visible to everyone | S (check how the app decides who is admin) |

### Student form and new flows (Phase G)

| # | Improvement | Effort |
|---|---|---|
| U1 | Field validation and clear error messages on the student form | M |
| U2 | Confirmation / "received" screen after submit | S |
| U3 | Pre-filled fields where the data already exists (if not already done; check the current app) | M |
| N1 | Daily health check flow (connections alive, last runs OK, templates intact) posting to Teams | M |
| N2 | "Resend / retry this item" flow called from the admin page | M |
| N3 | Rollover assistant flow (runs the steps in order with checks) | L |
| N4 | Weekly status summary to the PIC | S |

## 7. Decisions and questions for the supervisor / CDO

1. **Scope:** approve D-11 (improvements are in scope after stabilization). Which items matter most to the staff who use the system?
2. **Rollover date** (PRD Q1): the whole timeline hangs on it.
3. **New owner account and shared mailbox** (PRD Q6, Phase C).
4. **Your internship end date:** everything must be handed over and documented before it.
5. **PowerApp access:** edit access or an export of `SIIP Report Duty Form` / `IPBAS`.
6. **Licensing:** is any premium Power Platform licence available? (Decides R9, and any HTTP/Dataverse ideas.)
7. **Duplicates policy** (MANUAL-TODO B): skip, update or add again when a company/supervisor already exists. R3 implements whatever CDO decides.
8. **Public repository:** the GitHub repo is public and contains the live flow exports, site/list ids and a staff email. Keep it public or make it private?

## 8. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Kamal's account disabled before Phase C | Every flow stops | Do Phase C right after B; ask CDO/IT not to disable the account before then |
| Rollover date arrives before Phases A–C | Rollover runs on the unfixed system | Phase A/B first; the class R flows already have their probe in place; freeze rule |
| Improvements change behaviour staff rely on | Confusion, new failure modes | One change at a time, sandbox success tests, runbook updated in the same visit |
| PowerApp access not granted | Phase F/G blocked | Ask in Phase A; Phase E does not need it |
| Premium licence needed for an idea | Can't ship it | Rule 2: design with standard connectors |
| You leave before handover | Nobody can maintain it | Runbook + co-owners in Phase C; every phase ends with docs |

## 9. What you can do now, from home

- Fill the runbook's contact details and the questions in §7 into an email/message for the supervisor.
- Prepare Phase A: copy `build/office/` and `testdata/`, re-read the execution doc, check the hashes in OFFICE-CHECKLIST.
- Ask (by message, before the visit) for the flow 11 export and PowerApp access, so they are ready on the day.
- Once D-11 is approved: R1 and R2 can be designed and sandbox-tested at home (Claude builds them the same way as the fixes).
