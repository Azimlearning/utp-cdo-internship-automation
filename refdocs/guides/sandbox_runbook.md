# Sandbox Runbook — testing flow fixes on the personal account

> Why this exists: D-08 in `../changelog/DECISIONS.md`. Nothing in this project had ever been *run* — every finding came from reading exports. The sandbox is where a finding gets reproduced and a fix gets proven, without touching production. Browser-driven version of steps 3–6: `.claude/skills/flow-sandbox-tester`.

**The one rule:** a sandbox flow must never be able to read or write production data, or message anyone but you. Everything below exists to guarantee that.

---

## 0. The workflow in one picture

```
flows/<export>.zip ──tools/build.py──► build/baseline/flowNN-baseline.zip ─┐
                          │                                                ├─► import as NEW into your account → run test cases → record results
                          ├──────────► build/fixed/flowNN-fixed.zip ───────┘
                          └──────────► build/prod/flowNN-prod.zip ──► office laptop only (Import → Update), after a fresh backup
```

- **baseline** = today's logic, pointed at sandbox data. Run the failure case here first: it proves the problem is real.
- **fixed** = the same, plus the fix. Run every test case: it proves the fix works.
- **prod** = the fix, pointed at production. Never import it into the sandbox.

## 1. One-time: create the sandbox SharePoint site

> **Result 2026-09-30:** UTP blocks self-service site creation (SharePoint → Build → *Site* is disabled). The sandbox uses option 2, the user's OneDrive site `https://utpmy-my.sharepoint.com/personal/fakhrul_22012087_utp_edu_my`. The lists were created there via SharePoint REST from the logged-in Playwright browser (`/_api/web/lists`, then `fields/CreateFieldAsXml` with `Options: 8` so internal names stay exact). The SharePoint connector accepted the OneDrive URL on import.
>
> **Also:** check *Connections* for **Reconnect** before importing. An expired connection makes import fail with `Unauthorized`.

Try in this order (the first your tenant allows wins):

1. **A private Microsoft 365 group / Team site:** SharePoint start page → *+ Create site* → *Team site* → name `CDO Sandbox – <your name>`, Privacy **Private**, add no members. The URL looks like `https://utpmy.sharepoint.com/sites/CDOSandbox-<name>`.
2. **Fallback, your OneDrive's site:** `https://utpmy-my.sharepoint.com/personal/<your_upn_with_underscores>`. Microsoft Lists → *+ New list* → Save to: *My lists*. The SharePoint connector accepts this URL as a custom site address (Tier 3: expected to work, to be confirmed on first use).

Write the site URL into `tools/sandbox.json` (step 2).

## 2. One-time: create the sandbox lists, then fill `tools/sandbox.json`

Copy `tools/sandbox.example.json` → `tools/sandbox.json`. Each key is a production identifier found in the flow exports, and each value is your sandbox equivalent. `tools/build.py` refuses to build until every placeholder that a flow actually uses is filled in.

