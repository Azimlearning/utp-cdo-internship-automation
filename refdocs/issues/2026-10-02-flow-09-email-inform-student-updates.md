# Flow 9: Email To Inform Student Updates

> Sandbox workflow (D-08). Fix module: `tools/fixes/f09_email_inform_student_updates.py`, using the shared `tools/fixes/trycatch.py`.

## Status

🔶 **Sandbox-tested; one check left for you (Teams alert wording).** 2026-10-02. The only sandbox changes are the trigger (a list-item trigger replaces the PowerApp button) and the five PowerApp text fields, which are fixed test values; the recipient is always your own address. The Outlook send and the Teams messages are real.

## What it does

PowerApp button with five text fields (to, name, message, cc, subject) → RUNNING ×2 → sends an email to the student → Teams message to the student → COMPLETED ×2; FAILED ×2 hangs off the COMPLETED posts.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 9.1 | **A failed email reports "Succeeded".** A malformed address fails the send step (`emailMessage/To` must be of type string/email), the COMPLETED posts are skipped, the generic FAILED posts fire, and the header reads "Your flow ran successfully" | **Observed** | ✅ Try/Catch + Terminate |
| 9.2 | The address typed into the PowerApp field is not validated by the flow, so a typo is the realistic trigger for 9.1 | Observed (same mechanism) | ➖ PowerApp-side validation is a suggestion (see MANUAL-TODO B) |
| 9.3 | FAILED message has no step, error or link | Read | ✅ names `Send_an_email_(V2)` and the error |
| 9.4 | The Teams message to the student is sent only if the email succeeded, so a failed email leaves the student with nothing and staff with a vague alert | Read | ➖ acceptable; the alert now says what to resend |

## Test results (sandbox)

| Case | Package | Result |
|---|---|---|
| badaddr (`not-an-email`) | baseline | `Send_an_email_(V2)` failed, run **Succeeded**, generic FAILED posts sent. Evidence `evidence/flow-09/01-…` |
| badaddr | fixed | Try failed on `Send_an_email_(V2)` → Catch → Terminate → run **Failed**, banner names the action and error. Evidence `evidence/flow-09/02-…` |
| ok | baseline | run **Succeeded** (email to your inbox) |
| ok | fixed | run **Succeeded** (email to your inbox) |

**Not confirmed:** Teams alert wording. The send results were read from the run data afterwards (2026-10-02): `Send_an_email_(V2)` **Succeeded** in both ok runs and **Failed** in both bad-address runs, so exactly 2 emails went out.

## Office steps

1. Back up flow 9 into `flows/` and commit.
2. Wrap `Send an email (V2)` + `Post message in a chat or channel 2` in `Try - Email student`; Catch/Terminate as in flow 3. Or import `build/prod/flow09-prod.zip` with **Update**.
3. Test once with a PowerApp email addressed to a staff member's own mailbox.
