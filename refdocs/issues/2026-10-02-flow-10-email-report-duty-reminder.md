# Flow 10: Email for Report Duty Reminder

> Sandbox workflow (D-08). Fix module: `tools/fixes/f10_email_report_duty_reminder.py`, using the shared `tools/fixes/trycatch.py`.

## Status

🔶 **Sandbox-tested; one check left for you (Teams alert wording).** 2026-10-02. Sandbox changes: list-item trigger instead of the PowerApp button, and **every reminder is redirected to your own address** (subject tagged `[SANDBOX reminder for <student address>]`). Outlook sends, both SharePoint reads and the Teams posts are real. A student whose address has no `@` keeps that address, so its send fails for real.

## What it does

PowerApp button → RUNNING ×2 → reads the Student List and the Report Duty Registration list → for every student whose email is **not** in the registration list, sends a "please fill in the Report Duty form" email (CC the PIC) and counts it → COMPLETED ×2; FAILED ×2 hangs off the COMPLETED posts.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 10.1 | **A failed send reports "Succeeded".** One student with a malformed address failed the send inside the loop; the loop failed, COMPLETED was skipped, generic FAILED posts fired, header read "Your flow ran successfully" | **Observed** | ✅ Try/Catch + Terminate |
| 10.2 | One bad address does not stop the loop: the other students are still emailed, so a failed run is a **partly sent** batch with no list of who was missed | **Observed** (run data: 2 sent + 1 failed in one run) | 🔶 the alert now names the failing action and error; it still does not list the students not reached |
| 10.3 | A student who appears twice on the Student List gets two reminders (the condition only checks the *registered* emails, sent emails are not tracked) | **Observed** (run data: both B and its duplicate D were emailed) | ⬜ duplicate policy decision (MANUAL-TODO B) |
| 10.4 | Re-clicking the button re-emails everyone still unregistered; no "already reminded" memory | Read | ➖ by design; note for the admin guide |
| 10.5 | Teams summary: "No. of Student Completed" is the number of **registration rows** (duplicates and non-students included); "NOT Completed" is the number of reminders sent | Read | ➖ wording only |
| 10.6 | FAILED message has no step, error or link | Read | ✅ |

## Test data (sandbox)

Student List: A (registered), B (pending), C (address `not-an-email`), D (duplicate of B). Registration list: A.

## Test results (sandbox)

| Case | Package | Result |
|---|---|---|
| A, B, C, D | baseline | `Apply to each` failed, run **Succeeded**; generic FAILED posts sent. Evidence `evidence/flow-10/01-…`, `01b-…`, `01c-…` |
| A, B, C | fixed | Try failed in the loop → Catch → Terminate → run **Failed**. Evidence `evidence/flow-10/02-…` |
| A, B | fixed | run **Succeeded** |

**Not confirmed:** the Teams alert wording.

### Re-run with the scenario runner (2026-10-02, `python tools/sandbox/pw.py run 10 <scenario> <package>`)

Counts are per loop iteration, read from the run itself (no inbox counting needed). The fixed copy now includes the shared wrapper's nested-condition check, so the alert names `Send_an_email_(V2)` instead of `Condition`; `readfail` proves the Catch still alerts when the failure happens before the loop ever ran (the check then points at a Condition that never executed).

| Scenario | Package | Run status | Failed actions | Counts | Matches expectation | Result file |
|---|---|---|---|---|---|---|
| badaddr | baseline | **Succeeded** | Send_an_email_(V2) | Send_an_email_(V2) Succeeded=2, Failed=1, Skipped=1 | ✅ | `results/badaddr-baseline.json` |
| badaddr | fixed | **Failed** | Send_an_email_(V2) | Send_an_email_(V2) Succeeded=2, Failed=1, Skipped=1 | ✅ | `results/badaddr-fixed.json` |
| ok | fixed | **Succeeded** | — | Send_an_email_(V2) Succeeded=1, Skipped=1 | ✅ | `results/ok-fixed.json` |
| readfail | fixed | **Failed** | Get_items | Send_an_email_(V2)  | ✅ | `results/readfail-fixed.json` |

## Office steps

1. Back up flow 10 into `flows/` and commit.
2. Wrap `Get items`, `Get items 2`, `Apply to each 3` and `Apply to each` in `Try - Send reminders`; Catch/Terminate as in flow 3. Or import `build/prod/flow10-prod.zip` with **Update**.
3. Test with the Student List pointed at a **copy** containing only staff addresses.