| Sandbox list | Columns (create with **exactly** these names; the flows address columns by internal name, which is fixed at creation) | Used by | Replaces production ID |
|---|---|---|---|
| `Control Template` | `TeamsNotification1`, `TeamsNotification2` (single line of text). Add **one item** and put your own UTP email in both. It must be item ID 1 | Every flow with a Teams alert | `be7f2b53-cc4e-42b1-a043-a7d6a849ba42` |
| `Report Duty Registration` | `field_2` (student name), `field_5` (student email), single line of text | Flow 1 | `287cbf2d-74fc-44ee-8bca-f26719b1feb3` |
| *(flows 2–3 add their own rows here when they're reached)* | | | |

To get a list's GUID: open the list → ⚙ → *List settings* → the URL ends in `List=%7B<GUID>%7D`. The GUID is the part between `%7B` and `%7D`.

Also map `kamalazreel.k@utp.edu.my` → your own address, because some flows hard-code it as a sender.

## 3. Build

```bash
python tools/build.py 1 baseline
python tools/build.py 1 fixed
```

If it prints `Refusing to build sandbox package — production identifiers remain`, the listed IDs need a sandbox mapping in `tools/sandbox.json`. **That refusal is the safety net working. Don't work around it.**

## 4. Import and run (scripted, D-09)

Normal path: `tools/sandbox/pw.py` (details and traps in `.claude/skills/flow-sandbox-tester/SKILL.md`).

```bash
python tools/sandbox/pw.py load                          # once per browser session
python tools/sandbox/pw.py import NN baseline|fixed      # import as new; connections = yours; left Off
python tools/sandbox/pw.py run NN <scenario> <package>   # seed, trigger, wait, read run, switch Off, check expectation
python tools/sandbox/pw.py report NN                     # results table for the issue doc
python tools/sandbox/pw.py alloff                        # after any error: everything Off, verified
```
Each prints a script path to run with `browser_run_code_unsafe(filename=…)`.

Manual fallback (if the API or import page changes):
1. make.powerautomate.com → check the environment picker (top right) is your default UTP environment.
2. *My flows* → *Import* → *Import Package (Legacy)* → upload `build/baseline/flowNN-baseline.zip`.
3. Flow row → Setup must say **Create as new**. If it says *Update*, stop: the wrong package was picked.
4. Each connection row → *Select during import* → your own connection (or *+ Create new*) → Save. Rows come in a different order per package.
5. Import. The flow shows up as `[SANDBOX-BASELINE] …`. Turn on/off sits under the "…" overflow menu on the flow's page.

## 5. Check before turning a sandbox flow on

Open the flow in the designer and confirm:

- [ ] The trigger and every SharePoint action show the **sandbox** site URL.
- [ ] Every Outlook recipient is either sourced from a sandbox list item (which you control) or is your own address.
- [ ] The Teams recipient comes from the sandbox `Control Template` item.

Then turn it on, run the test cases from the flow's issue doc, and **turn it off afterwards.**

### 5b. Trigger harnesses (when a flow can't run end to end in the sandbox)

Some flows depend on things a sandbox can't reproduce (Office Scripts bound to production Excel files, Word templates, Teams approvals). For those, `python tools/build.py NN harness` builds a **small flow that copies only the parts being changed**, e.g. flow 2's trigger plus the three actions that consume its outputs, and runs them on the sandbox library `Documents/CDO-Sandbox/{Drop File,Archive}` (created via REST, folders only). It needs a `harness` section in `tools/sandbox.json`:

```json
"harness": { "library": "<GUID of the sandbox Documents library>", "root": "/Documents/CDO-Sandbox" }
```

Rules: a harness proves the **changed part**; it says nothing about the rest of the flow, which stays untested until the office run. Say so in the issue doc.

## 6. Record

Each test case's result goes in the flow's issue doc (`refdocs/issues/2026-09-30-flow-NN-*.md`, template in the skill's `references/test-report-template.md`) and in the STATUS.md verification ledger. Pass or fail, both count: a baseline that *doesn't* reproduce a suspected failure kills a hypothesis, which is just as useful.

## 7. Office-laptop handoff

When a flow's fixed package passes: STATUS.md marks it *sandbox-verified, ready for office*. At the office laptop: export a fresh backup into `flows/` and commit it (rule 5), then either apply the fix by hand following the issue doc's "Office steps", or import `build/prod/flowNN-prod.zip` with **Update** on the existing flow and re-select the production connections. Re-run the sandbox test cases that are safe to run against production, and read the run history.

## Data rules

- Only made-up students go in sandbox lists (e.g. `Test Student A`, with your own address as the email).
- Don't open real CDO lists or real run history through Playwright. They contain student PII, which must stay inside the tenant. Look at those yourself and relay the error text.
- Delete a sandbox flow when its issue is closed. Imported copies still carry the original logic, so don't leave stray ones switched on.
