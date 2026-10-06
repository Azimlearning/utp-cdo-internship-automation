# Flow 1 — UTP/CSD/CDO Success Submit Email

> Per-flow review under the sandbox workflow (D-08). Package: `flows/UTPCSDCDO Success Submit Email.zip`. Fix module: `tools/fixes/f01_success_submit_email.py`. Tiers: `../guides/methodology.md` (T1 = read in the JSON, T2 = Microsoft docs, T3 = hypothesis until a run confirms it).

## Status

🔶 **Sandbox set up. Baseline imported. Fixed import blocked on a Teams re-sign-in.** (2026-09-30)

- Sandbox lists were created in the user's OneDrive site via SharePoint REST: `CDO Sandbox - Control Template` (item 1 → user's address) and `CDO Sandbox - Report Duty Registration` (`field_2`, `field_5`).
- `[SANDBOX-BASELINE]` imported successfully as *Create as new*, with the user's SharePoint and Outlook connections.
- `[SANDBOX-FIXED]` import failed with `DynamicOperationRequestClientFailure … API 'teams' operation 'GetUnifiedActionSchema' … 'Unauthorized'`. The cause was the user's **expired Teams connection** (Connections page showed *Reconnect*), not the package. It gets re-imported after the reconnect.
- **Finding 1.7 (observed, T1):** Power Automate connections expire and then fail with `Unauthorized` until someone re-signs in. The 12 flows' existing Teams alerts depend on the owner's Teams connection, so an expired one silences success *and* failure alerts together. This matters for the ownership migration (P4) and the admin guide: check Connections for *Reconnect* before each semester.

## What the flow does

Every minute it polls the student registration list (`287cbf2d-…` on the CDO site). For each new item, it sends the student a "Successful SIIP Report Duty Form Recorded" email to `field_5` (email), addressed to `field_2` (name), from the mailbox of the connection owner (currently Kamal).

```
When an item is created ──► Send an email (V2)  ──[only if TimedOut]──► Compose body ──► SharePoint "SendEmail" API (From: kamalazreel…)
```

## Findings

