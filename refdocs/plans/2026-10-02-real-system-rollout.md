# Plan — Apply the sandbox-tested fixes to the real system, and prove them there

> Replaces the superseded P2 plan (`2026-09-16-observability-and-error-handling.md`). Companion execution doc: [`../execution/2026-10-02-real-system-rollout.md`](../execution/2026-10-02-real-system-rollout.md). Covers P2 + P3 of the PRD roadmap in one rollout, done at the office laptop (CLAUDE.md hard constraint), not P4 (ownership migration).

## 1. Why this exists

Twelve flows have a fix that passes in the sandbox (`refdocs/updates/FLOW-TRACKER.md`). A sandbox pass proves the *design*; nothing has run in the real system, and the real system is the only place the Excel reads/writes, the Office Scripts, the real triggers and the real Teams recipients can be tested. The user wants to apply the fixes to the real system and test them there. There is no dev/test tier (D-07), so the rollout itself has to be built so that a mistake is small, visible and reversible.

## 2. What's already covered (don't rebuild)

- **Fix packages:** `python tools/office_pack.py` → `build/office/flowNN-prod.zip` (the tested fix against production IDs) and `flowNN-probe.zip` (the same plus a first step that always fails), with hashes and each flow's office steps in `refdocs/updates/OFFICE-CHECKLIST.md`.
- **Forced-failure test without side effects:** the probe package. Its mechanism was proven in the sandbox on flows 9 and 10 (the probe failed first, the real send never ran, both alerts posted, run marked Failed).
- **"Is what's live what we tested?":** `python tools/compare_prod.py NN` compares the post-apply re-export in `flows/` with the tested package.
- **Rollback:** the backup `.zip` committed to git before every change (D-07).
- **Sandbox evidence per flow** (what was observed, what was stubbed): the issue docs and `refdocs/updates/ISSUES-BY-FLOW.md`.

## 3. Scope

**In:** applying and proving the fixes for flows **1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14**; flow **2's** trigger swap last (its guard was re-tested in the sandbox 2026-10-02); recording every result.

**Out, with reasons:**
- **Flow 11:** blocked; its export is a duplicate of flow 4. Resumes when the real export arrives (MANUAL-TODO C).
- **P4 ownership migration** (moving connections off Kamal's account): a separate session; doing it in the same visit would make a failed test impossible to attribute.
- **Issue 2** (hard-coded Excel/script ids, D-03) and **duplicate-handling** (flows 3, 4, 5, 10, 14): need CDO decisions first; the fixes here do not change either.
- **PowerApp changes:** the app is not in this repo and no fix needs it. The flows' trigger schemas are unchanged, so the app keeps working.

## 4. Approach

**One flow at a time, in waves from lowest to highest consequence.** The next flow starts only after the current one's evidence is in (CLAUDE.md: observed, not assumed).

**Per flow, the same sequence:** backup → apply the **probe** package → run once → confirm the run fails at the probe and the Teams alert arrives, with no data touched → apply the **prod** package → real success-path test → re-export and `compare_prod` → record.

**The success-path test depends on what a success run does** (this is the honest part: some flows can't be test-run without acting on real people):

| Class | What a success run does | Flows | Success-path proof |
|---|---|---|---|
| **S: safe** | Harmless or only affects a staff address | 9, 1 | Run it on purpose with a staff address / one test submission |
| **W: writes that can be undone** | Creates files or rows we can remove, staff-only emails | 3, 4, 7, 12, 13, 14 | Run on one clearly-labelled test input, then clean up |
| **R: acts on real people or deletes data** | Emails real students, deletes a whole list or table, sends approvals | 5, 10, 8, 6, 2 | Probe test only now. The **first genuine operational run is the success-path test**, with staff watching the run history and a backup taken first |

For class R the fix adds no new side effect on success (the same actions run inside a Try scope; sandbox runs of the same packages passed on real SharePoint/Outlook/Teams), so the residual risk is small, but it is *not yet observed in production*, and the docs say so until the first genuine run is read.

**Stop rule:** anything unexpected (a probe run that sends or writes something, an alert that doesn't arrive, a success run that behaves differently, `compare_prod` differences nobody can explain) → restore the backup, mark the flow ⛔ Blocked in STATUS.md naming the exact finding, and do not continue to the next flow.

**Apply method:** Import → **Update** with the tested package, selecting the existing production connections. It keeps the flow's id, so the PowerApp keeps calling it. Fallback if Import behaves unexpectedly: make the same edits by hand from the flow's "Office steps" in its issue doc.

## 5. Risks & unknowns

| Risk / unknown | Confidence | Mitigation |
|---|---|---|
| Import → Update on a real flow has not been tried (connection re-selection; whether anything else resets) | Medium: it is the standard path, untested here | Pilot on flow 9 (smallest blast radius); by-hand fallback |
| Excel/Office Script/folder behaviour inside the new Try scope | Medium: the actions are unchanged, only wrapped; never run outside production | Class W tests with one-file / one-row inputs; read the run |
| A probe applied to a flow with a **real trigger** (flows 1 and 14) fails any real event that arrives during the probe window | High (by design) | Do these in quiet hours, keep the window to minutes, re-run any missed item |
| Test data left behind in real lists/templates/folders | Medium | Every test row/file is labelled `ZZ TEST` and tracked in the cleanup list in the execution doc; templates are cleared **in place** (D-03), never replaced |
| Teams alerts reach nobody (recipients come from the shared config item, row id 1) | Unknown | Verified on the pilot by someone actually receiving the alert; also closes the open "alert wording" manual item |
| `compare_prod.py` has never run on a real export | Medium | First use is on the pilot; unexplained differences are reported, not waved through |
| **How the PowerApp reacts to a flow that now ends Failed** (the fix marks failed runs Failed; before, they looked successful to the caller). Never observed; the app is not readable from the personal account (viewer-only, Edit/Export greyed out) | Unknown | Observe it on the pilot: press the app's button with the probe applied and note what the user sees. Ask for the app export (MANUAL-TODO C) |
| Rollover date unknown (PRD Open Question #1) | Unknown | Sequence so the class W/S waves land first; class R proofs wait for the real operations |
| Flow 2's subfolder guard as a live trigger condition | Re-tested in the sandbox 2026-10-02 (works); the rest of flow 2 is still untested | Flow 2 goes last, with staff aware |
| Flow 7's concurrency change (parallel Excel writes → one at a time) unproven | Medium | Record the old typical run duration first; compare |

## 6. Definition of done

Per flow (all observable): the backup zip is committed; the probe run in production shows **Failed** at the Probe step with the Teams alert received; the prod package is applied; `compare_prod` says IDENTICAL; a success-path run (test or first genuine run) shows **Succeeded** with the expected side effects and the normal COMPLETED alerts; the changelog entry names the run and its result.

Overall: flows 1, 3–10, 12, 13, 14 applied (2 if its guard re-test passed), none left half-applied, every class R flow either proven by its first genuine run or explicitly listed as "awaiting first real run" in STATUS.md, flow 11 and P4 listed as next.
