# UTP CDO Internship Automation — Build Status

> **Read this first to know where we are.** Updated at the end of every session. Phases and scope come from `refdocs/cdo-internship-automation-PRD.md` §6. Don't reorder phases without updating this file and saying why (CLAUDE.md "keep docs current").

**Build philosophy:** This is an existing production system being stabilized and migrated, not built from scratch. Confirmed-working logic (match detection, Teams success notifications) is left alone; work targets confirmed gaps (no failure alerts, a deprecated trigger, hard-coded Excel file/script IDs, ownership on a departing account).

**Right now (2026-10-02):** **No live flow has been changed.** Fixes are built as packages by `tools/build.py`, tested in a sandbox on the personal account by the scripted runner `tools/sandbox/pw.py` (D-08/D-09), and only then applied at the office laptop. **Per-flow status lives in one generated place: `refdocs/updates/FLOW-TRACKER.md`** (source `refdocs/updates/flows.json`; index `refdocs/updates/README.md`). Office-visit packages and checklist: `python tools/office_pack.py` → `refdocs/updates/OFFICE-CHECKLIST.md`. What only the user can do: `refdocs/updates/MANUAL-TODO.md` (kept until all flows are done).

**Docs:** the admin runbook (M8) exists as a draft: `refdocs/guides/admin_runbook.md`; it is final only after the rollover dry run (P5).

**Next action:** apply the fixes to the real system at the office laptop, by waves, following `refdocs/execution/2026-10-02-real-system-rollout.md` (plan: `refdocs/plans/2026-10-02-real-system-rollout.md`, D-10). First visit (Phase A of the roadmap): flow 9 pilot, flow 1, collect the flow 11 export and PowerApp access. Test workbooks with fake data: `testdata/` (`tools/testdata.py`).

**Roadmap (2026-10-06):** `refdocs/plans/2026-10-06-next-phase-roadmap.md`: stabilize (rollout) → secure (ownership migration, rollover) → improve (robustness, PowerApp admin page, small new flows). The improvement phases P7–P9 depend on **D-11**, which needs the supervisor's confirmation.

**Where we are:** flows 1–10, 12, 13 and 14 are sandbox-tested; **flow 11 is blocked:** its export is a duplicate of flow 4 (same flow id, identical definition), so the real "Get Status" flow was never exported. It needs a fresh export (MANUAL-TODO C). Flow 2's trigger swap and subfolder guard are harness-tested (the guard re-tested live 2026-10-02: a direct file fires once, a subfolder file does not); its approvals/scripts/letters can only be tested at the office.

- **The one finding common to flows 3–10, 12, 13 and 14 (observed in each baseline run):** a failed run is reported **"Succeeded"** because the last step is a Teams FAILED message that itself succeeds. The shared fix (`tools/fixes/trycatch.py`: Try scope → Catch with step/error/run link → Terminate Failed) passes on each. It makes failures visible; it does not stop them or roll back partial work.
- **Other observed behaviour (decisions needed from CDO, listed in MANUAL-TODO B):** flows 3, 4, 5 write duplicates on rerun; flow 10 emails a student listed twice twice and leaves a half-sent batch when one address is bad; flow 14 creates duplicate students when files arrive together and leaves a failed file in the drop folder.
- **The check → add pipeline (observed in the definitions, X11):** flow 12 writes the *Exactly Not Matched* table that flow 3 reads, and flow 13 writes the one flow 4 reads, so a partial check run changes what the add flow imports. Flows 12 and 13 also process every file in the folder and email the PIC once per file (observed with a stubbed folder).
- **Not provable in the sandbox (stubbed; needs a real office run):** Excel reads/writes in flows 3, 4, 5, 6, 7 and 14 and Office Scripts in flows 3–7, 12, 13 and 14 (flows 12 and 13 **were** also run with real Excel reads/writes/attachment on 2026-10-02, only their scripts stay stubbed), flow 7's concurrency fix, flow 14's `{Identifier}` read, and everything in flow 2 beyond the trigger.
- **Wrapper detail learned on flows 7 and 10:** the alert names the real failing step only if a Condition inside a loop is checked, but Power Automate rejects `result()` on a Condition that contains further loops; `trycatch._has_loop` handles both. Flows 5 and 10 were re-tested after that change.
- ⚠️ **Issue 1 was wrong as stated.** 12 of 14 flows already had a Teams FAILED alert; the P2 plan/execution pair is **superseded; do not execute it**.