| # | Finding | Tier | Impact |
|---|---|---|---|
| 1.1 | If the Outlook send **fails** (a bad or blank address, an expired connection, a mailbox problem), nothing else runs. The backup path only runs on `TimedOut`, never on `Failed`. There's no Teams connector in the flow at all, so nobody is told. | T1 | The student never gets a confirmation and staff never find out. This fits the brief's "email have to manual" (T3 until reproduced, see T1 below). |
| 1.2 | The backup path uses SharePoint's `SP.Utilities.Utility.SendEmail` API, which Microsoft **retired on 31 Oct 2025** ([Microsoft Support](https://support.microsoft.com/en-us/office/retirement-of-the-sharepoint-sendemail-api-b35bbab1-7d09-455f-8737-c2de63fe0821), [MC921752](https://mc.merill.net/message/MC921752)). | T1 + T2 | The backup is dead code even when it does run. |
| 1.3 | The backup hard-codes `From: kamalazreel.k@utp.edu.my`, and builds its JSON body with single quotes around the name, so a name with an apostrophe (e.g. *Nur'Aina*) would break it. | T1 | Moot once 1.2 is fixed by removing the path, but it's another hard-coded dependency on the departing account. |
| 1.4 | The flow's `flowFailureAlertSubscribed` is `false`. | T1 (meaning T3) | This probably means Power Automate's own "your flow failed" digest email is off for the owner too, which would make this flow silent on every channel. |
| 1.5 | The subject says "…for *<current month>* Semester", using the UTC month at send time. | T1 | Cosmetic. **Noted, not changed.** |
| 1.6 | It's the only export without a `[LIVE-CDO]` prefix, so whether it's switched on in production is unconfirmed (existing `ASSUMED:`). | — | The sandbox can't answer this. Someone with access to the real flow list must check. |

## Fix (in the `fixed` / `prod` packages)

```
When an item is created
  └─ Try – Send confirmation email (Scope)
        └─ Send an email (V2)                                  ← unchanged
  └─ Catch – Alert CDO staff (Scope, runs if Try Failed/TimedOut)
        ├─ Get item: Control Template, ID 1                    ← same config item every other flow uses
        └─ Post failure alert to Teams (Flow bot → TeamsNotification1)
              Flow name, time (MYT), "student confirmation email FAILED", student name,
              email, list item ID, the error text, and a link to the run
  └─ Terminate – Mark run as failed (after Catch, whatever Catch's outcome)
```

- The dead backup (Compose + SendEmail API) is **removed**. That also removes the hard-coded Kamal address in finding 1.3.
- **No Teams success message is added.** This flow fires once per student registration, and a success ping per student would drown out the alerts that matter. The earlier plan (execution doc Task 2a) proposed one; this is a deliberate change from it.
- The run ends as **Failed** with code `ConfirmationEmailFailed`, so run history shows it honestly even when the alert was delivered.
- Not in scope here: changing the sending mailbox from Kamal to a shared one (issue 5 / P4).

## Sandbox test cases

| # | Package | Input (a new item in the sandbox `Report Duty Registration` list) | Expected |
|---|---|---|---|
| T1 | baseline | name `Test Student A`, email `not-an-email` | Run **Failed** at *Send an email (V2)*. Compose/HTTP **skipped**. No alert anywhere. *(Proves finding 1.1.)* |
| T2 | fixed | name `Test Student B`, email = your address | Email arrives. Run Succeeded. Catch and Terminate skipped. No Teams message. |
| T3 | fixed | name `Test Student C`, email `not-an-email` | A Teams Flow-bot alert with name, email, item ID, error and run link. Run **Failed** with `ConfirmationEmailFailed`. |
| T4 | fixed | name `Test Student D`, email blank | Same as T3. |
| T5 | fixed | name `Nur'Aina Test`, email = your address | Email arrives with the apostrophe intact. |
| T6 | fixed | Clear `TeamsNotification1` in the sandbox Control Template, then repeat T3 | The alert fails (no recipient), but the run is still **Failed** via Terminate. Documents the known limit: no recipient means no alert. Restore the field afterwards. |

## Office steps (after sandbox pass)

**Option A, by hand in the designer** (about 10 minutes, easy to audit):

1. Export a backup into `flows/` and commit (rule 5).
2. Add a **Scope** at the top named `Try - Send confirmation email`, and drag *Send an email (V2)* into it.
3. Delete *Compose - EmailBody* and *Send an HTTP request to SharePoint*.
4. Add a **Scope** after Try named `Catch - Alert CDO staff`. Under ⋯ → *Configure run after*, tick only **has failed** and **has timed out**.
5. Inside Catch, add SharePoint **Get item** (CDO site, list *Control Template*, Id `1`), then Teams **Post message in a chat or channel** (Post as *Flow bot*, Post in *Chat with Flow bot*, Recipient = dynamic `TeamsNotification1`). Copy the message text from `ALERT_HTML` in `tools/fixes/f01_success_submit_email.py`.
6. After Catch, add **Terminate** (Status *Failed*, Code `ConfirmationEmailFailed`). Under *Configure run after*, tick **is successful**, **has failed** and **has timed out**.
7. Save. Check the next real registration's run in run history.

**Option B, import:** `python tools/build.py 1 prod` → Import → *Update* on the existing flow → select the production connections (Teams is new to this flow).

## Sandbox test results — 2026-09-30

**Result:** The baseline **reproduced the silent failure** (T1). The fixed package **passed 5 of 6 cases with run history read** (T2, T3, T4, T6 confirmed in run history; T5 the run succeeded, but the email content is unchecked, see below). The Teams message *arriving in the chat* (rather than the Teams action succeeding) is **not yet visually confirmed**.

| Package | Built from | Imported as | Flow id |
|---|---|---|---|
| baseline | `flows/UTPCSDCDO Success Submit Email.zip`, retargeted to sandbox | `[SANDBOX-BASELINE] …` | `aa9c9a63-…` |
| fixed | same + `tools/fixes/f01_success_submit_email.py` | `[SANDBOX-FIXED] …` | `a56d61bd-…` |

| # | Case | Package | Input | Expected | Observed | Pass? |
|---|---|---|---|---|---|---|
| T1 | bad email | baseline | `Test Student A`, `not-an-email` | Run fails at Send; nothing else tells anyone | Run **Failed**: `Send_an_email_(V2)` → `OpenApiOperationParameterTypeConversionFailed … 'emailMessage/To' … "not-an-email" … 'string/email'`. Compose and the SharePoint backup were **skipped**. No alert anywhere. Trigger-to-failure ≈ 1 min | ✅ Finding 1.1 confirmed |
| T2 | good email | fixed | `Test Student B`, own address | Succeeds; Catch/Terminate skipped | Run **Succeeded**. Try ran 2 s, Catch and Terminate skipped | ✅ (arrival of the email itself not checked) |
| T3 | bad email | fixed | `Test Student C`, `not-an-email` | Catch alerts; run marked Failed | Try **Failed** (same error as T1) → Catch **Succeeded** (`Get item` ✓, `Post failure alert to Teams` ✓) → run **Failed** | ✅ (Teams chat not viewed) |
| T4 | blank email | fixed | `Test Student D`, no email | Same as T3 | Try **Failed**: `BadRequest - To Field cannot be null or empty` → Catch **Succeeded** (`Get item` ✓ 0.4 s, Teams ✓ 2 s) → Terminate ran → run **Failed** | ✅ (Teams chat not viewed) |
| T5 | apostrophe | fixed | `Nur'Aina Test`, own address | Email arrives with the name intact | Run **Succeeded** | ⚠️ run only. **User to confirm the email body reads "Dear Nur'Aina Test"** |
| T6 | no recipient | fixed | `TeamsNotification1` blank, bad email | Alert can't be delivered; run still Failed | Catch **Failed** (`Post failure alert to Teams`), `Get item` ✓. Run **Failed**. Config restored afterwards | ✅ Known limit documented. Terminate's own status not individually inspected |

**Evidence** (`evidence/flow-01/`): `01-baseline-silent-failure.png` (T1: Send failed, backup steps skipped), `02-fixed-try-catch-alert.png` (T4: Try failed → Catch ✓ → Teams ✓), `03-fixed-no-recipient-limit.png` (T6). All sandbox pages with fake data only.

**New findings from the test:**
- **1.8 (T1, observed):** The bad-address failure produced a **different error for a blank address than for a malformed one** (`BadRequest - To Field cannot be null or empty` vs `OpenApiOperationParameterTypeConversionFailed`). The alert reports whichever comes back, so both are covered. Its `coalesce(...)` error expression was exercised only via the Teams action succeeding, so **the exact text posted in Teams still needs a look** (see below).
- **1.9:** Power Automate's imported flow shows **Created Sep 18, 2025** (carried from the export), which is cosmetic and safe to ignore.
- The tenant's **Copilot is off** and the site-creation button is disabled. Nothing in the fix depends on either.

**User confirmation (phone screenshots, 2026-09-30 ~02:08):**
- ✅ **T2 and T5 emails arrived.** Subject "Successful SIIP Report Duty Form Recorded for September Semester"; "Dear Test Student B," and "Dear Nur'Aina Test," (apostrophe intact).
- ✅ **T3 and T4 alerts arrived in Teams** (chat "Workflows"): flow name, MYT time, "The student confirmation email is FAILED!", student, email, list item ID, error text, "Open this run" link.
- ❌→🔧 **Defect found in the T4 alert:** the blank-email case posted the connector's **raw JSON** (`Error: {"error":{"code":400,"message":"Bad Request - To Field cannot be null or empty","source":"default-84187be3-…","path":"choose[7]\\when[1]",…}}`). Cause: for a blank address `result().error.message` is null, so the expression fell through to `string(outputs.body)`. **Fixed** in `f01_success_submit_email.py` by reading `outputs.body.error.message` before the raw fallback. Re-imported as a new `[SANDBOX-FIXED]` copy (`3fd211eb-…`, the earlier copy `a56d61bd-…` is Off and can be deleted) and re-ran **T4b** (blank) and **T3b** (malformed): both runs Failed with Catch executed. **User: please check the two newest alerts in Teams — the blank-email one should now read just "Bad Request - To Field cannot be null or empty"**, with no JSON.
- Teams sender is named **"Workflows"** (the Flow bot), so the docs' "Flow bot" wording means that chat.

**Status:** 🔶 **Sandbox-verified pending one look at the two newest Teams alerts.** Then office-ready (option A by hand, or B import of `build/prod/flow01-prod.zip`, rebuilt with the fixed expression).

**Sandbox state:** both `[SANDBOX-*]` flows Off, config item restored to your address, list holds 8 fake items.
