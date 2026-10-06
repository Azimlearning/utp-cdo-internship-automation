# Flow 5: Bulk Email To Start Registration

> Sandbox workflow (D-08). Fix module: `tools/fixes/f05_bulk_email_start_registration.py`, using the shared `tools/fixes/trycatch.py` (generalised from flows 3/4/14).

## Status

🔶 **Sandbox-tested; one check left for you (Teams alert wording, and the batch emails in your inbox).** 2026-09-30.

Safety: this flow emails real students. **Every sandbox recipient was redirected to your own address** (To, Cc and every BCC entry) and no production address exists in the sandbox packages (the builder refuses if one remains).

## What it does

PowerApp button → RUNNING ×2 → reads a logo image → reads the guideline attachments (list item **282**), other attachment files and link files from the CDO library → reads all students → adds each student's email to a batch; whenever the batch reaches "max recipients per email" (config item) it sends one BCC email, and after the last student it sends the leftover batch → COMPLETED ×2; FAILED ×2 hangs off the last COMPLETED post.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 5.1 | **A failed run reports "Succeeded"**. Sandbox baseline, failing send: the loop failed, COMPLETED was skipped, the generic FAILED messages fired, and the run header said "Your flow ran successfully" | **Observed** | ✅ Try/Catch + Terminate |
| 5.2 | **No rollback on a mid-batch failure:** batches already sent stay sent, and a re-click resends to the same students | Read (design) | 🔶 the alert now says which step failed; deduping needs a CDO decision |
| 5.3 | The FAILED message says only "…process is FAILED" | Read | ✅ step + error + run link |
| 5.4 | FAILED also fires if only the COMPLETED message fails | Read | ✅ |
| 5.5 | The guideline attachment is fetched by a **hard-coded list item ID (282)** from a hard-coded list; delete or recreate that item and the flow breaks | Read | ⬜ note for the admin guide / issue 2 |
| 5.6 | Emails send from a personal mailbox (`shared_office365` under Kamal's account) | Read | ⬜ P4 |
| 5.7 | The logo file is read before the first alert-worthy step; a missing logo stopped the flow with no alert | Read | ✅ logo read moved inside Try |

## Test results

| Case | Package | Result |
|---|---|---|
| (first attempt) | baseline | invalid: my logo stub broke the first variable (harness bug, not a flow bug). Re-imported both copies with a corrected stub |
| ok (3 students, max 2 per email) | baseline | Succeeded (emails sent to your inbox) |
| sendfail (bad address) | baseline | Apply-to-each failed; **run header "ran successfully"**; generic FAILED posts sent. Evidence `evidence/flow-05/01-…` |
| ok | fixed | Succeeded |
| sendfail | fixed | Try failed → **Catch ✓ (4 actions)** → **Terminate ✓** → **"Flow run failed"**; COMPLETED skipped. Evidence `evidence/flow-05/02-…` |

**Not confirmed:** Teams alert wording. ~~How many emails arrived for `ok`~~: answered by the 2026-10-02 re-run below (exactly 2: one batch, one leftover).

### Re-test 2026-10-02 (shared wrapper change)

The shared Try/Catch wrapper now also checks Conditions directly inside a loop, so the alert names the real failing step (`Send_an_email_(V2)`, previously `Condition`). Flow 5 is one of the three flows that change picked up, so its fixed copy was rebuilt, re-imported and re-run with the scenario runner (`python tools/sandbox/pw.py run 05 <scenario> fixed`). Counts are per loop iteration, read from the run:

| Scenario | Package | Run status | Failed actions | Counts | Matches expectation | Result file |
|---|---|---|---|---|---|---|
| ok | fixed | **Succeeded** | — | Send_an_email_(V2) Succeeded=1, Skipped=2; Send_an_email_(V2)_2 Succeeded=1, Skipped=2 | ✅ | `results/ok-fixed.json` |
| sendfail | fixed | **Failed** | Send_an_email_(V2): The 'inputs.parameters' of workflow operation 'Send_an_email_(V2)' of type 'Open | Send_an_email_(V2) Failed=1, Skipped=2; Send_an_email_(V2)_2 Skipped=3 | ✅ | `results/sendfail-fixed.json` | **Not tested:** the attachment/link scopes and the real logo read (stubbed in the sandbox), and the real Student List.

## Office steps

1. Back up flow 5 into `flows/` and commit.
2. Build the fix on the real flow: move the logo read into the Try scope (init `imageStr` empty at top level, fill it inside Try with Set variable), wrap logo + three attachment scopes + `Get items` + `Apply to each` in `Try - Send bulk emails`, then Catch/Terminate as in flow 3. Or import `build/prod/flow05-prod.zip` with **Update**.
3. **Test only with the CC/BCC list temporarily set to your own address**, never to the live student list, before the real send.
