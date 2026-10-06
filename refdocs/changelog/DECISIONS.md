# Architectural Decisions — UTP CDO Internship Automation

> Record decisions here so they aren't re-debated in future sessions.
> Format: **Decision** → **Why** → **Trade-offs / what was rejected**.
> Canonical one-line list lives in `refdocs/cdo-internship-automation-PRD.md` §7; this file expands the load-bearing ones under the same id.

An ADR is worth writing when the decision (a) is expensive to reverse, (b) will look arbitrary to a future reader, or (c) had a real alternative someone will propose again. Everything else is just a commit message.

---

### D-01 — Stabilization/migration, not a rebuild

**Decision:** Treat this project as stabilizing and migrating an existing production system, not redesigning it.

**Why:** Reading all 14 flow exports directly confirmed that new-vs-partial-match company/supervisor detection and Teams success notifications — both explicitly requested in the brief — are already implemented correctly. The brief's framing ("system only for student to fill in") suggested more was broken than actually is.

**Trade-offs / rejected:** A ground-up rebuild was considered (see `sources.md` "Considered and rejected") and rejected — it would throw away working logic and contradicts the deadline pressure of the next semester rollover.

---

### D-02 — Batch live changes into office-laptop sessions

**Decision:** Group all live flow edits into as few, well-prepared sessions as possible (P2, P3, P4), each executed at the physical office admin laptop.

**Why:** Confirmed via user: admin/edit access to the live Power Automate environment and SharePoint site requires the office admin laptop; the personal account used for analysis is read/test-only. Ad-hoc single-flow trips would multiply office visits and increase the risk of an unreviewed change going live.

**Trade-offs / rejected:** This slows iteration compared to fixing things one at a time as discovered — accepted deliberately, because the alternative (frequent office trips, or risky edits made in a rush) is worse.

---

### D-03 — Excel master-list templates are cleared in place, never replaced

**Decision:** The semester-rollover procedure for master-list Excel templates must clear/reset rows within the *same* file object — never delete-and-reupload, "Save As" a new file, or otherwise create a new file to replace the old one.

**Why:** Confirmed by direct inspection (Tier 1 — see `guides/methodology.md`) of the Host Company Info MasterList Checking flow: its `Run_script` (Office Script) and `Get_file_content_using_path` actions reference the template by a hard-coded SharePoint drive-item ID (`01QW2RL4GFFAT2NQYTXFEZ45YLOE4VKNIH`) and a hard-coded Office Script ID bound to that same file object. Office Scripts are bound to the file's internal identity, not its filename or path (Tier 2 — Microsoft's own docs) — a same-named replacement file gets a new drive-item ID and silently breaks every flow referencing the old one. **This mechanism is the most concrete, evidence-backed explanation for the brief's "process ID reading Excel doesn't work" — it is a Tier 3 causal hypothesis, not yet confirmed against an actual failed run's error message.** A second, independent candidate cause (an Excel formatting mismatch) is tracked as issue 2b in `guides/issues_backlog.md`; the two need to be told apart before committing to a fix, ideally via the affected flows' run history rather than guessing.

**Trade-offs / rejected:** The alternative — fixing every flow to resolve the file by path at runtime instead of a fixed ID — is the actual long-term fix and is scheduled as P3. D-03 is the interim/permanent operating rule regardless of whether P3 ships, because "always edit in place" is good practice even after the path-based lookup exists.

---

### D-04 — Stay low-code by default; small custom code only where it clearly wins

**Decision:** Default to Power Platform-native fixes (flow actions, Office Scripts). Introduce a small piece of custom code (e.g., one Azure Function) only where it measurably outperforms the low-code option for a specific, named problem.

**Why:** User confirmed openness to custom code when asked directly, but the deciding constraint is who maintains this system after the current owner's internship ends — CDO staff, who operate Power Automate/SharePoint/Excel day to day and would not be able to maintain a custom Azure Function.

**Trade-offs / rejected:** Pure "never write custom code" was rejected as too rigid — if company-name fuzzy-matching (Module M2) ever needs real fuzzy-matching logic beyond what Power Automate expressions can do cleanly, a small function is preferable to a fragile 40-step flow.

---

### D-05 — No secret-guard hook, no `.env.example`

**Decision:** Skip the standard `newproject` secret-guard hook and `.env.example` scaffolding for this project.

**Why:** This project holds no API keys or client secrets in any file — every integration (SharePoint, Excel Online, Outlook, Teams, Word Online) authenticates via Microsoft's own OAuth connections, configured inside Power Automate Studio, never stored in this repo. The hook exists to catch a key pasted into source; there is no such class of file here.

