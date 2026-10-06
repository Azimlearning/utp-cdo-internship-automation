# UTP CDO Internship Automation — Product Requirements Document (PRD)

> A PowerApp + Power Automate + SharePoint/Excel system that runs UTP's Career Development Office (CDO) internship program each semester: students self-enroll and fill report-duty details, the system detects new vs. already-known host companies/supervisors so staff only manually check the new/partial matches, personalized appointment letters go out automatically, and the whole dataset resets cleanly for the next intake. This project **stabilizes and migrates an existing production system** — it does not rebuild it.

- **Owner:** Fakhrul (CDO internship student, `fakhrulazim.am@gmail.com` / `fakhrul_22012087@utp.edu.my`)
- **Users:** CDO admin staff (operate the flows/buttons), interning students (fill the form, receive emails), host company supervisors (receive personalized appointment letters/emails)
- **Status:** Scaffolded 2026-09-16 — existing production system being stabilized, not pre-implementation
- **Last updated:** 2026-09-16
- **Source of record:** [cdo-internship-automation-sources.md](cdo-internship-automation-sources.md)
- **Founding context:** [context-2026-09-16-brief.md](context-2026-09-16-brief.md) (raw brief), [guides/flow_inventory.md](guides/flow_inventory.md) (extracted from the 14 live flow exports in `flows/`)

---

## 1. Context & Hard Constraints

Confirmed from the founding brief and the flow-export analysis. These drive every downstream decision.

