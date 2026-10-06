---
name: flow-sandbox-tester
description: Import, run and verify CDO Power Automate flow packages in the user's personal sandbox using the logged-in Playwright browser and the scripted runner (tools/sandbox/pw.py), then record the result in the flow's issue doc. Use when testing a baseline or fixed flow package from build/, reproducing a suspected failure, checking a fix works, re-testing after a change to tools/fixes/trycatch.py, or documenting a sandbox test for the office-laptop handoff.
---

# Flow sandbox tester

Sandbox workflow (D-08, `refdocs/guides/sandbox_runbook.md`). Since 2026-10-02 the browser is driven by generated scripts, not
click-by-click: `tools/sandbox/pw.py` writes a script into `tmp/pw/`, and you run it with
`browser_run_code_unsafe(filename=<path it printed>)`. One call imports a package, or runs a whole test scenario.

## Operating rules

- **Sandbox only.** Never open, edit, switch, import over or run a real `[LIVE-CDO]` flow; never touch the `CareerDevelopmentOfficeCDO` site. Enforced twice: `lib.js` refuses non-`[SANDBOX-*]` flows and non-OneDrive SharePoint calls, and the `.claude/hooks/sandbox_guard.py` PreToolUse hook blocks browser steps that name production or upload a non-sandbox package.
- **Only packages from `build/baseline|fixed|harness`.** Never `flows/*.zip` or `build/prod/*.zip`.
- **Every email in a sandbox copy goes to the user's own address** (the fix module's `sandboxify()` redirects To/CC). Check this in the built definition before the first import of any email-sending flow.
- **The user logs in; Claude never sees credentials.** The runner reads the Power Automate bearer token off the page's own requests and keeps it only in memory (`page.__flowAuth`); it is never printed, saved or sent anywhere but `api.flow.microsoft.com`.
- **Fake data only.** Seeds live in the fix module's `SCENARIOS` (made-up students, `@sandbox.test` addresses).
- **Baseline before fix**, and a result is only a result when the run was read: the runner records run status, failed actions, per-iteration counts and the Terminate message from the run itself.
- **Everything ends Off.** `cmd_run` switches the copy off in a `finally`; after any error run `pw.py alloff` and check `stillOn` is empty.

## Workflow (per flow)

```bash
python tools/build.py NN baseline && python tools/build.py NN fixed     # sandbox packages
python tools/sandbox/pw.py load            # once per browser session, and after editing lib.js / commands.js
python tools/sandbox/pw.py import NN baseline ; python tools/sandbox/pw.py import NN fixed   # also `fixedprobe` (build.py NN fixedprobe) to test the probe mechanism
python tools/sandbox/pw.py run NN <scenario> baseline|fixed [--noshot]
#   -> browser_run_code_unsafe(filename=tmp/pw/run_NN_<scenario>_<pkg>.js)
#   -> browser_evaluate(function="() => window.__pwResult", filename=<results path it printed>)   # save the JSON
python tools/sandbox/pw.py report NN       # markdown table for the issue doc
```
Then: write the issue doc, edit `refdocs/updates/flows.json`, run `python tools/docs.py` (regenerates the tracker and
issues-by-flow, then checks links/evidence), add a CHANGELOG entry. Before an office visit: `python tools/office_pack.py`.

Scenarios go in the fix module: `SCENARIOS = {name: {clear, seed, trigger, count, countLists, expect: {baseline|fixed: {status, failedAction, counts, after}}}}`. Sandbox-only failure switches (e.g. `trigger: 'badaddr'`) are wired in `sandboxify()` so the prod build never contains them; check with a grep of `build/prod`.

## Traps already hit (don't relearn them)

| Trap | What happens | Handled by |
|---|---|---|
| Polling trigger watermark | A SharePoint "item created" trigger's first check after switching on only records a starting point; an item created before that check never fires (run TIMEOUT) | `cmd_run` waits for the first trigger-history entry before creating the trigger item |
| Token expiry | The page's token may be near expiry when captured → 401 | `api()` re-captures and retries once |
| SharePoint cookie expiry | `page.request` to SharePoint → 401 after a while on the PA page | `sp()` visits the site (SSO renew) and retries once |
| `$top` limit | Flow listing rejects `$top` > 50 | `listFlows` pages via `nextLink` |
| Connection rows reorder | Import screen lists connectors in a different order per package | `cmd_import` picks rows by text, checks Import is enabled |
| File chooser | Clicking Upload inside a script hangs on the chooser | `setInputFiles` on the iframe's `input[type=file]` |
| "…" menu moves | Turn on/off sits in an overflow menu whose position depends on flow state | not used any more: on/off via the API (`/start`, `/stop`), then state re-read |
| MCP path check | `filename` must start with lowercase `c:\` | `pw.py` prints paths that way |
| Scripts can't write files | No `fs`/`require`/`fetch` in the script sandbox | results via `window.__pwResult` + `browser_evaluate(filename=)`; HTTP via `page.request` |
| `result()` on nested scopes | Allowed on a Condition one loop deep; **rejected (InvalidTemplate) when that Condition contains further loops** (flow 7) | `trycatch._has_loop` skips those; the import error text is surfaced by `cmd_import` |
| Required `Title` | Sandbox lists may require Title | `spAdd` always sets `Title: 'sandbox'` |
| Every tool call echoes its script | ~13 KB library per call | `pw.py load` once; commands are ~1.5 KB and refuse a stale library (version hash) |

## Completion gate

A flow's sandbox test is complete when: the baseline failure case was reproduced (or shown not to reproduce), every fixed
scenario passed `expect` with its result JSON saved under `refdocs/issues/evidence/flow-NN/results/`, the issue doc and
`flows.json` are updated and `tools/docs.py` checks pass, and `pw.py alloff` shows nothing on. A sandbox pass proves the fix
*design*; production is fixed only after the office-laptop step and a read of the real run history.
