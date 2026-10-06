# UTP CDO Internship Automation — Claude Context

> Read this file at the start of every session, then run through `.claude/memory/preflight.md` — it's the six-question gate that turns these rules into something you actually did. A PowerApp + Power Automate + SharePoint/Excel system running UTP CDO's semester internship process — being stabilized and migrated off a departing staff member's account, not rebuilt.
> The PRD is the source of truth; this file is the short operating brief; preflight is the gate. Keep all three short.

---

## Order of authority (when docs conflict, surface it — don't resolve silently)

0. `refdocs/STATUS.md` — **where we are right now.** Phase checklist + the current module's progress. Check this first, every session.
1. `refdocs/cdo-internship-automation-PRD.md` — **what & why.** Owns scope, architecture, roadmap, Decision Log.
2. `refdocs/changelog/DECISIONS.md` — **settled calls.** Read before re-debating an architectural choice.
3. `refdocs/plans/*.md` — **what to build & why.**
4. `refdocs/execution/*.md` — **how & in what order.**
5. `refdocs/issues/*.md` — **the narrative per-issue home.** Analysis, review, and fix design for whichever backlog item is currently being worked — opened from `refdocs/guides/issues_backlog.md`, links out to its plan/execution pair rather than duplicating them.
6. `refdocs/guides/` — **operational reference.** `methodology.md` (the confidence-tier system every "confirmed" claim in this project should be read through — read this one first), `flow_inventory.md` (every flow's trigger/connectors/purpose — read before touching any flow), `env_setup.md` (site URLs, item IDs), `checklist.md` (pre-change checklist for live edits), `issues_backlog.md` (the full tracked issue list — pick one at a time).
7. `refdocs/cdo-internship-automation-sources.md` — **raw research** (external references, connected services).

If two docs disagree, stop and ask. Don't pick one and move on.

---

## Mandatory rules

### 1. Update the changelog after every session
After any session that changed a flow, made a decision, or modified a plan, add an entry to **`refdocs/changelog/CHANGELOG.md`** (format is in that file). Do not skip. Even a one-line fix gets a one-line entry.

### 2. Plan before you build
Before editing any live flow, a **plan doc** (`refdocs/plans/`) and an **execution doc** (`refdocs/execution/`) must exist. If they don't, create them first.

### 3. Log decisions as ADRs
New architectural/design decision → add an ADR to `refdocs/changelog/DECISIONS.md` (Decision → Why → Rejected/Trade-off). Mark unresolved assumptions `ASSUMED:` and surface them at the next checkpoint.

### 4. Keep docs current
If you deviate from a plan during execution, update the execution doc to match reality. Stale docs are worse than no docs.

### 5. Never edit a live flow without a fresh backup first
Export a `.zip` from Power Automate Studio into `flows/` *before* changing anything, every time. This repo's git history is the only rollback mechanism this project has (D-07) — there is no separate dev/test environment.

### 6. Live edits happen at the office admin laptop; fixes are proven in the sandbox first (D-08)
The personal account never edits a production flow. It *may* host **sandbox copies** built by `tools/build.py` (baseline + fixed), imported as new flows against a sandbox SharePoint site with fake data — that's where every fix is tested before it goes to the office laptop. Workflow and guardrails: `refdocs/guides/sandbox_runbook.md`; browser-driven testing: `.claude/skills/flow-sandbox-tester`. Flag sandbox-verified fixes as ready for the next office-laptop session in STATUS.md.

---

## The hard constraints (these are mechanism, not preference)

- **Physical access:** Live/admin changes (flow ownership, connections, publishing) require the office admin laptop. Personal-account sessions are for reading, analysis, and planning only.
- **Deadline:** Next semester rollover — exact date still unconfirmed (PRD Open Question #1). Sequence work to land the trigger/Excel-ID fixes *before* rollover.
- **No test environment:** No separate Power Platform dev/test tier exists. `flows/` in this repo is the real safety net now (D-07) — see rule 5 above.
- **Scope boundary:** Power Platform low-code by default (D-04). Small custom code only where it clearly outperforms the low-code option, and only if CDO staff can still maintain the system without it after handover.
- **Data sensitivity:** Student PII and host company data must stay inside the UTP Microsoft 365 tenant — no third-party services.
- **Ownership:** All 14 flows currently run under `kamalazreel.k@utp.edu.my`. This is total, not partial — every flow needs new connections when Module M6 executes.

---

## Stack

Power Apps (canvas app, not in this repo) → SharePoint Lists + Excel Online (Business) master-list templates, on the `CareerDevelopmentOfficeCDO` SharePoint team site → 14 Power Automate cloud flows (this repo's subject matter, exported as `.zip` in `flows/`) → Outlook / Microsoft Teams / Word Online for delivery and notifications. No custom code exists yet (D-04 permits it later, narrowly). No traditional build system — see "Running it" below.

## Surfaces

Single integrated system, but four component types that must be reasoned about together:

| Component | Where it lives | Changed by editing... | Shares source with |
|---|---|---|---|
| PowerApp | Power Platform environment (not exported here) | Power Apps Studio | Its manual-trigger calls are a contract with every `PowerAppV2`-triggered flow — a form field rename breaks the flow silently if the flow's schema isn't updated too |
| Power Automate flows (13) | `flows/*.zip` in this repo | Power Automate Studio, then re-exported into this repo | SharePoint Lists (read/write), Excel templates (Run Script), Outlook/Teams (send/post) |
| SharePoint Lists | `CareerDevelopmentOfficeCDO` site | SharePoint list settings, or via a flow | The PowerApp's data source *and* every flow's trigger/data source |
| Excel master-list templates | Same SharePoint site, document library | Office Scripts (via `Run script` flow actions) or direct Excel Online editing | Flows #2, #7, #12, #13 — see `guides/flow_inventory.md`. **Never replace these files; clear in place (D-03).** |

**A change to one of these routinely requires a matching change in another.** See preflight Q5 below — this is this project's actual invariant, not a hypothetical one.

## Running it

There is no build/test/deploy pipeline — this is a low-code Power Platform system plus its documentation. "Running" a flow means executing it in Power Automate Studio.

| What | Command | Notes |
|---|---|---|
| Inspect a flow's current exported definition | `python tools/show_flow.py NN` (or `--build fixed NN`) | Reads `flows/<name>.zip` directly, so no extracted copy is created. If you must unzip, do it in `tmp/` and delete it afterwards: `flows/` keeps only the `.zip` files |
| Build sandbox/prod packages | `python tools/build.py NN baseline\|fixed\|prod` | Output in `build/` (gitignored). Sandbox builds need `tools/sandbox.json` (from `sandbox.example.json`) and refuse if a production ID remains |
| Test a fix | `python tools/sandbox/pw.py import NN baseline\|fixed`, then `pw.py run NN <scenario> <pkg>`; run each printed script with `browser_run_code_unsafe(filename=…)` | D-08/D-09; skill `.claude/skills/flow-sandbox-tester`. Scenarios live in the fix module. Never import a `flows/*.zip` or `build/prod` package (a hook blocks it) |
| Update the tracking docs | Edit `refdocs/updates/flows.json`, then `python tools/docs.py` | Regenerates FLOW-TRACKER/ISSUES-BY-FLOW tables and checks links/evidence. MANUAL-TODO stays hand-written |
| Fake-data test workbooks | `python tools/testdata.py [--staff-email you@… --semester "Sep 2026"]` (`--check` verifies them against `flows/*.zip`) | `testdata/README.md` lists each file, its flow and the expected result. Mock templates are never for the real system (D-03) |
| Check what is live matches what was tested | `python tools/compare_prod.py NN` after re-exporting the flow into `flows/` | Probe packages: `python tools/build.py NN probe` (production forced-failure test, D-10) |
| Prepare an office visit | `python tools/office_pack.py` | `build/office/*.zip` + `refdocs/updates/OFFICE-CHECKLIST.md` (readiness, hashes, per-flow office steps) |
| Test-run a production flow | Open in Power Automate Studio → Test → check run history | Office admin laptop only — see hard constraints |
| Re-export after a live fix | Studio → Export → Package (.zip) → save into `flows/`, overwriting the old copy | Do this every time, immediately after any live edit (rule 5) |

---

## Build sequence

P0 (docs, done) → P1 (design the fixes, remote) → P2 (office-laptop: observability/error-handling) → P3 (office-laptop: deprecated trigger + Excel-ID root-cause fixes) → P4 (office-laptop: ownership migration) → P5 (rollover dry run + admin guideline) → P6 (live rollover). Full detail: `refdocs/cdo-internship-automation-PRD.md` §6.

**Never start the next office-laptop session's fixes until the current one's Definition of Done is fully observed, not assumed** — this system has no test environment, so an unverified "should be fine" carries directly into production.

---

## When blocked

- **Open question:** check the PRD's Open Questions section. If unresolved, write your assumption to `DECISIONS.md` as `ASSUMED:`, proceed, surface at the next checkpoint.
- **Doc conflict:** stop. Quote both passages and ask. Don't pick silently.
- **Ambiguous spec:** prefer the **option that's cheapest to reverse without another office visit** — if a choice can be tested/validated on the personal account before committing it at the office laptop, prefer that path. Log the choice.

---

*Companion brief to `refdocs/cdo-internship-automation-PRD.md`. Last updated: 2026-09-16.*