| Constraint | Value | Consequence |
|---|---|---|
| Physical access | Live/admin changes (flow ownership, connections, publishing) require the **office admin laptop**; the personal account is read/analyze-only | Every fix is designed and reviewed remotely first, then executed in batched **office-laptop sessions** to minimize trips |
| Deadline | Tied to the **next semester rollover** — exact date not yet given (Open Question #1) | Roadmap sequences the trigger/Excel-ID fixes to land *before* rollover, not after |
| No test environment | No separate Power Platform dev/test tier exists; the 14 exported `.zip` files were the only existing backup/rollback mechanism | This repo (git) becomes the real safety net from here forward; still export a fresh `.zip` backup immediately before editing any live flow |
| Scope boundary | Stay Power Platform low-code by default; small custom code (e.g. one Azure Function) is acceptable only where it clearly outperforms the low-code option | Keeps the system maintainable by CDO staff after this project's owner leaves |
| Data sensitivity | Student PII and host company data; must stay inside the UTP Microsoft 365 tenant | No third-party services in the fix design; everything stays within SharePoint/Excel/Outlook/Teams/Power Automate |
| Current ownership | All 14 flows' connections are authenticated as `kamalazreel.k@utp.edu.my` (confirmed, not partial) | The ownership migration touches every flow, not a subset — see Module M6 |
| Single semester environment | One live SharePoint site (`CareerDevelopmentOfficeCDO`) — no separate dev/prod site | Every fix is tested as carefully as production, because it *is* production |

---

## 2. Product Principles

1. **Diagnose before rebuilding.** Several requirements in the original brief (new/partial-match detection, Teams success notifications) are already implemented correctly — see [flow_inventory.md](guides/flow_inventory.md) "Confirmed working". Fix what's broken; don't redesign what works.
2. **No silent failure.** Every flow must report both success *and* failure to Teams. A flow that stops silently is indistinguishable from a flow that isn't running, and that's the root cause of "email has to be sent manually" — staff resort to manual work because they have no signal anything broke.
3. **Reference by path/lookup, not by fixed identity.** The recurring root cause across this system (see D-03) is Excel files and Office Scripts referenced by a hard-coded internal ID that breaks the moment the referenced file is replaced instead of edited in place. New/fixed flows resolve their target file at runtime wherever practical.
4. **Batch live changes.** Because live edits require physical office access, group fixes into as few, as well-tested office-laptop sessions as possible — never "just quickly fix one thing" as a standalone trip if it can be bundled.
5. **Leave it maintainable.** This system will be run by CDO staff after the current owner's internship ends. Every fix should reduce the amount of tribal knowledge required to operate it, not increase it — this is *why* the admin guideline (Module M8) is a first-class deliverable, not an afterthought.

---

## 3. Architecture

A single integrated system with four component types that must be reasoned about together — a change to one routinely requires a matching change in another (see the invariant in `.claude/memory/preflight.md` Q5).

```
┌─────────────┐   submit    ┌──────────────────┐   trigger    ┌───────────────────┐
│  PowerApp    │ ──────────► │ SharePoint Lists  │ ───────────► │  Power Automate    │
│ (data entry, │             │ (student records, │              │  flows (13)        │
│  autofill,   │ ◄────────── │  company records)  │ ◄─────────── │  — this repo's     │
│  admin       │   read for  └──────────────────┘   read/write  │  subject matter     │
│  buttons)    │   autofill           ▲                          └─────────┬──────────┘
└─────────────┘                       │                                    │
                                       │ reconcile against                 │ Run Script (Office Scripts),
                                       │                                    │ Send email, Post to Teams
                                       ▼                                    ▼
                           ┌────────────────────────┐            ┌───────────────────┐
                           │ Excel master-list       │            │ Outlook / Teams /   │
                           │ templates (SharePoint    │            │ Word Online          │
                           │ team site doc library)   │            │ (email, letters,     │
                           └────────────────────────┘            │  notifications)      │
                                                                   └───────────────────┘
```

### 3.1 Components

- **PowerApp** — student-facing data-entry form (with autofill from prior data) and staff-facing admin buttons that trigger the manual (`PowerAppV2`) flows. Not exported into this repo; lives in the Power Platform environment. Referenced here because every flow's manual trigger schema is a contract with it.
- **Power Automate flows (13)** — the automation layer. Full inventory, triggers, connectors, and confirmed issues per flow: [guides/flow_inventory.md](guides/flow_inventory.md).
- **SharePoint Lists** — the per-semester student and company records (the "database by year" from the brief).
- **Excel master-list templates** — company/supervisor master lists and raw-data staging, stored as `.xlsx` files in the CDO SharePoint team site document library, manipulated via Office Scripts (`Run script` / `RunScriptProd` actions). This is where the hard-coded-ID fragility (D-03) lives.
- **Outlook, Teams, Word Online** — delivery channels: personalized emails/letters to students and host company supervisors, and running/processing/success/failure notifications to CDO staff in Teams.

### 3.2 Data & state

- **Per-semester SharePoint list** holds the live student/company records for the current intake.
- **Excel master-list templates** (Host Company, HC Supervisor) are the cross-semester "memory" — new records get reconciled against them, confirmed new/partial entries get appended.
- **Semester rollover** = clear the SharePoint list (flow #8) + reset/clear the raw Excel staging (flow #6) + reseed with the new semester's template, **in place**, never by uploading a replacement file (D-03).

---

## 4. Modules / Feature Areas

| Module | Covers | Flows involved |
|---|---|---|
| **M1 — Student Data Entry & Onboarding** | PowerApp intake with autofill, submit → SharePoint, confirmation email | Success Submit Email, Store Student List into SharePoint List |
| **M2 — Company & Supervisor MasterList Management** | New-vs-partial-match detection, manual reconfirm/re-upload, master list updates | Add Host Company into MasterList, Add HC Supervisor into MasterList, Host Company Info MasterList Checking, HC Supervisor Info MasterList Checking, Combine raw data, Clear Raw Database |
| **M3 — Acknowledgement / Appointment Letter Process** | Personalized PDF letter generation + approval + send to host company supervisors | Acknowledgement Letter Email Process |
| **M4 — Report Duty Communications** | Bulk start-registration email, reminders for non-respondents, status emails, update notifications | Bulk Email To Start Registration, Email for Report Duty Reminder, Email for Student Report Duty Status, Email To Inform Student Updates |
| **M5 — Semester Rollover & Data Lifecycle** | Clear current-semester data, reset templates in place, seed new batch | Delete Student List from SharePoint List + the template-reset procedure (to be documented as a runbook, not just a flow) |
| **M6 — Ownership, Access & Identity** | Migrate all 14 flows off `kamalazreel.k@utp.edu.my`; move Outlook sends to a shared mailbox | Cross-cutting — all 14 flows |
| **M7 — Observability & Reliability** | Teams running/processing/success/**failure** notifications; error handling on every flow | Cross-cutting — all 14 flows |
| **M8 — Admin Guideline Documentation** | The "guideline as admin" deliverable named in the brief — a runbook a non-technical CDO staff member can follow | Not a flow; a doc deliverable, written once M1–M7 are stable |

---

## 5. Non-Goals

Explicitly out of scope. Revisit only by adding an ADR that says why.

- **Not a platform migration.** Not moving off Power Platform / SharePoint / Excel onto a custom web app or database, even though the owner is open to *small* custom code (D-04). The brief never asked for this and it would leave CDO staff unable to maintain the system.
- **Not building new features beyond what the brief describes.** New-vs-partial-match detection, Teams notifications, personalized letters, and bulk/reminder emails are the full scope — see Module table. Nothing new is being added on top.
- **Not fixing UI/UX of the PowerApp form itself** unless a fix specifically requires it (e.g., a manual-trigger schema change). This project's scope is the automation layer and its reliability, not a PowerApp redesign.
- **Not standing up a formal Power Platform dev/test environment** — no budget/need has been stated for one; the mitigation is git-tracked backups and batched, reviewed office-laptop sessions instead (D-07).

---

## 6. Build Roadmap

| Phase | Scope | Exit criteria |
|---|---|---|
| **P0 — Docs & git baseline** | Scaffold this project (this session): PRD, STATUS, sources, guides, changelog, plans/execution pair, `.claude/` config | This doc set exists, is committed, and `flows/` is under version control |
| **P1 — Design the fixes (remote, no live access needed)** | Spec the exact error-handling pattern (Configure run after → Failed → Teams post), the path-based Excel lookup replacement for hard-coded IDs, and the modern-trigger replacement for the 2 deprecated-trigger flows | A reviewed execution doc exists for P2 and P3 with concrete per-flow steps, ready to execute in one sitting |
| **P2 — Office-laptop session 1: Observability** | Add failure-path error handling + Teams alerts to all 14 flows | Every flow posts to Teams on both success and failure; a deliberately-forced failure in a test run is visible in Teams |
| **P3 — Office-laptop session 2: Root-cause fixes** | Replace the deprecated "file created" trigger (2 flows); rearchitect the hard-coded Excel file/script ID references to resolve by path | Both deprecated-trigger flows run on the modern trigger; an Excel template file can be cleared and reused without breaking any flow that references it |
| **P4 — Office-laptop session 3: Ownership migration** | Move all 14 flows' connections off `kamalazreel.k@utp.edu.my`; move Outlook sends to a shared CDO mailbox | Every flow runs successfully under the new owner/connections with Kamal removed as owner |
| **P5 — Semester rollover dry run + admin guideline** | Execute a full rollover (M5) against the fixed system in a controlled way; write the admin runbook (M8) | A non-technical CDO staff member can follow the guideline doc to run a rollover unsupervised |
| **P6 — Live semester rollover** | The actual deadline event, monitored via the new Teams alerts from P2 | Rollover completes with zero silent failures; any failure that does occur is caught and visible in Teams within the same session |

---

## 7. Decision Log

Canonical one-line list. Load-bearing entries are expanded as ADRs in `changelog/DECISIONS.md` under the same id.

| # | Decision | Why |
|---|---|---|
| D-01 | Treat this as a stabilization/migration project on an existing production system, not a rebuild | Confirmed working logic exists (match detection, Teams success posts) — rebuilding would waste it and risk regressing it |
| D-02 | Group live fixes into batched office-laptop sessions (P2/P3/P4) rather than ad-hoc single fixes | Admin/edit access requires physical office presence; batching minimizes trips and keeps each live-change window short and pre-reviewed |
| D-03 | Master-list Excel templates must be cleared/reset **in place** every semester, never replaced or re-uploaded as a new file | Flows reference SharePoint drive-item IDs and Office Script IDs bound to the specific file object; replacing the file breaks every flow that touches it — this is the confirmed root cause of "process ID reading Excel doesn't work" |
| D-04 | Scope stays Power Platform low-code by default; small custom code only where it clearly outperforms the low-code option | User confirmed openness to it, but CDO staff must be able to maintain this after handover — minimize new infrastructure |
| D-05 | No secret-guard hook / `.env.example` for this project | No API keys exist to leak — all auth is Microsoft Power Platform OAuth connections; config facts (site URL, item IDs) are documented as reference in `guides/env_setup.md`, not treated as secrets |
| D-06 | Replace the deprecated "When a file is created in a folder (deprecated)" trigger in the 2 flows that use it | Microsoft has been actively retiring this trigger; it's a strong, confirmed candidate for missed/flaky runs reported as "sharefolder issues" |
| D-07 | Track the 14 flow `.zip` exports in git going forward, replacing informal zip-copies as the versioning/rollback mechanism | No Power Platform dev/test environment exists; the zips were the only backup. Git gives real diff history and rollback without needing a new environment |
| D-08 | Test every fix in a personal-account sandbox (baseline / fixed / prod packages) before the office laptop | No dev/test tier exists; the first attempt to act on a static-analysis claim showed it was wrong for 12 of 14 flows, so fixes must be proven by running them |
| D-09 | Drive the sandbox through the Power Automate API with scripted scenarios (`tools/sandbox/pw.py`), guarded by a PreToolUse hook | UI clicking cost ~77 browser steps per flow with repeated failures; the API also yields per-iteration run data, replacing manual inbox checks |
| D-10 | Roll fixes out in waves with a forced-failure probe; class R flows (real students/deletes/approvals) are proven by their first genuine run | No test environment; some flows cannot be test-run without acting on real people or data; the probe proves the alert path without side effects |

---

## 8. Open Questions

Unresolved. Anything marked `ASSUMED:` is a working assumption, not a confirmed fact — it may be wrong, and it must be confirmed before anything load-bearing is built on it.

1. **Exact semester rollover deadline date** — confirmed to exist, exact date not yet given. Needed to sequence P2–P6 against a real calendar.
2. `ASSUMED:` **`UTPCSDCDO Success Submit Email`** (the one flow without a `[LIVE-CDO]` prefix) is a currently-published/live flow, same as the other 12. Confirm in Power Automate Studio — if it's actually a draft or deprecated, Module M1's confirmation-email path may be running differently than this PRD assumes.
3. ~~`ASSUMED:` The exported package `[LIVE-CDO] UTPCSDCDO Email for Student Report Duty Status.zip` is correctly named~~ **Resolved 2026-10-02:** it is not. The file is a re-export of "Add Host Company into MasterList" (same flow id `a66117f3…`, identical definition). The real "Email for Student Report Duty Status" flow was never exported; 13 distinct flows are in `flows/`, not 14. It needs a fresh export before it can be reviewed.
4. ~~`ASSUMED:` The "Standard approvals" step inside the Acknowledgement Letter Email Process flow is still an intentional, actively-used step.~~ **Resolved 2026-09-16** — confirmed via the original 2023–2024 admin guide (`refdocs/context-2023-2024-admin-user-guide.pdf`): it's a deliberate two-stage approval gate, not a leftover. See `refdocs/guides/previous_system_guide_notes.md`.
5. `ASSUMED:` No Power Platform dev/test environment tier exists in the UTP tenant at all (not even an unused one). If one does exist, P2/P3 could be tested there before touching the live flows, changing the "batched office-laptop session" approach in D-02.
6. **Who exactly holds the shared-mailbox decision** for Module M6 (does CDO already have `cdo@utp.edu.my` or similar, or does one need to be requested from IT)?

---

## 9. Glossary

| Term | Meaning |
|---|---|
| **CDO** | Career Development Office (UTP) — owns this internship program |
| **HC** | Host Company — the organization a student interns at |
| **Master list** | The Excel-based cross-semester record of known host companies / HC supervisors, used to detect new vs. already-known entries each semester |
| **Report duty** | The process by which a student confirms/logs that they've reported for duty at their internship placement |
| **Rollover** | The end-of-semester process: clear current data, reset templates, seed the next batch |
| **Office Script** | A TypeScript/JS script that runs against an Excel Online workbook via the `Run script` Power Automate action — this is the "backend js" referenced in the original brief |
| **Drive-item ID** | SharePoint's internal, stable identifier for a specific file object — breaks if the file is deleted/replaced, even if a new file has the identical name and path |
