# Execution — Apply the fixes to the real system and prove them

> **Companion plan:** [`../plans/2026-10-02-real-system-rollout.md`](../plans/2026-10-02-real-system-rollout.md). Written to be followed at the office admin laptop without Claude present. Each flow follows **Procedure P** below; a flow is done when its Verify steps pass, not when the import finishes. **Never start the next flow before the current one's evidence is in.**
> The per-flow Studio steps (if you ever apply by hand instead of importing) are in each flow's issue doc under "Office steps"; the packages, hashes and ready/not-ready status are in `refdocs/updates/OFFICE-CHECKLIST.md`; test inputs are in `testdata/README.md`.

## Before starting (once per visit)

- [ ] At the office admin laptop, signed in as the account that owns the flows (still `kamalazreel.k@utp.edu.my`'s connections, D-02). A staff member knows tests are running.
- [ ] Choose a quiet period: no students submitting the form, nobody using the PowerApp. Flows 1 and 14 have real triggers; the probe step (Procedure P3) makes any real event that arrives while it is applied fail.
- [ ] **Connections:** Power Automate → Connections shows no *Reconnect* for SharePoint, Outlook, Teams, Excel Online. An expired connection fails with `Unauthorized` and also silences the alerts.
- [ ] **Alerts have an audience:** read config item id 1 in the `Control Template` list (`TeamsNotification1`, `TeamsNotification2`). Those people will receive the FAILED alerts; make sure they are watching Teams during the test and tell you what they see.
- [ ] `build/office/` copied to the laptop; the hash of each file you use matches `refdocs/updates/OFFICE-CHECKLIST.md`. The repo (or at least `flows/`) is on the laptop with `git status` clean.
- [ ] **Capture "before" for every flow** you will touch: whether it is On, and a screenshot of its last runs (status and duration). Flow 7's typical duration matters (its fix runs rows one at a time).
- [ ] `testdata/` copied over; `python tools/testdata.py --staff-email <your address> --semester "<current semester as in the Control Template>"` run if flow 2 will be tested.
- [ ] Agree the stop rule with whoever is with you: **if anything unexpected happens, restore the backup and stop.**

## Procedure P (every flow, in this order)

| Step | Do | Verify (what must be true) |
|---|---|---|
| **P1 Backup** | Studio → the flow → Export → Package (.zip) into `flows/`, overwriting the repo copy. `git add flows/ && git commit`. Write down the commit hash. | `git log` shows the commit; the zip opens |
| **P2 Probe** | Import → Import Package (Legacy) → `flowNN-probe.zip`. Setup must say **Update** (not *Create as new*) on the real flow. Choose the existing production connections. Import. | Import reports success; the flow is still On; the flow checker shows no errors |
| **P3 Check the probe** | Open the flow: inside the `Try - …` scope the **first** step is `Probe - Force a failure (DELETE AFTER TEST)` and everything else in the scope waits for it. | You can see it |
| **P4 Run it once** | Start the flow normally (the PowerApp button, or the real trigger for flows 1 and 14). The probe fails before any real work, so this is safe on any flow (checked on every probe package: nothing outside the Try scope can send, write or delete; flow 14's archive step runs only after Try succeeds). A real file that triggers flow 14, or a real form submission that triggers flow 1, during this window just fails and has to be re-dropped / re-submitted. | Nothing real happened: no email sent, no row written, no file moved/deleted |
| **P5 Read the result** | Run history → the run | Status **Failed**; the failing step is the Probe; `Catch - Alert CDO staff` ✓; `Terminate` ✓; the **Teams alert arrived** for the people in the config item and says *Failed step*, *Error* and has an *Open this run* link. Screenshot it. |
| **P6 Apply the fix** | Import `flowNN-prod.zip` the same way (**Update**). | The Probe step is gone from the Try scope |
| **P7 Success-path test** | Per the table below. For **class R** flows this step is *not run now*: write "awaiting first real run" in STATUS.md and watch the first genuine run instead. | A **Succeeded** run, the expected side effects, the normal COMPLETED alerts |
| **P8 Re-export** | Export the flow again into `flows/` (overwrite). | — |
| **P9 Compare** | `python tools/compare_prod.py NN` (on the laptop if Python is there, otherwise at home before the next visit). | `IDENTICAL`. Any difference: report it, do not assume it is harmless |
| **P10 Record** | Commit; tick the row in OFFICE-CHECKLIST.md; STATUS.md ledger row; CHANGELOG entry naming the run and its result. | The entry says what was actually run, not "fixed" |

**Rollback / stop rule.** If P3–P7 shows anything unexpected: recover the backup with `git show <hash from P1>:"flows/<file>.zip" > rollback.zip`, Import → **Update** with it, confirm the flow is back to its old shape (re-export and `git diff --stat`), mark the flow ⛔ Blocked in STATUS.md with the exact finding, and **do not continue to the next flow**.

## Order, and each flow's success-path test (P7)

Class S = safe to test; W = writes that can be undone; R = acts on real people or deletes data (see the plan §4).

| Wave | Flow | Class | P7 success-path test | Cleanup / notes |
|---|---|---|---|---|
| **1 Pilot** | **9** Email To Inform Student Updates | S | Press "Inform Student" (or run it from the app) with **your own address** in the *To* field. Expect: the email arrives, the Teams message goes to that address, run **Succeeded**, COMPLETED alerts as before | None. This pilot also proves Import → Update, the alert audience and `compare_prod`. **At P4, press the real app button (not Test)** and write down exactly what the app shows when the probe makes the flow fail (an error message, nothing, a spinner that never ends): we have never seen how the PowerApp reacts to a flow that ends Failed |
| **2** | **1** Success Submit Email | S | Submit **one** test registration form with a staff address. Expect the confirmation email and a Succeeded run | Delete the test row from `Report Duty Registration`. Quiet hours only (real trigger) |
| **3 Probe-only** | **8** Delete Student List | R | *Not now.* First real "Delete All Student" at rollover | Before that first run: export the Student List to Excel |
| | **10** Report Duty Reminder | R | *Not now.* First real reminder run; read the Teams summary counts | Watch for the duplicate-student behaviour (10.3) |
| | **5** Bulk Email To Start Registration | R | *Not now.* First real start-of-registration send; expect 2 emails per batch size as observed | The hard-coded attachment item 282 is unchanged |
| | **6** Clear Raw Database | R | *Not now.* First real clear at rollover | Run flow 7 first so the raw data is saved |
| **4** | **3** Add HC Supervisor | W | `testdata/Rows_for_Flow3…`: paste the row into the real template's *SVExactlyNotMatched* table, run once. Expect one new item `ZZ TEST Added SV` | Delete the item and the table row. Run **once** only (re-run duplicates) |
| | **4** Add Host Company | W | Same with `Rows_for_Flow4…` and the *ExactlyNotMatched* table | Same |
| **5 Pipeline** | **7** Combine raw data | W | Run it for real (staff-only effects: new RawData files and a PIC email). Expect **Succeeded**, the files present, one PIC email; compare the duration with the "before" screenshot | This is normal operation, not test data. Note any "file locked" error |
| | **12** HC Supervisor check | W | Per `testdata/README.md`: the two `ZZ TEST` SharePoint items, `RawData_HCSupervisor_TEST.xlsx` as the **only** file in `MasterList_RawData_ToBeProcess`. Expect Matched 2 / Partially 1 / Exactly Not Matched 1, one PIC email | Delete the items; clear the template tables in place; return the other files |
| | **13** Host Company check | W | Same with `RawData_HostCompany_TEST.xlsx` | Same |
| **6** | **14** Store Student List | W | Drop `StudentList_TEST.xlsx` directly in `StudentList_DropFile`. Expect **one** run, six test students, the file archived, **no second run** | Delete students with Student ID `99…` and the archived file. Quiet hours (real trigger) |
| **7 Last** | **2** Acknowledgement Letter | W/R | With staff aware (its subfolder guard was re-tested in the sandbox 2026-10-02): `RawData_Acknowledgement_TEST.xlsx`; follow both approval cards; letters and emails go only to you | Needs its own mini-plan from `issues/2026-09-30-flow-02-…`; no probe package (trigger swap only) |
| — | **11** Student Report Duty Status | — | ⛔ Blocked until the real flow is exported (MANUAL-TODO C) | — |

## Cleanup list (tick as each test row/file is removed)

- [ ] Report Duty Registration: test row (flow 1)
- [ ] HC Supervisor list: `ZZ TEST Added SV`, `ZZ TEST Exact SV`, `ZZ TEST Partial SV` (flows 3, 12)
- [ ] Host Company list: `ZZ TEST Added Co`, `ZZ TEST Exact Co`, `ZZ TEST Partial Co` (flows 4, 13)
- [ ] Both templates' tables cleared **in place** (never replaced)
- [ ] `MasterList_RawData_ToBeProcess`: other files restored, test input removed
- [ ] Student List: students with Student ID `99…`; `Archive Student List`: the test file
- [ ] Every flow is back **On** (if it was On before) and no probe step remains (`compare_prod` IDENTICAL)

## Report back

After each flow, send (or note in the changelog): the probe run's status and the alert you received (screenshot), the P7 run's status and what it did, the `compare_prod` output, and anything that surprised you. Claude updates the issue doc, `flows.json` and STATUS from that. Flows 3–10 and 12–14's **Teams alert wording** is judged at P5; record whether it was clear.

## Wrap-up (end of the visit)

- [ ] Every flow touched is listed in the changelog with its own Verify result (probe run, success run or "awaiting first real run").
- [ ] STATUS.md: phase table and ledger updated; class R flows listed as "applied, awaiting first genuine run" until it happens.
- [ ] `guides/flow_inventory.md` updated if a flow's shape changed; remove "no failure-path alert" gaps only for flows whose probe run passed.
- [ ] Cleanup list complete; `git status` shows only intended changes; final commit.
- [ ] Next: flow 11 once exported; flow 2; P4 (ownership migration) as its own session.
