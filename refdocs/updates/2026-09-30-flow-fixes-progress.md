# CDO Internship Automation: Flow Fixes Progress

**Date:** 30 September 2026  **Scope of this update:** flows 1–3 of 14, one at a time
**Production status:** no live flow has been changed yet.

---

## Summary

- **How we'll fix things safely:** every fix is now built as a copy of the flow and tested on my own Power Automate account, using fake data and alerts sent only to me. Only a fix that passes goes to the CDO admin laptop. There is no test environment, so this is how we avoid experimenting on the live system.
- **A correction to earlier findings:** earlier I reported that no flow tells staff when it fails. Checking again more carefully, **12 of the 14 flows do send a Teams "FAILED" message.** The real gaps are narrower, and they're listed flow by flow below. The earlier fix plan would have added duplicate alerts, so it has been withdrawn.
- **Flow 1 is ready for testing.** The fix is built and waiting for the sandbox test. Flows 2 and 3 are next, in order.

## Flow-by-flow

### Flow 1: Success Submit Email (student confirmation email)

**What it does:** after a student submits the Report Duty form, it emails them a confirmation.

**Problems found:**

1. If the email fails to send (a mistyped or blank student email, or an expired connection), **the flow stops and nobody is told.** It has no Teams alert at all.
2. Its only backup method uses a Microsoft email service that **was retired on 31 October 2025**, so the backup does nothing now.
3. That backup is also hard-coded to send from Kamal's address.

**Fix:** if the email fails, CDO staff get a Teams message naming the student, the email address, the reason it failed, and a link to the failed run. The retired backup is removed. The run is also marked "Failed" in the history, so it can't be mistaken for a success.

**Tested (in my private sandbox, fake data only):**

- **Today's version really does fail silently.** A registration with a bad email address made the flow fail at the send step, skip its backup, and tell nobody. This is now observed, not just read from the design.
- **The fixed version works as designed.** With a bad or blank email, it detects the failure, runs the alert step successfully, and marks the run Failed. With a good email it behaves as before, with no extra messages.
- **One known limit:** if the Teams recipient list entry is empty, the alert can't be delivered. The run is still marked Failed.
- **Still to confirm:** that the alert message reads correctly in Teams and that the confirmation emails arrive. Those two checks are with me, and then the fix is ready for the office (about 10 minutes there).

**A finding that affects every flow:** Power Automate connections expire and then fail until someone signs in again. All 14 live flows depend on Kamal's connections. If one expires, the flows stop working, including the FAILED alerts. This matters for the handover, and the admin guide should include "check Connections for *Reconnect* before each semester".

**Still to confirm:** this flow's name lacks the "[LIVE-CDO]" tag the others have. Someone should check it's actually switched on in production.

### Flow 2: Acknowledgement Letter Email Process (appointment letters to host companies)

**Status:** queued, not yet reviewed in detail. Known so far from the earlier survey:

- It starts from a file-drop trigger that **Microsoft has marked deprecated**. This is a likely cause of the unreliable letter-drop folder.
- It only works if the dropped Excel file matches an exact format. For example, some column headers need a trailing space, and the table must be named `Database`. A file that's slightly off can make it fail.
- It has two deliberate approval steps in Teams (the raw file check, then the cleaned file check). These stay as they are.

### Flow 3: Add HC Supervisor into MasterList

**Status:** queued. Known so far:

- It already sends a Teams FAILED alert, but the alert doesn't say *which* step failed or *why*.
- It reads the master-list Excel file through a fixed internal file ID. If that file is ever replaced rather than edited in place, the flow breaks. The operating rule "always clear master-list files in place, never re-upload them" protects against this.

## What's needed from CDO

1. **Confirmation** that I may create a private test SharePoint site under my UTP account for sandbox testing (fake data only, no student information).
2. **A check** of whether "Success Submit Email" is switched on in production.
3. **The semester rollover date**, so the fixes can be scheduled before it.

## Next update

After flow 1's sandbox test, with the before-and-after results, and after flow 2's review.