---

## Phase checklist

| Phase | Scope | Status |
|---|---|---|
| P0 — Docs & git baseline | Scaffold PRD/STATUS/sources/guides/changelog/plans/execution + `.claude/` config | ✅ Done — this session |
| P1 — Design the fixes (remote) | Spec error-handling pattern, path-based Excel lookup, trigger replacement | 🔶 Error handling and trigger replacement designed **and sandbox-tested** (flows 1–10, 12–14; flow 11 blocked on its export). Excel-id guard (issue 2) researched, not built (now roadmap item R7) |
| P2 — Office-laptop session 1: Observability | Add failure-path error handling + Teams alerts to all 14 flows | ⬜ Not started on the live system. Packages ready (`build/office/`); applied flow by flow in the rollout waves (D-10), not in one session |
| P3 — Office-laptop session 2: Root-cause fixes | Replace deprecated trigger (2 flows); fix hard-coded Excel ID fragility | ⬜ Not started on the live system. Trigger swap for flows 2 and 14 is part of their rollout waves; Excel-id fragility moved to roadmap item R7 |
| P4 — Office-laptop session 3: Ownership migration | Move all 14 flows off Kamal's account; shared mailbox for Outlook | ⬜ Not started — needs office admin laptop access + confirmation of new owner account |
| P5 — Semester rollover dry run + admin guideline | Controlled rollover test; write the admin runbook (M8) | ⬜ Not started — blocked on P2–P4 |
| P6 — Live semester rollover | The actual deadline event | ⬜ Not started — blocked on P5; exact date still unknown (PRD Open Question #1) |
| P7 — Robustness *(proposed, D-11)* | Run log, plain-language alerts, no duplicates, validation, guards (roadmap §6 R1–R9) | ⬜ Not started — needs D-11 confirmed; ships after P4 |
| P8 — PowerApp admin / control page *(proposed, D-11)* | Status screen, confirmations, settings editor, rollover checklist (A1–A7) | ⬜ Not started — needs D-11 and PowerApp edit access |
| P9 — Student form polish + small new flows *(proposed, D-11)* | U1–U3, N1–N4 | ⬜ Not started — needs D-11 |

Status vocabulary — use these exactly, and never round up:
- ⬜ **Not started**
- 🔶 **In progress** — say precisely what works and what doesn't
- ✅ **Done** — built *and* verified. If it compiles but was never run, it is not done.
- ⛔ **Blocked** — name the blocker and who/what unblocks it

---

## P1 — Design the fixes (current phase)

| Item | Approach | Status |
|---|---|---|
| Error-handling (issue 1), **reworked per flow** | Try/Catch scope → Teams alert with step, error and run link → Terminate Failed, via the shared `tools/fixes/trycatch.py` | 🔶 Original design ⛔ superseded (wrong premise). Rework built and sandbox-tested on flows 1, 3–10, 12, 13 and 14; flow 11 blocked on a fresh export; nothing applied live |
| Sandbox workflow (D-08, D-09) | `tools/build.py` baseline/fixed/prod packages with a production-ID guard; scripted runner `tools/sandbox/pw.py`; PreToolUse hook `sandbox_guard.py`; `guides/sandbox_runbook.md`; skill `flow-sandbox-tester` | ✅ Built and used on flows 1–10, 12, 13 and 14 (sandbox = the user's OneDrive site, fake data) |
| Path-based Excel lookup design (issue 2) | ⚠️ **Revised, not abandoned:** researched Microsoft's own docs — the Excel Online (Business) `Run script` action's file parameter does not support dynamic/runtime selection, so a full path-based rearchitecture isn't cleanly available on this connector. New direction: (a) keep D-03's in-place-edit rule primary, (b) add a "file identity guard" check that fails loudly instead of opaquely, (c) write a recovery runbook | 🔶 Researched; not yet drafted into a plan doc — see `guides/issues_backlog.md` item 2a |
| Deprecated-trigger replacement design (issue 3) | Replace "When a file is created in a folder (deprecated)" with **"When a file is created (properties only)"** + a `Get file content` action, for flows #2 and #14. Confirmed via Microsoft community docs as the standard migration path; noted behavior difference (new trigger also fires on subfolder files) still needs checking per flow | 🔶 Replacement trigger identified; per-flow downstream-impact mapping and plan doc not yet written |

---

## Verification ledger

What has actually been run, not what has been written. A row here needs a real command and a real result.

| Date | What was verified | How | Result |
|---|---|---|---|
| 2026-09-16 | All 14 flow `.zip` exports contain valid `manifest.json` + `definition.json` | `unzip -l` / `unzip -o -q` extraction into scratch, then read every file | Confirmed — see `guides/flow_inventory.md` for the extracted facts (triggers, connectors, deprecated-trigger usage, hard-coded IDs, missing failure handling) |
| 2026-09-16 | ~~No flow has a `Failed`-branch action anywhere~~ | `grep -c '["]Failed["]'` runAfter pattern across all 14 `definition.json` | ❌ **Result was wrong.** See the 2026-09-30 row below |
| 2026-09-30 | Failure branches per flow, re-counted | Python walk of every action's `runAfter` (incl. nested scopes) in all 14 `definition.json` | 12 flows have a Teams FAILED post (`runAfter` Failed/Skipped/TimedOut). Success Submit Email has only a `TimedOut` backup. Store Student List has only a `Set_variable` |
| 2026-09-30 | SharePoint `SP.Utilities.Utility.SendEmail` (flow 1's backup path) status | WebSearch → Microsoft Support + MC921752 | Retired 2025-10-31, so flow 1's backup is dead code |
| 2026-09-30 | Flow 1 packages build and the sandbox guard works | `python tools/build.py 1 prod/baseline/fixed` with a test config; checked unzipped output | prod built. Sandbox refused with no config, with a placeholder, and with the `kamalazreel` sender unmapped. Once mapped: 0 production IDs in the baseline/fixed definition and manifest; creation type `New`. **Not yet imported into Power Automate** |
| 2026-09-30 | Flow 1 baseline reproduces the silent failure (T1) | Imported `[SANDBOX-BASELINE]` as new, turned on, added a sandbox item with email `not-an-email`, read run history | Run **Failed** at `Send_an_email_(V2)`; the Compose/SharePoint backup skipped; no alert. Finding 1.1 is now **observed**, not just inferred |
| 2026-09-30 | Flow 1 fix works in the sandbox (T2–T4, T6) | Imported `[SANDBOX-FIXED]`, ran 5 items, opened each run and expanded the Catch scope | T2 Succeeded; T3/T4 Try failed → Catch ✓ (`Get item` ✓, Teams post ✓) → run Failed; T6 (no recipient) Catch failed as predicted, run Failed. **Teams chat content and email arrival not yet viewed by the user** |
| 2026-09-30 | Expired connection breaks import | First `[SANDBOX-FIXED]` import failed `Unauthorized` on Teams; Connections page showed *Reconnect*; after re-sign-in the import succeeded | Confirmed. Expired connections fail with `Unauthorized` until re-authorised |
| 2026-09-30 | Flow 2 trigger swap works (harness) | Imported `[SANDBOX-HARNESS]`, dropped 5 test items in the sandbox `Drop File` folder, read run history + listed the library | 4 runs, all Succeeded; copies = original size (incl. 3 MB, exactly one run); odd names preserved without `%20`; the folder produced no run; a subfolder file **did** fire (guard added, not yet re-tested) |
| 2026-09-30 | A handled failure leaves the run "Succeeded" (flow 3 baseline) | Imported `[SANDBOX-BASELINE]`, ran ok/rowfail/readfail, read run history + the supervisor list | All 3 runs **Succeeded** (banner "Your flow ran successfully" over a failed loop). Partial write: 1 of 2 rows written on rowfail |
| 2026-09-30 | Flow 3 fix in the sandbox | `[SANDBOX-FIXED]` v1 then v2, same scenarios | v1: readfail OK; rowfail **exposed a bug** (loop `outputs` is an array). v2: rowfail → Try failed → Catch ✓ → Terminate ✓ → run **Failed**; ok → Succeeded. **Teams alert wording not yet viewed** |
| 2026-09-30 | Flows 4, 5, 14 in the sandbox | Baseline + fixed copies, scenarios ok / failure, run history read | Baseline reports failed runs "Succeeded" (4, 5, 14), partial/duplicate writes (4, 14), fixed copies: Try → Catch → Terminate → run Failed. Flow 14: archive move does not re-trigger |
| 2026-10-01 – 02 | Flows 6, 7, 8, 9 in the sandbox | Same method (6 and 7 with Excel/script stubbed; 8 with a real "Item Not Found"; 9 with a malformed address) | Baseline "Succeeded" on failure in all four; fixed copies Failed with the failing step named |
| 2026-10-02 | Flow 10 with the scenario runner | `pw.py run 10 badaddr/readfail/ok` on baseline + fixed, per-iteration counts from the run | Baseline: Succeeded with 2 sent + 1 failed (duplicate student emailed twice, partial batch **observed**). Fixed: Failed naming `Send_an_email_(V2)`; `readfail` (failure before the loop) still alerts; ok Succeeded |
| 2026-10-02 | Wrapper change re-tested (nested Condition) | Flow 5 `ok`/`sendfail`, flow 10 above; flow 7 import | Pass. Flow 7 import failed `InvalidTemplate` on a Condition containing loops, so the wrapper now skips those. Flow 5 `ok` sends exactly 2 emails |
| 2026-10-02 | Tooling checks | `sandbox_guard.py --selftest`; a browser step naming `[LIVE-CDO]` through the live hook; `tools/docs.py check`; `pw.py alloff` | Self-test passed; hook blocked the step; checks ok; nothing on |
| 2026-10-02 | Flows 12 and 13 with the scenario runner (Excel, scripts, folder listing stubbed; matching logic, loops, SharePoint, email real) | `pw.py run 12|13 ok/twofiles/scriptfail/addfail` on baseline + fixed, `readfail` on fixed | Baselines report failed runs "Succeeded"; a failed row write leaves a partial write and no PIC email; 2 files in the folder → every row twice and 2 emails. Fixed: Failed naming `Run_script` / `Get_items` / (nested loops) `Apply_to_each_2`; ok runs give identical bucket counts to baseline (1/1/1), so the logic is untouched |
| 2026-10-02 | Flow 11's export | Compared flow ids and definition hashes of all 14 packages | Flow 11's file has the same flow id (`a66117f3…`) and a byte-identical definition to flow 4; only 13 distinct flows are exported |
| 2026-10-02 | Flows 12 and 13 with **real Excel Online** (generated workbooks in the sandbox OneDrive; Office Scripts stubbed) | `pw.py stage / import / run` for flows 12 and 13, `ok` and `excelfail`, baselinex and fixedx, template read back and rows counted | `ok`: both packages write Matched 2 / Partially 1 / Exactly Not Matched 1 and send the email with the real attachment. `excelfail`: baselinex Succeeded despite a failed `List rows` (false success reproduced with a real failure); fixedx Failed/Terminated naming `List_rows_present_in_a_table`. An unplanned stray file with other columns reproduced the same false success. Excel Online locks a touched workbook ~8 min |
| 2026-10-06 | Flows 3, 4 and 14 with **real Excel Online** (generated workbooks in the sandbox OneDrive) | `pw.py stage / import / run` for flows 3 and 4 (`ok`, `readfail`, `rowfail`), flow 14 `ok` (dropped file) on baselinex and fixedx | Flows 3 and 4: all six runs each as expected (baseline hides a missing workbook and a rejected row as "Succeeded", fixed reports Failed at the step). Flow 14: **`{Identifier}` works as the Excel file value**; 8 rows give 6 items, file archived, each run 6-7 minutes. Flow 14 wrong-table `readfail`: baseline fails silently, fixed alerts in 12 s. All sandbox flows Off |
| 2026-10-02 | Rollout tooling | `build.py 09|10 fixedprobe` imported and run in the sandbox; `compare_prod.py` on prod vs itself, probe vs prod, original export vs prod; a scan of all 12 probe packages for side-effecting actions outside the Try scope; `tools/testdata.py --check` against `flows/*.zip` | The probe fails first and the real send never ran on flows 9 and 10 (alerts posted, run Failed). `compare_prod`: identical / only the probe / the whole fix. Nothing with side effects outside Try (flow 14's archive loop runs only after Try succeeds). Generated workbooks contain every column flows 12, 13 and 14 read (7, 12, 14) |
| 2026-10-02 | Flow 2's subfolder guard as a live trigger condition (T-H4b) | `pw.py filetest 02 guard`: harness with the guard, one file in `Drop File`, one in `Drop File/Sub`, 150 s settle | Exactly 1 run; the direct file was copied and archived; the subfolder file was not processed |
| 2026-09-30 | Who exported the 14 packages | Read every `manifest.json` → `details` | All by `fakhrul_22012087@utp.edu.my`, 2026-09-09 |
| 2026-09-16 | 2 flows use the deprecated file-trigger | `grep -c 'deprecated'` across all 14 `definition.json` | Exactly 2 matches: Acknowledgement Letter Email Process, Store Student List into SharePoint List |
| 2026-09-16 | Every flow's Teams-post recipient is dynamic, not hard-coded | `grep` for `PostMessageToConversation` parameters across all 14 `definition.json`, then traced the preceding `Get_item` action's `table`/`id` | Confirmed: `@{outputs('Get_item')?['body/TeamsNotification1']}` (13 flows) / `TeamsNotification2` (Combine raw data), from a shared config item `id: 1`, table `be7f2b53-cc4e-42b1-a043-a7d6a849ba42` |
| 2026-09-16 | Recommended replacement for the deprecated SharePoint trigger | `WebSearch` against Microsoft/community docs | "When a file is created (properties only)" + a separate `Get file content` action if file content is needed downstream |
| 2026-09-16 | Excel Online `Run script` action does not support a dynamic/runtime file parameter | `WebSearch` against Microsoft Learn + Power Platform community threads | Confirmed limitation — file must be picked via Studio's file browser at design time; revises the issue-2 fix direction (see P1 table above) |

---

## Known gaps

- **Full issues backlog now tracked in `guides/issues_backlog.md`** — 12 items, working one at a time per user instruction. Items 1–5 confirmed and root-caused; items 6–9 need user confirmation before they're plannable; items 10–12 need a quick Studio check.
- **No fixes applied yet.** The live system is unchanged. Flows 1, 3–10, 12, 13 and 14 have sandbox-tested fix packages ready (see OFFICE-CHECKLIST.md).
- **P3's design work (path-based Excel lookup, trigger replacement) has no plan/execution doc yet** — only P2 (observability) does. Write P3's pair before the second office-laptop session.
- **The PowerApp is unread.** Found 2026-10-02 (read-only app list + Details page): `SIIP Report Duty Form` (canvas, owner Kamal Azreel, created 2024-01-28, last modified 2024-06-08) and `IPBAS` (also Kamal's) are visible to the personal account, but only to run: **Edit and Export package are greyed out**, and the Flows/Connections tabs show nothing for it (inconclusive for a viewer). So which button calls which flow, with what inputs, and how the app reacts to a flow that now ends Failed are all unverified. Needs an export from the owner (MANUAL-TODO C); the rollout's pilot observes the failure behaviour live.
- **No automated test suite is possible for this stack.** Power Automate flows are verified by running them in Power Automate Studio and checking run history — there is no CI. `refdocs/guides/checklist.md` reflects this.
- **Exact rollover deadline date unknown** (PRD Open Question #1) — P2–P6 sequencing is a best-effort order, not date-scheduled, until this is confirmed.
- **3 unresolved `ASSUMED:` items from the flow inventory** (publish status of one flow, a name mismatch on another, the Standard Approvals step) — see PRD §8, items 2–4.