**Trade-offs / rejected:** If a future fix under D-04 introduces a real custom-code component with its own API key, this decision should be revisited and the hook added at that point — not before.

---

### D-06 — Replace the deprecated SharePoint "file created" trigger

**Decision:** Replace "When a file is created in a folder (deprecated)" in the Acknowledgement Letter Email Process and Store Student List into SharePoint List flows with a supported trigger.

**Why:** Confirmed by direct inspection — both flows use this trigger, and Microsoft has been actively retiring it. It is a strong, evidence-backed candidate for the reported flakiness around the student share folder and letter drop folder.

**Trade-offs / rejected:** The exact replacement (a different SharePoint trigger vs. re-architecting to trigger off the SharePoint list item that's already created downstream) is not yet decided — that's P3 design work, tracked as a gap in `STATUS.md`.

---

### D-07 — Git-track the flow exports; they replace the zip-copy safety net

**Decision:** From this project forward, the 14 flow `.zip` exports live in `flows/` under git version control. Before any live edit, export a fresh `.zip` backup into this folder and commit it.

**Why:** User confirmed there is no separate Power Platform dev/test environment — the exported zips were the *only* existing rollback mechanism, and they weren't being versioned or diffed, just accumulated. Git gives real history, diffs (once extracted for inspection), and an unambiguous "last known good" state.

**Trade-offs / rejected:** Extracting every flow's JSON into the repo for diffability was considered and deferred (not rejected outright) — see `sources.md` "Considered and rejected" and the `.gitignore` note on `flows/*/`. Kept simple for now: track the canonical re-importable `.zip`, extract to scratch on demand.

---

### D-08 — Test every fix in a personal-account sandbox before the office laptop

**Decision:** Fixes are developed and tested in a sandbox on the user's personal Power Automate account before they touch production. The workflow (agreed with the user 2026-09-30):

1. Claude edits the exported flow definition via `tools/build.py` + a per-flow fix module in `tools/fixes/`, producing three packages: **baseline** (sandbox copy, logic unchanged — reproduces today's behaviour), **fixed** (sandbox copy with the fix), **prod** (the fix against production IDs, for the office laptop only).
2. The user imports baseline and fixed as **new** flows into their own account, against a sandbox SharePoint site with fake data, with Teams/email going only to themselves. Claude may drive the browser via Playwright once the user has logged in themselves (skill: `.claude/skills/flow-sandbox-tester`).
3. At the office admin laptop: fresh backup export first (rule 5), then apply the verified fix by hand (small edits) or Import → **Update** with the prod package (larger edits).

**Why:** Every claim in this project so far came from reading exports, never from running a flow — and the first real attempt to act on one showed why that matters: the issue-1 claim "no flow has a failure branch" turned out to be false for 12 of 14 flows (see CHANGELOG 2026-09-30). There is no dev/test tier (D-07), so a sandbox the user controls is the only place a fix can be proven without risking production. It also cuts office-laptop time to applying already-proven changes.

**Guardrails (mechanism, not preference):**
- Sandbox packages are built with `suggestedCreationType: New` so the import screen can't default to overwriting a real flow.
- `tools/flowpkg.py` refuses to build a sandbox package if any production site URL, list/file ID, or the departing owner's address remains after retargeting.
- Sandbox flows stay off except while a test runs. Only fake student data goes into sandbox lists. Real run history and real lists (student PII) are not opened through Playwright — the user reads them and relays.

**Trade-offs / rejected:** Amends D-02/CLAUDE.md rule 6 (personal account was "read/test/analyze-only"): the personal account may now *create and run sandbox copies*, but still never edits a production flow. Rejected: (a) co-owner access to the real flows as the test bed — it's production; (b) importing copies unmodified — they'd still point at the real CDO lists, Excel files and Teams config, and SharePoint-triggered copies would fire on real student submissions. Limitation accepted: a sandbox pass proves the fix *design*; the production flow is fixed only once the office step is done and observed.

### D-09 — Drive the sandbox through the Power Automate API, with scripted scenarios

**Decision:** Sandbox testing (D-08) is run by `tools/sandbox/pw.py`, not by clicking through the UI. It generates Playwright scripts that (a) import packages through the import page, (b) switch flows on/off, list flows and read runs, actions and per-iteration results through `api.flow.microsoft.com`, using the bearer token the signed-in page already sends, held in memory only, and (c) seed SharePoint sandbox lists over REST. Each flow declares its test cases as `SCENARIOS` in its fix module; results are saved as JSON under `refdocs/issues/evidence/flow-NN/results/`. Approved by the user 2026-10-02, including the token handling.

**Why:** Flow 10 took 92 tool calls, 77 of them UI steps and 5 of those failures (moving "…" menu, reordered connection rows, file chooser, guessed waits). The same flow re-tested with the runner took one call per scenario. Run data also replaces manual inbox counting: per-iteration results showed flow 10's duplicate reminders and partial batch directly, which the UI never showed.

**Guardrails:** `lib.js` refuses to act on any flow not named `[SANDBOX-*]` and any SharePoint site other than the sandbox OneDrive; `.claude/hooks/sandbox_guard.py` (PreToolUse on the Playwright tools) blocks browser steps naming the production site or a `[LIVE-CDO]` flow, and uploads of non-sandbox packages. The token never leaves the browser process except to `api.flow.microsoft.com`.

**Trade-offs / rejected:** Uses an undocumented-for-this-purpose but stable Power Automate management API (`api-version=2016-11-01`); if it changes, fall back to the UI steps in `sandbox_runbook.md` §4. Rejected: the PowerShell `Microsoft.PowerApps` cmdlets (a second sign-in and module install, no package import), and staying with UI clicking (slow, flaky). Related tooling decided in the same session: `refdocs/updates/flows.json` + `tools/docs.py` generate the tracker/issue tables; `tools/office_pack.py` builds the office checklist and packages.

### D-10 — Roll the fixes out in waves with a probe, and let the first genuine run prove the destructive flows

**Decision:** The sandbox-tested fixes are applied to the real system one flow at a time in waves (safest first), each with the same procedure: backup → Update with a **probe** package (the fix plus a first step in the Try scope that always fails) → run it once and confirm the run is Failed at the probe and the alert arrives → Update with the clean **prod** package → success-path test → re-export and `tools/compare_prod.py`. The success-path test depends on class: safe flows (9, 1) and undoable writes (3, 4, 7, 12, 13, 14) are tested on labelled fake data (`testdata/`, `tools/testdata.py`); flows that email real students, delete whole lists or send approvals (5, 10, 8, 6, 2) get the probe test only, and their **first genuine operational run is the success-path test**, with staff watching and a backup first. Any surprise → restore the backup and stop. Details: `refdocs/plans/2026-10-02-real-system-rollout.md` and its execution doc.

**Why:** There is no test environment (D-07), so the real system is the only place the Excel/Office Script/real-trigger parts can be proven, and some flows cannot be test-run without acting on real people. The probe gives a forced-failure proof with no side effects (mechanism proven in the sandbox on flows 9 and 10; on all 12 probe packages nothing with side effects sits outside the Try scope). `compare_prod.py` turns "is what is live what we tested?" into a check.

**Trade-offs / rejected:** Class R flows are not success-tested before the first real run, so STATUS.md must say "awaiting first real run" until it is read; the residual risk is small because success runs of the same packages passed in the sandbox on real SharePoint/Outlook/Teams, but it is not zero. Rejected: (a) applying all 12 fixes in one sitting (a failure could not be attributed); (b) testing mass-email/delete flows against the real lists "just once" (it acts on real people or data); (c) editing flows by hand as the default (slower, unrepeatable, and not the artifact that was tested). A probe applied to a flow with a real trigger fails any real event in that window; the doc makes that explicit and puts those flows in quiet hours.

---

## Working assumptions (`ASSUMED:`)

Not decisions — guesses made to keep moving. Each one must be confirmed or killed before anything load-bearing is built on it. Canonical list: PRD §8. When one is resolved, delete it here and write a real ADR above.

- `ASSUMED:` `UTPCSDCDO Success Submit Email` (no `[LIVE-CDO]` prefix, unlike the other 13) is currently published/live.
- `ASSUMED:` No Power Platform dev/test environment tier exists anywhere in the UTP tenant.

**Resolved:** ~~The `Email for Student Report Duty Status.zip` export is correctly named~~: it is not (2026-10-02): same flow id `a66117f3…` and byte-identical definition as "Add Host Company into MasterList", so it is a re-export of flow 4 and the real status flow was never exported. Only 13 distinct flows are in `flows/`.

**Resolved:** ~~The "Standard approvals" step in the Acknowledgement Letter Email Process flow is still an intentional, actively-used step~~ — confirmed via `refdocs/context-2023-2024-admin-user-guide.pdf` (the original admin guide, pages 25–29): it's a deliberate two-stage human approval gate (raw-file check, then cleaned-file check) via Teams approval cards, not a leftover. Full detail: `refdocs/guides/previous_system_guide_notes.md`.
