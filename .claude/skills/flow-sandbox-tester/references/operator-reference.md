# Operator reference — Power Automate sandbox

## Browser

Use the Playwright MCP browser. Its profile persists between sessions, so the user's Microsoft login usually survives; if a sign-in page appears, hand over to the user. Microsoft 365 pages are heavy SPAs: prefer `browser_snapshot` (accessibility tree) over screenshots to confirm state, and wait for text rather than fixed delays.

Useful deep links (replace `{env}` with the environment id from the URL after first load):

| Page | URL |
|---|---|
| My flows | `https://make.powerautomate.com/environments/{env}/flows` |
| Import package (legacy) | `https://make.powerautomate.com/environments/{env}/flows/import` |
| Connections | `https://make.powerautomate.com/environments/{env}/connections` |
| A flow's run history | `https://make.powerautomate.com/environments/{env}/flows/{flowId}/runs` |
| Sandbox list | `{sandbox site URL}/Lists/{list name}/AllItems.aspx` |

Selectors change often; inspect the snapshot before relying on any.

## Import gotchas

- The file input on the import page is hidden behind an Upload button — use `browser_file_upload` after clicking it. The zip path must be absolute.
- Each connection row starts as "Select during import". Click it, choose the user's existing connection or *+ Create new*, then Save. Import stays disabled until every row is resolved.
- After import the flow may be **off**. Leave it off until the designer check (step 4 of the workflow) is done.
- If import fails with a schema/validation error, copy the error text into the issue doc — it means `tools/flowpkg.py` produced something Power Automate rejects; fix the builder, don't hand-edit in the designer (the next build would lose the edit).
- A SharePoint trigger polls every minute; allow up to ~2 minutes after adding a list item before concluding nothing ran.

## Reading a run

In run history, open the run and expand the failed action. Record: run status, failed action name, the error `code`/`message`. For a Try/Catch fix, also confirm the Catch scope ran and the Terminate step set the run to Failed. The Teams alert arrives as a 1:1 chat from "Power Automate" / Flow bot.

## Evidence policy

Default 2–3 screenshots per flow, saved under `refdocs/issues/evidence/flow-NN/` (only screenshots of sandbox pages with fake data):

1. `01-baseline-failure.png` — baseline run history showing the silent failure.
2. `02-fixed-alert.png` — the Teams alert from the fixed package.
3. `03-fixed-run-history.png` — fixed run marked Failed with the clear error.

Never keep screenshots of sign-in pages, connection dialogs showing account tokens, real CDO lists, or real run history. If one was taken by accident, delete that file and say so.

## Safety checks before turning a sandbox flow on

- Designer shows the sandbox site URL on the trigger and every SharePoint action.
- No Outlook action has a hard-coded recipient other than the user (fields sourced from sandbox list items are fine — the user controls those).
- Teams recipient comes from the sandbox config list (TeamsNotification1/2 = the user's own address).
