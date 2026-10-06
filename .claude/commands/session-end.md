---
description: Close out the session — changelog entry, STATUS update, ADRs, doc reconciliation
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

Close out this session per CLAUDE.md's mandatory rules. Do not skip a step because the session felt small.

1. `git status` and `git diff` — establish what actually changed. Don't rely on memory of the conversation. If any flow `.zip` in `flows/` changed, that's a live edit — confirm it was actually test-run in Power Automate Studio, not just re-exported.
2. Add an entry to `refdocs/changelog/CHANGELOG.md` in that file's documented format (newest first). The **Verified** line names what was actually run (a Studio test run + run history check, or a `grep`/`unzip` analysis command) and its actual result; if nothing was run this session, write "nothing verified this session" rather than implying otherwise.
3. Update `refdocs/STATUS.md`: the phase table, and the verification ledger if anything was genuinely verified. Status never rounds up — a flow edited but never test-run is 🔶, not ✅.
4. Any architectural decision made this session → an ADR in `refdocs/changelog/DECISIONS.md`, with an id matching the PRD's decision log. Any `ASSUMED:` that got resolved gets promoted or deleted.
5. If the work diverged from its execution doc, edit that doc to match reality and note it in the changelog's Deviations line.
6. Update the index tables in `refdocs/plans/README.md` and `refdocs/execution/README.md` if a doc was added or changed status. If any drive-item ID, folder path, or connection owner changed, update `refdocs/guides/env_setup.md` now. If any flow's trigger/connectors/purpose changed, update `refdocs/guides/flow_inventory.md` now.

Then show me the changelog entry you wrote, and list anything you couldn't resolve.
